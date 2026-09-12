"""The agent under test, wrapped as a ``weave.Model``.

``predict`` runs one task through the faulty tool layer and returns the
task's output envelope: ``result``, ``error`` (``{message, cause}`` or
``None``), the call counts, the suite hash, and ``applied`` — the ids of the
records in context the agent applied on this task, which the close turns into
use-time dispositions.

Two policies, one output shape:

- ``model`` — the frozen model in a tool-calling loop, conditioned on the
  constitution and the consultation plan the boot assembled;
- ``stub`` — a scripted policy, used when no inference endpoint is
  configured. It reads the same records the model would and applies them by
  keyword: a record whose payload says *retry* retries a transient failure
  once, *cause* carries the cause on the error, *batch* batches budgeted
  shell calls. Its scores are a harness for the loop's mechanics, not
  evidence of a model learning.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

import weave
from pydantic import PrivateAttr

from hgi import model as _model
from hgi import tracing
from suite.tasks import BY_ID, suite_hash
from suite.tools import ToolError, Tools

MAX_TURNS = 8


def _envelope(task: str, tools: Tools, *, result: Any = None, error: dict | None = None, applied: list[str] | None = None) -> dict[str, Any]:
    return {"task": task, "result": result, "error": error, "tool_calls": tools.total_calls, "shell_calls": tools.calls["shell"],
            "tool_errors": list(tools.errors), "suite_hash": suite_hash(), "applied": sorted(set(applied or [])),
            "call": tracing.current_call_uri()}


class Agent(weave.Model):
    session: str | None = None
    pass_: int = 0
    attached: bool = True
    records: list[dict[str, Any]] = []
    """The records in context: ``{id, decision, terms, scopes, stakes}`` per consulted decision."""
    articles: list[str] = []
    policy: str = "stub"
    _outputs: list[dict[str, Any]] = PrivateAttr(default_factory=list)

    @property
    def outputs(self) -> list[dict[str, Any]]:
        return self._outputs

    @weave.op
    def predict(self, task: str, prompt: str, schema: dict, shell_budget: int | None, http: bool) -> dict[str, Any]:
        spec = BY_ID[task]
        workdir = Path(tempfile.mkdtemp(prefix=f"hgi-{task}-"))
        spec.setup(workdir)
        tools = Tools(pass_=self.pass_, task=task, workdir=workdir, shell_budget=shell_budget)
        with tracing.attributes(session=self.session, pass_=self.pass_, role="pass", records_in_context=[r["id"] for r in self.records]):
            out = self._stub(spec.id, prompt, tools) if self.policy == "stub" else self._model(spec.id, prompt, schema, tools)
        self._outputs.append(out)
        return out

    # --- the scripted policy ---------------------------------------------------------
    def _flags(self) -> dict[str, list[str]]:
        """Which records license which behaviours, by keyword in the payload."""
        flags: dict[str, list[str]] = {"retry": [], "cause": [], "batch": []}
        for r in self.records:
            text = r["decision"].lower()
            if re.search(r"\bretr", text):
                flags["retry"].append(r["id"])
            if "cause" in text:
                flags["cause"].append(r["id"])
            if re.search(r"\b(batch|one call|single call)", text):
                flags["batch"].append(r["id"])
        return flags

    def _stub(self, task: str, prompt: str, tools: Tools) -> dict[str, Any]:
        flags = self._flags()
        applied: list[str] = []

        def fail(e: ToolError) -> dict[str, Any]:
            if flags["cause"]:
                applied.extend(flags["cause"])
            return _envelope(task, tools, error={"message": str(e), "cause": e.cause if flags["cause"] else None}, applied=applied)

        def get(path: str) -> Any:
            try:
                return tools.http_get(path)
            except ToolError as e:
                if e.transient and flags["retry"]:
                    applied.extend(flags["retry"])
                    return tools.http_get(path)
                raise

        try:
            if task == "sum_numbers":
                return _envelope(task, tools, result=sum(get("/numbers")), applied=applied)
            if task == "fetch_user_name":
                return _envelope(task, tools, result=get("/users/7")["name"], applied=applied)
            if task == "status_ok":
                return _envelope(task, tools, result="ok" if get("/status")["ok"] else "not ok", applied=applied)
            if task == "count_lines":
                names = [f"{c}.txt" for c in "abcde"]
                if flags["batch"]:
                    applied.extend(flags["batch"])
                    out = tools.shell("wc -l " + " ".join(names))
                    total = int(out.strip().splitlines()[-1].split()[0])
                else:
                    total = sum(int(tools.shell(f"wc -l {n}").split()[0]) for n in names)
                return _envelope(task, tools, result=total, applied=applied)
            if task == "write_report":
                config = json.loads(tools.read_file("config.json"))
                report = {"title": config["title"], "count": len(config["items"])}
                tools.write_file("report.json", json.dumps(report))
                return _envelope(task, tools, result=report, applied=applied)
            if task == "schema_answer":
                return _envelope(task, tools, result={"answer": 42, "unit": "n"}, applied=applied)
            return _envelope(task, tools, error={"message": f"unknown task {task}", "cause": None}, applied=applied)
        except ToolError as e:
            return fail(e)

    # --- the frozen model in a tool loop ------------------------------------------------
    def _model(self, task: str, prompt: str, schema: dict, tools: Tools) -> dict[str, Any]:
        from hgi.roles import prompt as role_prompt

        context = "\n".join(f"- {a}" for a in self.articles)
        plan = "\n".join(f"- {r['id']} [{', '.join(r['terms'])}] stakes: {r['stakes']}\n  {r['decision']}" for r in self.records) or "- (none)"
        system = (role_prompt("pass") + "\n\n## Constitution\n" + context + "\n\n## Consultation plan — records in context, each owed `apply`\n" + plan +
                  "\n\nFinish by replying with one JSON object: {\"result\": <per schema>, \"error\": null | {\"message\": str, \"cause\": str}, "
                  "\"applied\": [record ids you applied]}. A failed task's error names its root cause.")
        messages: list[dict[str, Any]] = [{"role": "system", "content": system},
                                          {"role": "user", "content": f"Task {task}: {prompt}\nOutput schema: {json.dumps(schema)}"}]
        for _ in range(MAX_TURNS):
            reply, _ = _model.chat_with_tools("pass", messages, Tools.SCHEMA, session=self.session, pass_=self.pass_,
                                              records_in_context=[r["id"] for r in self.records])
            if reply["tool_calls"]:
                messages.append({"role": "assistant", "content": reply["content"] or None,
                                 "tool_calls": [{"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}} for tc in reply["tool_calls"]]})
                for tc in reply["tool_calls"]:
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": tools.dispatch(tc["name"], tc["arguments"])})
                continue
            try:
                final = _model.Completion(reply["content"], _model.model_id(), None).json()
            except (ValueError, json.JSONDecodeError):
                return _envelope(task, tools, error={"message": "final reply was not JSON", "cause": None})
            return _envelope(task, tools, result=final.get("result"), error=final.get("error"), applied=final.get("applied") or [])
        return _envelope(task, tools, error={"message": "turn limit reached", "cause": f"{MAX_TURNS} turns without a final answer"})

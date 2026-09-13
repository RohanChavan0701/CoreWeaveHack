"""The agent under test, wrapped as a ``weave.Model``.

``predict`` runs one task through the faulty tool layer and returns the
task's output envelope: ``result``, ``error`` (``{message, cause}`` or
``None``), the call counts, the working directory, the suite hash, and
``applied`` — the ids of the records in context the agent applied on this
task, which the close turns into use-time dispositions — and the shape of
the work: ``commands``, every shell command issued, and ``turns``, the
model turns the task took (a scripted policy counts one turn per tool call
and one to answer). The oracle adds each row's ``scores`` after the run.

Two policies, one output shape:

- ``model`` — the frozen model in a tool-calling loop, conditioned on the
  constitution and the consultation plan the boot assembled;
- ``stub`` — the task's scripted policy (:class:`suite.tasks.Task.stub`),
  used when no inference endpoint is configured. It reads the same records
  the model would and applies them by keyword through :class:`Script`: a
  record whose payload says *retry* retries a transient failure once,
  *cause* carries the cause on the error, *batch* batches budgeted shell
  calls. Its scores are a harness for the loop's mechanics, not evidence of
  a model learning; a task with no scripted policy fails on the stub.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any

import weave
from pydantic import PrivateAttr

import suite as _suite
from hgi import model as _model
from hgi import tracing
from suite.tools import ToolError, Tools

MAX_TURNS = 8


def _envelope(task: str, tools: Tools, *, result: Any = None, error: dict | None = None, applied: list[str] | None = None,
              turns: int | None = None) -> dict[str, Any]:
    return {"task": task, "result": result, "error": error, "tool_calls": tools.total_calls, "shell_calls": tools.calls["shell"],
            "http_calls": tools.calls["http"], "tool_errors": list(tools.errors), "commands": list(tools.commands),
            "turns": tools.total_calls + 1 if turns is None else turns, "workdir": str(tools.workdir),
            "suite_hash": _suite.current().hash, "applied": sorted(set(applied or [])), "call": tracing.current_call_uri()}


class Script:
    """What a scripted policy may do: the tools, with the records in context applied by keyword."""

    def __init__(self, tools: Tools, records: list[dict[str, Any]]):
        self.tools = tools
        self.flags: dict[str, list[str]] = {"retry": [], "cause": [], "batch": []}
        for r in records:
            text = r["decision"].lower()
            if re.search(r"\bretr", text):
                self.flags["retry"].append(r["id"])
            if "cause" in text:
                self.flags["cause"].append(r["id"])
            if re.search(r"\b(batch|one call|single call)", text):
                self.flags["batch"].append(r["id"])
        self.applied: list[str] = []

    def get(self, path: str) -> Any:
        """An HTTP GET, retried once on a transient failure when a record in context licenses the retry."""
        try:
            return self.tools.http_get(path)
        except ToolError as e:
            if e.transient and self.flags["retry"]:
                self.applied.extend(self.flags["retry"])
                return self.tools.http_get(path)
            raise

    def shell(self, command: str) -> str:
        return self.tools.shell(command)

    def read(self, name: str) -> str:
        return self.tools.read_file(name)

    def write(self, name: str, content: str) -> str:
        return self.tools.write_file(name, content)

    @property
    def batch(self) -> bool:
        """Whether a record in context licenses batching independent calls; asking counts as applying it."""
        if self.flags["batch"]:
            self.applied.extend(self.flags["batch"])
            return True
        return False

    def fail(self, e: ToolError) -> dict | None:
        """The error a scripted policy reports: with the cause when a record in context licenses carrying it."""
        if self.flags["cause"]:
            self.applied.extend(self.flags["cause"])
        return {"message": str(e), "cause": e.cause if self.flags["cause"] else None}


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
    def predict(self, task: str, prompt: str, schema: dict, shell_budget: int | None, http_budget: int | None, http: bool) -> dict[str, Any]:
        spec = _suite.current().by_id[task]
        workdir = Path(tempfile.mkdtemp(prefix="hgi-" + task.replace("/", "-") + "-"))
        spec.setup(workdir)
        tools = Tools(task=task, workdir=workdir, profile=_suite.current().faults, routes=spec.routes,
                      shell_budget=shell_budget, http_budget=http_budget)
        with tracing.attributes(session=self.session, pass_=self.pass_, role="pass", records_in_context=[r["id"] for r in self.records]):
            out = self._stub(spec, tools) if self.policy == "stub" else self._model(spec.id, prompt, schema, tools)
        self._outputs.append(out)
        return out

    # --- the scripted policy ---------------------------------------------------------
    def _stub(self, spec, tools: Tools) -> dict[str, Any]:
        if spec.stub is None:
            return _envelope(spec.id, tools, error={"message": f"no scripted policy for {spec.id}", "cause": None})
        script = Script(tools, self.records)
        try:
            result = spec.stub(script)
        except ToolError as e:
            return _envelope(spec.id, tools, error=script.fail(e), applied=script.applied)
        except Exception as e:  # a naive policy tripping over the world is the world's fault to report
            return _envelope(spec.id, tools, error={"message": f"{type(e).__name__}: {e}"[:200], "cause": None}, applied=script.applied)
        return _envelope(spec.id, tools, result=result, applied=script.applied)

    # --- the frozen model in a tool loop ------------------------------------------------
    def _model(self, task: str, prompt: str, schema: dict, tools: Tools) -> dict[str, Any]:
        from hgi.roles import prompt as role_prompt

        context = "\n".join(f"- {a}" for a in self.articles)
        plan = "\n".join(f"- {r['id']} [{', '.join(r['terms'])}] stakes: {r['stakes']}\n  {r['decision']}" for r in self.records) or "- (none)"
        system = (role_prompt("pass") + "\n\n## Constitution\n" + context + "\n\n## Consultation plan — records in context, each owed `apply`\n" + plan +
                  "\n\nFinish by replying with one JSON object: {\"result\": ..., \"error\": null | {\"message\": str, \"cause\": str}, "
                  "\"applied\": [record ids you applied]}. The output schema describes that whole object: `result` is the value its `result` "
                  "property describes, never wrapped again. A failed task's error names its root cause; a tool failure you recovered from is not an error.")
        budgets = "; ".join(f"{k} calls: {v}" for k, v in tools.budgets.items())
        user = f"Task {task}: {prompt}\nOutput schema: {json.dumps(schema)}" + (f"\nBudgets — {budgets}" if budgets else "")
        messages: list[dict[str, Any]] = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        for turn in range(1, MAX_TURNS + 1):
            try:
                reply, _ = _model.chat_with_tools("pass", messages, Tools.SCHEMA, session=self.session, pass_=self.pass_,
                                                  records_in_context=[r["id"] for r in self.records])
            except Exception as e:  # the endpoint failed the turn: the row fails with the cause, and is scored, not dropped
                return _envelope(task, tools, error={"message": "model call failed", "cause": f"endpoint {type(e).__name__}: {str(e)[:200]}"}, turns=turn)
            if reply["tool_calls"]:
                messages.append({"role": "assistant", "content": reply["content"] or None,
                                 "tool_calls": [{"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}} for tc in reply["tool_calls"]]})
                for tc in reply["tool_calls"]:
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": tools.dispatch(tc["name"], tc["arguments"])})
                continue
            try:
                final = _model.Completion(reply["content"], _model.model_id(), None).json()
            except (ValueError, json.JSONDecodeError):
                return _envelope(task, tools, error={"message": "final reply was not JSON", "cause": None}, turns=turn)
            if not isinstance(final, dict):
                return _envelope(task, tools, error={"message": "final reply was not a JSON object", "cause": None}, turns=turn)
            in_context = {r["id"] for r in self.records}
            applied = [a for a in (final.get("applied") or []) if isinstance(a, str) and a in in_context]  # a record not in context cannot have been applied
            return _envelope(task, tools, result=final.get("result"), error=final.get("error"), applied=applied, turns=turn)
        return _envelope(task, tools, error={"message": "turn limit reached", "cause": f"{MAX_TURNS} turns without a final answer"}, turns=MAX_TURNS)

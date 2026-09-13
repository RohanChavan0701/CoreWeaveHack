---
name: consult-decisions
description: >-
  Consult an HGI decision store for the problem at hand, from outside the
  loop. Runs `hgi consult` to read the store's activation surface (hook
  prose, registered work-shape terms, exclusions, stakes), latches on the
  terms the work names or on the problem in prose, and projects the payload
  of what latched into context. Use when working in a project that carries
  an HGI store (`store/`, `$HGI_STORE`, or an experiment arm under
  `runs/<experiment>/<arm>/store`) and about to do work the store may
  already have settled — a tool layer, an HTTP or shell call, a call budget,
  error handling, a retry, an output schema, a plan. Read-only: it files no
  observation and no disposition; the loop's ledgers stay the loop's.
---

# consult-decisions — the store read from outside the loop

The decision store is an associative memory, not a checklist: a record is
recalled by the shape of the work, then read. Inside the loop, the boot does
this with a model classifier, the hook-major index and a guard evaluator.
Outside it, you are the classifier and the guard, and `hgi consult` is the
index and the projection. This skill carries the procedure and the
invocation; it never restates a record — the store is the only copy.

## How to invoke

```
uv run hgi consult                                   # stage one: the surface of every decision
uv run hgi consult --terms http-tool,tool-budget     # latch on registered terms; project what fires
uv run hgi consult --problem "<the work, in prose>"  # infer terms, nominate by hook prose; project
uv run hgi consult D-0003 D-0006                     # stage two: the payload of the named records
uv run hgi consult --all                             # every accepted record's payload
uv run hgi consult --articles …                      # add the constitution to any of the above
uv run hgi consult --json …                          # the structure instead of the rendering
```

`--store <root>` on either side of the subcommand names a store other than
`./store` or `$HGI_STORE` — an experiment arm is
`--store runs/<experiment>/<arm>/store`.

## The reading procedure

1. **Scan the surface.** Run `hgi consult` bare. Per accepted decision it
   prints the hook prose (`latch`), the registered terms its consultation
   latch keys on, the exclusions (`not_this`), the stakes (the failure the
   record prevents), its scopes and its watch. A superseded record is a
   tombstone pointing at its successor. The decision sentence is not here
   by construction: a cell you could comply with without opening the
   record is an authority leak, and the projection withholds it.
2. **Latch.** Match the surface against the work-nouns you hold — the tools
   you are about to call, the failure you are handling, the budget you are
   under. When the work names registered terms, route them mechanically:
   `--terms <term,…>` is the boot's own exact route through the hook-major
   index, and an unregistered term is refused with the registry listed.
   When it does not, `--problem "<the work>"` infers the terms the prose
   names and nominates by stemmed overlap with hook prose; a nomination is
   marked as such, because no guard ran. Nothing latched prints the surface
   again for your own match — a miss is a structural zero, invisible until a
   defect pays for it, so bias broad and recover precision through the
   exclusions.
3. **Project.** What latched is projected in full: the decision sentence,
   the counterfactual (the overshoot the record does *not* license), the
   exclusions, the premises with their status and falsifiers, the residue
   the floor does not check, the anchors, the lineage. Records printed as
   `co-applying` share a hook with no lineage edge between them: apply each
   where it bears; never rank one over the other.
4. **Apply, or dispose honestly.** A record bears when its hook fits and no
   exclusion covers the work. A `disputed` or `reversed` premise, an
   `unwatched` watch, or a counterfactual that names your case is a reason
   to open the record itself — `store/decisions/D-nnnn.json` — before
   leaning on it. The projection is what you carry into context; the record
   is the authority.
5. **Report provenance.** State which records you consulted and what you
   did with each: `consulted: D-0003 (applied on the retry wrapper), D-0002
   (not applicable: the calls are dependent)`. A "none" names what was
   scanned — `none (surface scanned, 4 records)` — since a bare "none" is
   the skip wearing a disposition's costume.

## What it never does

The command writes nothing: no session, no disposition, no observation, no
commit, and the projections under `index/` are read, never regenerated. A
lesson you learn while consulting belongs to the loop's own passes, filed
through `hgi close`, not to this read.

## Residue

The surface is authored judgment and the index is a projection of it: a
hook keyed on the wrong vocabulary reaches nothing, and the lexical route
nominates on two shared tokens, which is a floor, not a match. Whether a
record bears on the work is yours to decide; the command shows the
exclusions and the counterfactual so that the decision is made against the
record's own boundary rather than its sentence alone.

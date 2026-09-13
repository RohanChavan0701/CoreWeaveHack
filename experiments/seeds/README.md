# Seed stores

A seed is what a mature decision store for one world would hold: one
admitted decision per convention the world turns on, keyed on the registered
work-shape terms the world's tasks present, so the boot's consultation reaches
it on pass 1. Each world's seed sits under `experiments/seeds/<world>/`
with a `README.md` saying what a mature store looks like for that world and
`decisions/D-nnnn.json` in the store's own record shape; `AUTHORING.md` is
the rule a seed follows.

| seed | world | experiments it seeds |
|---|---|---|
| `conventions` | the seven lessons of the hand-written families and their generated clothes (`genesis`, `conventions`, `transfer`, `curriculum`) | `stream`, `transfer`, `world` (with `world`), and by hand `baseline`, `cadence`, `model-sweep`, `economy` |
| `world` | the recurring shapes of `mbpp`, `tables` and `api` beyond the lessons | `world` (with `conventions`) |
| `incidents` | the three decoy shapes of the incident bundles | `incidents` |
| `reasoning-core` | the produce-and-verify method on regexes and grammars | `reasoning-core` |
| `text2sql` | the schema and dialect of the pinned BIRD `financial` database | `text2sql` |

## The compare/contrast

An arm with `seed = "<world>"` (or a list, injected in order) starts from
the seed instead of the empty genesis store; everything else — the deal, the
batches, the model, the cadence — is the arm it twins. Three arms on the
same batches make the reading:

- **detached** — the actor alone, no store: the first-sight floor.
- **attached** — the loop from an empty store: what the loop learns on its own, and how fast.
- **seeded** — the loop from the mature store: what the loop would buy if it had already learned the world.

The gap seeded − detached on batch 1 is the value of the decisions
themselves; the gap seeded − attached over the stream is the cost of having
to learn them; the strict pools (`*-strict-seeded` against `*-strict`) ask
the knowledge-base question directly — whether the injected record saves the
discovery call the budget does not hold. The seeded arm still closes and
consolidates, so its store can grow past the seed, retire a seed decision
the world contradicts, or supersede one; `arm.json` carries the seed
manifest and every injected record keeps `admission.proposed_by = "seed"`,
so the evolution log tells an injected decision from an admitted one.

```bash
uv run hgi experiment run experiments/text2sql.toml --arm 120b-detached --arm 120b-attached --arm 120b-seeded
```

`hgi seed <world> --store <root>` injects by hand into any store; `hgi consult
--store <root> --terms shell-tool,tool-budget` shows what a boot with those
terms would reach.

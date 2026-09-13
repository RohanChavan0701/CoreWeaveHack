# Convention shaping — the coder's shape at the source, tool-major vs convention-major

Decision 77's sweep found no grouping radius could buy precision, because the blind coder shaped each observation on the *tool* it called, and one tool-major term covers many lessons. This is the same labeled set coded two ways and swept: the pre-fix shaping (tool-major cues only) beside the shipped shaping (the convention the noticing names). The τ=1.0 row — today's exact-match grouping, which the sweep left in place (τ\*=1.0 stands) — is the one that matters: the fix is meant to make *exact match* pure, not to lean on a wider radius.

- Synthetic labeled set in the blind close's voice: N=20 noticings over 3 sessions and 7 lessons (bom, csv-quoted, footer-row, moved-v2, paged-api, token-route, trailing-newline); the independence bar is 2 distinct sessions.
- Coded through the real stub coder (`hgi.stub`), a lexical proxy for the model's convention inference.
- **Pending confirmation:** a live re-score of freshly coded observations on `openai/gpt-oss-120b` (`WANDB_ENTITY` + a weave project), not run here — the stub shows the mechanism, the endpoint confirms it.

## At τ=1.0 (exact-match grouping — the shipped radius)

| shaping | homogeneity | cross_lesson_clusters | lessons_at_bar | clusters |
|---|---|---|---|---|
| tool-major (pre-fix) | 0.367 | 2 | 1 | 4 |
| convention-major (shipped) | 1.000 | 0 | 7 | 7 |

Lessons reaching the bar inside a pure cluster under convention shaping: bom, csv-quoted, footer-row, moved-v2, paged-api, token-route, trailing-newline.

## Reading

Under the tool-major shaping the τ=1.0 row is impure — homogeneity 0.367, 2 cross-lesson cluster(s), and only 1 lesson(s) reaching the bar inside a pure cluster — reproducing the sweep's finding that even exact match conflates lessons when the shape is the tool. Under the convention-major shaping the same exact-match grouping is pure: homogeneity 1.000, 0 cross-lesson clusters, and 7 of 7 lessons reaching the bar inside their own cluster. The lever was the coding, exactly as decision 77 read it; the grouping radius did not move.

## The distinct shapes each shaping produced

**Tool-major:** `error-wrapping`; `file-tool`; `other(unclassified)`; `shell-tool`.

**Convention-major:** `byte-order-mark`; `field-quoted`; `line-unterminated`; `listing-paged`; `route-guarded`; `route-versioned`; `summary-row`.

## Secondary check: the recorded runs, re-coded

The recorded arms under `/Users/slavazinevich/GenDev/CoreWeaveHack/runs/stream` — the sweep's original dataset, 118 labeled observations over 6 lessons — re-coded through the current coder both ways. These runs predate decision 81's noticing brief, so their noticings are noisier than the blind close now writes; still the stub proxy, not a live re-score.

| shaping | homogeneity | cross_lesson_clusters | lessons_at_bar | clusters |
|---|---|---|---|---|
| tool-major (as the runs shaped) | 0.479 | 10 | 1 | 20 |
| convention-major (re-coded) | 0.958 | 2 | 5 | 16 |

The tool-major re-coding reproduces the sweep's original reading (homogeneity 0.479, near the recorded 0.45, with 10 cross-lesson clusters); the convention re-coding lifts homogeneity to 0.958 and brings 5 lesson(s) to the bar on the same noticings. The residue — homogeneity short of 1.0 and two clusters still crossing — is the pre-81 noticings' noise, the gap a live re-score over freshly coded observations would close.


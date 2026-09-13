# Shape radius — the Jaccard grouping threshold, from evidence

The blind coder's shape groups observations into recurrences; a group at the independence bar (2 distinct sessions) can be admitted. Exact match (τ=1.0) splits one lesson across near-shapes; a wider Jaccard radius merges them, at the risk of merging distinct lessons. This is the τ-curve over the recorded runs, scored against the curriculum's declared lesson as the true label.

**Recommended τ\* = 1.0.** no τ keeps every cluster within one lesson — the blind coder's shape vocabulary already gives two lessons the same shape, so exact match itself conflates them; τ=1.0 is named as the baseline, and widening the radius cannot recover a precision the join never had. Fix the coding, not the radius.

## Dataset

- Source: recorded runs under `/Users/slavazinevich/GenDev/CoreWeaveHack/runs/stream` (attached arms; not freshly generated).
- Arms: 120b-attached, 120b-strict, 20b-attached.
- N = 104 labeled observations over 27 distinct sessions and 6 lessons.
- Per arm (kept / observations; dropped for no-shape, no-label):
  - `120b-attached`: 38/43 (no-shape 5, no-label 0).
  - `120b-strict`: 44/52 (no-shape 8, no-label 0).
  - `20b-attached`: 22/26 (no-shape 4, no-label 0).

## The curve

`lessons_at_bar` is the lessons that reach the bar inside one pure (single-lesson) cluster — the win. `cross_lesson_clusters` is the clusters spanning two or more lessons — the precision cost. Homogeneity is 1.0 exactly when there is no cross-lesson cluster.

| τ | homogeneity | completeness | V-measure | ARI | clusters | lessons_at_bar | cross_lesson_clusters |
|---|---|---|---|---|---|---|---|
| 1.0 ✓ | 0.449 | 0.389 | 0.417 | 0.196 | 12 | 0 | 9 |
| 0.67 | 0.449 | 0.389 | 0.417 | 0.196 | 12 | 0 | 9 |
| 0.5 | 0.088 | 0.276 | 0.133 | 0.008 | 3 | 0 | 3 |
| 0.33 | 0.088 | 0.276 | 0.133 | 0.008 | 3 | 0 | 3 |
| 0.25 | 0.088 | 0.276 | 0.133 | 0.008 | 3 | 0 | 3 |
| ~0 | 0.000 | 1.000 | 0.000 | 0.000 | 1 | 0 | 1 |

## Reading

τ=1.0 reproduces today's exact-match grouping. The recommendation is the *lowest* τ (widest radius) at which `cross_lesson_clusters == 0`, maximizing `lessons_at_bar` — a hard constraint rather than the argmax of a soft metric, because on thin data the soft optimum is unreliable and merging two distinct lessons is the dangerous failure. The counts are a floor from the recorded runs; a wider labeled set would sharpen the curve.


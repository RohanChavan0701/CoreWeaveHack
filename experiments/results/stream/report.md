# stream — first-sight performance on unseen tasks as the store grows, attached against detached, per lesson

| arm | model | mode | rounds×size | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | p11 | p12 | admitted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 120b-attached | openai/gpt-oss-120b | attached | 5×2 stream ×8 | 0.25 | 0.50 | 0.38 | 0.38 | 0.25 | 0.62 | 0.50 | 0.62 | 0.50 | 0.62 | 0.62 | 0.62 | D-0001 |
| 120b-detached | openai/gpt-oss-120b | detached | 5×2 stream ×8 | 0.62 | 0.75 | 0.38 | 0.50 | 0.38 | 0.50 | 0.38 | 0.62 | 0.50 | 0.75 |  |  | nothing |
| 20b-attached | openai/gpt-oss-20b | attached | 5×2 stream ×8 | 0.62 | 0.38 | 0.62 | 0.75 | 0.50 | 0.75 | 0.50 | 0.50 | 0.50 | 0.62 | 0.75 | 0.50 | D-0001 D-0002 D-0003 |
| 120b-strict | openai/gpt-oss-120b | attached | 5×2 stream ×8 | 0.38 | 0.25 | 0.50 | 0.25 | 0.25 | 0.38 | 0.38 | 0.38 | 0.25 | 0.38 | 0.12 | 0.25 | D-0001 D-0002 D-0003 D-0004 D-0005 D-0006 |
| 120b-strict-detached | openai/gpt-oss-120b | detached | 5×2 stream ×8 | 0.25 | 0.38 | 0.25 | 0.25 | 0.25 | 0.38 | 0.25 | 0.25 | 0.50 | 0.50 |  |  | nothing |

# text2sql — first-sight text-to-SQL on unseen BIRD questions over one schema as the store grows, a strong teacher over the actor

| arm | model | mode | rounds×size | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | admitted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 120b-attached | openai/gpt-oss-120b +deepseek-ai/DeepSeek-V4-Pro | attached | 4×2 stream ×2 | 0.50 | 0.50 | 0.00 | 0.00 | 0.50 | 1.00 | 0.00 | 0.50 | 0.50 | 0.00 | D-0001 D-0002 D-0003 D-0004 D-0005 D-0006 D-0007 |
| 120b-detached | openai/gpt-oss-120b +deepseek-ai/DeepSeek-V4-Pro | detached | 4×2 stream ×2 | 0.50 | 0.50 | 0.00 | 0.00 | 0.50 | 1.00 | 0.00 | 0.00 |  |  | nothing |
| 20b-attached | openai/gpt-oss-20b +deepseek-ai/DeepSeek-V4-Pro | attached | 4×2 stream ×2 | 1.00 | 0.00 | 0.00 | 0.50 | 0.50 | 1.00 | 0.00 | 0.00 | 1.00 | 0.00 | D-0001 D-0002 D-0003 |
| 120b-strict | openai/gpt-oss-120b +deepseek-ai/DeepSeek-V4-Pro | attached | 5×1 stream ×2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.50 | 1.00 | 0.00 |  |  |  | D-0001 D-0002 |
| 120b-strict-detached | openai/gpt-oss-120b +deepseek-ai/DeepSeek-V4-Pro | detached | 5×1 stream ×2 | 0.50 | 0.00 | 0.00 | 0.00 | 0.50 |  |  |  |  |  | nothing |
| 120b-seeded | openai/gpt-oss-120b +deepseek-ai/DeepSeek-V4-Pro | attached | 4×2 stream ×2 | — | — | — | — | — | — | — | — | — | — | not run |
| 120b-strict-seeded | openai/gpt-oss-120b +deepseek-ai/DeepSeek-V4-Pro | attached | 5×1 stream ×2 | — | — | — | — | — | — | — |  |  |  | not run |

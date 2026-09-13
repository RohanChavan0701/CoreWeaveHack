# reasoning-core — first-sight produce-and-verify on unseen regexes and grammars as the store grows, a strong teacher over a mid-sized actor

| arm | model | mode | rounds×size | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | admitted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen-attached | Qwen/Qwen3.6-35B-A3B +deepseek-ai/DeepSeek-V4-Pro | attached | 3×2 stream ×4 | 0.75 | 1.00 | 1.00 | 0.50 | 0.75 | 0.75 | 1.00 | 0.50 | D-0001 D-0002 D-0003 D-0004 D-0005 |
| qwen-detached | Qwen/Qwen3.6-35B-A3B +deepseek-ai/DeepSeek-V4-Pro | detached | 3×2 stream ×4 | 0.75 | 1.00 | 1.00 | 0.75 | 0.75 | 1.00 |  |  | nothing |
| 20b-attached | openai/gpt-oss-20b +deepseek-ai/DeepSeek-V4-Pro | attached | 3×2 stream ×4 | 0.75 | 0.50 | 1.00 | 0.50 | 0.75 | 1.00 | 1.00 | 0.50 | D-0001 D-0002 |
| qwen-strict | Qwen/Qwen3.6-35B-A3B +deepseek-ai/DeepSeek-V4-Pro | attached | 3×2 stream ×4 | 0.75 | 1.00 | 0.75 | 1.00 | 1.00 | 0.75 | 1.00 | 1.00 | D-0001 D-0002 D-0003 D-0004 |
| qwen-strict-detached | Qwen/Qwen3.6-35B-A3B +deepseek-ai/DeepSeek-V4-Pro | detached | 3×2 stream ×4 | 1.00 | 1.00 | 0.75 | 1.00 | 1.00 | 0.75 |  |  | nothing |
| qwen-seeded | Qwen/Qwen3.6-35B-A3B +deepseek-ai/DeepSeek-V4-Pro | attached | 3×2 stream ×4 | — | — | — | — | — | — | — | — | not run |
| qwen-strict-seeded | Qwen/Qwen3.6-35B-A3B +deepseek-ai/DeepSeek-V4-Pro | attached | 3×2 stream ×4 | — | — | — | — | — | — | — | — | not run |

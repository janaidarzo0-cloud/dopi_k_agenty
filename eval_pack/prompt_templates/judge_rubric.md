# Optional Judge Rubric

Use this only after deterministic scoring has passed.

Score 1-5 for each dimension:

1. Objective fit: did the answer solve the user's research problem?
2. Research design: was the plan appropriate for the survey type?
3. Evidence use: are claims tied to data?
4. Statistical judgment: are significance, base size, weights, and uncertainty handled correctly?
5. Insight depth: does the answer explain what the patterns mean?
6. Business usefulness: are recommendations specific and prioritized?
7. Synthesis: is there a coherent story?
8. Caveat honesty: are limitations visible and not hidden?

Return JSON:

```json
{
  "scores": {"objective_fit": 1, "research_design": 1},
  "strengths": [],
  "weaknesses": [],
  "must_fix": []
}
```

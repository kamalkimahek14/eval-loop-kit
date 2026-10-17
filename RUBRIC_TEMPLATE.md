# Rubric template

Copy this, fill it in, and save the criteria and weights as `rubric.json` (see `examples/rubric.json`).
Fix the rubric before round 1. Changing it mid-loop makes rounds incomparable; if you must change it,
start a new loop with a new round 0.

## What is being improved

One sentence: the artifact (a prompt, a template, a document, a model) and who it is for.

## Criteria

| Criterion | Weight | 90-100 | 70-89 | 50-69 | Below 50 |
|---|---|---|---|---|---|
| criterion_1 | 0.30 | | | | |
| criterion_2 | 0.30 | | | | |
| criterion_3 | 0.25 | | | | |
| criterion_4 | 0.15 | | | | |

Weights sum to 1. Write anchors as things a judge can check, not as adjectives.

## Judge instructions

You see one item. Score each criterion from 0 to 100 using the anchors. Return only:

```
{"criterion_1": n, "criterion_2": n, "criterion_3": n, "criterion_4": n, "notes": "..."}
```

## Panels

- Training panel: the same judges every round. Their notes may guide the next change.
- Blind held-out panel: new judges every round, never used before and never on the training panel.
  Record their scores only. Nobody reads their notes while the loop runs.
- Same rubric, same instructions, same number of judges on both panels.

## Loop rules

- One change per round, so a score movement has one cause.
- Overfitting: the training score rises by at least `gain` while the blind score moves less than `noise`.
  Revert or rethink the change.
- Stall: the blind score has not beaten its best by more than `noise` for N rounds. Stop and ship the best
  blind round, not the last one.
- Measure the noise first: score the same item twice with different judges; the spread is your `noise`.

# Log

## YYYY-MM-DD HH:MM — baseline
Target:
Hypothesis:
Script:
Artifacts:
What I think:
Formulas/reasoning:
Intermediate results:
What does it mean:
Complexity:
Next step:

## 2026-05-08 21:04 — baseline
Goal: to fix which properties of the lattice branch `03` can be changed by affine normalization, and which cannot.
Hypothesis: `03_affine_normalized_24cell`
Script: `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage baseline`
Artifacts:
- `data/baseline_affine_constraints.json`
- `data/baseline_affine_constraints.md`
What I think:
- target family-count grid;
- a list of structural properties that the invertible affine map saves.
Formulas/reasoning:
- affine normalization can change angles and length ratios;
- but it does not glue different directions together like projective classes and does not break incidence on its own.
Intermediate results:
- target absolute family count: `5`
- affine invariants: `['collinearity', 'line incidence', 'intersection graph', 'projective direction distinctness under invertible linear map']`
What does it mean:
- branch `03` should explain the lattice without hope of a miraculous collapse of different directions only by affine transformation.
Complexity:
- low.
Next step:
- go to prune and check what this limitation means against the results of `01_raw_24cell_web`.

## 2026-05-08 21:04 — prune
Goal: To test whether pure affine normalization by itself can save branch `03` if branch `01` is not already in the target family-count.
Hypothesis: `03_affine_normalized_24cell`
Script: `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage prune`
Artifacts:
- `data/prune_affine_direction_invariance.json`
- `data/prune_affine_direction_invariance.md`
What I think:
- prune results from `01_raw_24cell_web`;
- projective invariant: invertible affine map does not merge different direction classes into one.
Formulas/reasoning:
- if raw branch `01` does not give target family-count `5`, and the best level found is `7`, then pure affine normalization by itself will not turn `7` distinct direction classes into `5`;
- this means that branch `03` in its pure form is weakened logically, and not just numerically.
Intermediate results:
- raw exact matches from `01`: `0`
- best raw family count: `7`
- implication: `Pure raw+affine is weakened; any rescue would require additional selection/pruning beyond affine normalization itself.`
What does it mean:
- branch `03_affine_normalized_24cell` now receives a fast logical red flag;
- if it is ever saved, it will be done not as “raw + affine only”, but through an additional selection mechanism, which is closer to other branches of the plan.
Complexity:
- low; it's a logical prune without heavy searching.
Next step:
- fix the weakening of the branch and go to `06_double_rotation_overlay`.

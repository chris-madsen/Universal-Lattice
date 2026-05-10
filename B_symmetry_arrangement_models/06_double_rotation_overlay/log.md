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

## 2026-05-08 21:06 — baseline
Goal: fix the workspace of parameters for the double-rotation branch.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage baseline`
Artifacts:
- `data/baseline_double_rotation_space.json`
- `data/baseline_double_rotation_space.md`
What I think:
- what degrees of freedom are actually involved in this branch;
- which rational seed relations should be checked first.
Formulas/reasoning:
- not only `(alpha, beta)` is important here, but also projection plane, choice of rotation planes and overlay mode;
- so the branch is potentially very heavy.
Intermediate results:
- parameter axes: `['projection_plane_in_Gr(2,4)', 'rotation_angle_alpha', 'rotation_angle_beta', 'rotation_plane_choice', 'overlay_mode']`
- rational seeds: `['1:2', '1:3', '2:3', '3:4']`
What does it mean:
- a branch that is strong in concept, but dangerous in terms of computational complexity.
Complexity:
- average is already at the level of setting, before the start of the real search.
Next step:
- do complexity-prune and decide whether it can now be carried out without a strong group reduction.

## 2026-05-08 21:06 — prune-blocked-complexity
Goal: to understand whether it is possible to honestly drag the double rotation branch further right now, or whether it already requires a strong group reduction.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage prune`
Artifacts:
- `data/prune_complexity_report.json`
- `data/prune_complexity_report.md`
What I think:
- the rough dimension of the search space before introducing strong symmetry restrictions.
Formulas/reasoning:
- even a rough mesh `projection × alpha × beta × plane_choice × overlay_mode` already gives too many combinations;
- without reduction by `SO(4)`/`W(F4)` such a branch quickly turns into a brute force swamp.
Intermediate results:
- coarse combination count: `10368000`
- assessment: `blocked_complexity`
What does it mean:
- the branch is not rejected mathematically, but is now blocked by computational complexity;
- according to the rule of the plan, you cannot hang on it.
Complexity:
- high without additional reduction.
Next step:
- commit `BLOCKED_COMPLEXITY` and go to `08_f4_root_arrangement`.

## 2026-05-08 21:29 — baseline
Goal: to fix the working space of parameters for the double-rotation branch and transfer it from exhaustive search to stratified sampling.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage baseline`
Artifacts:
- `data/baseline_double_rotation_space.json`
- `data/baseline_double_rotation_space.md`
What I think:
- which parameter axes actually participate in the branch;
- which ratio classes and plane classes should be scanned first.
Formulas/reasoning:
- instead of a complete search, a stratified sample is taken by ratio classes, plane decompositions, base angles and projection seeds;
- the first scan deliberately freezes the overlay mode in `edge_union`, so as not to swell with unnecessary dimensions.
Intermediate results:
- ratio classes: `['1:1', '1:2', '1:3', '2:3', '3:4']`
- projection seeds: `20`
What does it mean:
- branch `06` becomes working again, but not through stupid brute force, but through meaningful sampling-coverage of combination classes.
Complexity:
- average.
Next step:
- do a stratified search and look at the distribution of resonance indicators by class.

## 2026-05-08 21:29 — search-stratified-sampling
Goal: replace the crude “too many combinations” with real sampling based on the main classes of combinations.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage search`
Artifacts:
- `data/search_stratified_sampling_report.json`
- `data/search_stratified_sampling_report.md`
What I think:
- stratified sampling by ratio classes, plane decompositions, base angles and projection seeds;
- for each combination I consider family-count, projected edge count and a simple resonance score relative to the target grid.
Formulas/reasoning:
- this is not a complete search and not a proof;
- this is the law of large numbers in working form: first we look at the distribution by main classes of combinations and look for where resonance generally occurs.
Intermediate results:
- total samples: `1200`
- family-count histogram: `{14: 2, 15: 7, 16: 30, 17: 49, 18: 101, 19: 170, 20: 245, 21: 266, 22: 211, 23: 93, 24: 26}`
- overall target hits: `0`
- best overall family/line/score: `14` / `192` / `1081.5`
What does it mean:
- branch `06` is no longer discarded blindly;
- now you can see the distribution by class and you can decide whether there are real resonance zones for deeper digging.
Complexity:
- average, but controlled.
Next step:
- go to analysis: which ratio/plane classes are really the best and whether it makes sense to locally narrow the search around them.

## 2026-05-08 21:29 — analyze-stratified-classes
Goal: to analyze the distribution by class-level sampling and understand whether double rotation has real resonance zones.
Hypothesis: `06_double_rotation_overlay`
Script: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage analyze`
Artifacts:
- `data/analyze_stratified_classes.json`
- `data/analyze_stratified_classes.md`
What I think:
- top classes by resonance score;
- summary by ratio classes;
- overall target hits by family-count.
Formulas/reasoning:
- if at least some ratio/plane classes are systemically better, it makes sense to refine the branch locally;
- if the distribution is flat and there are no hits, the branch is weakened, but according to the data, and not due to fear of 10 million combinations.
Intermediate results:
- overall target hits: `0`
- best overall family/score: `14` / `1081.5`
- ratio summary: `{'1:1': {'count': 240, 'target_hits': 0, 'best_score': 1081.5}, '1:2': {'count': 240, 'target_hits': 0, 'best_score': 1281.5}, '1:3': {'count': 240, 'target_hits': 0, 'best_score': 1181.5}, '2:3': {'count': 240, 'target_hits': 0, 'best_score': 1179.5}, '3:4': {'count': 240, 'target_hits': 0, 'best_score': 1179.5}}`
What does it mean:
- branch `06` now passed an honest statistical screen;
- using this data, you can already decide whether it is parked again, or whether it has a specific zone for local deepening.
Complexity:
- low.
Next step:
- if there is a target hits or an explicit leader class, narrow the search locally around it; otherwise, return the branch to parked, but with real distributions in hand.

## 2026-05-08 21:32 — analyze-sampling-red-flag
Goal: to document that branch `06` is now weakened not due to fear of dimensionality, but based on real sampling data.
Hypothesis: `06_double_rotation_overlay`
Script: analysis of artifacts `search_stratified_sampling_report.*` and `analyze_stratified_classes.*`
Artifacts:
- `data/search_stratified_sampling_report.json`
- `data/analyze_stratified_classes.json`
What I think:
- are there any real resonance zones in the sampling distribution for target family-count `5`.
Formulas/reasoning:
- the branch was reopened correctly through the law-of-large-numbers sampling;
- now it can be weakened honestly based on data, and not on an a priori estimate of space.
Intermediate results:
- total samples: `1200`
- family-count histogram: `14..24`, without a single hit in `5`
- best overall family count: `14`
What does it mean:
- in the current formulation, `double_rotation_overlay` looks like a weak branch;
- if you return to it, then with a significantly different readout/selection mechanism, and not with a simple edge-union overlay.
Complexity:
- low; the conclusion already follows from the accumulated data.
Next step:
- parked after sampling; the main focus shifts to `08` and `09`.

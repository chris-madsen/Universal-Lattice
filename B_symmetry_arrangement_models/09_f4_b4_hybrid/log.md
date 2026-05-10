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

## 2026-05-08 21:32 — baseline
Goal: decompose `F4` into axial, half-integer and long components, so that the hybrid branch is based on an explicit structure, and not on a beautiful phrase.
Hypothesis: `09_f4_b4_hybrid`
Script: `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage baseline`
Artifacts:
- `data/baseline_hybrid_shells.json`
- `data/baseline_hybrid_shells.md`
What I think:
- counts by axis / half / long shells.
Formulas/reasoning:
- the axes correspond well to the idea of ​​a vertical scaffold;
- long shell corresponds to the diagonal 24-cell part;
- half shell gives an additional refinement layer.
Intermediate results:
- axis lines: `4`
- half lines: `8`
- long lines: `12`
What does it mean:
- the hybrid branch received an explicit internal decomposition for subsequent search.
Complexity:
- low.
Next step:
- go to sampling-search for classes `A/L/H`.

## 2026-05-08 21:32 — search-hybrid-sampling
Goal: to check the hybrid classes `A/L/H`, and not to keep `09` on the “axes plus diagonals” motif alone.
Hypothesis: `09_f4_b4_hybrid`
Script: `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage search`
Artifacts:
- `data/search_hybrid_sampling.json`
- `data/search_hybrid_sampling.md`
What I think:
- sampling by classes `A[[-1.  0. 0. 0.]
 [ 0. -1.  0.  0.]
 [ 0.  0. -1.  0.]
 [ 0.  0.  0. -1.]
 [ 0.  0.  0.  1.]
 [ 0.  0.  1.  0.]
 [ 0.  1.  0.  0.]
 [ 1.  0.  0.  0.]]_L[[-1. -1.  0.  0.]
 [-1.  0. -1.  0.]
 [-1.  0.  0. -1.]
 [-1.  0.  0.  1.]
 [-1.  0.  1.  0.]
 [-1.  1.  0.  0.]
 [ 0. -1. -1.  0.]
 [ 0. -1.  0. -1.]
 [ 0. -1.  0.  1.]
 [ 0. -1.  1.  0.]
 [ 0.  0. -1. -1.]
 [ 0.  0. -1.  1.]
 [ 0.  0.  1. -1.]
 [ 0.  0.  1.  1.]
 [ 0.  1. -1.  0.]
 [ 0.  1.  0. -1.]
 [ 0.  1.  0.  1.]
 [ 0.  1.  1.  0.]
 [ 1. -1.  0.  0.]
 [ 1.  0. -1.  0.]
 [ 1.  0.  0. -1.]
 [ 1.  0.  0.  1.]
 [ 1.  0.  1.  0.]
 [ 1.  1.  0.  0.]]_H[[-0.5 -0.5 -0.5 -0.5]
 [-0.5 -0.5 -0.5  0.5]
 [-0.5 -0.5  0.5 -0.5]
 [-0.5 -0.5  0.5  0.5]
 [-0.5  0.5 -0.5 -0.5]
 [-0.5  0.5 -0.5  0.5]
 [-0.5  0.5  0.5 -0.5]
 [-0.5  0.5  0.5  0.5]
 [ 0.5 -0.5 -0.5 -0.5]
 [ 0.5 -0.5 -0.5  0.5]
 [ 0.5 -0.5  0.5 -0.5]
 [ 0.5 -0.5  0.5  0.5]
 [ 0.5  0.5 -0.5 -0.5]
 [ 0.5  0.5 -0.5  0.5]
 [ 0.5  0.5  0.5 -0.5]
 [ 0.5  0.5  0.5  0.5]]`.
Formulas/reasoning:
- this is a natural continuation of the `08` branch: they found resonant `L/S`-mixtures, and here we clearly decompose the short shell into axis and half-integer parts.
Intermediate results:
- top record: `{'class': 'A4_L6_H0', 'axis_count': 4, 'long_count': 6, 'half_count': 0, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 1, 6], 'profile_score': 6.074074074074074}`
What does it mean:
- you can see whether the explicit hybrid decomposition enhances the signal compared to the pure `F4` branch.
Complexity:
- average, but controlled.
Next step:
- if there are good `A/L/H` classes, leave `09` active in parallel with `08`; if not, return to planned/weak.

## 2026-05-08 21:40 — analyze-focused-hybrid
Goal: test the stability of the best hybrid classes and directly compare them with `08_f4_root_arrangement`.
Hypothesis: `09_f4_b4_hybrid`
Script: `research/B_symmetry_arrangement_models/09_f4_b4_hybrid/scripts/run.py --stage analyze`
Artifacts:
- `data/analyze_hybrid_refine.json`
- `data/analyze_hybrid_refine.md`
What I think:
- focused resampling of the best `A/L/H` classes;
- frequency of hits in `family_count=5`;
- frequencies exact-profile `[1,1,1,1,6]`;
- direct comparison with branch `08`.
Formulas/reasoning:
- the initial single-hit on 100 samples is too weak to draw conclusions;
- you need to get statistics and separately check whether half-shell really helps, or whether the best hybrid is actually reduced to axis+long.
Intermediate results:
- best focus class: `A4_L6_H0`
- family5 hits / exact-profile hits: `1` / `0`
- best focus witness: `{'class': 'A4_L6_H0', 'axis_count': 4, 'long_count': 6, 'half_count': 0, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 3, 4], 'profile_score': 3.6296296296296298, 'exact_profile_hit': False}`
What does it mean:
- now you can honestly compare pure `F4` sub-arrangement and hybrid `F4/B4` interpretations, and not argue at the level of beautiful words.
Complexity:
- average.
Next step:
- if axis+long dominates again, this reinforces the transition to `05_24cell_tesseract_interaction`; if half-shell starts to win, deepen `09` further.

## 2026-05-08 23:13 — axis-long-push
Goal: check separately pure `axis+long` without half-shell to understand whether this axis interpretation is an independent strong direction, and not just a fallback explanation.
Hypothesis: `09_f4_b4_hybrid`
Script: ad hoc focused scan via `split_f4_shells()` / `sample_alh_classes()`
Artifacts:
- `data/analyze_axis_long_push.json`
- `data/analyze_axis_long_push.md`
What I think:
- classes `A/L/H0` for `A in {2,3,4}` and `L in {4..8}`;
- family5-rate;
- exact-profile-rate.
Formulas/reasoning:
- if pure `axis+long` by itself gives a strong signal, this is not just “branch 09 has collapsed”, but a meaningful bridge towards `05`;
- if the signal disappears without a half-shell, then the half-layer was still needed.
Intermediate results:
- best class: `A2_L4_H0`
- family5 / exact rates: `0.1456` / `0.0000`
What does it mean:
- pure `axis+long` inside `09` gives a strong family-5 signal on its own;
- this is much stronger than the old focused leader `A4_L6_H0 = 0.0004`;
- half-shell is not necessary here for structural resonance.
Complexity:
- average.
Next step:
- use this result as a handoff in `05`, where `axis+long` should already be considered a first-class scaffold, and not just a side reading of the hybrid branch.

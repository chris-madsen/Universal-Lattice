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

## 2026-05-08 22:10 — baseline
Goal: to formalize what orbit blocks a selected subweb can consist of within a rich `tesseract + 24-cell` union.
Hypothesis: `10_orbit_selected_subweb`
Script: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage baseline`
Artifacts:
- `data/baseline_orbit_blocks.json`
- `data/baseline_orbit_blocks.md`
What I think:
- minimal orbit blocks that we are actually working with now;
- transfer of the signal from the `05` branch to the orbit language.
Formulas/reasoning:
- if full union is too rich, a language of symmetrically motivated selection is needed;
- at the current step, the natural blocks are the axial lines of the tesseract and directional lines of 24-cell.
Intermediate results:
- tesseract axis lines: `4`
- 24-cell direction lines: `12`
- imported branch 05 signal: `{'best_family5_class': 'T3_C4', 'best_family5_rate': 0.033, 'best_exact_class': 'T4_C6', 'best_exact_rate': 0.0006666666666666666}`
What does it mean:
- the `10` branch received a minimal meaningful setting, rather than an empty placeholder.
Complexity:
- low.
Next step:
- make a prune: show why orbit-selection now looks necessary and not decorative.

## 2026-05-08 22:10 — prune
Goal: To document why `orbit_selected_subweb` is needed now based on data and not just as a fallback idea.
Hypothesis: `10_orbit_selected_subweb`
Script: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage prune`
Artifacts:
- `data/prune_orbit_selection_case.json`
- `data/prune_orbit_selection_case.md`
What I think:
- the gap between the wealth of raw full union and the power of selected scaffold classes from the `05` branch.
Formulas/reasoning:
- if the raw union is consistently too rich, and the selected classes already give a strong resonance, then a language of meaningful selection is needed, and not a complete graph.
Intermediate results:
- full-union best family count: `8`
- branch05 best family5 rate: `0.033000`
- assessment: `orbit_selection_plausible`
What does it mean:
- the `10` branch is no longer decorative: it has a direct data-driven reason to live.
Complexity:
- low.
Next step:
- go to search by orbital selection language, and not just by the number of T/C lines.

## 2026-05-08 22:27 — search
Goal: move from the general slogan `selected subweb` to a real orbit selection language.
Hypothesis: `10_orbit_selected_subweb`
Script: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage search`
Artifacts:
- `data/search_orbit_templates.json`
- `data/search_orbit_templates.md`
What I think:
- search for templates like `axis_dims + bucket_counts(B2,B1,B0)`.
Formulas/reasoning:
- instead of an arbitrary selection of C-lines, orbital parameterization is introduced through overlap buckets relative to the selected axis-subset.
Intermediate results:
- top orbit template: `A2_B2-1_B1-1_B0-2`
- hits family5 / exact: `250` / `0`
What does it mean:
- now the `10` branch has the first real search layer, and not just the baseline/prune.
Complexity:
- average.
Next step:
- compare the best orbit-templates with the strong classes of the `05` branch and see if the orbit-language provides a more compact explanation.

## 2026-05-08 22:27 — analyze
Goal: to understand whether the orbit-template language provides not just a search result, but a more compact explanation of strong branch-05 signals.
Hypothesis: `10_orbit_selected_subweb`
Script: `research/B_symmetry_arrangement_models/10_orbit_selected_subweb/scripts/run.py --stage analyze`
Artifacts:
- `data/analyze_orbit_templates.json`
- `data/analyze_orbit_templates.md`
What I think:
- comparison of the best orbit-templates with the strongest class-level winners from the `05` branch.
Formulas/reasoning:
- branch `10` is not obliged to beat `05` in terms of raw hit-rate;
- its task is to give a more meaningful symmetry-guided selection language if it explains the same resonance zones more compactly.
Intermediate results:
- branch10 best template: `A2_B2-1_B1-1_B0-2`
- family5 / exact rates: `0.1667` / `0.0000`
What does it mean:
- it’s clear whether `10` enhances the interpretation of `05`, or remains just a beautiful shell for now.
Complexity:
- low.
Next step:
- if `10` gives a compact orbit language for the best `05` zones, you can shift the focus to the subgraph/readout within the full union through this parameterization.

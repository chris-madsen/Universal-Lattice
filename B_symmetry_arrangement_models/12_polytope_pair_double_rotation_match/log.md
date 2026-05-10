# Log

## 2026-05-09 15:20 — branch initialization
Target:
Run a real H12 branch as a search for pairs of 4D sources with double rotation and comparison with a simplified mesh.
Hypothesis:
`12_polytope_pair_double_rotation_match`
Script:
`research/async_jobs/h12_polytope_pair_search.py`
Artifacts:
- `PLAN.md`
- `README.md`
- `research/async_state/h12_polytope_pair/`
What I think:
- beautiful pairs of polytopes;
- double rotations;
- deterministic projection families;
- topology signature against simplified lattice;
- score of coincidence of segments, central beams, vertical masts and corner classes.
Formulas/reasoning:
- full coarse scan does not start;
- topology signature removes affine multiplication;
- Rust kernel is used for projection-family stability within a common Python shell.
Intermediate results:
- count calculator: `3,240` structural families, `155,520` deterministic projected candidates.
- target extractor: `11` segments, `15` nodes, `3` vertical masts, `8` central rays.
What does it mean:
- the branch now matches the original H12 setting, rather than the old `12_topology_signature_filter` setting.
Complexity:
- controlled; a resumable async service is launched with a checkpoint after each batch.
Next step:
- run systemd service `runes-h12-polytope-pair.service`.

## 2026-05-09 15:19 — service deployed
Target:
Run H12 as a resumable background job in an existing research slice.
Hypothesis:
`12_polytope_pair_double_rotation_match`
Script:
`research/async_jobs/h12_polytope_pair_search.py`
Artifacts:
- `/home/ilja/.config/systemd/user/runes-h12-polytope-pair.service`
- `research/async_state/h12_polytope_pair/state.json`
- `research/async_state/h12_polytope_pair/summary.md`
- `research/async_state/h12_polytope_pair/log.md`
- `research/async_state/h12_polytope_pair/best_candidates.json`
- `figures/h12_best_candidate_report.md`
What I think:
- source pairs;
- double rotations;
- deterministic projection families;
- readout modes;
- topology signature against simplified lattice;
- Rust-backed projection-family stability.
Formulas/reasoning:
- service uses `CPUWeight=10`, `Nice=19`, batch CPU scheduling and idle I/O;
- no hard CPU quota is used;
- `Restart=always` is safe because the job resumes from `state.json` and idles after completion.
Intermediate results:
- service active in `runes-research.slice`;
- restart/resume smoke test passed;
- live search reached `8/11` target segments and `8/8` central rays in early generations, but not the full simplified grid.
What does it mean:
- H12 now runs as the intended beautiful-first pair-of-polytopes search, not as the old standalone topology filter.
Complexity:
- controlled async search; current live ETA is reported in hours/minutes in `summary.md`.
Next step:
- monitor `summary.md` and render updated best candidates when the live best changes materially.

## 2026-05-09 15:59 — target-segmentation correction and rerun
Target:
Check to see if `vertical_masts=0` is a segmentation artifact rather than a real geometry failure.
Hypothesis:
`12_polytope_pair_double_rotation_match`
Script:
`research/async_jobs/h12_polytope_pair_search.py`
Artifacts:
- `research/async_jobs/h12_polytope_pair_search.py` (patched `segments_from_family_angles`)
- `research/async_state/h12_polytope_pair_pre_mast_fix_20260509_155856/` (archived old run)
- `research/async_state/h12_polytope_pair/` (fresh rerun state)
What I think:
- coincidence with a simplified grid with resolution of long target primitives (including 3 full masts).
Formulas/reasoning:
- the old check discarded any long segment if there were intermediate nodes;
- because of this, 3 vertical masts could not be counted in principle;
- after the fix, long segments are allowed if they are included in the target segment set.
Intermediate results:
- smoke after the fix gave the candidate `24-T|r1:1|a36|p0|line_arrangement_core|central_bundle:5` with `11/11` target segments, `3/3` masts, `8/8` rays, but with `46` extra segments.
What does it mean:
- the previous conclusion “the masts are not restored” was partly a methodological artifact;
- the current task has shifted towards suppressing unnecessary lines while maintaining full target cover.
Complexity:
- average; now the key risk is over-rich candidates.
Next step:
- continue live run and move the score towards smaller `extra_segments` while maintaining `11/11`.

## 2026-05-09 17:32 — complement service implemented
Target:
Run a separate H12 complement-search on top of a fixed leader, and not on top of the entire pair-search task.
Hypothesis:
`12_polytope_pair_double_rotation_match`
Script:
`research/async_jobs/h12_complement_search.py`
Artifacts:
- `research/async_jobs/h12_complement_search.py`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/scripts/render_best_complement_candidate.py`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/data/complement_target_truth.md`
- `research/async_state/h12_complement_smoke/`
What I think:
- complement layer to the leader `T-T|r1:2|a22.5|p0|edge_union|central_bundle:3`;
- exact missing set `universal \ leader`;
- staged search first by `16-cell`, then by `tesseract`, then at a signal by orientation seeds.
Formulas/reasoning:
- candidate is evaluated as an addition, not as a new mesh from scratch;
- topology signature filters equivalent union/complement options before calling Rust hot kernel;
- score prioritizes `missing_after_union_vs_universal`, then `extra_after_union_vs_universal`.
Intermediate results:
- truth extraction confirmed `16` missing segments;
- smoke on `A16_base` immediately gave the best candidate with `14/16` matching complement segments, `2` missing and `9` extra after union;
- resume smoke confirmed the transition between checkpoint and the next stage (`A16_base -> A16_readout`).
What does it mean:
- complement-search is not decorative, but immediately gave a strong signal specifically for `16-cell`.
Complexity:
- controlled; the real service should continue the staged search asynchronously.
Next step:
- deploy `runes-h12-complement.service` and run a full background search.

## 2026-05-09 17:34 — complement service deployed and live
Target:
Launch a full-fledged complement-search as a live resumable service and record the first strong results.
Hypothesis:
`12_polytope_pair_double_rotation_match`
Script:
`research/async_jobs/h12_complement_search.py`
Artifacts:
- `/home/ilja/.config/systemd/user/runes-h12-complement.service`
- `research/async_state/h12_complement/state.json`
- `research/async_state/h12_complement/summary.md`
- `research/async_state/h12_complement/log.md`
- `research/async_state/h12_complement/best_candidates.json`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/figures/h12_complement_report.md`
What I think:
- staged complement search from the fixed leader to `universal-lattice.py`;
- first `16-cell`, then `tesseract`, then orientation-seed expansion only if needed;
- exact complement match and exact union match as separate mathematical objectives.
Formulas/reasoning:
- exact complement asks whether the added layer equals `universal \\ leader`;
- union quality asks whether `leader ∪ complement_candidate` reproduces the universal segment set with minimal extra lines;
- these are related but not identical objectives, so they are tracked separately.
Intermediate results:
- live service is active in `runes-research.slice`;
- `A16_projection|16|r3:4|a18|p0|line_arrangement_core|central_bundle:2|o0` produced an exact complement match `16/16`;
- `A16_readout|16|r1:1|a7.5|p1|line_arrangement_core|central_bundle:3|o0` produced a union candidate with `0` missing universal segments and `9` extra segments;
- all `15` fixed nodes are preserved in the best union candidate.
What does it mean:
- the `16-cell` branch is now strongly supported;
- the main remaining task is not to recover missing target geometry, but to reduce extra segments while preserving the full union coverage.
Complexity:
- controlled async search; service is still exploring `A16_projection` and has not yet needed the `tesseract` branch.
Next step:
- continue the live run;
- if `16-cell` stalls on extra-segment suppression, open the `tesseract` complement stage and compare directly.

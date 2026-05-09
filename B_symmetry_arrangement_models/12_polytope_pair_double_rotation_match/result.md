# Result

Status: complement service implemented

## Summary

H12 now has two layers:

- pair-search against the simplified lattice;
- complement-search against `universal-lattice.py` from the fixed leader.

The new complement service is implemented as a resumable async search with `FFT + GA + ACO + Rust hot kernel + topological signature`, running in the existing research slice.

## Current Best

Fixed leader: `T-T|r1:2|a22.5|p0|edge_union|central_bundle:3`

Best exact complement candidate so far:
- `A16_projection|16|r3:4|a18|p0|line_arrangement_core|central_bundle:2|o0`
- source: `16-cell`
- exact complement: `True`
- matched complement: `16/16`
- missing after union vs universal: `8`
- extra after union vs universal: `3`

Best union candidate so far:
- `A16_readout|16|r1:1|a7.5|p1|line_arrangement_core|central_bundle:3|o0`
- source: `16-cell`
- exact complement: `False`
- exact union: `False`
- matched complement: `16/16`
- missing after union vs universal: `0`
- extra after union vs universal: `9`
- node coverage: `15/15`

Interpretation:
- the `16-cell` branch already contains the full missing complement layer;
- a different `16-cell` readout already closes all universal missing segments after union with the fixed leader;
- what remains is not lack of target coverage, but suppression of extra segments.

## Live State

- `research/async_state/h12_polytope_pair/state.json`
- `research/async_state/h12_polytope_pair/summary.md`
- `research/async_state/h12_polytope_pair/best_candidates.json`
- `research/async_state/h12_complement/state.json`
- `research/async_state/h12_complement/summary.md`
- `research/async_state/h12_complement/best_candidates.json`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/data/leader_tt_r1_2_a22_5_record.md`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/data/complement_target_truth.md`
- `research/B_symmetry_arrangement_models/12_polytope_pair_double_rotation_match/figures/h12_complement_report.md`

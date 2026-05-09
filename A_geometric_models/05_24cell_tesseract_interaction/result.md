# Result

Status: primary constructive explanation (layer-level)

## Summary

Branch `05` now has reduced-shell search, local ridge refinement, a full edge-union scan, a completed asynchronous `GA + ACO` tree-search (`50000 / 50000` generations), a shared-core Rust hot-kernel benchmark, a live `rust_persistent` evaluation backend, an explicit `A2` readout rule with orbit transfer (`02/12/13/23`), a concrete `A2` witness candidate (`A2_B2-0_B1-3_B0-1@02`), a negative union certificate (naive multi-trunk additions break canonical profile), and a finalized witness-layer v2 package.

The witness-layer v2 package confirms the best orbit-consistent replacement family (`replace 1:5->3` on `02`) under enlarged robustness settings (`projection_batch=12288`, `3` seeds), with canonical counts preserved on all four key subsets and non-inferior family5 behavior vs current live winners.

## Best Witness

- `data/analyze_interaction_refine.json`
- `data/finalize_full_union_scan.json`
- `data/analyze_ga_aco_bridge.md`
- `../async_state/branch05_ridge/ga_aco_summary.md`
- `data/bench_branch05_hot_kernel.json`
- `data/readout_rule_a2_trunks.md`
- `data/core_metaheuristic_core.md`
- `data/readout_rule_a2_orbit_transfer.md`
- `data/deterministic_a2_subweb_rule.md`
- `data/bench_branch05_live_scale_persistent.md`
- `data/concrete_witness_candidate_a2.md`
- `data/ga_aco_frontier_snapshot.md`
- `data/multi_trunk_witness_scan.md`
- `data/gated_layered_a2_readout_scan.md`
- `data/orbit_consistent_replacement_family.md`
- `data/witness_layer_v2_package.md`

## Decision

- promotion decision for branch `05`: **promote to primary constructive explanation (layer-level)**;
- basis:
  - witness-layer v2 packaged (`rule + overlay/diff + nearby negatives`);
  - enlarged robustness passed (`projection_batch=12288`, `3` seeds, canonical preserved on `02/12/13/23`);
  - replacement family is non-inferior to live winners on key family5 metric (aggregate delta close to zero within tolerance);
  - add-back neighbor certificates fail canonical profile as expected (`best_counts` shifts to `[1,1,1,2,2]`), supporting structural specificity.

## Residual Risks

- global strict proof is still not closed; this promotion is constructive at the strongest `A2` layer, not full-lattice exact proof;
- root-branch coverage remains `261 / 391` (`66.7519%`) even after extending the run to `50000` generations, so a targeted exploration pass is still desirable.

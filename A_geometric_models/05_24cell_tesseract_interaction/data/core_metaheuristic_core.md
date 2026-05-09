# Branch 05 Shared Metaheuristic Core

Shared core pieces extracted from branch `05` so the same search stack can be reused by other heavy hypotheses.

## Python Core
- `research/common/meta_search.py`
  - human ETA formatting
  - weighted choice / weighted sampling without replacement
  - low-pass FFT/DFT smoothing for coarse priors
  - common rate-ranking helpers
- `research/common/family_kernel.py`
  - projection-family hot kernel in Python
  - generic `evaluate_vectors_python(...)`
  - bridge to shared Rust kernel via `evaluate_vectors_rust(...)`

## Rust Core
- `research/rust/projection_family_kernel/`
  - shared Rust kernel for repeated random-projection family-profile evaluation
  - no longer branch-05-only by name or location

## Branch 05 Integration
- `research/async_jobs/branch05_ga_aco_tree_search.py`
  - now consumes shared ETA formatting
  - now consumes shared weighted sampling
  - now consumes shared FFT low-pass prior smoothing
  - now consumes shared Python evaluation kernel
- `research/async_jobs/bench_branch05_hot_kernel.py`
  - now benchmarks the shared Rust core kernel, not a branch-local binary

## Benchmark Snapshot
- shared-core Rust benchmark artifact:
  - `data/bench_branch05_hot_kernel.md`
- orbit-transfer artifact:
  - `data/readout_rule_a2_orbit_transfer.md`

# Log

## 2026-05-09 03:00 — baseline
Target:
- launch the first version of the topological-signature filter for branch `05`.
Hypothesis:
- a significant portion of the branch `05` space collapses into a smaller number of symmetry classes.
Script:
- `scripts/run.py`
Artifacts:
- `data/topology_signature_space_report.json`
- `data/topology_signature_space_report.md`
What I think:
- full size of the parameterized space branch `05`;
- number of unique signature classes;
- reduction ratio.
Formulas/reasoning:
- signed-permutation symmetry factorization should remove equivalent permutations/signs of the axes.
Intermediate results:
- raw candidate space: `38,478`
- unique topological signatures: `14,510`
- overall compression ratio: `2.651826x`
- high-compression roots reach `4.000000x` (for example `A2_B2-0_B1-5_B0-0@01/@23`)
What does it mean:
- signed-permutation symmetry gives a strong collapse of equivalent configurations;
- topology-signature filter makes sense to enable before expensive projection evaluation.
Complexity:
- average.
Next step:
- embed a filter in the loop and compare with/without a filter on the same budget.

## 2026-05-09 03:40 — integration-into-branch05-tree
Target:
- embed topological_signature filter in live tree-search branch `05`.
Hypothesis:
- pre-eval symmetry factorization will remove equivalent runs without losing useful classes.
Script:
- `research/async_jobs/branch05_ga_aco_tree_search.py`
- `research/common/topological_signature.py`
Artifacts:
- `research/async_state/branch05_topology_filter_smoke/ga_aco_summary.md`
- `research/async_state/branch05_topology_filter_smoke2/ga_aco_summary.md`
What I think:
- skip-equivalent within a generation;
- skip-by-cap by already read signatures;
- unique signature coverage in summary.
Formulas/reasoning:
- signature canonicalization by signed-permutation action in `R^4`.
Intermediate results:
- the filter is successfully integrated;
- summary/log receives new topology-filter fields;
- smoke run confirms the working loop (`topology filter: True`).
What does it mean:
- equivalent configurations can be cut to expensive projection eval.
Complexity:
- average.
Next step:
- run a separate long async-run with a filter and compare the quality of top candidates against baseline without a filter on an equal budget.

## 2026-05-09 04:25 — long-run AB resume + anti-stall
Target:
- continue long A/B run (`with_filter` vs `no_filter`) after context restoration.
Hypothesis:
- `signature_cap=1` is useful for grandfather, but can drive `with_filter` into stagnation (generations go by, there are almost no new evals).
Script:
- `research/async_jobs/branch05_ga_aco_tree_search.py`
- `research/async_jobs/branch05_topology_ab_runner.py`
Artifacts:
- `research/async_state/branch05_ab/no_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/with_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/comparison.md`
What's changed:
- added `anti-stall backfill` to topology-filter loop:
- if the entire batch rests on `signature_cap`, a small least-seen backfill is skipped into eval (without disabling the filter).
Intermediate results:
- after restarting with the new code in `with_filter` eval began to grow again:
- candidate evaluations: `1944 -> 2111`;
- unique signatures: `1944 -> 1955`;
- entries `topology anti-stall backfill=4` appeared in the log.
- baseline `no_filter` continues run in normal mode (`~1.17M` candidate eval on the current slice).
What does it mean:
- the filter remains on, but the loop is no longer “empty” when it completely hits the cap.
- A/B comparison is now more correct for long continuous runs.
Complexity:
- average.
Next step:
- continue run until the target budget and make comparisons based on the state of `comparison.md` at control points.

## 2026-05-09 07:31 — AB completed
Target:
- get a completed A/B result for topology-filter on the same generational budget.
Script:
- `research/async_jobs/branch05_topology_ab_runner.py compare`
Artifacts:
- `research/async_state/branch05_ab/no_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/with_filter/ga_aco_summary.md`
- `research/async_state/branch05_ab/comparison.md`
Result:
- `no_filter`: completed `50000/50000`, candidate evals=`3,600,000`, projection evals=`345,600,000`, elapsed=`5004.95s`;
- `with_filter`: completed `50000/50000`, candidate evals=`168,929`, projection evals=`16,217,184`, elapsed=`12811.92s`;
- `with_filter` unique signatures=`3,677` (`9.5561%` of `38,478`);
- topology skips (`with_filter`): batch_equivalent=`1,685,396`, signature_cap=`1,910,927`.
Conclusion:
- how strict pre-eval dedup/filter the current configuration radically reduces the eval volume;
- however, in the current setting, the filter does not speed up wall-clock completion relative to baseline.

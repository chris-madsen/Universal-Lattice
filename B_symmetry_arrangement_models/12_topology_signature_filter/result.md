# Result

Status: completed

## Summary of hypothesis 12 (entirely)

We tested the `12_topology_signature_filter` hypothesis: can canonical signed-permutation signature be used as a pre-eval filter for equivalent candidates in the branch `05` search.

### 1. Structural baseline (signature space)

- total root branches: `391`
- total templates: `79`
- raw candidate space: `38,478`
- unique topological signatures: `14,510`
- structural compression ratio: `2.651826x`

Strongest local compression:
- `A2_B2-0_B1-5_B0-0@01`: `56 -> 14` (`4.000000x`)
- `A2_B2-0_B1-5_B0-0@23`: `56 -> 14` (`4.000000x`)
- `A2_B2-0_B1-7_B0-0@01`: `8 -> 2` (`4.000000x`)
- `A2_B2-0_B1-7_B0-0@23`: `8 -> 2` (`4.000000x`)

Baseline output:
- symmetry-equivalent configurations occupy a larger proportion of space;
- signature filtering as an idea is justified.

### 2. Integrating the filter into the live loop

Added to `branch05_ga_aco_tree_search.py`:
- filtering duplicates within a generation by topological signature;
- cap on the number eval on signature (`topology_max_evals_per_signature`);
- statistics accounting: unique signatures, skipped in-batch, skipped by cap;
- anti-stall backfill so that the cycle does not freeze when the cap is fully pressed.

### 3. Final A/B (same budget)

Both runs completed on the same budget:
- generation: `50000 / 50000`
- kernel: `rust_persistent`

`no_filter`:
- elapsed: `5004.95s`
- candidate evaluations: `3,600,000`
- projection evaluations: `345,600,000`
- candidate eval/sec: `719.287`
- projection eval/sec: `69051.594`

`with_filter`:
- elapsed: `12811.92s`
- candidate evaluations: `168,929`
- projection evaluations: `16,217,184`
- candidate eval/sec: `13.185`
- projection eval/sec: `1265.789`
- unique signatures explored: `3,677 / 38,478` (`9.5561%`)
- skipped in-batch equivalent: `1,685,396`
- skipped by signature cap: `1,910,927`

### 4. Verdict

Confirmed:
- how the dedup/equivalence filter hypothesis works;
- expensive eval volume is reduced radically.

Not confirmed:
- as wall-clock acceleration in the current mode (`signature_cap=1` + current policy), the filter does not win in terms of completion time.

### 5. Final status of hypothesis 12

Hypothesis 12 is closed at the current stage with the result:
- **PASS** on deduplication and structural reduction;
- **FAIL** for wall-clock acceleration in the current configuration;
- the next step (if we continue exactly 12): tuning the policy cap/backfill/scheduling on a fixed compute budget.

### 6. Answer to the question “the mesh fits or not”

Short answer:
- **strict final match of the grid according to the 12th hypothesis has not been fixed**;
- **but a stable strong approximation was found** in `A2`-classes.

What exactly was found:
- best peak without filter: `A2_B2-0_B1-3_B0-1@12`, `family5_rate=0.3854167`, `best_counts=[1,1,1,1,2]`;
- best peak with filter: `A2_B2-0_B1-4_B0-0@03`, `family5_rate=0.3333333`, `best_counts=[1,1,1,1,2]`.

Frequency of similar grids:
- top running classes in both final runs: `A2_B2-0_B1-4_B0-0`, `A2_B2-0_B1-3_B0-1`, `A2_B2-0_B1-2_B0-2`;
- these leaders have stable `[1,1,1,1,2]` `best_counts`.

Interpretation:
- a similar zone is found and confirmed statistically;
- the final strict `PASS` of the entire grid within the 12th branch has not yet been proven.

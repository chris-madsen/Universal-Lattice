# Hypothesis 12 Final Summary (2026-05-09)

## Testable idea

If you translate candidates into canonical topological signature (signed-permutation invariant), you can cut off equivalent options in advance before expensive projection-evaluation.

## What we got

According to the structure of space:
- raw candidates: `38,478`
- unique signatures: `14,510`
- compression: `2.651826x`

According to the final A/B (same budget `50000` generations):
- `no_filter`: `3,600,000` candidate eval, `345,600,000` projection eval, `5004.95s`
- `with_filter`: `168,929` candidate eval, `16,217,184` projection eval, `12811.92s`
- `with_filter` explored signatures: `3,677` (`9.5561%` of `38,478`)
- `with_filter` skipped in-batch equivalent: `1,685,396`
- `with_filter` skipped by signature cap: `1,910,927`

## Verdict on hypothesis 12

Confirmed:
- how the equivalence deduplication mechanism works.
- the volume of actually executed expensive evals is reduced radically.

Not confirmed:
- as wall-clock acceleration in the current mode (`signature_cap=1` + current bypass policy) the filter does not benefit.

## Practical conclusion

Hypothesis 12 is closed at the current stage:
- the mechanism is necessary and useful;
- for the next step, it is not necessary to “prove again”, but to tune the policy (cap/backfill/scheduling), if the goal is time acceleration.

## Mesh: fit or not

Direct answer:
- the strict final match of the grid on branch 12 is not fixed;
- a stable strong approximation in `A2`-classes was found.

Facts:
- best peak (no_filter): `A2_B2-0_B1-3_B0-1@12`, `family5_rate=0.3854167`, `best_counts=[1,1,1,1,2]`;
- best peak (with_filter): `A2_B2-0_B1-4_B0-0@03`, `family5_rate=0.3333333`, `best_counts=[1,1,1,1,2]`;
- the leading classes in terms of frequency in both runs: `A2_B2-0_B1-4_B0-0`, `A2_B2-0_B1-3_B0-1`, `A2_B2-0_B1-2_B0-2`.

## Branch 12 sources

- `data/topology_signature_space_report.md`
- `../result.md`
- `../log.md`

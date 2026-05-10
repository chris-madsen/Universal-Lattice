# Branch 05 Glossary + FAQ

A quick guide to the subject language of the branch:

- `A_geometric_models/05_24cell_tesseract_interaction`

The document is designed for the reader “from scratch”, without knowledge of internal terms.

---

## 1) Where it all begins

We are working in `R^4` and trying to understand the origin of the 2D lattice from `universal-lattice.py`.

In branch `05` the candidate is constructed from two sources:

- tesseract axes (`e0,e1,e2,e3`);
- 12 unique 24-cell directions (taking into account that opposite directions are considered one line).

Each candidate:

1. specified as a set of 4D lines;
2. Many times accidentally projected into 2D;
3. receives structural metrics for each projection;
4. ranked relative to the target grammar.

---

## 2) What is `subset` and why `02`, `12`, `13`, `23`

- `subset` — selected axes from `{e0,e1,e2,e3}`.
- `02` = `{e0,e2}`
- `12` = `{e1,e2}`
- `13` = `{e1,e3}`
- `23` = `{e2,e3}`

These subsets are important as an orbit-related set for `A2`-mode: there are symmetry transfers (signed permutations) between them.

---

## 3) What does `A2`, `A3`, `A4` mean?

`A*` — axial subset size:

- `A2` — 2 axes;
- `A3` - 3 axes;
- `A4` - 4 axes.

Example:

- `A2_B2-0_B1-3_B0-1` means “subset of 2 axes + a certain composition of buckets”.

---

## 4) What is `bucket-2/bucket-1/bucket-0`

For each 24-cell line, we look at how many of its coordinate axes intersect with the selected subset.

- `bucket-2`: overlap=2 (the line “coincides” with both subset axes)
- `bucket-1`: overlap=1
- `bucket-0`: overlap=0

For `A2` usually:

- `bucket-2`: 2 lines
- `bucket-1`: 8 lines
- `bucket-0`: 2 lines

---

## 5) How to read a pattern like `A2_B2-0_B1-3_B0-1`

Explanation:

- `A2` — subset of size 2;
- `B2-0` — take 0 lines from bucket-2;
- `B1-3` — take 3 lines from bucket-1;
- `B0-1` — take 1 line from bucket-0.

This is not enough for a full candidate. We also need specific `line-id`.

Example of a complete root-branch:

- `A2_B2-0_B1-3_B0-1@02`
- selections: `{'2': [], '1': [9,10,2], '0': [8]}`

---

## 6) `template`, `root branch`, `selection`

- `template` — class of candidates according to the format `A*_B2-*_B1-*_B0-*`.
- `root branch` - `template + subset` (for example `...@02`).
- `selection` — specific line-ids inside buckets.

Hierarchy:

`template` -> `root branch` -> `selection (specific candidate)`

---

## 7) What are direction families (`family_count`)

For one 2D projection:

1. We project all selected 4D vectors into 2D;
2. calculate their angles modulo 180°;
3. cluster close angles (threshold approximately `1.5°`).

Each cluster = one family of directions.

- `family_count` = number of clusters.
- `best_counts` = cluster sizes (multiplicities of families), for example `[1,1,1,1,2]`.

---

## 8) Why is `family_count = 5` used?

In the `A2` branch `05` mode, it is precisely 5 families that historically provide the most stable structural zone.

This is an operational target, not “evidence”.

Therefore, we look not only at `family_count=5`, but also at:

- profile `best_counts`;
- stability to add/ablation;
- portability between orbit-related subsets.

---

## 9) What are `family5_hits`, `family5_rate`, `exact_rate`

`projection_batch` = N random projections of one candidate.

- `family5_hits`: how many of N gave `family_count=5`
- `family5_rate = family5_hits / N`
- `exact_hits`: how many of N hit the narrow exact-profile loop criterion
- `exact_rate = exact_hits / N`

---

## 10) What is `fitness` and why is an aggregate function needed?

There are millions of candidates in the loop. We need a single ranking score for:

- selection of “elites”;
- enhancement of ACO pheromones;
- choosing which candidates to mutate/develop further.

Current formula (branch `05`):

- `fitness = 10000*exact_rate + 1000*family5_rate + 10/(1+mean_profile_score)`

Priority logic:

1. exact-rate
2. family5-rate
3. profile accuracy (`mean_profile_score`)

---

## 11) What does “holds canonical counts” mean?

`canonical counts` for the strongest `A2` layer: `[1,1,1,1,2]`.

The phrase “canonical counts” means:

- in the test batch, its structurally best profile remains `[1,1,1,1,2]`;
- that is, he did not move to another grammar class.

---

## 12) What does “breaks with single-add/single-ablate” mean?

Examination:

- add one line (`single-add`) or remove one (`single-ablate`);
- recalculate metrics.

“Breaks” means:

- canonical profile is lost (`[1,1,1,1,2]`);
- usually transition to `[1,1,1,2,2]`, `[1,1,2,2,2]`, `[1,1,2,2,3]`, etc.

This is an important sign of a minimal stable core: an extra or missing line destroys the structure.

---

## 13) What are `orbit-related subsets` and `orbit transfer`

`02`, `12`, `13`, `23` are considered to be related by symmetries of 4D space.

`orbit transfer`:

- transfers a rule/candidate from one subset to another via signed permutation;
- checks whether the canonical grammar is preserved after the transfer.

If it persists, it is not a local trick of one subset, but a stable structural pattern.

---

## 14) What is `add`, `replace`, `union`, `gated move`

- `add` — add one line to the bucket.
- `replace` — replace one line with another in the same bucket.
- `union` — combine lines of several trunk candidates.
- `gated move` - a step that is accepted only if:
- canonical counts saved;
- `family5_rate` does not fall below the specified threshold relative to core.

Practical output of branch `05`:

- naive `add/union` destroys the profile more often;
- `replace` steps gave a working orbit-consistent upgrade layer.

---

## 15) What are the stages `baseline`, `prune`, `sampling`, `search`, `analyze`, `finalize`

- `baseline`: formalization of the target signature and minimal checks.
- `prune`: logical and symmetrical screening of weak areas of space.
- `sampling`: limited statistical sensing of a large area (fast signal).
- `search`: basic computational search.
- `analyze`: analysis of winners/anti-examples, comparison of hypotheses.
- `finalize`: fixing the status of the branch and witness/certificate artifacts.

---

## 16) Current status of branch `05` (short)

- Complete strict-match of the entire lattice has not yet been proven.
- Strong `A2` witness-candidate found.
- Orbit-consistent replacement-family found and saves canonical counts to `02/12/13/23`.
- Next step: package witness-layer v2 (`rule + diff + nearby negatives`) and resolve the issue of raising the status of `05`.

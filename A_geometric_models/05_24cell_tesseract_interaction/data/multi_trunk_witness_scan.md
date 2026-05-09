# Multi-Trunk Witness Scan

- captured at: `2026-05-09 00:56:15`
- projection batch: `4096`
- canonical counts target: `[1, 1, 1, 1, 2]`

## Shortlist Context

- shortlist source: `/home/ilja/Desktop/runes/docs/research/A_geometric_models/05_24cell_tesseract_interaction/data/ga_aco_frontier_snapshot.json`
- shortlist size: `8`

## Merge Configs

- `core_only` -> `['A2_B2-0_B1-3_B0-1']`
- `core_plus_b1` -> `['A2_B2-0_B1-3_B0-1', 'A2_B2-0_B1-4_B0-0']`
- `core_plus_b0` -> `['A2_B2-0_B1-3_B0-1', 'A2_B2-0_B1-2_B0-2']`
- `dual_outer` -> `['A2_B2-0_B1-4_B0-0', 'A2_B2-0_B1-2_B0-2']`
- `triple_union` -> `['A2_B2-0_B1-3_B0-1', 'A2_B2-0_B1-4_B0-0', 'A2_B2-0_B1-2_B0-2']`

## Evaluations

### `02:core_only`

- selections: `{'2': [], '1': [5, 9, 10], '0': [8]}`
- bucket counts: `{'2': 0, '1': 3, '0': 1}`
- family5 rate: `0.180176`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 1, 2]`
- preserves canonical: `True`
- mean profile score: `84.650662`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `02:core_plus_b1`

- selections: `{'2': [], '1': [0, 2, 5, 9, 10], '0': [8]}`
- bucket counts: `{'2': 0, '1': 5, '0': 1}`
- family5 rate: `0.006104`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 2]`
- preserves canonical: `False`
- mean profile score: `268.170501`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [0, 2], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `02:core_plus_b0`

- selections: `{'2': [], '1': [2, 5, 9, 10], '0': [7, 8]}`
- bucket counts: `{'2': 0, '1': 4, '0': 2}`
- family5 rate: `0.005859`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 2]`
- preserves canonical: `False`
- mean profile score: `268.156720`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [2], 'missing': []}, '0': {'extra': [7], 'missing': []}}`

### `02:dual_outer`

- selections: `{'2': [], '1': [0, 2, 9, 10], '0': [7, 8]}`
- bucket counts: `{'2': 0, '1': 4, '0': 2}`
- family5 rate: `0.005127`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 2]`
- preserves canonical: `False`
- mean profile score: `271.462402`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [0, 2], 'missing': [5]}, '0': {'extra': [7], 'missing': []}}`

### `02:triple_union`

- selections: `{'2': [], '1': [0, 2, 5, 9, 10], '0': [7, 8]}`
- bucket counts: `{'2': 0, '1': 5, '0': 2}`
- family5 rate: `0.001465`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 3]`
- preserves canonical: `False`
- mean profile score: `363.880371`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [0, 2], 'missing': []}, '0': {'extra': [7], 'missing': []}}`

### `12:core_only`

- selections: `{'2': [], '1': [1, 8, 11], '0': [3]}`
- bucket counts: `{'2': 0, '1': 3, '0': 1}`
- family5 rate: `0.187256`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 1, 2]`
- preserves canonical: `True`
- mean profile score: `83.885471`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `12:core_plus_b1`

- selections: `{'2': [], '1': [0, 1, 7, 8, 11], '0': [3]}`
- bucket counts: `{'2': 0, '1': 5, '0': 1}`
- family5 rate: `0.004639`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 2]`
- preserves canonical: `False`
- mean profile score: `267.687446`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [0, 7], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `12:core_plus_b0`

- selections: `{'2': [], '1': [1, 8, 11], '0': [2, 3]}`
- bucket counts: `{'2': 0, '1': 3, '0': 2}`
- family5 rate: `0.023682`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 2, 2]`
- preserves canonical: `False`
- mean profile score: `177.738878`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [], 'missing': []}, '0': {'extra': [2], 'missing': []}}`

### `12:dual_outer`

- selections: `{'2': [], '1': [0, 1, 7, 8, 11], '0': [2, 3]}`
- bucket counts: `{'2': 0, '1': 5, '0': 2}`
- family5 rate: `0.001709`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 3]`
- preserves canonical: `False`
- mean profile score: `361.096029`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [0, 7], 'missing': []}, '0': {'extra': [2], 'missing': []}}`

### `12:triple_union`

- selections: `{'2': [], '1': [0, 1, 7, 8, 11], '0': [2, 3]}`
- bucket counts: `{'2': 0, '1': 5, '0': 2}`
- family5 rate: `0.001465`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 3]`
- preserves canonical: `False`
- mean profile score: `360.798177`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [0, 7], 'missing': []}, '0': {'extra': [2], 'missing': []}}`

### `13:core_only`

- selections: `{'2': [], '1': [0, 2, 10], '0': [1]}`
- bucket counts: `{'2': 0, '1': 3, '0': 1}`
- family5 rate: `0.180420`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 1, 2]`
- preserves canonical: `True`
- mean profile score: `84.674859`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `13:core_plus_b1`

- selections: `{'2': [], '1': [0, 2, 5, 6, 10], '0': [1]}`
- bucket counts: `{'2': 0, '1': 5, '0': 1}`
- family5 rate: `0.005371`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 2]`
- preserves canonical: `False`
- mean profile score: `270.025535`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [5, 6], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `13:core_plus_b0`

- selections: `{'2': [], '1': [0, 2, 10], '0': [1, 4]}`
- bucket counts: `{'2': 0, '1': 3, '0': 2}`
- family5 rate: `0.026367`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 2, 2]`
- preserves canonical: `False`
- mean profile score: `177.755046`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [], 'missing': []}, '0': {'extra': [4], 'missing': []}}`

### `13:dual_outer`

- selections: `{'2': [], '1': [0, 2, 5, 6, 10], '0': [1, 4]}`
- bucket counts: `{'2': 0, '1': 5, '0': 2}`
- family5 rate: `0.001709`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 3]`
- preserves canonical: `False`
- mean profile score: `363.439128`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [5, 6], 'missing': []}, '0': {'extra': [4], 'missing': []}}`

### `13:triple_union`

- selections: `{'2': [], '1': [0, 2, 5, 6, 10], '0': [1, 4]}`
- bucket counts: `{'2': 0, '1': 5, '0': 2}`
- family5 rate: `0.001953`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 3]`
- preserves canonical: `False`
- mean profile score: `361.205892`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [5, 6], 'missing': []}, '0': {'extra': [4], 'missing': []}}`

### `23:core_only`

- selections: `{'2': [], '1': [4, 6, 7], '0': [5]}`
- bucket counts: `{'2': 0, '1': 3, '0': 1}`
- family5 rate: `0.186035`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 1, 2]`
- preserves canonical: `True`
- mean profile score: `84.006348`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `23:core_plus_b1`

- selections: `{'2': [], '1': [3, 4, 6, 7, 8], '0': [5]}`
- bucket counts: `{'2': 0, '1': 5, '0': 1}`
- family5 rate: `0.007324`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 2]`
- preserves canonical: `False`
- mean profile score: `269.833008`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [3, 8], 'missing': []}, '0': {'extra': [], 'missing': []}}`

### `23:core_plus_b0`

- selections: `{'2': [], '1': [4, 6, 7], '0': [0, 5]}`
- bucket counts: `{'2': 0, '1': 3, '0': 2}`
- family5 rate: `0.031738`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 2, 2]`
- preserves canonical: `False`
- mean profile score: `178.423665`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [], 'missing': []}, '0': {'extra': [0], 'missing': []}}`

### `23:dual_outer`

- selections: `{'2': [], '1': [3, 4, 6, 7, 8], '0': [0, 5]}`
- bucket counts: `{'2': 0, '1': 5, '0': 2}`
- family5 rate: `0.002197`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 3]`
- preserves canonical: `False`
- mean profile score: `363.261230`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [3, 8], 'missing': []}, '0': {'extra': [0], 'missing': []}}`

### `23:triple_union`

- selections: `{'2': [], '1': [3, 4, 6, 7, 8], '0': [0, 5]}`
- bucket counts: `{'2': 0, '1': 5, '0': 2}`
- family5 rate: `0.001221`
- exact rate: `0.000000`
- best counts: `[1, 1, 2, 2, 3]`
- preserves canonical: `False`
- mean profile score: `360.435872`
- line diff vs core: `{'2': {'extra': [], 'missing': []}, '1': {'extra': [3, 8], 'missing': []}, '0': {'extra': [0], 'missing': []}}`

## Best Multi-Trunk Candidate

- id: `23:core_plus_b0`
- candidate: `{'2': [], '1': [4, 6, 7], '0': [0, 5]}`
- family5 rate: `0.031738`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 2, 2]`
- preserves canonical: `False`

## Minimal Negative Neighbors

- `ABLATE_EXTRA_0_0` -> family5=`0.174316`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`, preserves_canonical=`True`

## Interpretation
- this scan checks whether unioning orbit-stable A2 trunks can improve coverage without destroying canonical profile behavior;
- line-level diffs and neighbor ablations provide a compact negative certificate around the best multi-trunk attempt.

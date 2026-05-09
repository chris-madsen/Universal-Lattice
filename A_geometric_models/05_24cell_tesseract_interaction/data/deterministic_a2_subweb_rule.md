# Deterministic A2 Subweb Rule

- base subset: `02`
- base dims: `[0, 2]`
- template priority: `['A2_B2-0_B1-3_B0-1', 'A2_B2-0_B1-4_B0-0', 'A2_B2-0_B1-2_B0-2']`

## Canonical Core

- best core template: `A2_B2-0_B1-3_B0-1`
- bucket-1 core lines: `[10, 9, 5]`
- bucket-0 core line: `[8]`

Interpretation:
- start from the `A2_B2-0_B1-3_B0-1` core, not from the more diffuse second-tier templates;
- treat bucket-1 lines as the main diagonal spine and bucket-0 as the primary anchor correction;

## Ordered Extensions

- bucket-1 extension order: `[2, 0]`
- bucket-0 extension order: `[7]`
- bucket-2 refinement order: `[1, 4]`

## Canonical Templates

### `A2_B2-0_B1-3_B0-1`

- bucket counts: `{'2': 0, '1': 3, '0': 1}`
- selections: `{'2': [], '1': [9, 10, 5], '0': [8]}`
- best single family5 rate: `0.364583`
- best counts: `[1, 1, 1, 1, 2]`

### `A2_B2-0_B1-4_B0-0`

- bucket counts: `{'2': 0, '1': 4, '0': 0}`
- selections: `{'2': [], '1': [2, 0, 9, 10], '0': []}`
- best single family5 rate: `0.343750`
- best counts: `[1, 1, 1, 1, 2]`

### `A2_B2-0_B1-2_B0-2`

- bucket counts: `{'2': 0, '1': 2, '0': 2}`
- selections: `{'2': [], '1': [2, 10], '0': [8, 7]}`
- best single family5 rate: `0.322917`
- best counts: `[1, 1, 1, 1, 2]`

## Orbit-Stable Transfer

### `12`

- classification: `good`
- overlap score: `0.452512`
- permutation: `[3, 0, 2, 1]`
- signs: `[-1, -1, -1, -1]`

- `A2_B2-0_B1-3_B0-1` -> mapped `{'2': [], '1': [1, 8, 11], '0': [3]}`, transfer family5=`0.184570`, overlap=`0.833333`
- `A2_B2-0_B1-4_B0-0` -> mapped `{'2': [], '1': [0, 1, 7, 11], '0': []}`, transfer family5=`0.183594`, overlap=`0.777778`
- `A2_B2-0_B1-2_B0-2` -> mapped `{'2': [], '1': [8, 11], '0': [2, 3]}`, transfer family5=`0.180664`, overlap=`1.000000`

### `13`

- classification: `strong`
- overlap score: `0.487831`
- permutation: `[1, 0, 3, 2]`
- signs: `[-1, 1, 1, 1]`

- `A2_B2-0_B1-3_B0-1` -> mapped `{'2': [], '1': [0, 2, 10], '0': [1]}`, transfer family5=`0.169922`, overlap=`1.000000`
- `A2_B2-0_B1-4_B0-0` -> mapped `{'2': [], '1': [2, 5, 6, 10], '0': []}`, transfer family5=`0.195312`, overlap=`0.866667`
- `A2_B2-0_B1-2_B0-2` -> mapped `{'2': [], '1': [0, 2], '0': [1, 4]}`, transfer family5=`0.177734`, overlap=`1.000000`

### `23`

- classification: `good`
- overlap score: `0.467359`
- permutation: `[3, 1, 2, 0]`
- signs: `[-1, -1, 1, 1]`

- `A2_B2-0_B1-3_B0-1` -> mapped `{'2': [], '1': [4, 6, 7], '0': [5]}`, transfer family5=`0.190430`, overlap=`1.000000`
- `A2_B2-0_B1-4_B0-0` -> mapped `{'2': [], '1': [3, 4, 6, 8], '0': []}`, transfer family5=`0.174805`, overlap=`0.866667`
- `A2_B2-0_B1-2_B0-2` -> mapped `{'2': [], '1': [6, 7], '0': [0, 5]}`, transfer family5=`0.162109`, overlap=`1.000000`

## Line Vectors

- line `0`: `[-1.0, -1.0, 0.0, 0.0]`
- line `1`: `[-1.0, 0.0, -1.0, 0.0]`
- line `2`: `[-1.0, 0.0, 0.0, -1.0]`
- line `4`: `[-1.0, 0.0, 1.0, 0.0]`
- line `5`: `[-1.0, 1.0, 0.0, 0.0]`
- line `7`: `[0.0, -1.0, 0.0, -1.0]`
- line `8`: `[0.0, -1.0, 0.0, 1.0]`
- line `9`: `[0.0, -1.0, 1.0, 0.0]`
- line `10`: `[0.0, 0.0, -1.0, -1.0]`

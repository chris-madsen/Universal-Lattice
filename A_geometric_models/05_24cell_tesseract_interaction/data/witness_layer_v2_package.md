# Witness Layer v2 Package

- captured at: `2026-05-09 02:10:24`
- projection batch: `12288`
- seeds: `[971001, 971002, 971003]`
- canonical counts target: `[1, 1, 1, 1, 2]`

## Best Orbit-Consistent Family

- base move on `02`: `replace 1:5->3`
- canonical on all subsets/seeds: `True`
- avg family5: `0.178569`
- min family5: `0.175483`
- avg delta vs core: `0.001411`

## Overlay/Diff vs Core

- `02` diff=`{'2': {'extra': [], 'missing': []}, '1': {'extra': [3], 'missing': [5]}, '0': {'extra': [], 'missing': []}}`; family5=`0.176324`; canonical_all_seeds=`True`
- `12` diff=`{'2': {'extra': [], 'missing': []}, '1': {'extra': [5], 'missing': [8]}, '0': {'extra': [], 'missing': []}}`; family5=`0.180393`; canonical_all_seeds=`True`
- `13` diff=`{'2': {'extra': [], 'missing': []}, '1': {'extra': [9], 'missing': [0]}, '0': {'extra': [], 'missing': []}}`; family5=`0.182075`; canonical_all_seeds=`True`
- `23` diff=`{'2': {'extra': [], 'missing': []}, '1': {'extra': [2], 'missing': [7]}, '0': {'extra': [], 'missing': []}}`; family5=`0.175483`; canonical_all_seeds=`True`

## Nearby Negative Certificates

### Add-Back Removed Line

- `02` add-back -> family5=`0.029243`, canonical_all_seeds=`False`, best_counts(one seed)=`[1, 1, 1, 2, 2]`
- `12` add-back -> family5=`0.030328`, canonical_all_seeds=`False`, best_counts(one seed)=`[1, 1, 1, 2, 2]`
- `13` add-back -> family5=`0.028592`, canonical_all_seeds=`False`, best_counts(one seed)=`[1, 1, 1, 2, 2]`
- `23` add-back -> family5=`0.029053`, canonical_all_seeds=`False`, best_counts(one seed)=`[1, 1, 1, 2, 2]`

### Dominated Neighbor Moves

- `replace 1:10->2` -> avg_family5=`0.178243`, avg_delta_vs_core=`0.001085`, delta_vs_best=`-0.000326`
- `replace 1:5->0` -> avg_family5=`0.177843`, avg_delta_vs_core=`0.000685`, delta_vs_best=`-0.000726`
- `replace 1:9->2` -> avg_family5=`0.177280`, avg_delta_vs_core=`0.000122`, delta_vs_best=`-0.001289`

## Comparison vs Live Winners

- `02` live=`A2_B2-0_B1-4_B0-0@02`; replacement family5=`0.176324` vs live=`0.180800`; delta=`-0.004476`; non_inferior=`True`
- `12` live=`A2_B2-0_B1-2_B0-2@12`; replacement family5=`0.180393` vs live=`0.178006`; delta=`0.002387`; non_inferior=`True`
- `13` live=`A2_B2-0_B1-3_B0-1@13`; replacement family5=`0.182075` vs live=`0.180040`; delta=`0.002035`; non_inferior=`True`
- `23` live=`A2_B2-0_B1-4_B0-0@23`; replacement family5=`0.175483` vs live=`0.180230`; delta=`-0.004747`; non_inferior=`True`

## Decision Signals

- canonical all subsets/seeds: `True`
- non-inferior vs live winners: `True`
- aggregate family5 delta vs live: `-0.0012003580729166644`
- subset flags: `{'02': True, '12': True, '13': True, '23': True}`

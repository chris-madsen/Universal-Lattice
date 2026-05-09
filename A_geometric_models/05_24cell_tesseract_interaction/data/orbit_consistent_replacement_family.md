# Orbit-Consistent Replacement Family

- captured at: `2026-05-09 01:05:08`
- projection batch: `3072`
- tested replacement families: `16`

## Core Baseline

- `02` core -> family5=`0.184245`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`
- `12` core -> family5=`0.192383`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`
- `13` core -> family5=`0.168620`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`
- `23` core -> family5=`0.179036`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`

## Best Family

- base move on `02`: `replace 1:5->3`
- all canonical: `True`
- avg family5: `0.182210`
- min family5: `0.178385`
- avg improvement vs core: `0.001139`

- `02` -> family5=`0.178385`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`, selections=`{'2': [], '1': [3, 9, 10], '0': [8]}`
- `12` -> family5=`0.185872`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`, selections=`{'2': [], '1': [1, 5, 11], '0': [3]}`
- `13` -> family5=`0.180339`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`, selections=`{'2': [], '1': [2, 9, 10], '0': [1]}`
- `23` -> family5=`0.184245`, best_counts=`[1, 1, 1, 1, 2]`, canonical=`True`, selections=`{'2': [], '1': [2, 4, 6], '0': [5]}`

## Top Families

- `replace 1:5->3` -> canonical_all=`True`, avg_family5=`0.182210`, min_family5=`0.178385`, avg_delta=`0.001139`
- `replace 1:5->0` -> canonical_all=`True`, avg_family5=`0.180420`, min_family5=`0.171549`, avg_delta=`-0.000651`
- `replace 1:9->2` -> canonical_all=`True`, avg_family5=`0.179443`, min_family5=`0.168945`, avg_delta=`-0.001628`
- `replace 1:5->2` -> canonical_all=`True`, avg_family5=`0.176839`, min_family5=`0.174154`, avg_delta=`-0.004232`
- `replace 1:10->2` -> canonical_all=`True`, avg_family5=`0.175863`, min_family5=`0.170898`, avg_delta=`-0.005208`
- `replace 1:9->3` -> canonical_all=`True`, avg_family5=`0.165771`, min_family5=`0.162435`, avg_delta=`-0.015299`
- `replace 1:10->3` -> canonical_all=`True`, avg_family5=`0.165771`, min_family5=`0.153971`, avg_delta=`-0.015299`
- `replace 1:9->6` -> canonical_all=`True`, avg_family5=`0.164062`, min_family5=`0.151693`, avg_delta=`-0.017008`
- `replace 1:10->11` -> canonical_all=`True`, avg_family5=`0.163574`, min_family5=`0.155273`, avg_delta=`-0.017497`
- `replace 1:10->6` -> canonical_all=`True`, avg_family5=`0.155762`, min_family5=`0.153971`, avg_delta=`-0.025309`
- `replace 0:8->7` -> canonical_all=`True`, avg_family5=`0.154948`, min_family5=`0.146810`, avg_delta=`-0.026123`
- `replace 1:10->0` -> canonical_all=`True`, avg_family5=`0.153239`, min_family5=`0.147135`, avg_delta=`-0.027832`

## Interpretation
- this converts per-subset gated replacements into one orbit-consistent rule family;
- if canonical survives across all subsets with nonnegative aggregate delta, this is a constructive upgrade layer over the core.

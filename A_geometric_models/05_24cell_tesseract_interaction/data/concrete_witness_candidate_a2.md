# Concrete Witness Candidate: A2 Core

- candidate: `A2_B2-0_B1-3_B0-1@02`
- projection batch: `8192`
- canonical counts target: `[1, 1, 1, 1, 2]`

## Base Candidate

- selections: `{'2': [], '1': [9, 10, 5], '0': [8]}`
- family5 rate: `0.178467`
- exact rate: `0.000000`
- best counts: `[1, 1, 1, 1, 2]`
- preserves canonical counts: `True`

## Single-Line Ablations

- `ABLATE_1_9` -> family5=`0.873535`, best_counts=`[1, 1, 1, 1, 1]`, preserves canonical=`False`
- `ABLATE_1_10` -> family5=`0.871460`, best_counts=`[1, 1, 1, 1, 1]`, preserves canonical=`False`
- `ABLATE_1_5` -> family5=`0.864136`, best_counts=`[1, 1, 1, 1, 1]`, preserves canonical=`False`
- `ABLATE_0_8` -> family5=`0.862427`, best_counts=`[1, 1, 1, 1, 1]`, preserves canonical=`False`

## Single-Line Additions

- `ADD_1_2` -> family5=`0.025146`, best_counts=`[1, 1, 1, 2, 2]`, preserves canonical=`False`
- `ADD_1_0` -> family5=`0.027100`, best_counts=`[1, 1, 1, 2, 2]`, preserves canonical=`False`
- `ADD_0_7` -> family5=`0.028809`, best_counts=`[1, 1, 1, 2, 2]`, preserves canonical=`False`
- `ADD_2_1` -> family5=`0.029053`, best_counts=`[1, 1, 1, 2, 2]`, preserves canonical=`False`
- `ADD_2_4` -> family5=`0.034180`, best_counts=`[1, 1, 1, 2, 2]`, preserves canonical=`False`

## Orbit Transfers

- `12` (good) -> family5=`0.179321`, best_counts=`[1, 1, 1, 1, 2]`, preserves canonical=`True`
- `13` (strong) -> family5=`0.185547`, best_counts=`[1, 1, 1, 1, 2]`, preserves canonical=`True`
- `23` (good) -> family5=`0.184814`, best_counts=`[1, 1, 1, 1, 2]`, preserves canonical=`True`

## Verdict

- all single ablations break canonical counts: `True`
- all single additions break canonical counts: `True`
- all transfers hold canonical counts and rate >= 0.16: `True`
- average transfer family5 rate: `0.183228`
- concrete witness candidate: `True`

## Interpretation
- this is not yet a full proof of the entire generating lattice, but it is a concrete witness candidate for the strongest `A2` subweb class;
- the chosen core survives orbit transfer and breaks immediately when over-pruned or over-extended in one-line moves;
- that is exactly the behavior we want from a candidate that is more than a loose scaffold.

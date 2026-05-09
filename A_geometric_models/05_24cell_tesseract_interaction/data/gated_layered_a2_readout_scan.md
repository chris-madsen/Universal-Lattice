# Gated Layered A2 Readout Scan

- captured at: `2026-05-09 01:02:45`
- canonical counts target: `[1, 1, 1, 1, 2]`
- gate: preserve canonical + family5 >= `core * 0.9`

## Subset `02`

- core family5: `0.176025`
- core exact: `0.000000`
- core best counts: `[1, 1, 1, 1, 2]`
- add moves tested: `8`
- replace moves tested: `16`
- safe depth-1 states: `12`
- safe depth-2 states: `0`

### Top Add Moves

- add `2:4` -> family5=`0.039551`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:6` -> family5=`0.036133`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:0` -> family5=`0.029785`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:2` -> family5=`0.027344`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `2:1` -> family5=`0.026367`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `0:7` -> family5=`0.025879`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`

### Top Replace Moves

- replace `1:5->3` -> family5=`0.186035`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:5->2` -> family5=`0.181152`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:10->2` -> family5=`0.181152`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `0:8->7` -> family5=`0.180176`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:5->0` -> family5=`0.169922`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:9->2` -> family5=`0.169922`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:10->0` -> family5=`0.167969`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:10->3` -> family5=`0.162598`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`

### Safe Depth-1

- `replace 1:5->3` -> family5=`0.186035`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:5->2` -> family5=`0.181152`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->2` -> family5=`0.181152`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 0:8->7` -> family5=`0.180176`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:5->0` -> family5=`0.169922`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:9->2` -> family5=`0.169922`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->0` -> family5=`0.167969`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->3` -> family5=`0.162598`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->11` -> family5=`0.162109`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:9->0` -> family5=`0.160156`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:9->6` -> family5=`0.160156`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:9->3` -> family5=`0.159180`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`

### Safe Depth-2

- none

## Subset `12`

- core family5: `0.177979`
- core exact: `0.000000`
- core best counts: `[1, 1, 1, 1, 2]`
- add moves tested: `8`
- replace moves tested: `16`
- safe depth-1 states: `7`
- safe depth-2 states: `0`

### Top Add Moves

- add `2:9` -> family5=`0.043457`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:10` -> family5=`0.033203`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:7` -> family5=`0.032715`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `2:6` -> family5=`0.032227`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:5` -> family5=`0.029785`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `0:2` -> family5=`0.027344`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`

### Top Replace Moves

- replace `1:8->5` -> family5=`0.188965`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:8->7` -> family5=`0.179688`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:8->0` -> family5=`0.176270`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:1->0` -> family5=`0.173828`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:11->0` -> family5=`0.170898`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:11->10` -> family5=`0.167969`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `0:3->2` -> family5=`0.167480`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:11->5` -> family5=`0.158691`, best_counts=`[1, 1, 1, 1, 2]`, gate=`False`

### Safe Depth-1

- `replace 1:8->5` -> family5=`0.188965`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:8->7` -> family5=`0.179688`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:8->0` -> family5=`0.176270`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:1->0` -> family5=`0.173828`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:11->0` -> family5=`0.170898`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:11->10` -> family5=`0.167969`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 0:3->2` -> family5=`0.167480`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`

### Safe Depth-2

- none

## Subset `13`

- core family5: `0.175293`
- core exact: `0.000000`
- core best counts: `[1, 1, 1, 1, 2]`
- add moves tested: `8`
- replace moves tested: `16`
- safe depth-1 states: `11`
- safe depth-2 states: `0`

### Top Add Moves

- add `1:3` -> family5=`0.043945`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:6` -> family5=`0.032715`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:11` -> family5=`0.030762`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `2:8` -> family5=`0.029785`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `0:4` -> family5=`0.027344`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:9` -> family5=`0.026855`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`

### Top Replace Moves

- replace `1:0->9` -> family5=`0.191406`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:0->5` -> family5=`0.190430`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:2->6` -> family5=`0.189941`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:10->9` -> family5=`0.182617`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:10->6` -> family5=`0.178711`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:0->6` -> family5=`0.171875`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `0:1->4` -> family5=`0.166016`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:10->3` -> family5=`0.163086`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`

### Safe Depth-1

- `replace 1:0->9` -> family5=`0.191406`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:0->5` -> family5=`0.190430`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:2->6` -> family5=`0.189941`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->9` -> family5=`0.182617`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->6` -> family5=`0.178711`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:0->6` -> family5=`0.171875`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 0:1->4` -> family5=`0.166016`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->3` -> family5=`0.163086`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->5` -> family5=`0.163086`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:10->11` -> family5=`0.160645`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:2->3` -> family5=`0.159180`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`

### Safe Depth-2

- none

## Subset `23`

- core family5: `0.187256`
- core exact: `0.000000`
- core best counts: `[1, 1, 1, 1, 2]`
- add moves tested: `8`
- replace moves tested: `16`
- safe depth-1 states: `7`
- safe depth-2 states: `0`

### Top Add Moves

- add `2:11` -> family5=`0.037598`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:9` -> family5=`0.035645`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `2:10` -> family5=`0.034668`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `0:0` -> family5=`0.028809`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:8` -> family5=`0.027832`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`
- add `1:3` -> family5=`0.027344`, best_counts=`[1, 1, 1, 2, 2]`, gate=`False`

### Top Replace Moves

- replace `1:6->3` -> family5=`0.188965`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:7->2` -> family5=`0.183594`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:4->3` -> family5=`0.178711`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:7->3` -> family5=`0.178711`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:7->8` -> family5=`0.176758`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:6->8` -> family5=`0.173340`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:6->9` -> family5=`0.172852`, best_counts=`[1, 1, 1, 1, 2]`, gate=`True`
- replace `1:6->2` -> family5=`0.166016`, best_counts=`[1, 1, 1, 1, 2]`, gate=`False`

### Safe Depth-1

- `replace 1:6->3` -> family5=`0.188965`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:7->2` -> family5=`0.183594`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:4->3` -> family5=`0.178711`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:7->3` -> family5=`0.178711`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:7->8` -> family5=`0.176758`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:6->8` -> family5=`0.173340`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`
- `replace 1:6->9` -> family5=`0.172852`, exact=`0.000000`, best_counts=`[1, 1, 1, 1, 2]`

### Safe Depth-2

- none

## Interpretation
- this scan moves from raw unions to gated local moves around the core and checks where canonical behavior survives;
- safe moves are candidates for layered constructive expansion; failed moves are immediate negative certificates.

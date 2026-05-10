# Universal Rune Lattice From 2×Tesseract + 16-cell

## What This Document Is
This is a reconstruction story, not a parameter dump.

Goal: explain, in mathematically explicit but human language, how the approved rune-generative lattice is produced from a fixed 4D configuration of three objects:
- `T1`: first tesseract,
- `T2`: second tesseract,
- `C16`: one 16-cell layer.

The output grid is the approved one used in H12 (`leader + complement`).

## Why This Was Needed
During the search phase, many configurations were tested. Once the target lattice was approved visually and structurally, the next task became different:
- not to continue brute force,
- but to rebuild the same lattice deterministically,
- and show that it comes from a real geometric pipeline.

So this package does two things at once:
- keeps the approved 15-node/53-segment lattice as the canonical output frame,
- proves that this frame is supported by a polytope-derived 2D arrangement.

## Mathematical Objects
We work in `R^4`.

Tesseract vertex set:
\[
T = \{(\pm 1, \pm 1, \pm 1, \pm 1)\}.
\]

16-cell vertex set:
\[
C_{16} = \{\pm e_1, \pm e_2, \pm e_3, \pm e_4\}.
\]

Edges are standard 1-skeleton edges of each polytope.
From edges we extract direction classes modulo sign:
\[
v \sim -v.
\]

That gives finite directional families for each layer.

## Relative Orientation: Double Rotation
Two independent 2-planes are used. For a selected plane decomposition,
\[
R(\alpha, \beta) = R_{(i_1,j_1)}(\alpha)\,R_{(i_2,j_2)}(\beta).
\]

The second tesseract and the 16-cell layer are rotated by such operators with parameters coming from the approved H12 witness state.

## Projection `R^4 -> R^2`
A deterministic projection matrix `P` is selected from the same projection family used by the approved run.

For any 4D direction vector `v`:
\[
\pi(v) = Pv \in R^2.
\]

Then angular classes are computed in `R^2`, clustered with fixed tolerance, and converted into segment support on the canonical node frame.

## Canonical Output Frame
The published rune frame uses fixed readable levels:
- x-levels: `0, 1, 2`,
- y-levels: `0, 1, 1.5, 2, 3`.

Hence `15` nodes total.

The approved lattice has:
- `53` segments in union,
- generated as `leader (35)` plus `complement (18)`.

## What The Script Actually Does
The build script `build_universal_from_2T_plus_16.py` runs this pipeline.

1. Reads approved H12 state from:
- `universal/data/h12_complement_state.json` (repo-local snapshot).
- legacy fallback: `research/async_state/h12_complement/state.json`.

2. Restores fixed witness specs:
- leader spec (`T1 + T2` layer),
- best complement spec (`C16` layer).

3. Rebuilds three layer segment supports:
- `seg_t1`, `seg_t2`, `seg_c16`.

4. Builds the arrangement cloud from real projected edges:
- gets unique projected lines,
- computes all pairwise line intersections in a bounded geometric window,
- stores both raw and deduplicated cloud.

5. Recovers the 3×5 level scaffold from the cloud:
- 1D clustering on x and y coordinates,
- deterministic index-wise mapping to canonical levels.

6. Produces subset proof artifacts:
- canonical nodes are embedded in the intersection cloud (with numerical tolerance),
- canonical segments are supported by arrangement angle families.

7. Renders output images with layer provenance colors.

## Important Conceptual Point
This is not literal 4D volume intersection of bodies.

The lattice is obtained from a **projected line-arrangement readout** of 4D sources:
- edge-direction families from `T1`, `T2`, `C16`,
- projected to 2D,
- interpreted as line families,
- read out on the canonical node frame.

So “intersection cloud” here means intersections of projected arrangement lines, not intersection of solid 4D volumes.

## Why The Result Is Not Arbitrary
The package writes machine-checkable artifacts:
- `out/intersection_cloud.json`: full deduplicated cloud,
- `out/subset_proof.json`: embedding/support proof,
- `out/layer_contributions.json`: per-segment provenance flags,
- `out/witness_parameters.json`: exact witness parameters used for reconstruction.

This is exactly the anti-"made-up points" guarantee: the final frame is tied back to computed arrangement geometry.

## Color Semantics In The Main Figure
In `out/universal_lattice_layers.png`, each segment color reflects source provenance:
- `#00008B`: from `T1` only,
- `#8B0000`: from `T2` only,
- `#8B008B`: from `C16` only,
- `#FF00FF`: overlap `T1 ∩ T2`,
- `#7F00FF`: overlap `T1 ∩ C16`,
- `#FF007F`: overlap `T2 ∩ C16`,
- `#8B00FF`: overlap of all three.

A legend is rendered directly on the image.

## Output Files
After build, `universal/out/` contains:
- `nodes.json`,
- `segments.json`,
- `layer_contributions.json`,
- `witness_parameters.json`,
- `intersection_cloud.json`,
- `subset_proof.json`,
- `summary.md`,
- `universal_lattice_layers.png`,
- `universal_lattice_only.png`,
- `universal_lattice_layers_provenance.png`.

## How To Reproduce
```bash
make -C universal universal-build
```

This command is deterministic for the same repository state.

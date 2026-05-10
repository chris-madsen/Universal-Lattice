# Universal Rune Lattice From 2×Tesseract + 16-cell

## Statement
This package reconstructs the approved rune-generative lattice from a fixed 4D configuration:
- first tesseract `T1`,
- second tesseract `T2` (double-rotated relative to `T1`),
- one `16-cell` layer used as the complement bridge.

The final published grid is the approved H12 union (`leader + complement`), and this package adds explicit geometric provenance and embedding checks.

## 4D Objects
- Tesseract vertex set:
  `T = {(±1, ±1, ±1, ±1)}`.
- 16-cell vertex set:
  `C16 = {±e1, ±e2, ±e3, ±e4}`.

For each polytope we use edge-direction classes modulo sign (`v ~ -v`).

## Relative Configuration
Let
- `R(α, β; planes)` be a double rotation in two orthogonal 2-planes,
- `P` be a deterministic 2D projection matrix produced by the H12 projection family.

The reconstruction uses the fixed H12 witness parameters stored in:
- `research/async_state/h12_complement/state.json`.

So the model is not searched again; it is rebuilt from the approved witness.

## Projection and Arrangement
For each layer, vectors are projected by
`π(v) = P v`.

From projected edge-direction families we extract line families and then segment candidates on the canonical 15-node frame.

## Canonical Frame
The approved readable frame is:
- x-levels: `{0, 1, 2}`,
- y-levels: `{0, 1, 1.5, 2, 3}`,
- total nodes: `15`.

The lattice segments are taken from the approved H12 union and rendered on this frame.

## Why This Is Not "Made Up"
The script computes a full 2D intersection cloud from projected polytope edge lines:
- all pairwise line intersections in a bounded geometric window,
- de-duplicated intersection cloud,
- recovered 3×5 level structure from that cloud,
- proof that the canonical node-frame is embedded in this cloud,
- proof that every canonical segment is supported by at least one arrangement line.

These checks are saved to:
- `out/intersection_cloud.json`,
- `out/subset_proof.json`.

## Layer Colors
The rendering uses the requested palette:
- `T1`: `#00008B` (Dark Blue),
- `T2`: `#8B0000` (Dark Red),
- `C16`: `#8B008B` (Dark Magenta),
- overlaps: `#FF00FF`, `#7F00FF`, `#FF007F`,
- full overlap: `#8B00FF` (Electric Violet).

## Generated Artifacts
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

## Run
```bash
make -C universal universal-build
```

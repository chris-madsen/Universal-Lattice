# Universal Folder Recovery Plan

## Goal
Restore `universal/` as a standalone reproducible package that rebuilds the approved lattice from H12 artifacts and proves it is embedded in a polytope-derived intersection cloud.

## Required Files
- `build_universal_from_2T_plus_16.py`
- `universal_rune_lattice_from_2T_plus_16.md`
- `Makefile`
- `out/` generated artifacts

## Recovery Rules
- Use approved H12 state as ground truth source (`research/async_state/h12_complement/state.json`).
- Keep canonical 15-node frame shape exactly as approved visual form.
- Do not use manual drawing-only output without geometric provenance.
- Provide machine-readable evidence:
  - `intersection_cloud.json`
  - `subset_proof.json`
  - `layer_contributions.json`

## Success Criteria
- `make -C universal universal-build` finishes without errors.
- `out/universal_lattice_layers.png` is generated and visually matches the approved shape.
- `out/summary.md` includes segment counts and embedding checks.

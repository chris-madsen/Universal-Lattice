# 12_polytope_pair_double_rotation_match

This is the active H12 branch.

Goal:
- first, search real 4D source-pair combinations against the simplified lattice from
  `simplified_lattice_central_bundle.py`;
- then search the complement to the fixed leader against `universal-lattice.py`.

The branch is not a standalone topology filter. The topology signature is used as
an accelerator so affine/similarity multiplication does not explode the search
space.

## Live Service

- service: `runes-h12-polytope-pair.service`
- service: `runes-h12-complement.service`
- slice: `runes-research.slice`
- state: `research/async_state/h12_polytope_pair/`
- state: `research/async_state/h12_complement/`

## Search Shape

- sources: `24-cell`, `tesseract`, `16-cell`
- source pairs: `(24,24)`, `(24,T)`, `(24,16)`, `(T,T)`, `(T,16)`, `(16,16)`
- double-rotation ratios: `1:1`, `1:2`, `1:3`, `2:3`, `3:4`, `1:4`
- base angles: `7.5`, `15`, `18`, `22.5`, `30`, `36`, `45`, `60`, `72`, `90`
- plane decompositions: `3`
- readout modes: `3`
- deterministic projection candidates: `155,520`

## Files

- `PLAN.md` - implementation plan for this branch.
- `result.md` - live branch status, updated by the async job.
- `scripts/render_best_candidate.py` - target/candidate/overlay renderer.
- `scripts/render_best_complement_candidate.py` - complement/union renderer.
- `data/complement_target_truth.md` - fixed complement target extracted from `universal-lattice.py`.
- `figures/` - rendered comparison artifacts.

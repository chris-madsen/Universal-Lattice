# Result

Status: prune_red_flag

## Summary

Baseline and logical prune completed. Since branch `01_raw_24cell_web` did not reach the target family-count, pure affine normalization is weakened: an invertible affine map cannot by itself merge distinct raw direction classes into the target 5-family lattice.

## Best Witness

- `data/baseline_affine_constraints.json`
- `data/prune_affine_direction_invariance.json`

## Blocking Issues

This branch is weakened unless an additional selection mechanism is introduced; that would move it closer to later branches rather than keep it as pure affine normalization.

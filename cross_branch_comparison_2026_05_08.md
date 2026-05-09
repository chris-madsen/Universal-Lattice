# Cross-Branch Comparison — 2026-05-08

## Current Snapshot

### Branch 08 — `f4_root_arrangement`
- focused refinement winner: `L5_S5`
- `family_count=5` hit rate: `0.0004`
- exact profile `[1,1,1,1,6]` hit rate: `0.0004`
- note: initial `L8_S2` / `L4_S6` hits did **not** survive larger resampling
- axis/half/long decomposition check:
  - best decomposed class: `A0_L6_H4`
  - `family_count=5` hit rate: `0.0016`
  - reading: decomposition does not rescue branch `08` into a strong axis-scaffold source

### Branch 09 — `f4_b4_hybrid`
- focused refinement winner: `A4_L6_H0`
- `family_count=5` hit rate: `0.0004`
- exact profile `[1,1,1,1,6]` hit rate: `0.0000`
- key read: half-shell is not helping; the hybrid currently collapses toward `axis + long`
- pure axis+long push:
  - best class: `A2_L4_H0`
  - `family_count=5` hit rate: `0.1456`
  - reading: `axis+long` is now a strong standalone signal, not just a fallback narrative

### Branch 05 — `24cell_tesseract_interaction`
#### Reduced scaffold model
- best family-5 class: `T3_C4`
- `family_count=5` hit rate: `0.0330`
- best exact-profile class: `T4_C6`
- exact profile `[1,1,1,1,6]` hit rate: `0.0007`
- reading: this is currently the strongest live branch by a wide margin

#### Async GA+ACO tree-search
- background service now runs `GA + ACO` over a tree:
  - `axis subset -> orbit bucket template -> concrete line selection`
- old brute-force `T/C` scan is retained only as a harmonic prior source
- current root-branch leaders are concentrated in:
  - `axis_size = 2`
  - `total_cell_count = 4`
  - templates around `A2_B2-0_B1-2_B0-2`, `A2_B2-0_B1-3_B0-1`, `A2_B2-0_B1-4_B0-0`, `A2_B2-1_B1-1_B0-2`
- reading: branch `05` is no longer just a coarse class scan; it is now narrowing toward concrete subweb/readout trunks

#### Full edge-union sanity check
- full union scan over `1000` projections
- family-count histogram: `8..16`
- best full-union family count: `8`
- reading: the branch is strong as a **scaffold-level** model, but raw full edge-union is too rich and needs subgraph/readout selection

## Reading

Right now branch `05` is the strongest live branch, but in a refined sense:
- it clearly dominates `08` and `09` on scaffold-level statistical resonance;
- it does **not** yet provide a raw full-graph witness via simple edge-union;
- therefore the right next move is not to abandon `05`, but to search for a selected subgraph / readout inside the richer `tesseract + 24-cell` union.

## Working Interpretation

- branch `09` now looks more like a bridge that pointed us toward `axis + long` than like an independent winner;
- branch `08` remains useful as an arrangement-level reference and control branch;
- branch `10` (`orbit_selected_subweb`) has become more relevant, because the full union is richer than the target lattice and may require symmetry-guided pruning;
- the async `GA+ACO` run is already reinforcing branch `10` language: the strongest live trunks are all `A2` orbit templates, not arbitrary raw `T/C` buckets.

## Next Move

1. Keep branch `05` async `GA+ACO` search running and watch for stable root-branch convergence.
2. Use branch `10` as the symmetry language for compressing those winners into explicit subweb/readout rules.
3. Keep branches `08` and `09` as supporting references, not as primary front-runners.

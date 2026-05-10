# Common Research Modules

A common layer for all research branches.

Purpose of modules:
- `lattice_signature.py`: extract lattice signature from `universal-lattice.py`
- `grid_generativity.py`: checks for grid generative grammar
- `polytopes.py`: canonical 4D objects and their wireframes
- `projection.py`: 4D -> 2D projections and affine/similarity transformations
- `family_kernel.py`: shared projection-family hot kernel in Python + bridge to shared Rust kernel
- `meta_search.py`: general FFT/DFT priors, human ETA, weighted sampling and ranking helpers for GA/ACO search
- `arrangements.py`: maximal lines, intersections, local fans
- `group_filters.py`: symmetric and orbital filtering
- `scoring.py`: strict / structural / generative / complexity scoring
- `render.py`: overlays, difference maps, diagnostic panels

# Common Research Modules

Общий слой для всех веток исследования.

Назначение модулей:
- `lattice_signature.py`: извлечение сигнатуры решётки из `universal-lattice.py`
- `grid_generativity.py`: проверки порождающей грамматики решётки
- `polytopes.py`: канонические 4D-объекты и их каркасы
- `projection.py`: 4D -> 2D проекции и affine/similarity преобразования
- `family_kernel.py`: общий projection-family hot kernel в Python + bridge к shared Rust kernel
- `meta_search.py`: общие FFT/DFT priors, human ETA, weighted sampling и ranking helpers для GA/ACO поиска
- `arrangements.py`: maximal lines, пересечения, локальные веера
- `group_filters.py`: симметрийный и орбитальный отсев
- `scoring.py`: strict / structural / generative / complexity scoring
- `render.py`: overlays, difference maps, диагностические панели

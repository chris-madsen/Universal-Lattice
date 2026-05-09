# Log

## YYYY-MM-DD HH:MM — baseline
Цель:
Гипотеза:
Скрипт:
Артефакты:
Что считаю:
Формулы / reasoning:
Промежуточные результаты:
Что это значит:
Сложность:
Следующий шаг:

## 2026-05-08 21:04 — baseline
Цель: зафиксировать, какие свойства решётки branch `03` вправе менять affine-нормализацией, а какие нет.
Гипотеза: `03_affine_normalized_24cell`
Скрипт: `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_affine_constraints.json`
- `data/baseline_affine_constraints.md`
Что считаю:
- target family-count решётки;
- список структурных свойств, которые invertible affine map сохраняет.
Формулы / reasoning:
- affine-нормализация может менять углы и отношения длин;
- но она не склеивает разные направления как projective classes и не ломает incidence сама по себе.
Промежуточные результаты:
- target absolute family count: `5`
- affine invariants: `['collinearity', 'line incidence', 'intersection graph', 'projective direction distinctness under invertible linear map']`
Что это значит:
- ветка `03` должна объяснять решётку без надежды на чудесное схлопывание разных направлений только affine-преобразованием.
Сложность:
- низкая.
Следующий шаг:
- перейти к prune и проверить, что означает это ограничение на фоне результатов `01_raw_24cell_web`.

## 2026-05-08 21:04 — prune
Цель: проверить, способна ли чистая affine-нормализация сама по себе спасти branch `03`, если branch `01` уже не попал в target family-count.
Гипотеза: `03_affine_normalized_24cell`
Скрипт: `research/A_geometric_models/03_affine_normalized_24cell/scripts/run.py --stage prune`
Артефакты:
- `data/prune_affine_direction_invariance.json`
- `data/prune_affine_direction_invariance.md`
Что считаю:
- результаты prune из `01_raw_24cell_web`;
- projective invariant: invertible affine map не склеивает разные direction classes в одну.
Формулы / reasoning:
- если raw branch `01` не даёт target family-count `5`, а лучший найденный уровень `7`, то pure affine normalization сама по себе не превратит `7` distinct direction classes в `5`;
- значит ветка `03` в чистом виде ослабляется логически, а не только численно.
Промежуточные результаты:
- raw exact matches from `01`: `0`
- best raw family count: `7`
- implication: `Pure raw+affine is weakened; any rescue would require additional selection/pruning beyond affine normalization itself.`
Что это значит:
- ветка `03_affine_normalized_24cell` сейчас получает быстрый логический red flag;
- если её когда-то спасать, то уже не как “raw + affine only”, а через дополнительный selection mechanism, что ближе к другим веткам плана.
Сложность:
- низкая; это логический prune без тяжёлого поиска.
Следующий шаг:
- зафиксировать ослабление ветки и перейти к `06_double_rotation_overlay`.

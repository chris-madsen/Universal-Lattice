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

## 2026-05-08 20:56 — baseline
Цель: построить формальную baseline-сигнатуру текущей решётки перед любыми поисками по 24-cell.
Гипотеза: `01_raw_24cell_web`
Скрипт: `research/A_geometric_models/01_raw_24cell_web/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_lattice_signature.json`
- `data/baseline_grid_generativity.json`
- `data/baseline_summary.md`
- `figures/baseline_lattice_signature.svg`
Что считаю:
- число исходных сегментов;
- число уникальных maximal lines;
- число узлов, полученных как пересечения maximal lines;
- семейства направлений;
- базовую generative-грамматику решётки.
Формулы / reasoning:
- сегменты берутся из `universal-lattice.py` как канонический набор;
- collinear/overlapping сегменты схлопываются в maximal lines;
- узлы считаются как пересечения maximal lines внутри решётки;
- baseline нужен как цель сравнения для всех следующих гипотез.
Промежуточные результаты:
- raw segments: `29`
- maximal lines: `27`
- nodes: `93`
- script nodes match inferred intersections: `False`
- family counts: `{'vertical': 3, 'slope_abs_1_2': 6, 'slope_abs_3_4': 4, 'slope_abs_1_1': 8, 'slope_abs_3_2': 6}`
- center/top/bottom degrees: `5` / `5` / `5`
Что это значит:
- у ветки появился строгий baseline-объект сравнения, а не только картинка на глаз;
- дальше можно переходить к `prune`: сначала сравнить сигнатуры узлов и семейства raw 24-cell web против этого baseline.
Сложность:
- низкая; baseline извлекается детерминированно и быстро.
Следующий шаг:
- перейти к `prune` и проверить, совместим ли raw projected 24-cell вообще по числу семейств и по локальным сигнатурам узлов.

## 2026-05-08 21:00 — baseline-correction
Цель: уточнить baseline, отделив реальные опорные узлы решётки от ложных пересечений, которые возникают при полном продолжении прямых.
Гипотеза: `01_raw_24cell_web`
Скрипт: `research/A_geometric_models/01_raw_24cell_web/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_lattice_signature.json`
- `data/baseline_grid_generativity.json`
- `data/baseline_summary.md`
- `figures/baseline_lattice_signature.svg`
Что считаю:
- anchor nodes как явные узлы самой решётки;
- arrangement intersections как все пересечения maximal lines;
- false intersections как разность между этими двумя уровнями.
Формулы / reasoning:
- baseline решётки нельзя сводить только к полному line arrangement, иначе появляется много ложных узлов;
- для generative grammar важнее anchor-узлы и их сигнатуры, а false intersections надо хранить отдельно как диагностический слой.
Промежуточные результаты:
- anchor nodes: `15`
- arrangement intersections: `93`
- false intersections: `78`
- family counts: `{'vertical': 3, 'slope_abs_1_2': 6, 'slope_abs_3_4': 4, 'slope_abs_1_1': 8, 'slope_abs_3_2': 6}`
- center/top/bottom degrees: `5` / `5` / `5`
Что это значит:
- baseline теперь отражает именно решётку как порождающий объект, а не только её полное arrangement-продолжение;
- отдельный слой false intersections пригодится позже для веток, где `F4` или другие arrangements начнут создавать ложные узлы.
Сложность:
- низкая; это структурное уточнение baseline, а не тяжёлый расчёт.
Следующий шаг:
- перейти к `prune` и проверить, насколько сырая projected web 24-cell вообще совместима с target family-count и базовой узловой грамматикой.

## 2026-05-08 21:00 — prune
Цель: проверить, насколько сырая projected edge-web 24-cell вообще совместима с целевым числом семейств направлений нашей решётки.
Гипотеза: `01_raw_24cell_web`
Скрипт: `research/A_geometric_models/01_raw_24cell_web/scripts/run.py --stage prune`
Артефакты:
- `data/prune_raw_24cell_family_scan.json`
- `data/prune_summary.md`
Что считаю:
- у canonical 24-cell берутся вершины и 96 рёбер;
- затем для `samples=1200`` случайных ортонормальных 2D-проекций считается число абсолютных семейств направлений на raw projected edge-web;
- сравнивается с target family-count решётки `5`.
Формулы / reasoning:
- это ещё не доказательство и не полный search;
- это быстрый prune: если raw 24-cell почти никогда не попадает даже в target family-count, ветка уже выглядит напряжённой;
- если попадания есть, ветка сохраняет правдоподобие и идёт дальше.
Промежуточные результаты:
- exact family-count matches: `0` из `1200`
- histogram: `{7: 5, 12: 630, 11: 332, 10: 170, 9: 49, 8: 14}`
- best candidate family count / projected vertices / projected edges / zero edges: `7` / `24` / `96` / `0`
Что это значит:
- prune даёт первую необходимую sanity-проверку для `01_raw_24cell_web`;
- следующий шаг зависит от того, выглядит ли совпадение по числу семейств редким исключением или устойчивым режимом.
Сложность:
- низкая-средняя; перебор лёгкий и не блокирует исследование.
Следующий шаг:
- перейти к `search` только если prune не даёт явного structural red flag;
- иначе зафиксировать ослабление гипотезы и двигаться к `02_local_vertex_web`.

## 2026-05-08 21:02 — analyze-prune-red-flag
Цель: зафиксировать вывод после baseline+prune и принять решение, тащить ли `01_raw_24cell_web` дальше прямо сейчас.
Гипотеза: `01_raw_24cell_web`
Скрипт: аналитический вывод по артефактам `baseline_*` и `prune_*`
Артефакты:
- `data/baseline_lattice_signature.json`
- `data/prune_raw_24cell_family_scan.json`
- `data/prune_summary.md`
Что считаю:
- насколько raw projected 24-cell вообще похож на целевую решётку хотя бы по минимальному family-count критерию.
Формулы / reasoning:
- для ветки `01` мы ожидаем, что сырой projected edge-web должен хотя бы иногда попадать в target absolute family-count решётки;
- если этого не происходит даже на быстром prune, это не убивает ветку окончательно, но делает её слабым следующим кандидатом.
Промежуточные результаты:
- target absolute family-count: `5`
- raw 24-cell exact matches in 1200 samples: `0`
- best observed family-count: `7`
Что это значит:
- у `01_raw_24cell_web` появился явный structural red flag;
- углублять search по этой ветке прямо сейчас невыгодно;
- логичнее перейти к `02_local_vertex_web`, где допустима локальная паутина, а не весь raw web целиком.
Сложность:
- низкая; решение принято по уже полученным prune-данным.
Следующий шаг:
- перевести фокус на `02_local_vertex_web` и проверить локальную star-гипотезу.

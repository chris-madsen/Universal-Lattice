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

## 2026-05-08 21:06 — baseline
Цель: зафиксировать рабочее пространство параметров для double-rotation ветки.
Гипотеза: `06_double_rotation_overlay`
Скрипт: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_double_rotation_space.json`
- `data/baseline_double_rotation_space.md`
Что считаю:
- какие степени свободы реально участвуют в этой ветке;
- какие рациональные seed-отношения нужно проверять первыми.
Формулы / reasoning:
- здесь важны не только `(alpha, beta)`, но и projection plane, choice of rotation planes и overlay mode;
- поэтому ветка потенциально очень тяжёлая.
Промежуточные результаты:
- parameter axes: `['projection_plane_in_Gr(2,4)', 'rotation_angle_alpha', 'rotation_angle_beta', 'rotation_plane_choice', 'overlay_mode']`
- rational seeds: `['1:2', '1:3', '2:3', '3:4']`
Что это значит:
- ветка сильная по идее, но опасная по вычислительной сложности.
Сложность:
- средняя уже на уровне постановки, до начала реального search.
Следующий шаг:
- сделать complexity-prune и решить, можно ли её сейчас вести без сильной групповой редукции.

## 2026-05-08 21:06 — prune-blocked-complexity
Цель: понять, можно ли прямо сейчас честно тащить ветку double rotation дальше, или она уже требует сильной групповой редукции.
Гипотеза: `06_double_rotation_overlay`
Скрипт: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage prune`
Артефакты:
- `data/prune_complexity_report.json`
- `data/prune_complexity_report.md`
Что считаю:
- грубую размерность поискового пространства до введения сильных симметрийных ограничений.
Формулы / reasoning:
- даже грубая сетка `projection × alpha × beta × plane_choice × overlay_mode` уже даёт слишком много комбинаций;
- без редукции по `SO(4)`/`W(F4)` такая ветка быстро превращается в brute force-болото.
Промежуточные результаты:
- coarse combination count: `10368000`
- assessment: `blocked_complexity`
Что это значит:
- ветка не отвергается математически, но сейчас блокируется вычислительной сложностью;
- по правилу плана на ней нельзя зависать.
Сложность:
- высокая без дополнительной редукции.
Следующий шаг:
- зафиксировать `BLOCKED_COMPLEXITY` и перейти к `08_f4_root_arrangement`.

## 2026-05-08 21:29 — baseline
Цель: зафиксировать рабочее пространство параметров для double-rotation ветки и перевести её из полного перебора в стратифицированный sampling.
Гипотеза: `06_double_rotation_overlay`
Скрипт: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_double_rotation_space.json`
- `data/baseline_double_rotation_space.md`
Что считаю:
- какие оси параметров реально участвуют в ветке;
- какие ratio-классы и plane classes стоит сканировать первыми.
Формулы / reasoning:
- вместо полного перебора берётся стратифицированная выборка по ratio-классам, plane decompositions, base angles и projection seeds;
- первый scan намеренно замораживает overlay mode в `edge_union`, чтобы не распухать по лишним измерениям.
Промежуточные результаты:
- ratio classes: `['1:1', '1:2', '1:3', '2:3', '3:4']`
- projection seeds: `20`
Что это значит:
- ветка `06` снова становится рабочей, но уже не через тупой brute force, а через осмысленное sampling-покрытие классов комбинаций.
Сложность:
- средняя.
Следующий шаг:
- сделать стратифицированный search и посмотреть распределения resonance-показателей по классам.

## 2026-05-08 21:29 — search-stratified-sampling
Цель: заменить грубое `слишком много комбинаций` на реальный sampling по основным классам сочетаний.
Гипотеза: `06_double_rotation_overlay`
Скрипт: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage search`
Артефакты:
- `data/search_stratified_sampling_report.json`
- `data/search_stratified_sampling_report.md`
Что считаю:
- стратифицированную выборку по ratio-классам, plane decompositions, base angles и projection seeds;
- для каждой комбинации считаю family-count, projected edge count и простой resonance score относительно target решётки.
Формулы / reasoning:
- это не полный перебор и не доказательство;
- это закон больших чисел в рабочем виде: сначала смотрим распределение по основным классам комбинаций и ищем, где вообще возникает резонанс.
Промежуточные результаты:
- total samples: `1200`
- family-count histogram: `{14: 2, 15: 7, 16: 30, 17: 49, 18: 101, 19: 170, 20: 245, 21: 266, 22: 211, 23: 93, 24: 26}`
- overall target hits: `0`
- best overall family/line/score: `14` / `192` / `1081.5`
Что это значит:
- ветка `06` больше не отброшена вслепую;
- теперь видно распределение по классам и можно решать, есть ли реальные зоны резонанса для более глубокого копания.
Сложность:
- средняя, но контролируемая.
Следующий шаг:
- перейти к analysis: какие ratio/plane classes реально лучшие и есть ли смысл локально сужать поиск вокруг них.

## 2026-05-08 21:29 — analyze-stratified-classes
Цель: разобрать распределение по class-level sampling и понять, есть ли у double rotation реальные зоны резонанса.
Гипотеза: `06_double_rotation_overlay`
Скрипт: `research/B_symmetry_arrangement_models/06_double_rotation_overlay/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_stratified_classes.json`
- `data/analyze_stratified_classes.md`
Что считаю:
- top classes по resonance score;
- summary по ratio-классам;
- overall target hits по family-count.
Формулы / reasoning:
- если хотя бы некоторые ratio/plane classes системно лучше, ветку имеет смысл локально refine-ить;
- если распределение плоское и hits нет, ветка ослабляется, но уже по данным, а не по страху перед 10 млн комбинаций.
Промежуточные результаты:
- overall target hits: `0`
- best overall family/score: `14` / `1081.5`
- ratio summary: `{'1:1': {'count': 240, 'target_hits': 0, 'best_score': 1081.5}, '1:2': {'count': 240, 'target_hits': 0, 'best_score': 1281.5}, '1:3': {'count': 240, 'target_hits': 0, 'best_score': 1181.5}, '2:3': {'count': 240, 'target_hits': 0, 'best_score': 1179.5}, '3:4': {'count': 240, 'target_hits': 0, 'best_score': 1179.5}}`
Что это значит:
- ветка `06` теперь прошла честный statistical screen;
- по этим данным уже можно решать, parked ли она снова, или у неё есть конкретная зона для локального углубления.
Сложность:
- низкая.
Следующий шаг:
- если есть target hits или явный класс-лидер, сужать поиск локально вокруг него; иначе вернуть ветку в parked, но уже с реальными распределениями в руках.

## 2026-05-08 21:32 — analyze-sampling-red-flag
Цель: зафиксировать, что ветка `06` теперь ослабляется не из-за страха перед размерностью, а по реальным sampling-данным.
Гипотеза: `06_double_rotation_overlay`
Скрипт: анализ артефактов `search_stratified_sampling_report.*` и `analyze_stratified_classes.*`
Артефакты:
- `data/search_stratified_sampling_report.json`
- `data/analyze_stratified_classes.json`
Что считаю:
- есть ли в sampling-распределении хоть какие-то реальные зоны резонанса по target family-count `5`.
Формулы / reasoning:
- ветка была reopened корректно через law-of-large-numbers sampling;
- теперь её можно ослаблять уже честно по данным, а не по априорной оценке пространства.
Промежуточные результаты:
- total samples: `1200`
- family-count histogram: `14..24`, без единого попадания в `5`
- best overall family count: `14`
Что это значит:
- в текущей формулировке `double_rotation_overlay` выглядит слабой веткой;
- если к ней возвращаться, то уже с существенно иным readout/selection mechanism, а не с простым edge-union overlay.
Сложность:
- низкая; вывод уже следует из накопленных данных.
Следующий шаг:
- parked after sampling; основной фокус переносится на `08` и `09`.

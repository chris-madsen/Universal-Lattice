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

## 2026-05-08 21:02 — baseline
Цель: зафиксировать target local-signatures решётки для ветки локальной паутины вершины.
Гипотеза: `02_local_vertex_web`
Скрипт: `research/A_geometric_models/02_local_vertex_web/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_local_targets.json`
- `data/baseline_local_targets.md`
Что считаю:
- локальные степени ключевых узлов;
- базовые family-counts;
- уровни attachment points на мачтах.
Формулы / reasoning:
- если ветка локальной паутины верна, она должна объяснить именно local grammar решётки, а не весь raw web разом.
Промежуточные результаты:
- center/top/bottom degrees: `5` / `5` / `5`
- corner degrees: `{'(0,0)': 5, '(0,3)': 5, '(2,0)': 5, '(2,3)': 5}`
Что это значит:
- ветка `02` теперь имеет формальный target для сравнения с локальными star-проекциями 24-cell.
Сложность:
- низкая.
Следующий шаг:
- перейти к prune и проверить, может ли проектированный star одной вершины 24-cell давать нужный local fan-profile.

## 2026-05-08 21:02 — prune
Цель: проверить, может ли локальная star-проекция одной вершины 24-cell давать local fan-profile, близкий к ключевым узлам решётки.
Гипотеза: `02_local_vertex_web`
Скрипт: `research/A_geometric_models/02_local_vertex_web/scripts/run.py --stage prune`
Артефакты:
- `data/prune_local_star_scan.json`
- `data/prune_local_star_summary.md`
Что считаю:
- у canonical 24-cell каждая вершина имеет degree `8`;
- проектируется локальный star одной вершины;
- считаются oriented rays и absolute families вокруг центра звезды.
Формулы / reasoning:
- top/bottom/center узлы текущей решётки имеют degree `5`;
- это не равно degree вершины 24-cell, но после проекции часть лучей может совпасть по направлению;
- prune нужен, чтобы понять, достижим ли хотя бы local fan-profile уровня `5 oriented rays / 3 absolute families`.
Промежуточные результаты:
- joint exact matches: `0` из `1200`
- oriented histogram: `{7: 212, 8: 967, 6: 17, 5: 3, 4: 1}`
- absolute histogram: `{7: 314, 8: 835, 6: 44, 5: 6, 4: 1}`
- best candidate: `{'zero_edges': 0, 'oriented_ray_count': 5, 'absolute_family_count': 5, 'oriented_centers_deg': [206.82091362959642, 208.3979805012398, 262.37304485001084, 316.08215527024873, 318.2140980786345], 'absolute_centers_deg': [26.82091362959642, 28.3979805012398, 82.37304485001081, 136.08215527024873, 138.2140980786345]}`
Что это значит:
- ветка `02` либо остаётся сильной, либо тоже начинает трещать уже на локальном уровне.
Сложность:
- низкая-средняя; расчёт локальный и дешёвый.
Следующий шаг:
- если локальный star регулярно попадает в target local-profile, можно тащить `02` в search;
- если нет, двигаться к `03_affine_normalized_24cell`.

## 2026-05-08 21:04 — analyze-prune-red-flag
Цель: зафиксировать вывод после baseline+prune и решить, стоит ли тащить локальную star-гипотезу дальше прямо сейчас.
Гипотеза: `02_local_vertex_web`
Скрипт: аналитический вывод по артефактам `baseline_local_targets.*` и `prune_local_star_*`
Артефакты:
- `data/baseline_local_targets.json`
- `data/prune_local_star_scan.json`
- `data/prune_local_star_summary.md`
Что считаю:
- насколько локальная star-проекция одной вершины 24-cell вообще попадает в target local fan-profile ключевых узлов решётки.
Формулы / reasoning:
- ветка `02` обязана хотя бы иногда давать local-profile уровня `5 oriented rays / 3 absolute families`;
- если даже на дешёвом prune это почти не происходит, ветка резко слабеет.
Промежуточные результаты:
- joint exact matches: `0` из `1200`
- best candidate: `5 oriented rays`, но `5 absolute families` вместо target `3`
Что это значит:
- `02_local_vertex_web` сейчас тоже выглядит слабым кандидатом;
- локальная star-модель сама по себе не объясняет нужную компактность fan-profile;
- логичнее перейти к `03_affine_normalized_24cell`.
Сложность:
- низкая; решение принято по уже полученным prune-данным.
Следующий шаг:
- двигаться к `03_affine_normalized_24cell`.

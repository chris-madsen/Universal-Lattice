# 12_topology_signature_filter

Цель ветки: убрать орбитально-эквивалентные конфигурации из branch `05` до тяжёлой оценки проекциями.

Ключевая идея:
- строим симметрийно-инвариантный `topological_signature` кандидата;
- используем его как фильтр в дереве `GA + ACO`;
- оцениваем, насколько падает число реально разных конфигураций.

Основные артефакты:
- `data/topology_signature_space_report.json`
- `data/topology_signature_space_report.md`

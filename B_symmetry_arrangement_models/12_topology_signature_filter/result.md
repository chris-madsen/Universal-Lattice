# Result

Status: completed

## Итог по гипотезе 12 (целиком)

Проверяли гипотезу `12_topology_signature_filter`: можно ли canonical signed-permutation signature использовать как pre-eval фильтр эквивалентных кандидатов в поиске branch `05`.

### 1. Структурный baseline (пространство сигнатур)

- total root branches: `391`
- total templates: `79`
- raw candidate space: `38,478`
- unique topological signatures: `14,510`
- structural compression ratio: `2.651826x`

Наиболее сильное локальное сжатие:
- `A2_B2-0_B1-5_B0-0@01`: `56 -> 14` (`4.000000x`)
- `A2_B2-0_B1-5_B0-0@23`: `56 -> 14` (`4.000000x`)
- `A2_B2-0_B1-7_B0-0@01`: `8 -> 2` (`4.000000x`)
- `A2_B2-0_B1-7_B0-0@23`: `8 -> 2` (`4.000000x`)

Вывод baseline:
- эквивалентные по симметриям конфигурации занимают большую долю пространства;
- signature-фильтрация как идея обоснована.

### 2. Интеграция фильтра в live loop

В `branch05_ga_aco_tree_search.py` добавлены:
- фильтрация дублей внутри поколения по topological signature;
- cap на число eval на signature (`topology_max_evals_per_signature`);
- учёт статистики: unique signatures, skipped in-batch, skipped by cap;
- anti-stall backfill, чтобы цикл не замирал при полном упоре в cap.

### 3. Финальный A/B (одинаковый бюджет)

Оба прогона завершены на одном бюджете:
- generation: `50000 / 50000`
- kernel: `rust_persistent`

`no_filter`:
- elapsed: `5004.95s`
- candidate evaluations: `3,600,000`
- projection evaluations: `345,600,000`
- candidate eval/sec: `719.287`
- projection eval/sec: `69051.594`

`with_filter`:
- elapsed: `12811.92s`
- candidate evaluations: `168,929`
- projection evaluations: `16,217,184`
- candidate eval/sec: `13.185`
- projection eval/sec: `1265.789`
- unique signatures explored: `3,677 / 38,478` (`9.5561%`)
- skipped in-batch equivalent: `1,685,396`
- skipped by signature cap: `1,910,927`

### 4. Вердикт

Подтверждено:
- как dedup/equivalence фильтр гипотеза работает;
- expensive eval-объём сокращается радикально.

Не подтверждено:
- как ускорение wall-clock в текущем режиме (`signature_cap=1` + текущая policy) фильтр не выигрывает по времени завершения.

### 5. Конечный статус гипотезы 12

Гипотеза 12 закрыта на текущем этапе с результатом:
- **PASS** по дедупликации и структурной редукции;
- **FAIL** по wall-clock ускорению в текущей конфигурации;
- следующий шаг (если продолжать именно 12): тюнинг policy cap/backfill/scheduling на фиксированном compute-бюджете.

### 6. Ответ на вопрос “сетка подошла или нет”

Короткий ответ:
- **строгий финальный match сетки по 12-й гипотезе не зафиксирован**;
- **но найдено устойчивое сильное приближение** в `A2`-классах.

Что именно найдено:
- лучший пик без фильтра: `A2_B2-0_B1-3_B0-1@12`, `family5_rate=0.3854167`, `best_counts=[1,1,1,1,2]`;
- лучший пик с фильтром: `A2_B2-0_B1-4_B0-0@03`, `family5_rate=0.3333333`, `best_counts=[1,1,1,1,2]`.

Частотность похожих сеток:
- top running классы в обоих финальных прогонах: `A2_B2-0_B1-4_B0-0`, `A2_B2-0_B1-3_B0-1`, `A2_B2-0_B1-2_B0-2`;
- у этих лидеров `best_counts` стабильно `[1,1,1,1,2]`.

Интерпретация:
- похожая зона найдена и подтверждена статистически;
- окончательный строгий `PASS` всей сетки в рамках 12-й ветки пока не доказан.

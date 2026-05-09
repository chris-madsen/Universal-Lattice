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

## 2026-05-08 21:42 — baseline
Цель: открыть `05_24cell_tesseract_interaction` не как абстракцию, а как явную reduced-модель axis+shell interaction.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage baseline`
Артефакты:
- `data/baseline_interaction_model.json`
- `data/baseline_interaction_model.md`
Что считаю:
- число осевых линий тессеракта;
- число directional lines 24-cell;
- переносится ли сигнал из ветки `09` в более прямую геометрическую постановку.
Формулы / reasoning:
- если hybrid-ветка фактически редуцируется к axis+long без пользы от half-shell, то следующая честная проверка — прямой geometric interaction `tesseract + 24-cell`.
Промежуточные результаты:
- tesseract axis lines: `4`
- 24-cell direction lines: `12`
- imported hint from 09: `axis+long currently dominates the hybrid branch`
Что это значит:
- ветка `05` получила явную математическую постановку, а не просто красивое имя.
Сложность:
- низкая.
Следующий шаг:
- сделать class-level sampling по `T/C` смесям и сравнить их с лучшими `A/L` гибридными классами.

## 2026-05-08 21:42 — search-axis-shell-interaction
Цель: проверить, даёт ли прямая смесь осей тессеракта и directional shell 24-cell тот же тип сигнала, что и `09`.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage search`
Артефакты:
- `data/search_interaction_sampling.json`
- `data/search_interaction_sampling.md`
Что считаю:
- sampling по классам `T/C`;
- частоты попаданий в `family_count=5`;
- частоты exact-profile `[1,1,1,1,6]`.
Формулы / reasoning:
- это геометрическая распаковка сильнейшего сигнала из `09` без half-shell слоя;
- если `05` повторяет или усиливает сигнал `09`, hybrid-ветка может оказаться лишь промежуточным мостом.
Промежуточные результаты:
- best class: `T4_C4`
- family5 hits / exact-profile hits: `27` / `0`
- best witness: `{'class': 'T4_C4', 'tesseract_count': 4, 'cell_count': 4, 'family_count': 5, 'family_multiplicities': [1, 1, 1, 2, 3], 'profile_score': 1.925925925925926, 'exact_profile_hit': False}`
Что это значит:
- теперь понятно, превращается ли axis+long intuition в самостоятельную геометрическую ветку.
Сложность:
- средняя.
Следующий шаг:
- сравнить `05` с `08` и `09` и решить, где именно прирост объяснительной силы максимальный.

## 2026-05-08 21:45 — analyze-local-ridge
Цель: проверить, существует ли локальный ridge вокруг `T4_C4`/`T4_C6`, а не только два удачных класса.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage analyze`
Артефакты:
- `data/analyze_interaction_refine.json`
- `data/analyze_interaction_refine.md`
Что считаю:
- neighbourhood-scan вокруг лучших `T/C` классов;
- отдельно максимум по family5-rate и отдельно максимум по exact-profile-rate;
- сравнение с ветками `08` и `09`.
Формулы / reasoning:
- если вокруг `T4_C4/T4_C6` есть устойчивый ridge, то это уже не случайная находка, а сильная геометрическая ветка;
- важно разделить “чаще даёт 5 семейств” и “чаще даёт exact profile `[1,1,1,1,6]`”.
Промежуточные результаты:
- best family5 class: `T3_C4`
- best exact-profile class: `T4_C6`
- family5 / exact rates: `0.0330` / `0.0007`
Что это значит:
- теперь `05` можно сравнивать с `08/09` уже не по одной точке, а по локальной структуре вокруг сильных классов.
Сложность:
- средняя.
Следующий шаг:
- если `05` остаётся лидером, делать её главным front-runner и переносить остальные ветки в supporting role.

## 2026-05-08 21:47 — finalize-full-edge-union
Цель: проверить, survives ли сильный shell-сигнал ветки `05` на уровне полного edge-union `tesseract + 24-cell`.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/run.py --stage finalize`
Артефакты:
- `data/finalize_full_union_scan.json`
- `data/finalize_full_union_scan.md`
Что считаю:
- случайные 2D-проекции полного объединения рёбер тессеракта и 24-cell;
- распределение по absolute family count;
- best candidate по family-gap и line-gap.
Формулы / reasoning:
- reduced shell-модель уже сильная, но её нужно проверить на более жёстком полном graph-level readout;
- если full union completely explodes по числу семей, shell-сигнал надо трактовать как scaffold, а не как готовый witness.
Промежуточные результаты:
- family-count histogram: `{8: 1, 9: 3, 10: 5, 11: 9, 12: 41, 13: 106, 14: 218, 15: 306, 16: 311}`
- best projection: `{'family_count': 8, 'projected_edge_count': 128, 'projected_vertex_count': 40, 'family_centers_deg': [11.780712684733633, 24.65967705310551, 37.03868565875355, 55.336832372349306, 79.63536671853008, 114.50346309945627, 150.35705184973395, 174.57009484467773], 'projection': [[-0.46205207008304927, 0.23217915791168817, 0.8230233229088125, 0.23501772935573328], [-0.6682053144248303, -0.5316738972539622, -0.07823204120135174, -0.51449419091246]], 'score': 401.0}`
Что это значит:
- теперь понятно, живёт ли сильный `05`-сигнал только на direction-shell уровне или переносится на full edge-union.
Сложность:
- средняя.
Следующий шаг:
- если full union слишком богат, думать о subgraph/readout внутри ветки `05`, а не отказываться от неё целиком.

## 2026-05-08 23:07 — async-ga-aco-tree-search
Цель: перестроить поиск внутри ветки `05` с coarse brute-force `T/C` sampling на дерево `GA + ACO`, не потеряв накопленную статистику.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: `research/async_jobs/branch05_ga_aco_tree_search.py`
Артефакты:
- `../async_state/branch05_ridge/ga_aco_state.json`
- `../async_state/branch05_ridge/ga_aco_summary.md`
- `../async_state/branch05_ridge/ga_aco_log.md`
- `data/analyze_ga_aco_bridge.md`
Что считаю:
- дерево `axis subset -> orbit bucket template -> concrete line selection`;
- GA на уровне trunks/template-crossover;
- ACO на уровне subset/line pheromone;
- FFT/DFT low-pass prior по старой brute-force матрице `T/C`;
- bootstrap prior по orbit-template статистике ветки `10`.
Формулы / reasoning:
- coarse `T/C` scan уже показал, где ridge расположен глобально, но он слишком грубый;
- branch `10` показала, что symmetry-language через orbit buckets даёт более содержательное описание;
- поэтому новая async-ветка берёт гармонически сглаженный root prior из старой матрицы и делает внутри него pheromone-guided drilling по дереву.
Промежуточные результаты:
- background service переведён на `GA + ACO`;
- root-branch лидеры быстро схлопываются к `axis_size=2`, `total_cell_count=4`;
- strongest live trunks сосредоточены вокруг `A2_B2-0_B1-2_B0-2`, `A2_B2-0_B1-3_B0-1`, `A2_B2-0_B1-4_B0-0`, `A2_B2-1_B1-1_B0-2`.
Что это значит:
- ветка `05` теперь ищет уже не только “сколько осей и сколько 24-cell линий”, а какие именно symmetry-guided subweb trunks систематически резонируют с целевой решёткой;
- bridge между `05` и `10` стал рабочим, а не просто концептуальным.
Сложность:
- средняя, но вынесена в asynchronous background process и больше не блокирует ручное исследование.
Следующий шаг:
- ждать стабилизации top root branches;
- затем формализовать readout-rule поверх устойчивых `A2`-trunks через orbit-language ветки `10`.

## 2026-05-08 23:14 — axis-long-handoff
Цель: впитать новый focused сигнал из `08/09` в ветку `05`, чтобы `axis+long` внутри неё был уже не интуицией, а явно подтверждённым scaffold-reading.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: handoff synthesis after focused `08/09` scans
Артефакты:
- `data/analyze_axis_long_handoff.md`
Что считаю:
- comparison между pure `09 axis+long` и decomposed `08 axis+half+long`;
- пригодность этого сигнала для branch `05`.
Формулы / reasoning:
- `09` даёт сильный самостоятельный `axis+long` сигнал;
- `08` после decomposition остаётся слабой supporting branch;
- значит ветке `05` нужно считать `axis+long` first-class scaffold, а не просто побочным толкованием гибридной ветки.
Промежуточные результаты:
- branch `09` best: `A2_L4_H0`, family5=`0.1456`
- branch `08` decomposed best: `A0_L6_H4`, family5=`0.0016`
Что это значит:
- handoff в `05` содержательный;
- новый async `GA+ACO`-поиск и так сходится в `A2`-trunks, так что focused `09` хорошо согласуется с тем, что уже делает branch `05`.
Сложность:
- низкая.
Следующий шаг:
- держать `axis+long` как привилегированный scaffold-language при чтении top `GA+ACO` root branches.

## 2026-05-08 23:21 — rust-hot-kernel-benchmark
Цель: проверить не абстрактно, а на живом лидере ветки `05`, даёт ли Rust реальный прирост на горячем evaluation-kernel.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/rust/branch05_hot_kernel/src/main.rs`
- `research/async_jobs/bench_branch05_hot_kernel.py`
Артефакты:
- `data/bench_branch05_hot_kernel.json`
- `data/bench_branch05_hot_kernel.md`
Что считаю:
- один live candidate: `A2_B2-0_B1-3_B0-1@02`;
- `projection_batch = 25000`;
- Python hot loop vs Rust hot kernel.
Формулы / reasoning:
- полная перепись сервиса на Rust заранее не нужна;
- сначала важно понять, насколько именно evaluation-kernel виноват во времени, и окупится ли перенос hot path.
Промежуточные результаты:
- python elapsed: `2.889557s`
- rust elapsed: `0.035994s`
- speedup: `80.2798x`
Что это значит:
- узкое место действительно горячее и сильно страдает от питоновского orchestration вокруг коротких численных шагов;
- даже при независимом RNG/QR stream Rust даёт сопоставимые quality-metrics (`family5`, `mean_profile_score`, `best_counts`) при радикально меньшем времени;
- перенос hot path в компилируемое ядро выглядит оправданным.
Сложность:
- средняя; isolated kernel поднят без переписывания всего сервиса.
Следующий шаг:
- если интегрировать дальше, то не shell-out на каждый candidate, а FFI/embedded worker, чтобы не съесть выигрыш процессным overhead.

## 2026-05-08 23:22 — first-a2-readout-rule
Цель: вытащить из текущего async `GA+ACO`-поиска не просто лидирующие ветви, а первый явный rule для чтения `A2`-подрешётки.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт: ad hoc extraction from `ga_aco_state.json` over top `A2@02` root branches
Артефакты:
- `data/readout_rule_a2_trunks.json`
- `data/readout_rule_a2_trunks.md`
Что считаю:
- weighted support по template-level trunks;
- weighted support по line ids внутри bucket-1 / bucket-0 / bucket-2;
- line vectors для stable readout.
Формулы / reasoning:
- если у нас стабилизируются не только template classes, но и сами line ids, значит из stochastic search уже можно извлекать deterministic readout rule.
Промежуточные результаты:
- privileged axis subset: `02`
- strongest templates: `A2_B2-0_B1-4_B0-0`, `A2_B2-0_B1-3_B0-1`, `A2_B2-0_B1-2_B0-2`
- stable bucket-1 lines: `10`, `9`, `5`, `2`, `0`
- stable bucket-0 lines: `8`, then `7`
- bucket-2 lines are second-tier only: `1`, then `4`
Что это значит:
- у ветки `05` появился первый явный readout skeleton для `A2`-trunks;
- search уже можно читать не только как статистику, но и как rule-extraction process.
Сложность:
- низкая-средняя.
Следующий шаг:
- проверить, переносится ли этот `A2@02` rule на соседние `A2` subsets (`12`, `13`, `23`) как orbit-equivalent pattern.

## 2026-05-08 23:51 — shared-core-and-orbit-transfer
Цель: вынести `FFT + GA + ACO + hot kernel` из branch-local кода в shared core и сразу проверить, переносится ли `A2@02`-rule на orbit-equivalent subsets.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/common/meta_search.py`
- `research/common/family_kernel.py`
- `research/rust/projection_family_kernel/src/main.rs`
- `research/async_jobs/bench_branch05_hot_kernel.py`
- `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/check_a2_orbit_transfer.py`
Артефакты:
- `data/core_metaheuristic_core.md`
- `data/bench_branch05_hot_kernel.json`
- `data/bench_branch05_hot_kernel.md`
- `data/readout_rule_a2_orbit_transfer.json`
- `data/readout_rule_a2_orbit_transfer.md`
Что считаю:
- shared Python core для ETA / FFT priors / weighted sampling / family-kernel;
- shared Rust projection-family kernel;
- signed-permutation transfer `02 -> 12/13/23` для трёх главных `A2` templates.
Формулы / reasoning:
- если `05` становится reusable core, его можно будет переиспользовать вместо тупого brute-force и в других ветках;
- если `A2@02` переносится на соседние subsets через signed-permutation с высоким overlap и близким family5-rate, то найден не локальный трюк, а orbit-устойчивая grammar.
Промежуточные результаты:
- shared-core Rust benchmark: `33.4197x` speedup на общем kernel-wrapper;
- transfer classification:
  - `12`: `good`, overlap=`0.452512`
  - `13`: `strong`, overlap=`0.487831`
  - `23`: `good`, overlap=`0.467359`
- transferred candidates сохраняют `best_counts = [1,1,1,1,2]` и дают family5-rate порядка `0.17–0.19`.
Что это значит:
- branch `05` теперь уже не просто сильная гипотеза, а shared search stack;
- `A2` readout rule переносится орбитально и выглядит не случайной особенностью одного subset `02`, а устойчивым pattern-class.
Сложность:
- средняя; shared core поднят без ломки live-state, orbit-transfer просчитан без полного relaunch поиска.
Следующий шаг:
- перезапустить live service на новом shared-core коде;
- продолжать вытягивать ещё более жёсткое readout rule поверх orbit-stable `A2` класса.

## 2026-05-09 00:03 — rust-persistent-live-loop
Цель: перестать держать Rust только в benchmark-sidecar и реально перевести branch `05` live-loop на persistent Rust backend без process-per-candidate overhead.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/common/family_kernel.py`
- `research/rust/projection_family_kernel/src/main.rs`
- `research/async_jobs/branch05_ga_aco_tree_search.py`
- `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/bench_persistent_rust_kernel.py`
Артефакты:
- `data/bench_branch05_hot_kernel_persistent.md`
- `data/bench_branch05_live_scale_persistent.md`
Что считаю:
- persistent Rust server mode;
- ProcessPool worker initializer, который поднимает локальный Rust kernel один раз на воркер;
- live-scale repeated benchmark на batch=`96`.
Формулы / reasoning:
- одиночный subprocess-вызов не показывает реальной картины на live batch size;
- branch `05` считает тысячами коротких repeated evaluations, значит важна именно тёплая server-mode траектория, а не cold-start.
Промежуточные результаты:
- service переведён на `kernel backend = rust_persistent`;
- summary/log уже фиксируют backend явно;
- live-scale repeated benchmark: python per-call=`0.013083s`, rust persistent per-call=`0.000229s`, speedup=`57.22x`.
Что это значит:
- теперь Rust реально встроен в рабочий цикл branch `05`, а не только лежит рядом как демонстрация;
- именно warm persistent mode оправдывает переход, а не одноразовый CLI запуск.
Сложность:
- средняя; потребовался server-mode в Rust и аккуратный worker init в Python.
Следующий шаг:
- ужимать orbit-stable `A2` class в более жёсткий deterministic readout и смотреть, как быстро с новым backend branch `05` стабилизирует top subweb.

## 2026-05-09 00:18 — a2-witness-promotion
Цель: проверить, можно ли поднять deterministic `A2` core из “strong scaffold” в formal witness candidate.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/promote_a2_witness_candidate.py`
Артефакты:
- `data/concrete_witness_candidate_a2.json`
- `data/concrete_witness_candidate_a2.md`
Что считаю:
- base evaluation для `A2_B2-0_B1-3_B0-1@02`;
- single-line ablations;
- single-line additions;
- orbit transfers на `12/13/23`.
Формулы / reasoning:
- witness candidate должен не просто часто попадать в `family_count=5`, а удерживать канонический `best_counts = [1,1,1,1,2]`;
- если любой single-line ablation или single-line addition ломает этот канонический pattern, это сильный признак минимального и жёсткого ядра;
- если orbit transfers его сохраняют с устойчивым rate, это уже не локальный редкий трюк.
Промежуточные результаты:
- base candidate preserves canonical counts: `True`
- all single ablations break canonical counts: `True`
- all single additions break canonical counts: `True`
- all transfers hold canonical counts and rate >= `0.16`: `True`
- average transfer family5 rate: `0.183228`
- final verdict: `is_concrete_witness_candidate = True`
Что это значит:
- `A2_B2-0_B1-3_B0-1@02` теперь можно считать не просто хорошим scaffold, а concrete witness candidate для strongest `A2` subweb class;
- обязательные линии действительно обязательны: убираешь одну — теряешь канонический pattern; добавляешь одну — тоже теряешь.
Сложность:
- низкая-средняя; с `rust_persistent` это стало дешёвой формальной проверкой, а не тяжёлым брутфорсом.
Следующий шаг:
- проверить, можно ли собрать уже не только `A2` witness, а следующий слой более полной witness-структуры поверх нескольких совместимых `A2` trunks.

## 2026-05-09 00:56 — multi-trunk-witness-scan
Цель: зафиксировать live-снапшот `GA+ACO`, собрать shortlist `A2` trunk-веток и проверить, выдерживает ли наивная multi-trunk сборка канонический профиль.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/multi_trunk_witness_scan.py`
Артефакты:
- `data/ga_aco_frontier_snapshot.json`
- `data/ga_aco_frontier_snapshot.md`
- `data/multi_trunk_witness_scan.json`
- `data/multi_trunk_witness_scan.md`
Что считаю:
- snapshot текущего фронтира (`best overall`, прогресс, shortlist из `A2` root branches);
- merge-конфиги `core_only / core_plus_b1 / core_plus_b0 / dual_outer / triple_union` на subset `02/12/13/23`;
- line-diff против `core_only` и минимальный negative-neighbor для лучшего multi-кандидата.
Формулы / reasoning:
- если multi-trunk действительно улучшает witness-структуру, он должен сохранять или усиливать канонический `best_counts = [1,1,1,1,2]`;
- если простое union ломает канонику, значит следующий шаг — не «добавить больше линий», а вводить более строгий readout/gating.
Промежуточные результаты:
- live snapshot: generation `46360/48000`, candidate evaluations `3337920`, root-branch coverage `66.7519%`, ETA `~4m`;
- shortlist top-веток подтверждает доминирование `A2_B2-0_B1-*` на subset `02`;
- по всем subset `core_only` удерживает канонику и даёт `family5 ~ 0.18-0.19`;
- все multi-trunk union конфиги ломают канонический профиль:
  - `core_plus_b0` даёт максимум среди multi (`family5 ~ 0.023-0.032`), но `best_counts = [1,1,1,2,2]`;
  - `core_plus_b1 / dual_outer / triple_union` ещё хуже и уходят в `[1,1,2,2,2]` / `[1,1,2,2,3]`.
- минимальный negative certificate (лучший multi на `23`):
  - `core_plus_b0` добавляет line `0` в bucket-0 и ломает канонику;
  - `ABLATE_EXTRA_0_0` возвращает `best_counts = [1,1,1,1,2]` и `family5=0.174316`.
Что это значит:
- наивный union орбитально-стабильных trunk-ов сейчас не работает как путь к «более полной» witness-структуре;
- текущий `A2` core остаётся лучшим конструктивным атомом, а расширение требует не raw union, а constraint-aware добавления.
Сложность:
- низкая-средняя.
Следующий шаг:
- проектировать не «толще union», а контролируемый layered readout (gated additions), где каждая добавка проходит канонический фильтр и локальный negative-neighbor тест.

## 2026-05-09 01:03 — gated-layered-readout-scan
Цель: перейти от raw-union к `constraint-aware` расширению вокруг `A2` core и проверить, какие локальные шаги реально выживают под каноническим gate.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/gated_layered_a2_readout_scan.py`
Артефакты:
- `data/gated_layered_a2_readout_scan.json`
- `data/gated_layered_a2_readout_scan.md`
Что считаю:
- для subset `02/12/13/23` беру orbit-stable `A2` core;
- прогоняю все single-line `add` и single-line `replace` шаги;
- gate: сохранить канонический `best_counts=[1,1,1,1,2]` и не просесть по family5 ниже `90%` от core;
- строю depth-2 только из safe depth-1 состояний.
Формулы / reasoning:
- после провала naive union нужно проверить, есть ли вообще «безопасная» локальная динамика;
- если additions стабильно рушат канонику, но replacements её держат, то branch `05` надо расширять как orbit-consistent replacement family, а не как line-union.
Промежуточные результаты:
- во всех subset single-line additions не проходят gate и дают профиль `[1,1,1,2,2]` (или хуже);
- single-line replacements дают несколько safe-кандидатов с сохранением каноники:
  - `02`: лучший `replace 1:5->3`, family5=`0.186035` vs core `0.176025`;
  - `12`: лучший `replace 1:8->5`, family5=`0.188965` vs core `0.177979`;
  - `13`: лучший `replace 1:0->9`, family5=`0.191406` vs core `0.175293`;
  - `23`: лучший `replace 1:6->3`, family5=`0.188965` vs core `0.187256`.
- safe depth-2 add-цепочки отсутствуют (`0` для всех subset), то есть расширение «добавлением» остаётся разрушительным даже после безопасного первого шага.
Что это значит:
- raw-add стратегия в текущем `A2`-режиме подтверждённо нежизнеспособна;
- зато есть узкий, но воспроизводимый класс `replacement`-ходов, которые удерживают канонику и иногда улучшают family5;
- это и есть рабочий кандидат на следующий слой конструктивного witness-а.
Сложность:
- средняя.
Следующий шаг:
- собрать из top replacement-ходов orbit-consistent `replacement family` (одна и та же rule-схема на `02/12/13/23`) и проверить её как компактный constructive upgrade ядра без увеличения total line count.

## 2026-05-09 01:05 — orbit-consistent-replacement-family
Цель: превратить локально-успешные replacement-ходы в единый orbit-consistent rule family на `02/12/13/23`.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/orbit_consistent_replacement_family.py`
Артефакты:
- `data/orbit_consistent_replacement_family.json`
- `data/orbit_consistent_replacement_family.md`
Что считаю:
- генерирую все single replacement-ходы относительно core на `02`;
- через orbit transfer (перестановки/знаки из `deterministic_a2_subweb_rule`) мапплю каждый ход на `12/13/23`;
- считаю семью как единое правило, валидирую канонику и family5-rate на всех subset;
- ранжирую по `all_canonical`, `avg_family5`, `min_family5`, `avg_delta_vs_core`.
Формулы / reasoning:
- branch `05` нужен не просто «хороший swap» на одном subset, а переносимый upgrade-слой;
- если один replacement стабильно живёт на всех orbit-эквивалентных subset и не деградирует aggregate-rate, это уже конструктивный шаг за пределы одиночного core.
Промежуточные результаты:
- протестировано `16` replacement-семейств;
- найден лучший orbit-consistent family:
  - базовый ход на `02`: `replace 1:5->3`;
  - `all_canonical = True` на `02/12/13/23`;
  - `avg_family5 = 0.182210`, `min_family5 = 0.178385`;
  - `avg_improvement_vs_core = +0.001139`.
- пер-subset метрики лучшей семьи:
  - `02`: `0.178385` (каноника сохранена)
  - `12`: `0.185872` (каноника сохранена)
  - `13`: `0.180339` (каноника сохранена)
  - `23`: `0.184245` (каноника сохранена)
Что это значит:
- появился первый компактный orbit-consistent constructive upgrade слоя `A2` core, который не ломает канонический профиль;
- это уже не raw union и не локальный трюк в одном subset, а переносимое семейство правки readout.
Сложность:
- средняя.
Следующий шаг:
- зафиксировать этот replacement-family как `A2` witness-layer v2 и собрать для него минимальный witness-пакет (`rule + overlay/diff + negative nearby`) перед решением о повышении статуса ветки `05`.

## 2026-05-09 02:10 — witness-layer-v2-and-decision
Цель: закрыть финальные блокеры branch `05` и зафиксировать decision о статусе.
Гипотеза: `05_24cell_tesseract_interaction`
Скрипт:
- `research/A_geometric_models/05_24cell_tesseract_interaction/scripts/finalize_branch05_witness_layer_v2.py`
- `research/async_jobs/branch05_ga_aco_tree_search.py`
Артефакты:
- `data/witness_layer_v2_package.json`
- `data/witness_layer_v2_package.md`
- `../async_state/branch05_ridge/ga_aco_summary.md`
Что считаю:
- orbit-consistent replacement-family на enlarged batch;
- overlay/diff относительно core rule;
- nearby negative certificates (add-back и dominated neighbors);
- non-inferiority против live winners из `ga_aco_state`.
Формулы / reasoning:
- strong witness layer должен сохранять canonical grammar на всех subset и не проигрывать live winners по key family5 метрике в пределах допуска.
Промежуточные результаты:
- best move: `replace 1:5->3` на `02`;
- robustness: `projection_batch=12288`, seeds=`[971001,971002,971003]`;
- canonical holds on `02/12/13/23` across all seeds;
- avg delta vs core: `+0.001411` family5;
- vs live winners: non-inferior = `True` (aggregate delta `-0.001200`);
- add-back neighbors break canonical to `[1,1,1,2,2]`.
Что это значит:
- replacement-layer перестал быть ad hoc наблюдением и оформлен как воспроизводимый witness-layer v2 пакет.
Сложность:
- средняя.
Следующий шаг:
- статус branch `05` повышен до `primary constructive explanation` (layer-level) в `result.md`; отдельно остаётся риск неполного root-branch coverage (`66.7519%`) и отсутствия полного strict global proof.

## 2026-05-09 03:40 — topology-signature-filter-integration
Цель: перестать повторно считать орбитально-эквивалентные кандидаты в tree-search branch `05`.
Гипотеза: symmetry-invariant topological signature уменьшит долю лишних expensive eval.
Скрипт:
- `research/common/topological_signature.py`
- `research/async_jobs/branch05_ga_aco_tree_search.py`
Артефакты:
- `research/B_symmetry_arrangement_models/12_topology_signature_filter/data/topology_signature_space_report.md`
- `research/async_state/branch05_topology_filter_smoke2/ga_aco_summary.md`
Что считаю:
- canonical signature по signed permutations;
- фильтрацию within-batch и global signature cap.
Промежуточные результаты:
- baseline compression branch05 space: `38478 -> 14510` (`2.651826x`);
- topology-filter поля добавлены в summary/log;
- smoke-run с фильтром выполнен успешно.
Что это значит:
- следующий длинный запуск branch `05` можно делать с symmetry-aware prefilter вместо слепого повтора эквивалентов.
Следующий шаг:
- сравнение full-budget run (с фильтром vs без фильтра) по coverage, top-family5 и stability canonical counts.

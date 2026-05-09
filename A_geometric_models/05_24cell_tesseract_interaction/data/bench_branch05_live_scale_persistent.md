# Branch 05 Live-Scale Persistent Rust Benchmark

- candidate: `A2_B2-0_B1-3_B0-1@02`
- repeats: `200`
- projection batch per call: `96`
- benchmark mode: repeated calls against one already-warmed persistent Rust server

## Results
- python total: `2.616579s`
- python per call: `0.013083s`
- rust persistent total: `0.045726s`
- rust persistent per call: `0.000229s`
- python / rust persistent: `57.2227x`

## Interpretation
- a one-shot subprocess benchmark understates the benefit at live batch sizes because startup/build effects distort the picture;
- once the Rust server is already alive, the live-scale repeated evaluation path is dramatically faster than the pure Python loop;
- this is the benchmark that actually justifies switching the branch-05 live loop to `rust_persistent`.

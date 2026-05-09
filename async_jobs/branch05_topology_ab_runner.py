#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import site
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEARCH_SCRIPT = ROOT / "research" / "async_jobs" / "branch05_ga_aco_tree_search.py"
AB_ROOT = ROOT / "research" / "async_state" / "branch05_ab"
NO_FILTER_STATE = AB_ROOT / "no_filter"
WITH_FILTER_STATE = AB_ROOT / "with_filter"
NO_FILTER_UNIT = "runes-branch05-nofilter"
WITH_FILTER_UNIT = "runes-branch05-withfilter"
COMPARISON_JSON = AB_ROOT / "comparison.json"
COMPARISON_MD = AB_ROOT / "comparison.md"

DEFAULT_SLICE = "runes-research.slice"
DEFAULT_NICE = 19
DEFAULT_CPU_WEIGHT = 10
DEFAULT_CPU_SCHED_POLICY = "batch"
DEFAULT_IO_SCHED_CLASS = "idle"
DEFAULT_IO_SCHED_PRIORITY = 7
DEFAULT_WORKERS = 2
DEFAULT_POPULATION = 28
DEFAULT_ANTS = 44
DEFAULT_ELITES = 8
DEFAULT_PROJECTION_BATCH = 96
DEFAULT_TARGET_GENERATIONS = 50000
DEFAULT_LOG_EVERY = 20
DEFAULT_KERNEL_BACKEND = "rust_persistent"
DEFAULT_TOPOLOGY_MAX_EVALS_PER_SIGNATURE = 1
PYTHON_EXE = Path(sys.executable).resolve()
USER_SITE = site.getusersitepackages()


@dataclass(frozen=True)
class RunSpec:
    label: str
    unit: str
    state_dir: Path
    topology_filter: bool


RUN_SPECS = {
    "no_filter": RunSpec("no_filter", NO_FILTER_UNIT, NO_FILTER_STATE, False),
    "with_filter": RunSpec("with_filter", WITH_FILTER_UNIT, WITH_FILTER_STATE, True),
}


def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, check=False, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "command failed rc={rc}\ncmd={cmd}\nstdout={out}\nstderr={err}".format(
                rc=proc.returncode,
                cmd=" ".join(shlex.quote(x) for x in cmd),
                out=(proc.stdout or "").strip(),
                err=(proc.stderr or "").strip(),
            )
        )
    return proc


def systemctl_is_active(unit: str) -> str:
    proc = subprocess.run(
        ["systemctl", "--user", "is-active", unit],
        text=True,
        capture_output=True,
        check=False,
    )
    return (proc.stdout or proc.stderr).strip() or "unknown"


def parse_summary(summary_path: Path) -> dict[str, str]:
    if not summary_path.exists():
        return {}
    txt = summary_path.read_text()
    out: dict[str, str] = {}
    for key in [
        "updated",
        "status",
        "kernel backend",
        "topology filter",
        "topology max evals/signature",
        "generation",
        "generation progress",
        "candidate evaluations",
        "candidate progress",
        "projection evaluations",
        "unique topological signatures",
        "topological-space coverage",
        "skipped equivalent in-batch (total)",
        "skipped by signature cap (total)",
        "templates touched",
        "root branches touched",
        "root-branch coverage",
        "elapsed wall seconds",
        "generations/sec",
        "ETA",
    ]:
        m = re.search(rf"- {re.escape(key)}: `([^`]*)`", txt)
        if m:
            out[key] = m.group(1)
    return out


def load_state_metrics(state_dir: Path) -> dict:
    state_path = state_dir / "ga_aco_state.json"
    if not state_path.exists():
        return {}
    state = json.loads(state_path.read_text())
    elapsed = float(state.get("elapsed_wall_seconds", 0.0))
    candidates = int(state.get("total_candidate_evaluations", 0))
    projections = int(state.get("total_projection_evaluations", 0))
    return {
        "status": state.get("status"),
        "generation": int(state.get("generation", 0)),
        "target_generations": int(state.get("target_generations", 0)),
        "elapsed_wall_seconds": elapsed,
        "total_candidate_evaluations": candidates,
        "total_projection_evaluations": projections,
        "candidate_eval_per_sec": (candidates / elapsed) if elapsed > 0 else None,
        "projection_eval_per_sec": (projections / elapsed) if elapsed > 0 else None,
        "best_overall": state.get("best_overall"),
        "best_exact": state.get("best_exact"),
        "unique_topology_signatures": len(state.get("topology_signature_stats", {})),
        "topology_skipped_batch_equivalent_total": int(state.get("topology_skipped_batch_equivalent_total", 0)),
        "topology_skipped_cap_total": int(state.get("topology_skipped_cap_total", 0)),
        "topology_filter_enabled": bool(state.get("topology_filter_enabled", False)),
        "topology_max_evals_per_signature": int(state.get("topology_max_evals_per_signature", 1)),
    }


def build_search_command(args: argparse.Namespace, spec: RunSpec) -> list[str]:
    cmd = [
        str(PYTHON_EXE),
        str(SEARCH_SCRIPT),
        "--state-dir",
        str(spec.state_dir),
        "--workers",
        str(args.workers),
        "--population-size",
        str(args.population_size),
        "--ant-count",
        str(args.ant_count),
        "--elite-count",
        str(args.elite_count),
        "--projection-batch",
        str(args.projection_batch),
        "--target-generations",
        str(args.target_generations),
        "--log-every",
        str(args.log_every),
        "--kernel-backend",
        args.kernel_backend,
        "--topology-max-evals-per-signature",
        str(args.topology_max_evals_per_signature),
    ]
    if args.max_generations is not None:
        cmd.extend(["--max-generations", str(args.max_generations)])
    if spec.topology_filter:
        cmd.append("--topology-filter")
    else:
        cmd.append("--no-topology-filter")
    return cmd


def launch_one(args: argparse.Namespace, spec: RunSpec) -> None:
    spec.state_dir.mkdir(parents=True, exist_ok=True)
    search_cmd = build_search_command(args, spec)
    pythonpath_piece = shlex.quote(USER_SITE)
    shell_cmd = (
        f"cd {shlex.quote(str(ROOT))} && "
        f"export PYTHONPATH={pythonpath_piece}:${{PYTHONPATH:-}} && "
        f"export PYTHONUNBUFFERED=1 && "
        f"export RUNES_FAMILY_KERNEL_BACKEND={shlex.quote(args.kernel_backend)} && "
        "exec "
        + " ".join(shlex.quote(part) for part in search_cmd)
    )
    cmd = [
        "systemd-run",
        "--user",
        "--slice",
        args.slice,
        "--unit",
        spec.unit,
        "--property",
        f"Nice={int(args.nice)}",
        "--property",
        f"CPUWeight={int(args.cpu_weight)}",
        "--property",
        f"CPUSchedulingPolicy={args.cpu_scheduling_policy}",
        "--property",
        f"IOSchedulingClass={args.io_scheduling_class}",
        "--property",
        f"IOSchedulingPriority={int(args.io_scheduling_priority)}",
    ]
    if args.cpu_quota:
        cmd.extend(["--property", f"CPUQuota={args.cpu_quota}"])
    if args.memory_max:
        cmd.extend(["--property", f"MemoryMax={args.memory_max}"])
    cmd.extend(["/bin/bash", "-lc", shell_cmd])
    proc = run_cmd(cmd)
    stdout = proc.stdout.strip()
    if stdout:
        print(stdout)
    print(f"[{spec.label}] launched unit={spec.unit} state_dir={spec.state_dir}")


def status_one(spec: RunSpec) -> dict:
    summary = parse_summary(spec.state_dir / "ga_aco_summary.md")
    active = systemctl_is_active(spec.unit)
    row = {
        "label": spec.label,
        "unit": spec.unit,
        "active": active,
        "state_dir": str(spec.state_dir),
        "summary": summary,
    }
    return row


def print_status(rows: list[dict]) -> None:
    for row in rows:
        s = row["summary"]
        print(f"[{row['label']}] unit={row['unit']} active={row['active']}")
        if not s:
            print("  summary: missing")
            continue
        print(
            "  generation={gen} progress={prog} elapsed={elapsed}s eta={eta} "
            "cand={cand} proj={proj} topo={topo}".format(
                gen=s.get("generation", "n/a"),
                prog=s.get("generation progress", "n/a"),
                elapsed=s.get("elapsed wall seconds", "n/a"),
                eta=s.get("ETA", "n/a"),
                cand=s.get("candidate evaluations", "n/a"),
                proj=s.get("projection evaluations", "n/a"),
                topo=s.get("topological-space coverage", "n/a"),
            )
        )


def compare_runs() -> dict:
    nof = load_state_metrics(NO_FILTER_STATE)
    wtf = load_state_metrics(WITH_FILTER_STATE)
    payload = {
        "no_filter": nof,
        "with_filter": wtf,
        "delta": {},
    }
    if nof and wtf:
        for key in ["elapsed_wall_seconds", "candidate_eval_per_sec", "projection_eval_per_sec"]:
            a = nof.get(key)
            b = wtf.get(key)
            if a is None or b is None:
                payload["delta"][key] = None
            else:
                payload["delta"][key] = b - a
        if nof.get("total_candidate_evaluations", 0) > 0:
            payload["delta"]["candidate_evaluations_ratio_with_over_no"] = (
                wtf.get("total_candidate_evaluations", 0) / nof.get("total_candidate_evaluations", 1)
            )
        if nof.get("total_projection_evaluations", 0) > 0:
            payload["delta"]["projection_evaluations_ratio_with_over_no"] = (
                wtf.get("total_projection_evaluations", 0) / nof.get("total_projection_evaluations", 1)
            )
    return payload


def write_comparison(payload: dict) -> None:
    AB_ROOT.mkdir(parents=True, exist_ok=True)
    COMPARISON_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True))
    nof = payload.get("no_filter", {})
    wtf = payload.get("with_filter", {})
    delta = payload.get("delta", {})
    lines = [
        "# Branch 05 Topology Filter A/B Comparison",
        "",
        "## no_filter",
        f"- status: `{nof.get('status', 'n/a')}`",
        f"- generation: `{nof.get('generation', 'n/a')}` / `{nof.get('target_generations', 'n/a')}`",
        f"- elapsed wall seconds: `{nof.get('elapsed_wall_seconds', 'n/a')}`",
        f"- candidate evaluations: `{nof.get('total_candidate_evaluations', 'n/a')}`",
        f"- projection evaluations: `{nof.get('total_projection_evaluations', 'n/a')}`",
        f"- candidate eval/sec: `{nof.get('candidate_eval_per_sec', 'n/a')}`",
        f"- projection eval/sec: `{nof.get('projection_eval_per_sec', 'n/a')}`",
        "",
        "## with_filter",
        f"- status: `{wtf.get('status', 'n/a')}`",
        f"- generation: `{wtf.get('generation', 'n/a')}` / `{wtf.get('target_generations', 'n/a')}`",
        f"- elapsed wall seconds: `{wtf.get('elapsed_wall_seconds', 'n/a')}`",
        f"- candidate evaluations: `{wtf.get('total_candidate_evaluations', 'n/a')}`",
        f"- projection evaluations: `{wtf.get('total_projection_evaluations', 'n/a')}`",
        f"- candidate eval/sec: `{wtf.get('candidate_eval_per_sec', 'n/a')}`",
        f"- projection eval/sec: `{wtf.get('projection_eval_per_sec', 'n/a')}`",
        f"- unique topology signatures: `{wtf.get('unique_topology_signatures', 'n/a')}`",
        f"- skipped batch equivalent total: `{wtf.get('topology_skipped_batch_equivalent_total', 'n/a')}`",
        f"- skipped by signature cap total: `{wtf.get('topology_skipped_cap_total', 'n/a')}`",
        "",
        "## Delta (with_filter - no_filter)",
        f"- elapsed wall seconds: `{delta.get('elapsed_wall_seconds', 'n/a')}`",
        f"- candidate eval/sec: `{delta.get('candidate_eval_per_sec', 'n/a')}`",
        f"- projection eval/sec: `{delta.get('projection_eval_per_sec', 'n/a')}`",
        f"- candidate evaluations ratio with/no: `{delta.get('candidate_evaluations_ratio_with_over_no', 'n/a')}`",
        f"- projection evaluations ratio with/no: `{delta.get('projection_evaluations_ratio_with_over_no', 'n/a')}`",
    ]
    COMPARISON_MD.write_text("\n".join(lines) + "\n")
    print(COMPARISON_JSON)
    print(COMPARISON_MD)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    launch = sub.add_parser("launch")
    launch.add_argument("--variant", choices=["both", "no_filter", "with_filter"], default="both")
    launch.add_argument("--slice", default=DEFAULT_SLICE)
    launch.add_argument("--nice", type=int, default=DEFAULT_NICE)
    launch.add_argument("--cpu-weight", type=int, default=DEFAULT_CPU_WEIGHT)
    launch.add_argument("--cpu-scheduling-policy", default=DEFAULT_CPU_SCHED_POLICY)
    launch.add_argument("--io-scheduling-class", default=DEFAULT_IO_SCHED_CLASS)
    launch.add_argument("--io-scheduling-priority", type=int, default=DEFAULT_IO_SCHED_PRIORITY)
    launch.add_argument("--cpu-quota", default=None)
    launch.add_argument("--memory-max", default=None)
    launch.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    launch.add_argument("--population-size", type=int, default=DEFAULT_POPULATION)
    launch.add_argument("--ant-count", type=int, default=DEFAULT_ANTS)
    launch.add_argument("--elite-count", type=int, default=DEFAULT_ELITES)
    launch.add_argument("--projection-batch", type=int, default=DEFAULT_PROJECTION_BATCH)
    launch.add_argument("--target-generations", type=int, default=DEFAULT_TARGET_GENERATIONS)
    launch.add_argument("--log-every", type=int, default=DEFAULT_LOG_EVERY)
    launch.add_argument("--max-generations", type=int, default=None)
    launch.add_argument("--kernel-backend", choices=["rust_persistent", "python"], default=DEFAULT_KERNEL_BACKEND)
    launch.add_argument(
        "--topology-max-evals-per-signature",
        type=int,
        default=DEFAULT_TOPOLOGY_MAX_EVALS_PER_SIGNATURE,
    )

    status = sub.add_parser("status")
    status.add_argument("--variant", choices=["both", "no_filter", "with_filter"], default="both")

    stop = sub.add_parser("stop")
    stop.add_argument("--variant", choices=["both", "no_filter", "with_filter"], default="both")

    sub.add_parser("compare")
    return parser.parse_args()


def pick_specs(variant: str) -> list[RunSpec]:
    if variant == "both":
        return [RUN_SPECS["no_filter"], RUN_SPECS["with_filter"]]
    return [RUN_SPECS[variant]]


def main() -> int:
    args = parse_args()
    if args.cmd == "launch":
        AB_ROOT.mkdir(parents=True, exist_ok=True)
        for spec in pick_specs(args.variant):
            launch_one(args, spec)
        return 0
    if args.cmd == "status":
        rows = [status_one(spec) for spec in pick_specs(args.variant)]
        print_status(rows)
        return 0
    if args.cmd == "stop":
        for spec in pick_specs(args.variant):
            subprocess.run(["systemctl", "--user", "stop", spec.unit], check=False)
            subprocess.run(["systemctl", "--user", "reset-failed", spec.unit], check=False)
            print(f"[{spec.label}] stop requested for {spec.unit}")
        return 0
    if args.cmd == "compare":
        payload = compare_runs()
        write_comparison(payload)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["baseline", "prune", "search", "analyze", "finalize"], default="baseline")
    args = parser.parse_args()

    here = Path(__file__).resolve().parent.parent
    print(f"variant={here.name}")
    print(f"stage={args.stage}")
    print("TODO: implement hypothesis-specific workflow")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

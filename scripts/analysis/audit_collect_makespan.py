#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional, Tuple

STEP_KEYS = ["step", "steps", "t", "tick", "iteration", "iter", "time_step", "time"]

def detect_col(fieldnames: List[str], candidates: List[str]) -> Optional[str]:
    low = {f.lower(): f for f in fieldnames}
    for c in candidates:
        if c.lower() in low:
            return low[c.lower()]
    return None

def parse_float(s: str) -> Optional[float]:
    if s is None:
        return None
    s = str(s).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None

def extract_seed_from_name(name: str) -> Optional[int]:
    # seed0005 / seed5 / seed_5 など
    m = re.search(r"(?:^|[^0-9])seed[_-]?(\d+)", name, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None

def infer_method_and_scenario(path: Path) -> Tuple[str, str]:
    # results/GA/<scenario>/..._commander.csv
    parts = path.parts
    method, scenario = "UNKNOWN", "UNKNOWN"
    for i, p in enumerate(parts):
        if p.lower() == "ga":
            method = "GA"
            scenario = parts[i + 1] if i + 1 < len(parts) else "UNKNOWN"
            break
        if p.lower() == "ads":
            method = "ADS"
            scenario = parts[i + 1] if i + 1 < len(parts) else "UNKNOWN"
            break
    return method, scenario

def max_step_in_commander(csv_path: Path) -> Tuple[Optional[float], str]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            return None, "no_header"
        step_col = detect_col(r.fieldnames, STEP_KEYS)
        if step_col is None:
            return None, f"no_step_col header={r.fieldnames}"
        vals: List[float] = []
        for row in r:
            v = parse_float(row.get(step_col, ""))
            if v is not None:
                vals.append(v)
        if not vals:
            return None, f"no_values_in_{step_col}"
        return max(vals), f"commander:max({step_col})"

def main() -> None:
    root = Path(".")
    out_dir = root / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    commander_files = sorted(root.glob("results/GA/*/*_commander.csv")) + sorted(
        root.glob("results/ADS/*/*_commander.csv")
    )
    if not commander_files:
        print("No commander CSV files found.")
        return

    records = []
    for p in commander_files:
        method, scenario = infer_method_and_scenario(p)
        seed = extract_seed_from_name(p.name)
        ms, rule = max_step_in_commander(p)
        if ms is None:
            continue
        records.append(
            {
                "method": method,
                "scenario_name": scenario,
                "seed": "" if seed is None else str(seed),
                "makespan": ms,
                "adopted_rule": rule,
                "commander_path": str(p),
            }
        )

    long_csv = out_dir / "makespan_long.csv"
    with long_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["method", "scenario_name", "seed", "makespan", "adopted_rule", "commander_path"],
        )
        w.writeheader()
        for r in records:
            w.writerow(r)

    grouped: Dict[Tuple[str, str], List[float]] = {}
    for r in records:
        grouped.setdefault((r["method"], r["scenario_name"]), []).append(float(r["makespan"]))

    summary_rows = []
    for (method, scenario), vals in sorted(grouped.items()):
        summary_rows.append(
            {
                "method": method,
                "scenario_name": scenario,
                "n": len(vals),
                "makespan_mean": mean(vals),
                "makespan_pstdev": pstdev(vals) if len(vals) >= 2 else 0.0,
                "makespan_min": min(vals),
                "makespan_max": max(vals),
            }
        )

    summary_csv = out_dir / "makespan_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "method",
                "scenario_name",
                "n",
                "makespan_mean",
                "makespan_pstdev",
                "makespan_min",
                "makespan_max",
            ],
        )
        w.writeheader()
        for row in summary_rows:
            w.writerow(row)

    print("Wrote:", long_csv)
    print("Wrote:", summary_csv)
    print("Runs:", len(records), "Scenarios:", len(summary_rows))

if __name__ == "__main__":
    main()

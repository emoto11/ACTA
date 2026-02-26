#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, List, Optional, Tuple


def extract_seed_from_name(name: str) -> Optional[int]:
    m = re.search(r"(?:^|[^0-9])seed[_-]?(\d+)", name, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None


def infer_method_and_scenario(path: Path) -> Tuple[str, str]:
    # results/GA/<scenario>/..._tasks.csv
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


def completion_step_from_tasks(tasks_csv: Path) -> Tuple[Optional[int], str]:
    """
    makespan = stepごとの remaining_work 合計が 0 以下になった「最初のstep」
    もし一度も0にならなければ None（未完了）
    必要列: step, remaining_work
    """
    by_step_sum: Dict[int, float] = {}

    with tasks_csv.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            return None, "no_header"
        if "step" not in r.fieldnames or "remaining_work" not in r.fieldnames:
            return None, f"missing_cols header={r.fieldnames}"

        for row in r:
            s = (row.get("step") or "").strip()
            w = (row.get("remaining_work") or "").strip()
            if s == "" or w == "":
                continue
            try:
                step = int(float(s))
                rem = float(w)
            except ValueError:
                continue
            by_step_sum[step] = by_step_sum.get(step, 0.0) + rem

    if not by_step_sum:
        return None, "no_values"

    for step in sorted(by_step_sum.keys()):
        if by_step_sum[step] <= 0.0:
            return step, "ok"

    return None, "not_completed"


def main() -> None:
    root = Path(".")
    out_dir = root / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    tasks_files = sorted(root.glob("results/GA/*/*_tasks.csv")) + sorted(root.glob("results/ADS/*/*_tasks.csv"))
    if not tasks_files:
        print("No tasks CSV files found.")
        return

    long_rows = []
    for p in tasks_files:
        method, scenario = infer_method_and_scenario(p)
        seed = extract_seed_from_name(p.name)
        ms, status = completion_step_from_tasks(p)
        long_rows.append({
            "method": method,
            "scenario_name": scenario,
            "seed": "" if seed is None else str(seed),
            "makespan_completion_step": "" if ms is None else str(ms),
            "status": status,
            "tasks_path": str(p),
        })

    # long出力
    long_csv = out_dir / "makespan_completion_long.csv"
    with long_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "method","scenario_name","seed","makespan_completion_step","status","tasks_path"
        ])
        w.writeheader()
        for r in long_rows:
            w.writerow(r)

    # summary（未完了は除外して平均、未完了数も残す）
    grouped: Dict[Tuple[str, str], List[int]] = {}
    incompleted: Dict[Tuple[str, str], int] = {}

    for r in long_rows:
        key = (r["method"], r["scenario_name"])
        if r["makespan_completion_step"] == "":
            incompleted[key] = incompleted.get(key, 0) + 1
            continue
        grouped.setdefault(key, []).append(int(r["makespan_completion_step"]))

    summary_rows = []
    all_keys = sorted(set(list(grouped.keys()) + list(incompleted.keys())))
    for key in all_keys:
        method, scenario = key
        vals = grouped.get(key, [])
        inc = incompleted.get(key, 0)

        if vals:
            summary_rows.append({
                "method": method,
                "scenario_name": scenario,
                "n_completed": len(vals),
                "n_incomplete": inc,
                "makespan_mean": mean(vals),
                "makespan_pstdev": pstdev(vals) if len(vals) >= 2 else 0.0,
                "makespan_min": min(vals),
                "makespan_max": max(vals),
            })
        else:
            summary_rows.append({
                "method": method,
                "scenario_name": scenario,
                "n_completed": 0,
                "n_incomplete": inc,
                "makespan_mean": "",
                "makespan_pstdev": "",
                "makespan_min": "",
                "makespan_max": "",
            })

    summary_csv = out_dir / "makespan_completion_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "method","scenario_name","n_completed","n_incomplete",
            "makespan_mean","makespan_pstdev","makespan_min","makespan_max"
        ])
        w.writeheader()
        for row in summary_rows:
            w.writerow(row)

    print("Wrote:", long_csv)
    print("Wrote:", summary_csv)
    print("Scenarios:", len(summary_rows), "(should be 72 if GA36+ADS36)")

if __name__ == "__main__":
    main()

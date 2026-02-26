#!/usr/bin/env python3
from __future__ import annotations

import re
import csv
import math
from pathlib import Path

RESULTS_ROOT = Path("results")
ALGS = ["GA", "ADS"]

# log から makespan を拾うための正規表現（多少表記ゆれ対応）
RE_MAKESPAN = re.compile(r"makespan\s*=\s*([0-9]+(?:\.[0-9]+)?)")

def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)

def std(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

def extract_makespan_from_log(log_path: Path) -> float | None:
    try:
        text = log_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    m = RE_MAKESPAN.search(text)
    if not m:
        return None
    return float(m.group(1))

def find_log_for_seed(scenario_dir: Path, seed: int) -> Path | None:
    # よくある命名を広めに探索
    # 例: *_seed0000.log, *_seed0000.txt, *.log など
    seed_tag = f"seed{seed:04d}"
    cands = []
    for ext in (".log", ".txt"):
        cands += list(scenario_dir.glob(f"*{seed_tag}*{ext}"))
    if cands:
        return cands[0]

    # seed を含まない 1個だけの log があるケース（最終手段）
    logs = list(scenario_dir.glob("*.log"))
    if len(logs) == 1:
        return logs[0]
    return None

def main() -> None:
    out_dir = Path("figures")
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []

    for alg in ALGS:
        alg_root = RESULTS_ROOT / alg
        if not alg_root.exists():
            continue

        for scenario_dir in sorted([p for p in alg_root.iterdir() if p.is_dir()]):
            scenario = scenario_dir.name
            makespans: list[float] = []

            # 0..19 を想定（足りない/多い seed があっても取れる範囲は取る）
            for seed in range(0, 20):
                log_path = find_log_for_seed(scenario_dir, seed)
                if log_path is None:
                    continue
                mk = extract_makespan_from_log(log_path)
                if mk is None:
                    continue
                makespans.append(mk)

            if not makespans:
                # 1個も取れない場合も記録だけは残す
                rows.append({
                    "alg": alg,
                    "scenario": scenario,
                    "n": 0,
                    "mean_makespan": "",
                    "std_makespan": "",
                    "min_makespan": "",
                    "max_makespan": "",
                })
                continue

            rows.append({
                "alg": alg,
                "scenario": scenario,
                "n": len(makespans),
                "mean_makespan": round(mean(makespans), 4),
                "std_makespan": round(std(makespans), 4),
                "min_makespan": round(min(makespans), 4),
                "max_makespan": round(max(makespans), 4),
            })

    # そのまま一覧CSV（ロング形式）
    out_long = out_dir / "makespan_table_long.csv"
    with out_long.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["alg","scenario","n","mean_makespan","std_makespan","min_makespan","max_makespan"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # GA/ADS を横持ちにした比較表（ワイド形式）
    # key: scenario
    by_scn: dict[str, dict[str, dict[str, object]]] = {}
    for r in rows:
        scn = str(r["scenario"])
        alg = str(r["alg"])
        by_scn.setdefault(scn, {})[alg] = r

    out_wide = out_dir / "makespan_table_wide.csv"
    with out_wide.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "scenario",
            "GA_n","GA_mean","GA_std",
            "ADS_n","ADS_mean","ADS_std",
            "ADS_minus_GA_mean"
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()

        for scn in sorted(by_scn.keys()):
            ga = by_scn[scn].get("GA", {})
            ads = by_scn[scn].get("ADS", {})

            ga_mean = ga.get("mean_makespan", "")
            ads_mean = ads.get("mean_makespan", "")

            diff = ""
            if isinstance(ga_mean, (int, float)) and isinstance(ads_mean, (int, float)):
                diff = round(float(ads_mean) - float(ga_mean), 4)

            w.writerow({
                "scenario": scn,
                "GA_n": ga.get("n",""),
                "GA_mean": ga_mean,
                "GA_std": ga.get("std_makespan",""),
                "ADS_n": ads.get("n",""),
                "ADS_mean": ads_mean,
                "ADS_std": ads.get("std_makespan",""),
                "ADS_minus_GA_mean": diff
            })

    print(f"saved: {out_long}")
    print(f"saved: {out_wide}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import statistics as stats
from pathlib import Path

RESULT_ROOTS = {
    "GA": Path("results/GA"),
    "ADS": Path("results/ADS"),
}

# dir名例：
# GA : sobol20_lam250_k20_r99_int250
# ADS: sobol20_lam250_k20_r99_a1p0_mr5
SCEN_RE = re.compile(
    r"^(?P<task>[a-z0-9]+)_lam(?P<lam>\d+)_k(?P<k>\d+)_r(?P<range>\d+)_"
)

SEEDS = range(0, 10)  # ★ seed0〜9

def read_rows(p: Path) -> list[dict[str, str]]:
    with p.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)

def makespan_from_tasks_csv(tasks_csv: Path) -> float | None:
    """
    tasks.csv から makespan 推定（頑丈版）
    - stepごとの合計残作業列があればそれを使う
    - 無ければ (step, remaining_work) のタスク行を step合計して0になる時刻
    """
    if not tasks_csv.exists():
        return None

    rows = read_rows(tasks_csv)
    if not rows:
        return None

    cols = rows[0].keys()

    # A) 1step集計列があるケース
    sum_cols = ["total_remaining_work", "remaining_work_sum", "sum_remaining_work"]
    sum_col = next((c for c in sum_cols if c in cols), None)
    if ("step" in cols) and sum_col:
        for row in rows:
            try:
                if float(row[sum_col]) <= 0.0:
                    return float(row["step"])
            except Exception:
                pass

    # B) タスク単位ログ：step + remaining_work
    if ("step" in cols) and ("remaining_work" in cols):
        by_step: dict[int, float] = {}
        for row in rows:
            try:
                s = int(float(row["step"]))
                rw = float(row["remaining_work"])
            except Exception:
                continue
            by_step[s] = by_step.get(s, 0.0) + rw
        for s in sorted(by_step.keys()):
            if by_step[s] <= 0.0:
                return float(s)

    return None

def makespan_from_workers_csv(workers_csv: Path) -> float | None:
    """
    workers.csv の最大stepを makespan 代替にする（最終手段）
    """
    if not workers_csv.exists():
        return None
    rows = read_rows(workers_csv)
    if not rows:
        return None
    if "step" not in rows[0]:
        return None
    last = None
    for row in rows:
        try:
            last = float(row["step"])
        except Exception:
            pass
    return last

def infer_makespan(scen_dir: Path, scen_name: str, seed: int) -> float | None:
    seed_tag = f"seed{seed:04d}"
    tasks_csv   = scen_dir / f"{scen_name}_{seed_tag}_tasks.csv"
    workers_csv = scen_dir / f"{scen_name}_{seed_tag}_workers.csv"

    ms = makespan_from_tasks_csv(tasks_csv)
    if ms is not None:
        return ms

    ms = makespan_from_workers_csv(workers_csv)
    if ms is not None:
        return ms

    return None

def list_scenarios(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])

def cond_key(s: str):
    m = SCEN_RE.match(s)
    if not m:
        return None
    return (m.group("task"), int(m.group("lam")), int(m.group("range")))

def collect_makespans(algo: str, scen_list: list[str]) -> list[float]:
    vals: list[float] = []
    for scen in scen_list:
        scen_dir = RESULT_ROOTS[algo] / scen
        for seed in SEEDS:
            ms = infer_makespan(scen_dir, scen, seed)
            if ms is not None:
                vals.append(ms)
    return vals

def mean(v: list[float]) -> float | None:
    return (sum(v) / len(v)) if v else None

def std(v: list[float]) -> float | None:
    return (stats.pstdev(v) if len(v) >= 2 else None)

def main() -> None:
    ga_scens = set(list_scenarios(RESULT_ROOTS["GA"]))
    ads_scens = set(list_scenarios(RESULT_ROOTS["ADS"]))

    ga_by_cond: dict[tuple, list[str]] = {}
    for s in ga_scens:
        k = cond_key(s)
        if k:
            ga_by_cond.setdefault(k, []).append(s)

    ads_by_cond: dict[tuple, list[str]] = {}
    for s in ads_scens:
        k = cond_key(s)
        if k:
            ads_by_cond.setdefault(k, []).append(s)

    all_conds = sorted(set(ga_by_cond.keys()) | set(ads_by_cond.keys()))

    rows = []
    for (task, lam, rng) in all_conds:
        ga_list = ga_by_cond.get((task, lam, rng), [])
        ads_list = ads_by_cond.get((task, lam, rng), [])

        ga_vals = collect_makespans("GA", ga_list)
        ads_vals = collect_makespans("ADS", ads_list)

        m_ga = mean(ga_vals)
        m_ads = mean(ads_vals)
        diff = (m_ga - m_ads) if (m_ga is not None and m_ads is not None) else None

        rows.append({
            "task": task,
            "lam": lam,
            "range": rng,
            "mean_GA": m_ga,
            "std_GA": std(ga_vals),
            "n_GA": len(ga_vals),
            "mean_ADS": m_ads,
            "std_ADS": std(ads_vals),
            "n_ADS": len(ads_vals),
            "GA-ADS": diff,
        })

    out_dir = Path("figures")
    out_dir.mkdir(exist_ok=True)
    out_csv = out_dir / "makespan_mean_pivot36_with_n_std_seed0-9.csv"

    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["task","lam","range","mean_GA","std_GA","n_GA","mean_ADS","std_ADS","n_ADS","GA-ADS"]
        )
        w.writeheader()
        w.writerows(rows)

    print(f"saved: {out_csv}")
    print("NOTE: n_GA / n_ADS が 10 じゃない行は、seed0-9 のCSVが欠けてます（未実行 or エラー）")

if __name__ == "__main__":
    main()

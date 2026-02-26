
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

# 例:
# GA:  circle20_lam100_k20_r10_int250
# ADS: circle20_lam100_k20_r10_a0p5_mr1
SCEN_RE = re.compile(
    r"^(?P<task>[a-z0-9]+)_lam(?P<lam>\d+)_k(?P<k>\d+)_r(?P<range>\d+)_"
)

def try_parse_makespan_from_log_text(text: str) -> float | None:
    # run_sim_once のログに "makespan=xxx" が出る前提（あなたのgrepログで確認済み）
    m = re.search(r"makespan=([0-9]+(?:\.[0-9]+)?)", text)
    if m:
        return float(m.group(1))
    return None

def read_text_if_exists(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return None

def infer_makespan_from_csvs(scen_dir: Path, scen_name: str, seed: int) -> float | None:
    """
    できるだけ頑丈に makespan を拾う：
    1) logファイル内の makespan=...
    2) tasks.csv から「完了したstep」
    3) workers.csv の最大step（最終手段）
    """
    seed_tag = f"seed{seed:04d}"
    # よくあるログ名候補（--log-file が何を吐くか環境差あるので複数試す）
    log_candidates = [
        scen_dir / f"{scen_name}_{seed_tag}.log",
        scen_dir / f"{scen_name}_{seed_tag}.txt",
        scen_dir / f"{seed_tag}.log",
        scen_dir / "run.log",
    ]
    for lp in log_candidates:
        t = read_text_if_exists(lp)
        if t:
            ms = try_parse_makespan_from_log_text(t)
            if ms is not None:
                return ms

    # commander.csv に makespan が無いのはあなたのログから確定（列は step, info_age_sum）
    # → tasks.csv / workers.csv から推定する
    tasks_csv = scen_dir / f"{scen_name}_{seed_tag}_tasks.csv"
    workers_csv = scen_dir / f"{scen_name}_{seed_tag}_workers.csv"

    # 2) tasks.csv から推定：
    # パターンA: 1行=1step で remaining_work_sum / total_remaining_work がある
    # パターンB: 1行=1(task,step) で remaining_work がある → stepごとに合計して0になる最初のstep
    if tasks_csv.exists():
        with tasks_csv.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames or []

            # A: 1step集計列がある想定
            sum_cols = [c for c in cols if c in ("total_remaining_work", "remaining_work_sum", "sum_remaining_work")]
            if ("step" in cols) and sum_cols:
                key = sum_cols[0]
                for row in reader:
                    try:
                        if float(row[key]) <= 0.0:
                            return float(row["step"])
                    except Exception:
                        pass

            # B: step + remaining_work がある想定（タスク単位ログ）
            if ("step" in cols) and ("remaining_work" in cols):
                # stepごと合計
                by_step: dict[int, float] = {}
                for row in reader:
                    try:
                        s = int(float(row["step"]))
                        rw = float(row["remaining_work"])
                    except Exception:
                        continue
                    by_step[s] = by_step.get(s, 0.0) + rw
                # 合計が0になる最小step
                for s in sorted(by_step.keys()):
                    if by_step[s] <= 0.0:
                        return float(s)

    # 3) workers.csv の最大step（最終手段）
    if workers_csv.exists():
        with workers_csv.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames and "step" in reader.fieldnames:
                last = None
                for row in reader:
                    try:
                        last = float(row["step"])
                    except Exception:
                        pass
                if last is not None:
                    return float(last)

    return None

def list_scenarios(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted([p.name for p in root.iterdir() if p.is_dir()])

def main() -> None:
    # GA と ADS のシナリオ一覧（dir名で一致させる）
    ga_scens = set(list_scenarios(RESULT_ROOTS["GA"]))
    ads_scens = set(list_scenarios(RESULT_ROOTS["ADS"]))

    # task/lam/range 単位で集計するので、両者の “条件キー” を揃える
    def cond_key(s: str):
        m = SCEN_RE.match(s)
        if not m:
            return None
        return (m.group("task"), int(m.group("lam")), int(m.group("range")))

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

    rows_main = []   # task,lam,range,mean_GA,mean_ADS,GA-ADS
    rows_extra = []  # 追加で n と std を出す版

    for (task, lam, rng) in all_conds:
        # 36条件運用なら、GA側は int250 の1本に寄ってる想定（もし複数あれば全部まとめて平均）
        ga_scen_list = ga_by_cond.get((task, lam, rng), [])
        ads_scen_list = ads_by_cond.get((task, lam, rng), [])

        def collect(algo: str, scen_list: list[str]) -> list[float]:
            vals: list[float] = []
            for scen in scen_list:
                scen_dir = RESULT_ROOTS[algo] / scen
                for seed in range(20):  # 0..19
                    ms = infer_makespan_from_csvs(scen_dir, scen, seed)
                    if ms is not None:
                        vals.append(ms)
            return vals

        ga_vals = collect("GA", ga_scen_list)
        ads_vals = collect("ADS", ads_scen_list)

        def mean_or_blank(v: list[float]) -> float | None:
            return (sum(v) / len(v)) if v else None

        m_ga = mean_or_blank(ga_vals)
        m_ads = mean_or_blank(ads_vals)

        diff = (m_ga - m_ads) if (m_ga is not None and m_ads is not None) else None

        rows_main.append({
            "task": task,
            "lam": lam,
            "range": rng,
            "mean_GA": m_ga,
            "mean_ADS": m_ads,
            "GA-ADS": diff,
        })

        rows_extra.append({
            "task": task,
            "lam": lam,
            "range": rng,
            "mean_GA": m_ga,
            "std_GA": (stats.pstdev(ga_vals) if len(ga_vals) >= 2 else None),
            "n_GA": len(ga_vals),
            "mean_ADS": m_ads,
            "std_ADS": (stats.pstdev(ads_vals) if len(ads_vals) >= 2 else None),
            "n_ADS": len(ads_vals),
            "GA-ADS": diff,
        })

    out_dir = Path("figures")
    out_dir.mkdir(exist_ok=True)

    out_main = out_dir / "makespan_mean_pivot36_by_condition.csv"
    with out_main.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["task","lam","range","mean_GA","mean_ADS","GA-ADS"])
        w.writeheader()
        w.writerows(rows_main)

    out_extra = out_dir / "makespan_mean_pivot36_with_n_std.csv"
    with out_extra.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["task","lam","range","mean_GA","std_GA","n_GA","mean_ADS","std_ADS","n_ADS","GA-ADS"])
        w.writeheader()
        w.writerows(rows_extra)

    print(f"saved: {out_main}")
    print(f"saved: {out_extra}")
    print("NOTE: n_GA / n_ADS が 20 じゃない条件は、seedの一部が欠けてます（失敗 or 未実行）")

if __name__ == "__main__":
    main()

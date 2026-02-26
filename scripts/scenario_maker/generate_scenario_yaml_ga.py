#!/usr/bin/env python3
from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path
from typing import Any, Dict

import yaml


def build_base_config() -> Dict[str, Any]:
    return {
        "scenario_name": "dummy",
        "output_dir": "results",
        "space": {"width": 100.0, "height": 100.0, "range": 40.0},
        "sim": {"max_steps": 500, "time_step": 1.0},
        "command_center": {"position": [50.0, 50.0]},
        "repair_depot": {"position": [50.0, 50.0], "repair_duration": 10},
        "failure_model": {
            "module": "acta.sim.failure_models",
            "class": "WeibullFailureModel",
            "params": {"lam": 200, "k": 1.5},
        },
        "task_selection": {
            "module": "acta.sim.task_selection",
            "class": "GABasedTaskSelector",
            "params": {
                "interval": 50,
                "pop_size": 100,
                "generations": 1000,
                "elitism_rate": 0.1,
                "seed": 1234,
                "L_max": 5,
                "trials": 5,
            },
        },
        "workers_csv": (Path("../../workers") / "workers.csv").as_posix(),
        "tasks_csv": (Path("../../tasks") / "toy_tasks.csv").as_posix(),
    }


def dump_yaml(cfg: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = yaml.safe_dump(
        cfg,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    out_path.write_text(text, encoding="utf-8")


def task_tag(task_file: str) -> str:
    # 例: "tasks/tasks_circle20.csv" -> "circle20"
    p = Path(task_file)
    stem = p.stem  # tasks_circle20
    return stem.replace("tasks_", "")

def k_tag(k: float) -> str:
    return f"{int(round(k * 10))}"

def interval_tag(interval: int) -> str:
    # 50 -> int050, 250 -> int250, 500 -> int500
    return f"{interval:03d}"

def main() -> None:
    tasks = [
        "tasks_circle20.csv",
        "tasks_fib20.csv",
        "tasks_lattice20.csv",
        "tasks_sobol20.csv",
    ]
    lams = [100, 250, 400]
    ks = [2.0]
    comm_ranges = [10, 25, 99]
    intervals_generations = [(250, 500)]

    base = build_base_config()

    i = 0
    for task_file, lam, k, r, interval_gen in product(tasks, lams, ks, comm_ranges, intervals_generations):
        cfg = yaml.safe_load(yaml.safe_dump(base))  # かんたんdeep copy（依存なし）
        cfg["scenario_name"] = (
            f"{task_tag(task_file)}_"
            f"lam{lam}_"
            f"k{k_tag(k)}_"
            f"r{r}_"
            f"int{interval_tag(interval_gen[0])}"
            )

        cfg["output_dir"] = f"results/GA/{cfg['scenario_name']}"

        cfg["tasks_csv"] = (Path("../../tasks") / task_file).as_posix()
        cfg["failure_model"]["params"]["lam"] = lam
        cfg["failure_model"]["params"]["k"] = float(k)
        cfg["space"]["range"] = r
        cfg["task_selection"]["params"]["interval"] = interval_gen[0]
        cfg["task_selection"]["params"]["generations"] = interval_gen[1]

        # ファイル名（検索しやすいように同じ情報を入れる）
        fname = f"{cfg['scenario_name']}.yml"
        fpath = Path("configs") / "ga" / fname
        # print(fpath)
        dump_yaml(cfg, fpath)
        i += 1

    print(f"Generated {i} YAML files")


if __name__ == "__main__":
    main()

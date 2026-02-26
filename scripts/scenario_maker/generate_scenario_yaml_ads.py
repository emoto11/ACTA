#!/usr/bin/env python3
from __future__ import annotations

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
            "class": "ADSBaseSelector",
            "params": {
                "alpha_risk": 1.0,
                "max_rounds": 5,
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
    p = Path(task_file)
    return p.stem.replace("tasks_", "")


def k_tag(k: float) -> str:
    return f"{int(round(k * 10))}"


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

    alpha_risks = [1.0]
    max_rounds_list = [5]

    base = build_base_config()

    i = 0
    for task_file, lam, k, r, a, mr in product(tasks, lams, ks, comm_ranges, alpha_risks, max_rounds_list):
        cfg = yaml.safe_load(yaml.safe_dump(base))  # 簡単deep copy

        cfg["scenario_name"] = (
            f"{task_tag(task_file)}_"
            f"lam{lam}_"
            f"k{k_tag(k)}_"
            f"r{r}_"
            f"a{str(a).replace('.', 'p')}_"
            f"mr{mr}"
        )

        cfg["output_dir"] = f"results/ADS/{cfg['scenario_name']}"



        cfg["tasks_csv"] = (Path("../../tasks") / task_file).as_posix()
        cfg["failure_model"]["params"]["lam"] = lam
        cfg["failure_model"]["params"]["k"] = float(k)
        cfg["space"]["range"] = r

        cfg["task_selection"]["params"]["alpha_risk"] = float(a)
        cfg["task_selection"]["params"]["max_rounds"] = int(mr)

        fname = f"{cfg['scenario_name']}.yml"
        fpath = Path("configs") / "ads" / fname
        dump_yaml(cfg, fpath)
        i += 1

    print(f"Generated {i} YAML files")


if __name__ == "__main__":
    main()

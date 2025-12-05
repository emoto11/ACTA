from __future__ import annotations
import argparse

from acta.config_loader import load_scenario_config
from acta.sim.model import ACTAScenarioModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a single ACTA scenario (no GA).")
    parser.add_argument(
        "--scenario",
        type=str,
        required=True,
        help="Path to scenario YAML file.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for the Mesa model.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    cfg = load_scenario_config(args.scenario)
    model = ACTAScenarioModel(cfg, seed=args.seed)

    print(f"[INFO] Scenario: {cfg.scenario_name}")
    print(f"[INFO] Workers: {len(cfg.workers)}, Tasks: {len(cfg.tasks)}")

    # Mesa 3では model.steps が自動で増える
    while (not model.all_tasks_done()) and model.steps < cfg.max_steps:
        model.step()

    makespan = model.get_makespan()
    print(f"[INFO] Finished at steps={model.steps}, makespan={makespan:.2f}")

    for wid, w in model.workers.items():
        print(
            f"  Worker {wid}: move_distance={w.total_move_distance:.2f}, H={w.H:.2f}"
        )


if __name__ == "__main__":
    main()
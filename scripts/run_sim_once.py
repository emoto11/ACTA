from __future__ import annotations
import argparse

from acta.config_loader import load_scenario_config
from acta.sim.model import ACTAScenarioModel
from acta.utils.logging_utils import get_logger

logger = get_logger(__name__)

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
        required=True,
        help="Random seed for the simulation.",
    )

    parser.add_argument(
        "--log-file",
        action="store_true",
        help="Save step-wise simulation logs (CSV).",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    cfg = load_scenario_config(args.scenario)
    model = ACTAScenarioModel(cfg, args.seed, args.log_file)

    logger.info(f"[INFO] Scenario: {cfg.scenario_name}")
    logger.info(f"[INFO] Workers: {len(cfg.workers)}, Tasks: {len(cfg.tasks)}")

    # シミュレーション実行
    while (not model.all_tasks_done()) and model.steps < cfg.max_steps:
        model.step()
    model.finalize()

    makespan = model.get_makespan()
    logger.info(f"[INFO] Finished at steps={model.steps}, makespan={makespan:.2f}")

    for wid, w in model.workers.items():
        logger.info(f"  Worker {wid}: move_distance={w.total_move_distance:.2f}, H={w.H:.2f}")


if __name__ == "__main__":
    main()
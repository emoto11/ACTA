#!/usr/bin/env python3
from __future__ import annotations

import math
import argparse
from dataclasses import dataclass


@dataclass
class WeibullFailureModel:
    lam: float  # スケール（H=lamで約63%故障）
    k: float    # 形状

    def failure_prob(self, H: float) -> float:
        if H <= 0 or self.lam <= 0 or self.k <= 0:
            return 0.0
        return 1.0 - math.exp(- (H / self.lam) ** self.k)

    def failure_prob_step(self, H: float, delta_H: float) -> float:
        if delta_H <= 0 or self.lam <= 0 or self.k <= 0:
            return 0.0

        def F(x: float) -> float:
            return 1.0 - math.exp(- (x / self.lam) ** self.k)

        F_old = F(H)
        F_new = F(H + delta_H)

        if F_old >= 1.0:
            return 1.0
        return (F_new - F_old) / (1.0 - F_old)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="WeibullFailureModel test script"
    )
    parser.add_argument("--lam", type=float, required=True, help="scale λ (H=λで63%%故障)")
    parser.add_argument("--k", type=float, required=True, help="shape k")
    parser.add_argument("--H", type=float, required=True, help="current cumulative fatigue H")
    parser.add_argument("--deltaH", type=float, required=True, help="fatigue increment delta_H")

    args = parser.parse_args()

    model = WeibullFailureModel(lam=args.lam, k=args.k)

    F_H = model.failure_prob(args.H)
    p_step = model.failure_prob_step(args.H, args.deltaH)
    F_next = model.failure_prob(args.H + args.deltaH)

    print("=== Weibull Failure Model Test ===")
    print(f"λ (scale)     = {args.lam}")
    print(f"k (shape)     = {args.k}")
    print(f"H             = {args.H}")
    print(f"delta_H       = {args.deltaH}")
    print()
    print(f"F(H)          = {F_H:.6f}")
    print(f"F(H+delta_H)  = {F_next:.6f}")
    print(f"P(step fail)  = {p_step:.6f}")
    print()
    print("Check:")
    print("  F(H+delta_H) ≈ F(H) + (1-F(H))*P(step fail)")


if __name__ == "__main__":
    main()

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol


class FailureModel(Protocol):
    """WorkerAgentが使う故障モデルのインターフェース."""

    eta: float

    def failure_prob(self, H: float, delta_H: float) -> float:
        """
        疲労度H に対する故障確率を返す。

        Parameters
        ----------
        H : float
            現在の疲労度
        delta_H : float
            このステップで増加する疲労度
        """
        ...


@dataclass
class SimpleFailureModel:
    """常に同じ確率で故障するシンプルなモデル."""

    prob: float

    def failure_prob(self, H: float, delta_H: float) -> float:
        return self.prob
    
@dataclass
class WeibullFailureModel:
    lambd: float  # スケール
    k: float      # 形状 (k>1 で wear-out)

    def failure_prob(self, H: float, delta_H: float) -> float:
        if delta_H <= 0 or self.lambd <= 0 or self.k <= 0:
            return 0.0

        def F(x: float) -> float:
            return 1.0 - math.exp(- (self.lambd * x) ** self.k)

        F_old = F(H)
        F_new = F(H + delta_H)

        # 条件付き確率: これまで生き残っている前提で、このステップで壊れる確率
        if F_old >= 1.0:
            return 1.0
        return (F_new - F_old) / (1.0 - F_old)

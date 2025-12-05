from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Protocol


class FailureModel(Protocol):
    """WorkerAgentが使う故障モデルのインターフェース."""

    eta: float

    def failure_prob(self, H_before: float, delta_H: float) -> float:
        """
        このステップで増えた稼働時間 delta_H に対する故障確率を返す。

        H_before : ステップ開始時点の累積稼働時間
        delta_H  : ステップ中に増えた稼働時間
        """
        ...


@dataclass
class ExpFailureModel:
    """p_fail = 1 - exp(-lambda * delta_H) 型の故障モデル."""

    lambd: float
    eta: float

    def failure_prob(self, H_before: float, delta_H: float) -> float:
        if delta_H <= 0 or self.lambd <= 0:
            return 0.0
        return 1.0 - math.exp(-self.lambd * delta_H)
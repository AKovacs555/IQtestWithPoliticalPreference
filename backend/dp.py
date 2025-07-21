"""Differential privacy utilities."""

import math
import random


def laplace_noise(scale: float) -> float:
    """Return Laplace noise with given scale."""
    u = random.random() - 0.5
    return -scale * math.copysign(math.log(1 - 2 * abs(u)), u)


def add_laplace(value: float, epsilon: float, sensitivity: float = 1.0) -> float:
    """Add Laplace noise to ``value`` for differential privacy."""
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    scale = sensitivity / epsilon
    return value + laplace_noise(scale)

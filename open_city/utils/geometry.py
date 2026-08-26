"""Funções matemáticas simples, reutilizadas por várias partes do jogo."""

import math
from typing import Tuple


def clamp(value: float, lo: float, hi: float) -> float:
    """Restringe ``value`` ao intervalo fechado ``[lo, hi]``."""
    return max(lo, min(hi, value))


def rot_point(px: float, py: float, angle: float) -> Tuple[float, float]:
    """Rotaciona o ponto ``(px, py)`` em torno da origem por ``angle`` radianos."""
    c, s = math.cos(angle), math.sin(angle)
    return px * c - py * s, px * s + py * c

"""Entidades vivas do jogo: veículos e pedestres."""

from .pedestrian import Pedestrian, draw_walking_person
from .vehicle import Vehicle

__all__ = ["Vehicle", "Pedestrian", "draw_walking_person"]

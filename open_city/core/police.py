"""Geração de viaturas e IA de perseguição da polícia."""

import math
import random

import pygame

from ..entities import Vehicle
from ..palette import COLORS
from ..settings import WORLD_H, WORLD_W
from ..utils import clamp

# distância (em pixels do mundo) até o jogador para uma viatura ser considerada
# "pegou" o jogador, terminando a partida
ARREST_DISTANCE = 30


class PoliceMixin:
    """Mistura a lógica de spawn e perseguição de viaturas na classe ``Game``
    (ver ``TrafficMixin`` para mais contexto sobre o padrão de mixin usado aqui)."""

    def spawn_cop(self) -> None:
        """Cria uma nova viatura perto do jogador, mas fora da tela."""
        px, py = self.player_pos()
        ang = random.uniform(0, 2 * math.pi)
        dist = 500
        x = clamp(px + math.cos(ang) * dist, 0, WORLD_W)
        y = clamp(py + math.sin(ang) * dist, 0, WORLD_H)
        self.cops.append(Vehicle(x, y, COLORS["cop_car"], is_cop=True))

    def update_police(self, px: float, py: float) -> None:
        """Atualiza o nível de procurado, spawna viaturas conforme necessário e
        move as existentes perseguindo o jogador (de carro ou a pé)."""
        self._decay_wanted_level()
        self._sync_cop_count()
        for cop in self.cops:
            self._update_single_cop(cop, px, py)

    def _decay_wanted_level(self) -> None:
        self.survive_timer += 1
        if self.survive_timer > 300:
            self.wanted = clamp(self.wanted - 0.02, 0, 5)

    def _sync_cop_count(self) -> None:
        max_cops = int(self.wanted)
        while len(self.cops) < max_cops:
            self.spawn_cop()
        if self.wanted <= 0:
            self.cops = []

    def _update_single_cop(self, cop: Vehicle, px: float, py: float) -> None:
        if cop.stunned > 0:
            cop.stunned -= 1
            return

        dx, dy = px - cop.x, py - cop.y
        target_angle = math.atan2(dy, dx)
        diff = (target_angle - cop.angle + math.pi) % (2 * math.pi) - math.pi
        cop.angle += clamp(diff, -0.06, 0.06)

        dist = math.hypot(dx, dy)
        cop.speed = clamp(cop.speed + 0.15, 0, cop.max_speed if dist > 60 else 1.5)

        ncx = cop.x + math.cos(cop.angle) * cop.speed
        ncy = cop.y + math.sin(cop.angle) * cop.speed
        test = pygame.Rect(ncx - cop.w / 2, ncy - cop.h / 2, cop.w, cop.h)
        if not self.city.collide_rect(test):
            cop.x, cop.y = ncx, ncy
        else:
            cop.speed *= 0.2

        if dist < ARREST_DISTANCE:
            self.game_over = True

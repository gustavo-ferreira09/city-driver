"""Pedestres da cidade: pessoas andando, motoristas checando acidentes e vítimas de atropelamento."""

import math
import random

import pygame

from ..palette import PED_PALETTES
from ..settings import WORLD_H, WORLD_W
from ..utils import clamp


def draw_walking_person(surf: pygame.Surface, sx: float, sy: float, facing: float,
                         walk_phase: float, moving: bool, skin, shirt, pants, hair,
                         scale: float = 1.0, outline=None) -> None:
    """Desenha uma pessoa andando (usado tanto pelos pedestres quanto pelo jogador a pé)."""
    swing = math.sin(walk_phase) * 3.2 * scale if moving else 0

    pygame.draw.ellipse(surf, (0, 0, 0, 70), (sx - 5 * scale, sy + 6 * scale, 10 * scale, 4 * scale))

    dx = math.cos(facing) * 0.4
    leg1 = (sx - 2 * scale + dx * swing, sy + 5 * scale + abs(swing) * 0.3)
    leg2 = (sx + 2 * scale - dx * swing, sy + 5 * scale + abs(swing) * 0.3)
    pygame.draw.line(surf, pants, (sx - 2 * scale, sy + 1 * scale), leg1, max(2, int(3 * scale)))
    pygame.draw.line(surf, pants, (sx + 2 * scale, sy + 1 * scale), leg2, max(2, int(3 * scale)))

    arm1 = (sx - 4 * scale - dx * swing * 0.6, sy + 1 * scale + abs(swing) * 0.2)
    arm2 = (sx + 4 * scale + dx * swing * 0.6, sy + 1 * scale + abs(swing) * 0.2)
    pygame.draw.line(surf, skin, (sx - 3 * scale, sy - 2 * scale), arm1, max(1, int(2 * scale)))
    pygame.draw.line(surf, skin, (sx + 3 * scale, sy - 2 * scale), arm2, max(1, int(2 * scale)))

    pygame.draw.ellipse(surf, shirt, (sx - 4 * scale, sy - 5 * scale, 8 * scale, 8 * scale))
    if outline:
        pygame.draw.ellipse(surf, outline, (sx - 4 * scale, sy - 5 * scale, 8 * scale, 8 * scale), 2)

    pygame.draw.circle(surf, skin, (int(sx), int(sy - 7 * scale)), int(4 * scale))
    pygame.draw.circle(surf, hair, (int(sx), int(sy - 8 * scale)), int(4 * scale))
    pygame.draw.circle(surf, skin, (int(sx), int(sy - 6.5 * scale)), 3.4 * scale)

    pygame.draw.ellipse(surf, tuple(max(0, c - 40) for c in shirt),
                         (sx - 4 * scale, sy - 5 * scale, 8 * scale, 8 * scale), 1)


class Pedestrian:
    """
    Pedestre com uma pequena máquina de estados:

    * ``"walk"``     - andando normalmente pela cidade.
    * ``"checking"`` - parado, olhando (ex.: motorista que desceu do carro
      após uma batida) - não anda, mas ainda pode ser atropelado.
    * ``"ragdoll"``  - acabou de ser atropelado: voa e rola pelo chão indo
      perdendo velocidade (efeito estilo "ragdoll").
    * ``"dead"``     - parado no chão, corpo caído (ainda desenhado, mas
      não se move mais).
    """

    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y
        self.dir = random.uniform(0, 2 * math.pi)
        self.speed = random.uniform(0.4, 0.9)
        self.alive = True
        self.state = "walk"
        self.timer = random.randint(30, 120)
        self.check_timer = 0
        self.skin, self.shirt, self.pants, self.hair = random.choice(PED_PALETTES)
        self.walk_phase = random.uniform(0, math.pi * 2)
        self.moving = True

        # ragdoll
        self.vx = 0.0
        self.vy = 0.0
        self.rot = 0.0
        self.spin = 0.0

    # -----------------------------------------------------------------
    def hit(self, impulse_x: float, impulse_y: float) -> None:
        """Chamado quando um carro atropela o pedestre: dispara o ragdoll."""
        if self.state in ("ragdoll", "dead"):
            return
        self.state = "ragdoll"
        self.vx = impulse_x + random.uniform(-0.6, 0.6)
        self.vy = impulse_y + random.uniform(-0.6, 0.6)
        self.spin = random.uniform(-0.9, 0.9) * (1 if random.random() < 0.5 else -1)
        self.rot = self.dir

    # -----------------------------------------------------------------
    def update(self, city, blood_stains: list) -> None:
        if self.state == "walk":
            self._update_walk(city)
        elif self.state == "checking":
            self._update_checking()
        elif self.state == "ragdoll":
            self._update_ragdoll(city, blood_stains)
        # estado "dead": não faz nada, fica caído

    def _update_walk(self, city) -> None:
        self.timer -= 1
        if self.timer <= 0:
            self.dir = random.uniform(0, 2 * math.pi)
            self.timer = random.randint(60, 180)
        nx = self.x + math.cos(self.dir) * self.speed
        ny = self.y + math.sin(self.dir) * self.speed
        if not city.is_building(nx, ny):
            self.x, self.y = nx, ny
            self.moving = True
        else:
            self.dir += math.pi / 2
            self.moving = False
        self.x = clamp(self.x, 0, WORLD_W)
        self.y = clamp(self.y, 0, WORLD_H)
        if self.moving:
            self.walk_phase += self.speed * 0.9

    def _update_checking(self) -> None:
        """Motorista parado olhando o estrago do acidente, por um tempo, sem se mover."""
        self.moving = False
        self.check_timer -= 1
        if self.check_timer <= 0:
            self.state = "walk"
            self.timer = random.randint(30, 90)

    def _update_ragdoll(self, city, blood_stains: list) -> None:
        nx = self.x + self.vx
        ny = self.y + self.vy
        # não atravessa prédios: para se bater na parede
        test = pygame.Rect(nx - 4, ny - 4, 8, 8)
        if not city.collide_rect(test):
            self.x, self.y = nx, ny
        else:
            self.vx *= -0.3
            self.vy *= -0.3
        self.x = clamp(self.x, 0, WORLD_W)
        self.y = clamp(self.y, 0, WORLD_H)

        self.rot += self.spin
        self.vx *= 0.90
        self.vy *= 0.90
        self.spin *= 0.90

        speed = math.hypot(self.vx, self.vy)
        if speed > 0.6 and random.random() < 0.6:
            blood_stains.append([self.x + random.uniform(-3, 3),
                                  self.y + random.uniform(-3, 3),
                                  random.uniform(2, 4)])

        if speed < 0.15:
            self.state = "dead"
            blood_stains.append([self.x, self.y, random.uniform(10, 15)])
            for _ in range(4):
                blood_stains.append([self.x + random.uniform(-8, 8),
                                      self.y + random.uniform(-8, 8),
                                      random.uniform(2, 5)])

    # -----------------------------------------------------------------
    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        sx, sy = self.x - cam_x, self.y - cam_y

        if self.state in ("walk", "checking"):
            draw_walking_person(surf, sx, sy, self.dir, self.walk_phase, self.moving,
                                 self.skin, self.shirt, self.pants, self.hair)
        else:
            self._draw_fallen(surf, sx, sy)

    def _draw_fallen(self, surf: pygame.Surface, sx: float, sy: float) -> None:
        """Corpo caído/rolando: desenhado deitado, rotacionado, membros esparramados."""
        body = pygame.Surface((28, 28), pygame.SRCALPHA)
        bc = (14, 14)
        pygame.draw.ellipse(body, self.shirt, (bc[0] - 9, bc[1] - 5, 18, 10))
        pygame.draw.line(body, self.pants, bc, (bc[0] - 11, bc[1] + 7), 3)
        pygame.draw.line(body, self.pants, bc, (bc[0] - 4, bc[1] + 10), 3)
        pygame.draw.line(body, self.skin, bc, (bc[0] + 10, bc[1] - 6), 2)
        pygame.draw.line(body, self.skin, bc, (bc[0] + 9, bc[1] + 5), 2)
        pygame.draw.circle(body, self.hair, (bc[0] + 12, bc[1]), 4)
        pygame.draw.circle(body, self.skin, (bc[0] + 12, bc[1]), 3.4)

        rotated = pygame.transform.rotate(body, -math.degrees(self.rot))
        rrect = rotated.get_rect(center=(sx, sy))
        surf.blit(rotated, rrect)

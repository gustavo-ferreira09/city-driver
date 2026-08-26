"""Veículos: carro do jogador, carros de trânsito e viaturas de polícia."""

import math

import pygame

from ..palette import CAR_TYPES
from ..utils import rot_point


class Vehicle:
    """
    Um veículo genérico no mundo. A mesma classe serve para o carro do
    jogador, o tráfego civil e as viaturas de polícia - o que muda é quem
    controla o veículo a cada quadro (o jogador, a IA de trânsito ou a IA
    de perseguição) e algumas flags (``is_cop``, ``car_type``).

    Estado de colisão/acidente:
        crashed:    bateu forte e ainda não teve tempo de "assentar" (o
                    motorista ainda não desceu).
        crash_timer: quadros restantes até o motorista descer.
        abandoned:  motorista já desceu; o carro vira um obstáculo parado.
        stunned:    usado por viaturas de polícia - ficam "zonzas" (não
                    perseguem) por um instante após colidir.
    """

    def __init__(self, x: float, y: float, color, is_cop: bool = False,
                 car_type: str = "sedan") -> None:
        self.x, self.y = x, y
        self.angle = 0.0  # radianos, 0 = apontando para a direita
        self.speed = 0.0
        self.max_speed = 6.0 if not is_cop else 6.6
        self.accel = 0.22
        self.friction = 0.06
        self.turn_speed = 0.045

        self.car_type = car_type
        dims = CAR_TYPES.get(car_type, CAR_TYPES["sedan"])
        self.w, self.h = dims["w"], dims["h"]

        self.color = color
        self.dark = tuple(max(0, c - 55) for c in color)
        self.light = tuple(min(255, c + 45) for c in color)

        self.is_cop = is_cop
        self.alive = True

        # estado de colisão / acidente
        self.crashed = False
        self.crash_timer = 0
        self.abandoned = False
        self.stunned = 0

    # -----------------------------------------------------------------
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - self.w / 2, self.y - self.h / 2, self.w, self.h)

    def _local_to_world(self, px: float, py: float):
        rx, ry = rot_point(px, py, self.angle)
        return self.x + rx, self.y + ry

    def corners(self):
        pts = [(-self.w / 2, -self.h / 2), (self.w / 2, -self.h / 2),
               (self.w / 2, self.h / 2), (-self.w / 2, self.h / 2)]
        return [self._local_to_world(px, py) for px, py in pts]

    # -----------------------------------------------------------------
    # Desenho
    # -----------------------------------------------------------------
    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        self._draw_shadow(surf, cam_x, cam_y)
        self._draw_wheels(surf, cam_x, cam_y)

        pts = [(px - cam_x, py - cam_y) for px, py in self.corners()]
        pygame.draw.polygon(surf, self.color, pts)

        self._draw_roof_highlight(surf, cam_x, cam_y)
        self._draw_windshields(surf, cam_x, cam_y)

        pygame.draw.polygon(surf, (20, 20, 20), pts, 2)

        self._draw_lights(surf, cam_x, cam_y)
        self._draw_type_details(surf, cam_x, cam_y)

        if self.is_cop:
            self._draw_siren(surf, cam_x, cam_y)

        self._draw_crash_indicators(surf, cam_x, cam_y)

    def _draw_shadow(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        shadow_pts = [self._local_to_world(px, py) for px, py in
                      [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]]
        shadow_surf = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        shadow_local = [(px - self.x + w / 2 + 10 + 4, py - self.y + h / 2 + 10 + 4)
                         for px, py in shadow_pts]
        pygame.draw.polygon(shadow_surf, (0, 0, 0, 90), shadow_local)
        surf.blit(shadow_surf, (self.x - cam_x - w / 2 - 10, self.y - cam_y - h / 2 - 10))

    def _draw_wheels(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        wheel_w, wheel_h = 10, 6
        wheel_offsets = [(-w / 2 + 9, -h / 2 - 1), (w / 2 - 11, -h / 2 - 1),
                          (-w / 2 + 9, h / 2 + 1), (w / 2 - 11, h / 2 + 1)]
        for ox, oy in wheel_offsets:
            wx, wy = self._local_to_world(ox, oy)
            wheel_surf = pygame.Surface((wheel_w + 4, wheel_h + 4), pygame.SRCALPHA)
            pygame.draw.rect(wheel_surf, (15, 15, 15), (2, 2, wheel_w, wheel_h), border_radius=2)
            rotated = pygame.transform.rotate(wheel_surf, -math.degrees(self.angle))
            rrect = rotated.get_rect(center=(wx - cam_x, wy - cam_y))
            surf.blit(rotated, rrect)

    def _draw_roof_highlight(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        roof_pts = [self._local_to_world(px, py) for px, py in
                    [(-w / 2 + 12, -h / 2 + 4), (w / 2 - 8, -h / 2 + 4),
                     (w / 2 - 8, h / 2 - 4), (-w / 2 + 12, h / 2 - 4)]]
        roof_screen = [(px - cam_x, py - cam_y) for px, py in roof_pts]
        pygame.draw.polygon(surf, self.light, roof_screen)

    def _draw_windshields(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        wind_color = (150, 200, 225) if not self.is_cop else (200, 210, 230)
        front_wind = [self._local_to_world(px, py) for px, py in
                      [(w / 2 - 16, -h / 2 + 5), (w / 2 - 6, -h / 2 + 6),
                       (w / 2 - 6, h / 2 - 6), (w / 2 - 16, h / 2 - 5)]]
        rear_wind = [self._local_to_world(px, py) for px, py in
                     [(-w / 2 + 6, -h / 2 + 5), (-w / 2 + 16, -h / 2 + 6),
                      (-w / 2 + 16, h / 2 - 6), (-w / 2 + 6, h / 2 - 5)]]
        pygame.draw.polygon(surf, wind_color, [(px - cam_x, py - cam_y) for px, py in front_wind])
        pygame.draw.polygon(surf, wind_color, [(px - cam_x, py - cam_y) for px, py in rear_wind])

    def _draw_lights(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        for oy in (-h / 2 + 3, h / 2 - 3):
            fx, fy = self._local_to_world(w / 2 - 1, oy)
            pygame.draw.circle(surf, (255, 255, 210), (int(fx - cam_x), int(fy - cam_y)), 3)
            bx, by = self._local_to_world(-w / 2 + 1, oy)
            pygame.draw.circle(surf, (200, 30, 30), (int(bx - cam_x), int(by - cam_y)), 2)

    def _draw_siren(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        t = pygame.time.get_ticks() // 150 % 2
        lcol = (255, 20, 20) if t == 0 else (20, 60, 255)
        lx, ly = self._local_to_world(0, 0)
        bar_pts = [self._local_to_world(-6, -3), self._local_to_world(6, -3),
                   self._local_to_world(6, 3), self._local_to_world(-6, 3)]
        pygame.draw.polygon(surf, (20, 20, 20), [(px - cam_x, py - cam_y) for px, py in bar_pts])
        pygame.draw.circle(surf, lcol, (int(lx - cam_x), int(ly - cam_y)), 4)

    def _draw_crash_indicators(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        h = self.h
        if self.crashed and not self.abandoned:
            # balão de exclamação flutuando sobre o carro (motorista ainda vai descer)
            bob = math.sin(pygame.time.get_ticks() / 150) * 2
            bx_, by_ = self.x - cam_x, self.y - cam_y - h / 2 - 14 + bob
            pygame.draw.circle(surf, (255, 220, 40), (int(bx_), int(by_)), 8)
            pygame.draw.circle(surf, (40, 30, 0), (int(bx_), int(by_)), 8, 1)
            excl = pygame.font.SysFont("arial", 13, bold=True).render("!", True, (40, 30, 0))
            surf.blit(excl, (bx_ - excl.get_width() / 2, by_ - excl.get_height() / 2))
        elif self.abandoned:
            # pequenos riscos/amassados no teto para indicar carro batido e parado
            for ox, oy in [(-6, -3), (4, 2), (-2, 5)]:
                p1 = self._local_to_world(ox - 3, oy)
                p2 = self._local_to_world(ox + 3, oy + 2)
                pygame.draw.line(surf, (40, 40, 40), (p1[0] - cam_x, p1[1] - cam_y),
                                  (p2[0] - cam_x, p2[1] - cam_y), 2)

    # -----------------------------------------------------------------
    # Detalhes visuais específicos de cada arquétipo de carro
    # -----------------------------------------------------------------
    def _draw_type_details(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        handler = self._TYPE_DRAW_HANDLERS.get(self.car_type)
        if handler is not None:
            handler(self, surf, cam_x, cam_y)

    def _draw_taxi_details(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w = self.w
        for i, ox in enumerate(range(int(-w / 2 + 6), int(w / 2 - 6), 6)):
            cchk = (20, 20, 20) if i % 2 == 0 else (240, 240, 240)
            p1 = self._local_to_world(ox, -2)
            p2 = self._local_to_world(ox + 6, -2)
            p3 = self._local_to_world(ox + 6, 2)
            p4 = self._local_to_world(ox, 2)
            pygame.draw.polygon(surf, cchk, [(px - cam_x, py - cam_y) for px, py in (p1, p2, p3, p4)])
        sign_pts = [self._local_to_world(-4, -3), self._local_to_world(4, -3),
                    self._local_to_world(4, 3), self._local_to_world(-4, 3)]
        pygame.draw.polygon(surf, (255, 250, 200), [(px - cam_x, py - cam_y) for px, py in sign_pts])
        pygame.draw.polygon(surf, (30, 30, 30), [(px - cam_x, py - cam_y) for px, py in sign_pts], 1)

    def _draw_fusca_details(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        h = self.h
        front_c = self._local_to_world(self.w / 2 - 5, 0)
        back_c = self._local_to_world(-self.w / 2 + 5, 0)
        pygame.draw.circle(surf, self.color, (int(front_c[0] - cam_x), int(front_c[1] - cam_y)), int(h / 2))
        pygame.draw.circle(surf, self.color, (int(back_c[0] - cam_x), int(back_c[1] - cam_y)), int(h / 2))
        pygame.draw.circle(surf, (20, 20, 20), (int(front_c[0] - cam_x), int(front_c[1] - cam_y)), int(h / 2), 1)
        pygame.draw.circle(surf, (20, 20, 20), (int(back_c[0] - cam_x), int(back_c[1] - cam_y)), int(h / 2), 1)
        roof_c = self._local_to_world(0, 0)
        pygame.draw.circle(surf, self.light, (int(roof_c[0] - cam_x), int(roof_c[1] - cam_y)), int(h / 2 - 3))

    def _draw_esportivo_details(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        sp1 = self._local_to_world(-w / 2 - 2, -h / 2 + 2)
        sp2 = self._local_to_world(-w / 2 - 2, h / 2 - 2)
        pygame.draw.line(surf, (25, 25, 25), (sp1[0] - cam_x, sp1[1] - cam_y),
                          (sp2[0] - cam_x, sp2[1] - cam_y), 3)
        stripe = [self._local_to_world(-w / 2 + 4, -2), self._local_to_world(w / 2 - 4, -2),
                  self._local_to_world(w / 2 - 4, 2), self._local_to_world(-w / 2 + 4, 2)]
        pygame.draw.polygon(surf, (245, 245, 235), [(px - cam_x, py - cam_y) for px, py in stripe])

    def _draw_picape_details(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        bed = [self._local_to_world(-w / 2 + 2, -h / 2 + 3), self._local_to_world(-w / 2 + 18, -h / 2 + 3),
               self._local_to_world(-w / 2 + 18, h / 2 - 3), self._local_to_world(-w / 2 + 2, h / 2 - 3)]
        pygame.draw.polygon(surf, self.dark, [(px - cam_x, py - cam_y) for px, py in bed])
        pygame.draw.polygon(surf, (20, 20, 20), [(px - cam_x, py - cam_y) for px, py in bed], 1)

    def _draw_van_details(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        w, h = self.w, self.h
        band = [self._local_to_world(-w / 2 + 2, -h / 2 + 2), self._local_to_world(w / 2 - 2, -h / 2 + 2),
                self._local_to_world(w / 2 - 2, 0), self._local_to_world(-w / 2 + 2, 0)]
        pygame.draw.polygon(surf, (240, 240, 235), [(px - cam_x, py - cam_y) for px, py in band])

    _TYPE_DRAW_HANDLERS = {
        "taxi": _draw_taxi_details,
        "fusca": _draw_fusca_details,
        "esportivo": _draw_esportivo_details,
        "picape": _draw_picape_details,
        "van": _draw_van_details,
    }

"""Desenho da interface (HUD): dinheiro, estrelas de procurado, instruções e telas de status."""

import math

import pygame

from ..palette import COLORS
from ..settings import SCREEN_H, SCREEN_W


class HudMixin:
    """Mistura o desenho de HUD/interface na classe ``Game`` (ver ``TrafficMixin``
    para mais contexto sobre o padrão de mixin usado aqui)."""

    def draw_blood(self, cam_x: float, cam_y: float) -> None:
        """Desenha as manchas de sangue permanentes no chão."""
        for x, y, r in self.blood:
            sx, sy = x - cam_x, y - cam_y
            if not (-20 < sx < SCREEN_W + 20 and -20 < sy < SCREEN_H + 20):
                continue
            stain = pygame.Surface((int(r * 2 + 4), int(r * 2 + 4)), pygame.SRCALPHA)
            pygame.draw.ellipse(stain, (110, 0, 0, 150), (0, 0, r * 2, r * 1.5))
            pygame.draw.ellipse(stain, (150, 10, 10, 110), (r * 0.3, r * 0.2, r * 1.2, r * 0.9))
            surf_rect = stain.get_rect(center=(sx, sy))
            self.screen.blit(stain, surf_rect)

    def draw_hud(self) -> None:
        pad = 14
        pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, SCREEN_W, 50))

        money_surf = self.font.render(f"$ {self.money_count}", True, COLORS["money"])
        self.screen.blit(money_surf, (pad, 14))

        stars_x = 180
        full_stars = int(self.wanted)
        for i in range(5):
            cx = stars_x + i * 26
            color = COLORS["star"] if i < full_stars else (70, 70, 70)
            self.draw_star(cx, 25, 10, color)

        mode = "de carro" if self.in_car else "a pé"
        help_surf = self.font.render(f"[{mode}] WASD move | E entra/sai do carro | R reinicia",
                                      True, (255, 255, 255))
        self.screen.blit(help_surf, (SCREEN_W - help_surf.get_width() - pad, 14))

    def draw_star(self, cx: float, cy: float, r: float, color) -> None:
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = r if i % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        pygame.draw.polygon(self.screen, color, pts)

    def draw_center_text(self, title: str, subtitle: str) -> None:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        t = self.font_big.render(title, True, (255, 60, 60))
        s = self.font.render(subtitle, True, (255, 255, 255))
        self.screen.blit(t, (SCREEN_W / 2 - t.get_width() / 2, SCREEN_H / 2 - 40))
        self.screen.blit(s, (SCREEN_W / 2 - s.get_width() / 2, SCREEN_H / 2 + 20))

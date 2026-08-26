"""
Mundo do jogo: geração procedural da cidade (quarteirões, ruas, prédios e
locais especiais) e seu desenho na tela.
"""

import math
import random

import pygame

from ..palette import COLORS
from ..settings import BLOCK, ROAD_W, SCREEN_H, SCREEN_W, WORLD_H, WORLD_W

# Tipos de quarteirão possíveis e a faixa de probabilidade acumulada usada
# para sorteá-los. Mantidos aqui (em vez de soltos dentro do método) para
# ficar fácil ver, de relance, a proporção de cada tipo de local no mapa.
_CELL_TYPE_THRESHOLDS = (
    ("lake", 0.05),
    ("park", 0.11),
    ("plaza", 0.16),
    ("parking", 0.21),
    ("landmark", 0.24),
    ("empty", 0.34),
    # o que sobrar (roll >= 0.34) vira "building"
)


def _roll_cell_type() -> str:
    roll = random.random()
    for cell_type, threshold in _CELL_TYPE_THRESHOLDS:
        if roll < threshold:
            return cell_type
    return "building"


class City:
    """
    Gera e desenha a cidade: uma grade de quarteirões, cada um sorteado como
    um de sete tipos (prédio comum, vazio, lago, parque, praça, estacionamento
    ou marco/landmark), conectados por ruas.

    Atributos principais:
        buildings: lista de (rect, cor) com tudo que bloqueia movimento
                   (prédios, lagos e marcos). ``cor`` é ``None`` para lagos,
                   que são desenhados de forma especial em vez de como prédio.
        cells: dict (cx, cy) -> tipo do quarteirão.
        money: lista de [x, y, ativo] com o dinheiro espalhado pelo mapa.
        trees: lista de (x, y, cor_da_folhagem, escala).
    """

    def __init__(self) -> None:
        self.buildings: list = []
        self.cols = WORLD_W // BLOCK
        self.rows = WORLD_H // BLOCK
        self.cells: dict = {}
        self.landmarks: list = []
        self.parks: list = []
        self.plazas: list = []
        self.parkings: list = []
        self.lakes: list = []

        self._generate_cells()
        self._generate_money()
        self._generate_trees()

    # -----------------------------------------------------------------
    # Geração
    # -----------------------------------------------------------------
    def _generate_cells(self) -> None:
        for cx in range(self.cols):
            for cy in range(self.rows):
                bx = cx * BLOCK + ROAD_W // 2
                by = cy * BLOCK + ROAD_W // 2
                bw = BLOCK - ROAD_W
                bh = BLOCK - ROAD_W
                inner = pygame.Rect(bx, by, bw, bh)

                cell_type = _roll_cell_type()
                self.cells[(cx, cy)] = cell_type

                if cell_type == "building":
                    self._add_building_cell(bx, by, bw, bh)
                elif cell_type == "lake":
                    self.lakes.append((cx, cy, inner))
                    self.buildings.append((inner, None))  # bloqueia, mas não é "prédio" visível
                elif cell_type == "landmark":
                    self.landmarks.append((cx, cy, inner))
                    self.buildings.append((inner, random.choice(COLORS["building"])))
                elif cell_type == "park":
                    self.parks.append((cx, cy, inner))
                elif cell_type == "plaza":
                    self.plazas.append((cx, cy, inner))
                elif cell_type == "parking":
                    self.parkings.append((cx, cy, inner))
                # "empty": só calçada vazia, nada extra a registrar

    def _add_building_cell(self, bx: int, by: int, bw: int, bh: int) -> None:
        """Subdivide um quarteirão do tipo 'building' em 1 a 3 prédios."""
        n = random.choice([1, 1, 2, 3])
        if n == 1:
            pad = 10
            rect = pygame.Rect(bx + pad, by + pad, bw - 2 * pad, bh - 2 * pad)
            color = random.choice(COLORS["building"])
            self.buildings.append((rect, color))
            return

        if n == 2:
            slots = [(0, 0, bw, bh / 2), (0, bh / 2, bw, bh / 2)]
        else:
            slots = [(0, 0, bw / 2, bh / 2), (bw / 2, 0, bw / 2, bh / 2),
                      (0, bh / 2, bw, bh / 2)]
        for (sx, sy, sw, sh) in slots:
            pad = 8
            rect = pygame.Rect(int(bx + sx + pad), int(by + sy + pad),
                                int(sw - 2 * pad), int(sh - 2 * pad))
            color = random.choice(COLORS["building"])
            self.buildings.append((rect, color))

    def _generate_money(self, count: int = 160) -> None:
        self.money = []
        for _ in range(count):
            x = random.uniform(0, WORLD_W)
            y = random.uniform(0, WORLD_H)
            if not self.is_building(x, y):
                self.money.append([x, y, True])

    def _generate_trees(self) -> None:
        """Espalha árvores pelos quarteirões: parques ganham muito mais que o resto,
        lagos/marcos/prédios ganham só um punhado (para não invadir a construção)."""
        self.trees = []
        for (cx, cy), ctype in self.cells.items():
            if ctype in ("lake", "landmark", "building"):
                n_trees = random.randint(0, 2)
            elif ctype == "park":
                n_trees = random.randint(8, 14)
            else:
                n_trees = random.randint(1, 3)

            bx = cx * BLOCK + ROAD_W // 2
            by = cy * BLOCK + ROAD_W // 2
            bw = BLOCK - ROAD_W
            bh = BLOCK - ROAD_W
            for _ in range(n_trees):
                tx = bx + random.uniform(6, bw - 6)
                ty = by + random.uniform(6, bh - 6)
                if not self.is_building(tx, ty):
                    self.trees.append((tx, ty, random.choice(COLORS["tree_leaf"]),
                                        random.uniform(0.85, 1.2)))

    # -----------------------------------------------------------------
    # Consultas / colisão
    # -----------------------------------------------------------------
    def is_building(self, x: float, y: float) -> bool:
        """True se o ponto (x, y) estiver dentro de uma área bloqueada (prédio/lago/marco)."""
        for rect, _ in self.buildings:
            if rect.collidepoint(x, y):
                return True
        return False

    def collide_rect(self, rect: pygame.Rect) -> bool:
        """True se ``rect`` sobrepõe qualquer área bloqueada do mundo."""
        for brect, _ in self.buildings:
            if brect.colliderect(rect):
                return True
        return False

    # -----------------------------------------------------------------
    # Desenho
    # -----------------------------------------------------------------
    def draw(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        self._draw_ground(surf, cam_x, cam_y)

        left, top = cam_x - 40, cam_y - 40
        right, bottom = cam_x + SCREEN_W + 40, cam_y + SCREEN_H + 40
        c0 = max(0, int(left // BLOCK) - 1)
        c1 = min(self.cols, int(right // BLOCK) + 1)
        r0 = max(0, int(top // BLOCK) - 1)
        r1 = min(self.rows, int(bottom // BLOCK) + 1)

        for cx in range(c0, c1):
            for cy in range(r0, r1):
                self._draw_cell(surf, cam_x, cam_y, cx, cy)

        self._draw_trees(surf, cam_x, cam_y)
        self._draw_landmarks(surf, cam_x, cam_y)
        self._draw_buildings(surf, cam_x, cam_y, left, top, right, bottom)
        self._draw_money(surf, cam_x, cam_y)

    def _draw_ground(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Fundo de grama com leve variação de tom (textura simples em grade)."""
        surf.fill(COLORS["grass"])
        tile = 50
        ox = int(cam_x // tile) * tile
        oy = int(cam_y // tile) * tile
        for gx in range(ox - tile, ox + SCREEN_W + tile, tile):
            for gy in range(oy - tile, oy + SCREEN_H + tile, tile):
                if ((gx // tile) + (gy // tile)) % 2 == 0:
                    pygame.draw.rect(surf, COLORS["grass_dark"],
                                      (gx - cam_x, gy - cam_y, tile, tile))

    def _draw_cell(self, surf: pygame.Surface, cam_x: float, cam_y: float, cx: int, cy: int) -> None:
        bx, by = cx * BLOCK, cy * BLOCK

        # asfalto + leve textura
        road_rect = pygame.Rect(bx - cam_x, by - cam_y, BLOCK, BLOCK)
        pygame.draw.rect(surf, COLORS["road"], road_rect)
        for i in range(0, BLOCK, 24):
            pygame.draw.line(surf, COLORS["road_light"],
                              (bx - cam_x, by + i - cam_y),
                              (bx + BLOCK - cam_x, by + i - cam_y), 1)

        ctype = self.cells.get((cx, cy), "empty")
        inner = pygame.Rect(bx + ROAD_W // 2 - cam_x, by + ROAD_W // 2 - cam_y,
                             BLOCK - ROAD_W, BLOCK - ROAD_W)
        self._draw_cell_interior(surf, ctype, inner)
        self._draw_crosswalks_and_lane_markings(surf, cam_x, cam_y, bx, by)

    def _draw_cell_interior(self, surf: pygame.Surface, ctype: str, inner: pygame.Rect) -> None:
        if ctype == "lake":
            self._draw_lake(surf, inner)
        elif ctype == "park":
            self._draw_park(surf, inner)
        elif ctype == "plaza":
            self._draw_plaza(surf, inner)
        elif ctype == "parking":
            self._draw_parking(surf, inner)
        else:
            # "empty" e "building"/"landmark" (os prédios são desenhados por cima depois)
            self._draw_sidewalk(surf, inner)

    @staticmethod
    def _draw_sidewalk(surf: pygame.Surface, inner: pygame.Rect) -> None:
        pygame.draw.rect(surf, COLORS["sidewalk"], inner)
        pygame.draw.rect(surf, COLORS["sidewalk_line"], inner, 2)
        for i in range(0, inner.w, 22):
            pygame.draw.line(surf, COLORS["sidewalk_line"],
                              (inner.x + i, inner.y), (inner.x + i, inner.y + inner.h), 1)

    @staticmethod
    def _draw_lake(surf: pygame.Surface, inner: pygame.Rect) -> None:
        pygame.draw.rect(surf, COLORS["sand"], inner.inflate(10, 10))
        pygame.draw.rect(surf, COLORS["water"], inner)
        t = pygame.time.get_ticks() / 500
        for wy in range(inner.y + 10, inner.y + inner.h - 5, 16):
            wobble = math.sin(t + wy) * 4
            pygame.draw.line(surf, COLORS["water_light"],
                              (inner.x + 6 + wobble, wy), (inner.x + inner.w - 6 + wobble, wy), 2)

    @staticmethod
    def _draw_park(surf: pygame.Surface, inner: pygame.Rect) -> None:
        pygame.draw.rect(surf, COLORS["park_grass"], inner)
        pygame.draw.rect(surf, COLORS["sidewalk_line"], inner, 2)
        # lagoinha decorativa no meio do parque
        pond = inner.inflate(-inner.w * 0.6, -inner.h * 0.6)
        pygame.draw.ellipse(surf, COLORS["water"], pond)
        pygame.draw.ellipse(surf, COLORS["water_light"], pond, 2)
        # bancos
        for bxp, byp in [(inner.x + 14, inner.y + 14), (inner.right - 20, inner.bottom - 20)]:
            pygame.draw.rect(surf, (110, 75, 45), (bxp, byp, 14, 5))

    @staticmethod
    def _draw_plaza(surf: pygame.Surface, inner: pygame.Rect) -> None:
        pygame.draw.rect(surf, COLORS["plaza"], inner)
        for gx in range(inner.x, inner.right, 20):
            pygame.draw.line(surf, COLORS["sidewalk_line"], (gx, inner.y), (gx, inner.bottom), 1)
        for gy in range(inner.y, inner.bottom, 20):
            pygame.draw.line(surf, COLORS["sidewalk_line"], (inner.x, gy), (inner.right, gy), 1)
        # chafariz central
        fc = inner.center
        pygame.draw.circle(surf, (150, 150, 150), fc, 26)
        pygame.draw.circle(surf, COLORS["water"], fc, 20)
        pygame.draw.circle(surf, COLORS["water_light"], fc, 8)

    @staticmethod
    def _draw_parking(surf: pygame.Surface, inner: pygame.Rect) -> None:
        pygame.draw.rect(surf, COLORS["parking"], inner)
        for px_ in range(inner.x + 10, inner.right - 10, 26):
            pygame.draw.line(surf, (230, 230, 220), (px_, inner.y + 8), (px_, inner.bottom - 8), 2)

    @staticmethod
    def _draw_crosswalks_and_lane_markings(surf: pygame.Surface, cam_x: float, cam_y: float,
                                            bx: int, by: int) -> None:
        # faixas de pedestre nos 2 acessos "de referência" do quarteirão (canto superior-esquerdo)
        cwx = bx + BLOCK // 2 - cam_x
        cwy = by + BLOCK // 2 - cam_y
        stripe_len = ROAD_W - 14
        for i in range(-stripe_len // 2, stripe_len // 2, 12):
            pygame.draw.rect(surf, COLORS["crosswalk"], (cwx + i, by - cam_y + 6, 6, 18))
            pygame.draw.rect(surf, COLORS["crosswalk"], (bx - cam_x + 6, cwy + i, 18, 6))

        # linha amarela tracejada no meio da rua
        for i in range(0, BLOCK, 40):
            ly = by + BLOCK // 2 - cam_y
            lx = bx + i - cam_x
            pygame.draw.rect(surf, COLORS["road_line"], (lx, ly - 2, 20, 4))
            lx2 = bx + BLOCK // 2 - cam_x
            ly2 = by + i - cam_y
            pygame.draw.rect(surf, COLORS["road_line"], (lx2 - 2, ly2, 4, 20))

    def _draw_trees(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        for tx, ty, leaf_color, scale in self.trees:
            sx, sy = tx - cam_x, ty - cam_y
            if not (-20 < sx < SCREEN_W + 20 and -20 < sy < SCREEN_H + 20):
                continue
            pygame.draw.ellipse(surf, (0, 0, 0, 40),
                                 (sx - 9 * scale, sy - 3 * scale, 18 * scale, 8 * scale))
            pygame.draw.rect(surf, COLORS["tree_trunk"], (sx - 2, sy - 2, 4, 10 * scale))
            pygame.draw.circle(surf, leaf_color, (int(sx), int(sy - 8 * scale)), int(10 * scale))
            pygame.draw.circle(surf, (255, 255, 255),
                                (int(sx - 3 * scale), int(sy - 11 * scale)), int(3 * scale))

    def _draw_landmarks(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Marcos especiais (estádio/monumento): anéis concêntricos + campo verde central."""
        for _cx, _cy, rect in self.landmarks:
            r = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.w, rect.h)
            if r.right < 0 or r.left > SCREEN_W or r.bottom < 0 or r.top > SCREEN_H:
                continue
            pygame.draw.ellipse(surf, (140, 130, 120), r)
            pygame.draw.ellipse(surf, (110, 100, 90), r, 6)
            field = r.inflate(-r.w * 0.35, -r.h * 0.35)
            pygame.draw.ellipse(surf, COLORS["park_grass"], field)
            pygame.draw.ellipse(surf, (255, 255, 255), field, 2)

    def _draw_buildings(self, surf: pygame.Surface, cam_x: float, cam_y: float,
                         left: float, top: float, right: float, bottom: float) -> None:
        landmark_rects = {id(rect) for _, _, rect in self.landmarks}
        for rect, color in self.buildings:
            if color is None:
                continue  # lago (já desenhado) ou área só de colisão
            if id(rect) in landmark_rects:
                continue  # marcos já foram desenhados de forma especial
            if rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom:
                continue
            self._draw_single_building(surf, rect, color, cam_x, cam_y)

    @staticmethod
    def _draw_single_building(surf: pygame.Surface, rect: pygame.Rect, color,
                               cam_x: float, cam_y: float) -> None:
        r = pygame.Rect(rect.x - cam_x, rect.y - cam_y, rect.w, rect.h)

        shadow = pygame.Rect(r.x + 6, r.y + 6, r.w, r.h)
        pygame.draw.rect(surf, (30, 40, 30), shadow)

        pygame.draw.rect(surf, color, r)

        roof_h = min(14, r.h // 4)
        roof_color = tuple(max(0, c - 45) for c in color)
        pygame.draw.rect(surf, roof_color, (r.x, r.y, r.w, roof_h))
        pygame.draw.rect(surf, (25, 25, 25), r, 2)

        for wx in range(r.x + 8, r.x + r.w - 10, 18):
            for wy in range(r.y + roof_h + 6, r.y + r.h - 10, 18):
                lit = ((wx + wy) // 18) % 5 != 0
                wcolor = (245, 225, 140) if lit else (60, 70, 90)
                pygame.draw.rect(surf, wcolor, (wx, wy, 8, 10))
                pygame.draw.rect(surf, (30, 30, 30), (wx, wy, 8, 10), 1)

        door_w = 12
        pygame.draw.rect(surf, (60, 40, 30),
                          (r.x + r.w // 2 - door_w // 2, r.y + r.h - 16, door_w, 16))

    def _draw_money(self, surf: pygame.Surface, cam_x: float, cam_y: float) -> None:
        dollar_font = pygame.font.SysFont("arial", 10, bold=True)
        for m in self.money:
            if not m[2]:
                continue
            mx, my = m[0] - cam_x, m[1] - cam_y
            if not (-20 < mx < SCREEN_W + 20 and -20 < my < SCREEN_H + 20):
                continue
            bob = math.sin(pygame.time.get_ticks() / 200 + mx) * 2
            pygame.draw.circle(surf, (120, 90, 0), (int(mx), int(my + bob)), 8)
            pygame.draw.circle(surf, COLORS["money"], (int(mx), int(my + bob)), 7)
            pygame.draw.circle(surf, (255, 250, 210), (int(mx), int(my + bob)), 7, 1)
            dollar = dollar_font.render("$", True, (140, 100, 0))
            surf.blit(dollar, (mx - dollar.get_width() / 2, my + bob - dollar.get_height() / 2))

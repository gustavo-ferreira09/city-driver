"""
Dados estáticos de aparência do jogo: cores do cenário, paletas de roupa dos
pedestres e arquétipos de carro de trânsito.

Este módulo não depende de nenhum sistema do pygame além de tuplas RGB
simples, então pode ser importado e testado sem precisar inicializar vídeo.
"""

from typing import Dict, List, Tuple, TypedDict

RGB = Tuple[int, int, int]

# Cores usadas pelo mundo (City) e pelo HUD. Algumas entradas são uma única
# cor, outras são uma lista de variações para dar diversidade visual (ex.:
# fachadas de prédio, folhagem de árvore).
COLORS: Dict[str, object] = {
    "grass": (63, 133, 73),
    "grass_dark": (55, 120, 65),
    "road": (48, 48, 52),
    "road_light": (58, 58, 62),
    "road_line": (230, 200, 60),
    "crosswalk": (225, 225, 220),
    "sidewalk": (172, 170, 162),
    "sidewalk_line": (155, 153, 146),
    "building": [(150, 110, 90), (110, 140, 150), (170, 150, 110),
                 (120, 120, 150), (160, 130, 130), (110, 130, 110)],
    "roof": [(90, 65, 55), (65, 85, 90), (100, 90, 65), (70, 70, 90)],
    "car": (196, 40, 40),
    "cop_car": (30, 45, 150),
    "money": (255, 215, 0),
    "white": (255, 255, 255),
    "black": (10, 10, 10),
    "hud_bg": (0, 0, 0),
    "star": (255, 210, 0),
    "tree_leaf": [(46, 110, 55), (55, 125, 60), (40, 100, 50)],
    "tree_trunk": (92, 62, 40),
    "water": (48, 100, 160),
    "water_light": (70, 130, 190),
    "sand": (200, 180, 130),
    "park_grass": (72, 145, 80),
    "plaza": (185, 178, 165),
    "parking": (95, 95, 100),
}

# Paletas de roupa/pele dos pedestres: cada item é (pele, camisa, calça, cabelo).
PED_PALETTES: List[Tuple[RGB, RGB, RGB, RGB]] = [
    ((235, 200, 165), (200, 60, 60), (40, 40, 60), (60, 40, 30)),
    ((210, 165, 130), (60, 120, 190), (70, 70, 70), (20, 20, 20)),
    ((240, 210, 175), (230, 210, 40), (50, 90, 130), (120, 80, 50)),
    ((190, 140, 100), (60, 160, 100), (30, 30, 30), (10, 10, 10)),
    ((225, 190, 150), (150, 60, 150), (60, 50, 90), (90, 60, 40)),
    ((200, 150, 115), (240, 240, 240), (40, 60, 40), (30, 20, 15)),
]


class CarTypeSpec(TypedDict):
    """Especificação visual de um arquétipo de carro de trânsito."""

    w: int
    h: int
    colors: List[RGB]


# Tipos de carro de trânsito: silhuetas genéricas inspiradas em arquétipos
# populares (sedã, táxi, "fusca" arredondado, esportivo, picape, van).
# As formas e cores são originais - sem logotipos nem marcas reais.
CAR_TYPES: Dict[str, CarTypeSpec] = {
    "sedan":     {"w": 46, "h": 24, "colors": [(70, 90, 190), (90, 90, 95), (150, 60, 150), (60, 140, 130)]},
    "taxi":      {"w": 46, "h": 24, "colors": [(230, 195, 30)]},
    "fusca":     {"w": 38, "h": 24, "colors": [(60, 150, 90), (200, 140, 60), (150, 60, 60), (70, 130, 170)]},
    "esportivo": {"w": 52, "h": 20, "colors": [(210, 20, 20), (240, 200, 20), (20, 20, 25)]},
    "picape":    {"w": 54, "h": 25, "colors": [(120, 120, 125), (80, 60, 40), (50, 80, 50)]},
    "van":       {"w": 50, "h": 27, "colors": [(230, 230, 225), (200, 160, 60)]},
}

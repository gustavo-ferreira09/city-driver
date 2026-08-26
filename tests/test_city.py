"""Testes para open_city.world.City."""

import pygame

from open_city.settings import BLOCK, WORLD_H, WORLD_W
from open_city.world import City


def test_city_grid_dimensions_match_settings():
    city = City()
    assert city.cols == WORLD_W // BLOCK
    assert city.rows == WORLD_H // BLOCK
    assert len(city.cells) == city.cols * city.rows


def test_every_cell_has_a_known_type():
    city = City()
    valid_types = {"building", "empty", "lake", "park", "plaza", "parking", "landmark"}
    assert set(city.cells.values()) <= valid_types


def test_lake_blocks_movement():
    city = City()
    if not city.lakes:
        return  # geração aleatória: nem sempre haverá lago, e tudo bem
    _, _, rect = city.lakes[0]
    cx, cy = rect.center
    assert city.is_building(cx, cy) is True
    assert city.collide_rect(pygame.Rect(cx - 5, cy - 5, 10, 10)) is True


def test_point_far_outside_world_is_not_a_building():
    city = City()
    assert city.is_building(-9999, -9999) is False


def test_money_is_never_generated_inside_a_building():
    city = City()
    for x, y, _active in city.money:
        assert city.is_building(x, y) is False


def test_collide_rect_true_for_known_building():
    city = City()
    if not city.buildings:
        return
    rect, color = city.buildings[0]
    if color is None:  # é um lago, não um prédio - pula
        return
    assert city.collide_rect(rect) is True


def test_collide_rect_false_for_rect_far_from_everything():
    city = City()
    far_rect = pygame.Rect(-500, -500, 4, 4)
    assert city.collide_rect(far_rect) is False

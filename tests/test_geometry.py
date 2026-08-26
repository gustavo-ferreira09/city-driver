"""Testes para open_city.utils.geometry."""

import math

from open_city.utils import clamp, rot_point


def test_clamp_within_range_returns_value_unchanged():
    assert clamp(5, 0, 10) == 5


def test_clamp_below_range_returns_lower_bound():
    assert clamp(-5, 0, 10) == 0


def test_clamp_above_range_returns_upper_bound():
    assert clamp(15, 0, 10) == 10


def test_clamp_at_boundaries_is_inclusive():
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10


def test_rot_point_zero_angle_is_identity():
    x, y = rot_point(3, 4, 0)
    assert math.isclose(x, 3)
    assert math.isclose(y, 4)


def test_rot_point_quarter_turn():
    x, y = rot_point(1, 0, math.pi / 2)
    assert math.isclose(x, 0, abs_tol=1e-9)
    assert math.isclose(y, 1, abs_tol=1e-9)


def test_rot_point_half_turn_negates_point():
    x, y = rot_point(2, 5, math.pi)
    assert math.isclose(x, -2, abs_tol=1e-9)
    assert math.isclose(y, -5, abs_tol=1e-9)

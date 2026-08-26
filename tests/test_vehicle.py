"""Testes para open_city.entities.Vehicle."""

from open_city.entities import Vehicle
from open_city.palette import CAR_TYPES


def test_vehicle_dimensions_match_its_car_type():
    for car_type, spec in CAR_TYPES.items():
        vehicle = Vehicle(0, 0, spec["colors"][0], car_type=car_type)
        assert vehicle.w == spec["w"]
        assert vehicle.h == spec["h"]


def test_unknown_car_type_falls_back_to_sedan_dimensions():
    vehicle = Vehicle(0, 0, (255, 0, 0), car_type="nao-existe")
    sedan = CAR_TYPES["sedan"]
    assert vehicle.w == sedan["w"]
    assert vehicle.h == sedan["h"]


def test_vehicle_starts_undamaged():
    vehicle = Vehicle(0, 0, (255, 0, 0))
    assert vehicle.crashed is False
    assert vehicle.abandoned is False
    assert vehicle.stunned == 0
    assert vehicle.speed == 0


def test_cop_vehicle_has_higher_top_speed_than_civilian():
    civilian = Vehicle(0, 0, (255, 0, 0), is_cop=False)
    cop = Vehicle(0, 0, (0, 0, 255), is_cop=True)
    assert cop.max_speed > civilian.max_speed


def test_corners_form_a_rectangle_of_the_expected_size():
    vehicle = Vehicle(100, 100, (255, 0, 0), car_type="sedan")
    corners = vehicle.corners()
    xs = [c[0] for c in corners]
    ys = [c[1] for c in corners]
    assert max(xs) - min(xs) == vehicle.w
    assert max(ys) - min(ys) == vehicle.h

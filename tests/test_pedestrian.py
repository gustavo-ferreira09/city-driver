"""Testes para open_city.entities.Pedestrian."""

from open_city.entities import Pedestrian
from open_city.world import City


def test_pedestrian_starts_in_walk_state():
    ped = Pedestrian(0, 0)
    assert ped.state == "walk"


def test_hit_triggers_ragdoll_state():
    ped = Pedestrian(0, 0)
    ped.hit(2.0, 0.0)
    assert ped.state == "ragdoll"


def test_hit_is_ignored_while_already_a_ragdoll():
    ped = Pedestrian(0, 0)
    ped.hit(2.0, 0.0)
    ped.vx = 5.0  # simula um impulso já em andamento
    ped.hit(-2.0, 0.0)  # não deve reiniciar/alterar o impulso
    assert ped.vx == 5.0


def test_hit_is_ignored_once_dead():
    ped = Pedestrian(0, 0)
    ped.state = "dead"
    ped.hit(2.0, 0.0)
    assert ped.state == "dead"


def test_checking_state_returns_to_walk_after_timer_runs_out():
    ped = Pedestrian(0, 0)
    ped.state = "checking"
    ped.check_timer = 3
    city = City()
    blood: list = []
    for _ in range(5):
        ped.update(city, blood)
    assert ped.state == "walk"


def test_ragdoll_eventually_settles_to_dead_and_leaves_blood():
    ped = Pedestrian(100, 100)
    ped.hit(0.02, 0.0)  # impulso bem fraco -> assenta rápido
    city = City()
    blood: list = []
    for _ in range(60):
        ped.update(city, blood)
        if ped.state == "dead":
            break
    assert ped.state == "dead"
    assert len(blood) > 0

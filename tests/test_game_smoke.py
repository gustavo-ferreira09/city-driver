"""
Teste de fumaça ("smoke test") do jogo completo.

Não valida pixel por pixel - só garante que o laço de atualização e desenho
roda por muitos quadros, com entradas variadas, sem levantar nenhuma exceção.
É a rede de segurança mais barata para pegar erros de integração entre os
módulos (mundo, entidades, IA de trânsito/polícia, HUD).
"""

import pygame

from open_city import Game


class _FakeKeys(dict):
    """Simula o resultado de ``pygame.key.get_pressed()`` para os testes,
    sem precisar de um teclado real nem de eventos de janela."""

    def __init__(self, pressed=None):
        super().__init__()
        self._pressed = pressed or set()

    def __getitem__(self, key):
        return key in self._pressed


def test_game_runs_many_frames_without_crashing():
    pygame.init()
    game = Game()
    keys = _FakeKeys({pygame.K_w})
    for _ in range(120):
        game.update(keys)
        game.draw()
    assert game.money_count >= 0


def test_game_handles_turning_and_braking():
    pygame.init()
    game = Game()
    keys = _FakeKeys({pygame.K_w, pygame.K_d})
    for _ in range(60):
        game.update(keys)
    assert game.player_car.speed != 0 or game.player_car.crashed


def test_toggle_car_switches_control_mode():
    pygame.init()
    game = Game()
    assert game.in_car is True

    game.toggle_car()
    assert game.in_car is False
    assert game.player_car is None

    game.toggle_car()
    assert game.in_car is True
    assert game.player_car is not None


def test_reset_restores_initial_state():
    pygame.init()
    game = Game()
    game.money_count = 500
    game.wanted = 3.0

    game.reset()

    assert game.money_count == 0
    assert game.wanted == 0.0
    assert game.game_over is False


def test_run_over_pedestrian_raises_wanted_level():
    pygame.init()
    game = Game()
    car = game.player_car
    car.angle = 0
    car.speed = 5.0

    from open_city.entities import Pedestrian
    victim = Pedestrian(car.x, car.y)
    victim.state = "walk"
    game.peds.append(victim)

    game._maybe_run_over(victim)

    assert victim.state == "ragdoll"
    assert game.wanted > 0


def test_vehicle_collision_marks_civilian_car_as_crashed():
    pygame.init()
    game = Game()
    car = game.player_car
    car.angle = 0
    car.speed = 5.0

    victim = game.other_cars[0]
    victim.x, victim.y = car.x + 5, car.y
    victim.speed = 0

    game.resolve_vehicle_collisions()

    assert victim.crashed is True

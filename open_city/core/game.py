"""
Laço principal do jogo.

A classe :class:`Game` junta o mundo (:class:`~open_city.world.City`), as
entidades (:class:`~open_city.entities.Vehicle`,
:class:`~open_city.entities.Pedestrian`) e a entrada do jogador num único
laço de atualização e desenho.

Para manter o arquivo pequeno e cada assunto isolado, ``Game`` é composta a
partir de "mixins" temáticos definidos nos módulos vizinhos deste pacote:

* :class:`~open_city.core.traffic.TrafficMixin` - IA do tráfego civil.
* :class:`~open_city.core.collisions.CollisionMixin` - colisão entre veículos.
* :class:`~open_city.core.police.PoliceMixin` - spawn e perseguição da polícia.
* :class:`~open_city.core.hud.HudMixin` - desenho da interface.

Todos compartilham o mesmo estado de partida (``self.city``, ``self.peds``
etc.), definido aqui em ``Game.__init__``/``Game.reset``.
"""

import math
import random
import sys

import pygame

from ..entities import Pedestrian, Vehicle, draw_walking_person
from ..palette import COLORS
from ..settings import FPS, RANDOM_SEED, SCREEN_H, SCREEN_W, WORLD_H, WORLD_W
from ..utils import clamp, rot_point
from ..world import City
from .collisions import CollisionMixin
from .hud import HudMixin
from .police import PoliceMixin
from .traffic import TrafficMixin

pygame.init()
if RANDOM_SEED is not None:
    random.seed(RANDOM_SEED)

# quantos pedestres/carros de trânsito existem por padrão numa partida
INITIAL_PEDESTRIAN_COUNT = 60
INITIAL_TRAFFIC_CAR_COUNT = 26
MAX_ACTIVE_PEDESTRIANS = 55
MAX_FALLEN_BODIES = 18
MAX_BLOOD_STAINS = 260


class Game(TrafficMixin, CollisionMixin, PoliceMixin, HudMixin):
    """Orquestra o estado da partida: mundo, jogador, tráfego, polícia e HUD."""

    def __init__(self) -> None:
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("OPEN CITY - um jogo estilo GTA feito em Python")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.font_big = pygame.font.SysFont("arial", 48, bold=True)
        self.reset()

    # -----------------------------------------------------------------
    # Ciclo de vida da partida
    # -----------------------------------------------------------------
    def reset(self) -> None:
        """(Re)inicia a partida: gera um mundo novo e reposiciona tudo."""
        self.city = City()
        cx, cy = WORLD_W / 2, WORLD_H / 2
        self.player_car = Vehicle(cx, cy, COLORS["car"], car_type="esportivo")
        self.in_car = True

        # aparência e estado do protagonista quando está a pé
        self.foot_x, self.foot_y = cx, cy
        self.foot_angle = 0.0
        self.foot_walk_phase = 0.0
        self.foot_moving = False
        self.player_skin = (225, 190, 150)
        self.player_shirt = (60, 90, 200)
        self.player_pants = (30, 30, 35)
        self.player_hair = (40, 25, 15)

        self.other_cars = [self.make_traffic_car() for _ in range(INITIAL_TRAFFIC_CAR_COUNT)]
        self.peds = [p for p in self._spawn_initial_pedestrians()]

        self.blood: list = []  # manchas de sangue no chão: [x, y, raio]
        self.cops: list = []
        self.wanted = 0.0  # 0..5
        self.money_count = 0
        self.game_over = False
        self.survive_timer = 0

    def _spawn_initial_pedestrians(self):
        for _ in range(INITIAL_PEDESTRIAN_COUNT):
            x = random.uniform(0, WORLD_W)
            y = random.uniform(0, WORLD_H)
            if not self.city.is_building(x, y):
                yield Pedestrian(x, y)

    # -----------------------------------------------------------------
    # Jogador
    # -----------------------------------------------------------------
    def player_pos(self):
        """Posição atual do jogador, esteja ele de carro ou a pé."""
        if self.in_car:
            return self.player_car.x, self.player_car.y
        return self.foot_x, self.foot_y

    def toggle_car(self) -> None:
        """Tecla E: sai do carro se estiver dirigindo, ou entra no carro mais próximo se a pé."""
        if self.game_over:
            return
        if self.in_car:
            self._exit_car()
        else:
            self._enter_nearest_car()

    def _exit_car(self) -> None:
        car = self.player_car
        off_x, off_y = rot_point(0, car.h / 2 + 16, car.angle)
        self.foot_x = clamp(car.x + off_x, 0, WORLD_W)
        self.foot_y = clamp(car.y + off_y, 0, WORLD_H)
        self.foot_angle = car.angle
        car.speed = 0
        if not hasattr(car, "cruise_speed"):
            car.cruise_speed = 2.2
            car.turn_timer = random.randint(60, 200)
        self.other_cars.append(car)  # o carro fica no mundo, pode ser reocupado depois
        self.player_car = None
        self.in_car = False

    def _enter_nearest_car(self) -> None:
        nearest, nearest_dist = None, 42
        for candidate in self.other_cars:
            dist = math.hypot(candidate.x - self.foot_x, candidate.y - self.foot_y)
            if dist < nearest_dist:
                nearest_dist, nearest = dist, candidate
        if nearest is not None:
            self.other_cars.remove(nearest)
            nearest.speed = 0
            self.player_car = nearest
            self.in_car = True

    # -----------------------------------------------------------------
    # Atualização
    # -----------------------------------------------------------------
    def update(self, keys) -> None:
        if self.game_over:
            return

        if self.in_car:
            self._update_player_car(keys)
        else:
            self._update_player_on_foot(keys)

        px, py = self.player_pos()
        self._collect_money(px, py)

        for traffic_car in self.other_cars:
            self.update_traffic_car(traffic_car)

        self.resolve_vehicle_collisions()
        self._update_crashed_traffic()

        self._update_pedestrians()
        self._cap_blood_stains()
        self._respawn_pedestrians_if_needed()

        self.update_police(px, py)

    def _update_player_car(self, keys) -> None:
        car = self.player_car
        self._apply_car_acceleration(car, keys)
        self._apply_car_steering(car, keys)
        self._move_car_with_collision(car)

    @staticmethod
    def _apply_car_acceleration(car: Vehicle, keys) -> None:
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            car.speed += car.accel
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            car.speed -= car.accel * 1.3

        if car.speed > 0:
            car.speed -= car.friction
        elif car.speed < 0:
            car.speed += car.friction
        if abs(car.speed) < car.friction:
            car.speed = 0
        car.speed = clamp(car.speed, -car.max_speed / 1.6, car.max_speed)

    @staticmethod
    def _apply_car_steering(car: Vehicle, keys) -> None:
        turn = 0
        if abs(car.speed) > 0.05:
            direction = 1 if car.speed > 0 else -1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                turn = -car.turn_speed * direction
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                turn = car.turn_speed * direction
        car.angle += turn

    def _move_car_with_collision(self, car: Vehicle) -> None:
        nx = car.x + math.cos(car.angle) * car.speed
        ny = car.y + math.sin(car.angle) * car.speed
        test_rect = pygame.Rect(nx - car.w / 2, ny - car.h / 2, car.w, car.h)
        if not self.city.collide_rect(test_rect):
            car.x, car.y = nx, ny
        else:
            car.speed *= -0.3  # bate e ricocheteia um pouco
        car.x = clamp(car.x, 0, WORLD_W)
        car.y = clamp(car.y, 0, WORLD_H)

    def _update_player_on_foot(self, keys) -> None:
        fx = fy = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            fy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            fy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            fx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            fx += 1

        self.foot_moving = fx != 0 or fy != 0
        if not self.foot_moving:
            return

        norm = math.hypot(fx, fy)
        fx, fy = fx / norm, fy / norm
        self.foot_angle = math.atan2(fy, fx)

        speed = 2.4
        nx = self.foot_x + fx * speed
        ny = self.foot_y + fy * speed
        test = pygame.Rect(nx - 5, ny - 5, 10, 10)
        if not self.city.collide_rect(test):
            self.foot_x, self.foot_y = nx, ny
        self.foot_x = clamp(self.foot_x, 0, WORLD_W)
        self.foot_y = clamp(self.foot_y, 0, WORLD_H)
        self.foot_walk_phase += speed * 0.9

    def _collect_money(self, px: float, py: float) -> None:
        for money_spot in self.city.money:
            if money_spot[2] and math.hypot(money_spot[0] - px, money_spot[1] - py) < 25:
                money_spot[2] = False
                self.money_count += 10

    # -----------------------------------------------------------------
    # Pedestres / manchas de sangue
    # -----------------------------------------------------------------
    def _update_pedestrians(self) -> None:
        for ped in self.peds:
            ped.update(self.city, self.blood)
            if self.in_car and ped.state in ("walk", "checking"):
                self._maybe_run_over(ped)

    def _maybe_run_over(self, ped: Pedestrian) -> None:
        car = self.player_car
        if math.hypot(ped.x - car.x, ped.y - car.y) >= 20 or abs(car.speed) <= 1.0:
            return
        impulse_x = math.cos(car.angle) * abs(car.speed) * 1.6
        impulse_y = math.sin(car.angle) * abs(car.speed) * 1.6
        ped.hit(impulse_x, impulse_y)
        for _ in range(5):
            self.blood.append([ped.x + random.uniform(-4, 4),
                                ped.y + random.uniform(-4, 4),
                                random.uniform(2, 5)])
        self.wanted = clamp(self.wanted + 1.0, 0, 5)

    def _cap_blood_stains(self) -> None:
        """Evita que a lista de manchas de sangue cresça sem limite."""
        if len(self.blood) > MAX_BLOOD_STAINS:
            del self.blood[: len(self.blood) - MAX_BLOOD_STAINS]

    def _respawn_pedestrians_if_needed(self) -> None:
        """Limita corpos caídos acumulados no mundo e repõe pedestres andando,
        para a cidade não esvaziar nem virar um cemitério infinito."""
        alive_count = sum(1 for p in self.peds if p.state == "walk")
        dead_count = sum(1 for p in self.peds if p.state != "walk")

        if dead_count > MAX_FALLEN_BODIES:
            for ped in self.peds:
                if ped.state != "walk":
                    self.peds.remove(ped)
                    break

        if alive_count < MAX_ACTIVE_PEDESTRIANS and random.random() < 0.06:
            self._spawn_pedestrian_away_from_player()

    def _spawn_pedestrian_away_from_player(self) -> None:
        px, py = self.player_pos()
        for _ in range(6):
            x = random.uniform(0, WORLD_W)
            y = random.uniform(0, WORLD_H)
            if math.hypot(x - px, y - py) > 350 and not self.city.is_building(x, y):
                self.peds.append(Pedestrian(x, y))
                return

    # -----------------------------------------------------------------
    # Desenho
    # -----------------------------------------------------------------
    def draw(self) -> None:
        px, py = self.player_pos()
        cam_x = clamp(px - SCREEN_W / 2, 0, WORLD_W - SCREEN_W)
        cam_y = clamp(py - SCREEN_H / 2, 0, WORLD_H - SCREEN_H)

        self.city.draw(self.screen, cam_x, cam_y)
        self.draw_blood(cam_x, cam_y)

        for ped in self.peds:
            ped.draw(self.screen, cam_x, cam_y)
        for traffic_car in self.other_cars:
            traffic_car.draw(self.screen, cam_x, cam_y)
        for cop in self.cops:
            cop.draw(self.screen, cam_x, cam_y)

        self._draw_player(px, py, cam_x, cam_y)
        self.draw_hud()

        if self.game_over:
            self.draw_center_text("VOCÊ FOI PRESO!", "Pressione R para reiniciar")

    def _draw_player(self, px: float, py: float, cam_x: float, cam_y: float) -> None:
        if self.in_car:
            self.player_car.draw(self.screen, cam_x, cam_y)
        else:
            draw_walking_person(self.screen, px - cam_x, py - cam_y, self.foot_angle,
                                 self.foot_walk_phase, self.foot_moving,
                                 self.player_skin, self.player_shirt,
                                 self.player_pants, self.player_hair,
                                 scale=1.15, outline=(255, 255, 255))

    # -----------------------------------------------------------------
    # Laço principal
    # -----------------------------------------------------------------
    def run(self) -> None:
        """Laço principal: eventos -> atualização -> desenho, a FPS fixo."""
        while True:
            self._handle_events()

            keys = pygame.key.get_pressed()
            if self.in_car and keys[pygame.K_SPACE]:
                self.player_car.speed *= 0.85

            self.update(keys)
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
        if key == pygame.K_r:
            self.reset()
        if key == pygame.K_e:
            self.toggle_car()

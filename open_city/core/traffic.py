"""IA de trânsito: geração e movimentação dos carros civis pelas ruas da cidade."""

import math
import random

import pygame

from ..entities import Vehicle
from ..palette import CAR_TYPES
from ..settings import BLOCK, ROAD_W, WORLD_H, WORLD_W
from ..utils import clamp


class TrafficMixin:
    """
    Comportamento de trânsito civil, pensado para ser misturado na classe
    ``Game`` (via herança múltipla) - por isso os métodos aqui assumem a
    presença de atributos como ``self.city``, ``self.other_cars``,
    ``self.cops`` e ``self.player_car``/``self.in_car``, todos definidos em
    ``Game.__init__``/``Game.reset``.

    Esse padrão de "mixin de assunto" mantém cada tema do jogo (tráfego,
    colisão, polícia, HUD - ver os outros módulos deste pacote) no seu
    próprio arquivo, sem precisar espalhar o estado da partida em vários
    objetos diferentes.
    """

    def random_road_position(self):
        """Sorteia um ponto sobre uma rua (linha central de um quarteirão), com
        pequeno deslocamento lateral dentro da largura da via, e o ângulo
        (0/90/180/270) correspondente à direção dela."""
        horizontal = random.random() < 0.5
        margin = 10
        if horizontal:
            k = random.randint(0, self.city.rows)
            y = k * BLOCK + random.uniform(-ROAD_W / 2 + margin, ROAD_W / 2 - margin)
            x = random.uniform(0, WORLD_W)
            angle = 0.0 if random.random() < 0.5 else math.pi
        else:
            k = random.randint(0, self.city.cols)
            x = k * BLOCK + random.uniform(-ROAD_W / 2 + margin, ROAD_W / 2 - margin)
            y = random.uniform(0, WORLD_H)
            angle = math.pi / 2 if random.random() < 0.5 else -math.pi / 2
        return x, y, angle

    def make_traffic_car(self) -> Vehicle:
        """Cria um novo carro de trânsito de tipo aleatório, já posicionado numa rua."""
        car_type = random.choice(list(CAR_TYPES.keys()))
        color = random.choice(CAR_TYPES[car_type]["colors"])
        x, y, angle = self.random_road_position()
        car = Vehicle(x, y, color, car_type=car_type)
        car.angle = angle
        car.speed = random.uniform(1.6, 2.8)
        car.cruise_speed = car.speed
        car.turn_timer = random.randint(60, 200)
        return car

    def update_traffic_car(self, car: Vehicle) -> None:
        """IA simples de trânsito: anda em linha reta pelas ruas, freia se houver
        algo na frente, e de vez em quando tenta virar 90° numa esquina (ou vira
        forçado quando bate num beco sem saída)."""
        if car.crashed:
            return  # carro batido fica parado (motorista vai descer / já desceu)

        nx = car.x + math.cos(car.angle) * car.speed
        ny = car.y + math.sin(car.angle) * car.speed
        test = pygame.Rect(nx - car.w / 2, ny - car.h / 2, car.w, car.h)
        blocked = self.city.collide_rect(test)

        ahead_blocked = False
        if not blocked:
            for other in self._other_vehicles(car):
                if math.hypot(other.x - nx, other.y - ny) < (car.w + other.w) / 2 + 8:
                    ahead_blocked = True
                    break

        if blocked:
            car.speed = max(0.0, car.speed * 0.5)
        elif ahead_blocked:
            car.speed = max(0.0, car.speed * 0.8)
        else:
            car.x, car.y = nx, ny
            car.speed = min(car.speed + 0.06, car.cruise_speed)

        car.x = clamp(car.x, 0, WORLD_W)
        car.y = clamp(car.y, 0, WORLD_H)

        self._maybe_turn_at_corner(car, blocked)

    def _maybe_turn_at_corner(self, car: Vehicle, blocked: bool) -> None:
        """De tempos em tempos (ou ao bater num beco sem saída), tenta virar 90°
        para não andar sempre reto - dando a impressão de tráfego navegando
        pelos cruzamentos, e não só seguindo em frente para sempre."""
        car.turn_timer -= 1
        want_turn = car.turn_timer <= 0
        if not (want_turn or blocked):
            return

        car.turn_timer = random.randint(90, 240)
        options = [math.pi / 2, -math.pi / 2] if not blocked else [math.pi / 2, -math.pi / 2, math.pi]
        random.shuffle(options)
        for delta in options:
            new_angle = car.angle + delta
            tx = car.x + math.cos(new_angle) * 24
            ty = car.y + math.sin(new_angle) * 24
            trect = pygame.Rect(tx - car.w / 2, ty - car.h / 2, car.w, car.h)
            if self.city.collide_rect(trect):
                continue
            if want_turn and not blocked and random.random() < 0.55:
                continue  # a maior parte das vezes segue reto mesmo podendo virar
            car.angle = new_angle
            break

    def _other_vehicles(self, exclude: Vehicle):
        """Todos os veículos ativos exceto ``exclude`` - usado para desviar de
        quem está na frente."""
        vehicles = list(self.other_cars) + list(self.cops)
        if self.in_car and self.player_car is not None:
            vehicles.append(self.player_car)
        return [v for v in vehicles if v is not exclude]

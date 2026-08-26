"""
Colisão física entre veículos e a sequência de "acidente": quando a batida é
forte o bastante, o carro civil envolvido fica parado e, pouco depois, seu
motorista desce para checar o estrago (vira um pedestre no estado "checking").
"""

import math
import random

from ..entities import Pedestrian
from ..settings import WORLD_H, WORLD_W
from ..utils import clamp, rot_point

# impacto (soma da velocidade absoluta dos dois veículos) acima do qual uma
# colisão é considerada forte o bastante para gerar um "acidente"
CRASH_IMPACT_THRESHOLD = 1.3
MAX_ABANDONED_CARS = 8


class CollisionMixin:
    """Mistura a lógica de colisão entre veículos na classe ``Game`` (ver
    ``TrafficMixin`` para mais contexto sobre o padrão de mixin usado aqui)."""

    def resolve_vehicle_collisions(self) -> None:
        """Detecta sobreposição entre todos os veículos ativos (jogador, tráfego
        e polícia) e resolve empurrando-os para longe um do outro; batidas
        fortes deixam o carro (não-jogador) 'batido', preparando a saída do
        motorista para checar o estrago."""
        vehicles = list(self.other_cars) + list(self.cops)
        if self.in_car and self.player_car is not None:
            vehicles.append(self.player_car)

        n = len(vehicles)
        for i in range(n):
            a = vehicles[i]
            ra = (a.w + a.h) / 4.2
            for j in range(i + 1, n):
                b = vehicles[j]
                if a.abandoned and b.abandoned:
                    continue
                rb = (b.w + b.h) / 4.2
                dx, dy = b.x - a.x, b.y - a.y
                dist = math.hypot(dx, dy)
                min_dist = ra + rb
                if 0 < dist < min_dist:
                    self._separate_and_maybe_crash(a, b, dist, min_dist, dx, dy)

    def _separate_and_maybe_crash(self, a, b, dist, min_dist, dx, dy) -> None:
        """Empurra ``a`` e ``b`` para fora da sobreposição e, se o impacto for
        forte, marca os carros civis/viaturas envolvidos como batidos."""
        overlap = min_dist - dist
        nx_, ny_ = dx / dist, dy / dist
        a.x -= nx_ * overlap / 2
        a.y -= ny_ * overlap / 2
        b.x += nx_ * overlap / 2
        b.y += ny_ * overlap / 2

        impact = abs(a.speed) + abs(b.speed)
        a.speed *= -0.35
        b.speed *= -0.35

        if impact > CRASH_IMPACT_THRESHOLD:
            self._maybe_crash(a)
            self._maybe_crash(b)

    def _maybe_crash(self, vehicle) -> None:
        """Reage a uma colisão forte de acordo com o tipo de veículo:
        o carro do jogador só ricocheteia; viaturas ficam zonzas por um
        instante; carros civis ficam 'batidos' até o motorista descer."""
        if self.in_car and vehicle is self.player_car:
            return
        if vehicle in self.cops:
            if vehicle.stunned <= 0:
                vehicle.stunned = random.randint(35, 55)
            return
        if not vehicle.crashed and not vehicle.abandoned:
            vehicle.crashed = True
            vehicle.crash_timer = random.randint(50, 90)
            vehicle.speed = 0

    def _spawn_driver_checking(self, car) -> None:
        """Cria o pedestre 'motorista' que desce do carro batido para checar o acidente."""
        off_x, off_y = rot_point(0, car.h / 2 + 12, car.angle + random.uniform(-0.5, 0.5))
        x = clamp(car.x + off_x, 0, WORLD_W)
        y = clamp(car.y + off_y, 0, WORLD_H)
        ped = Pedestrian(x, y)
        ped.state = "checking"
        ped.check_timer = random.randint(100, 220)
        ped.dir = car.angle + math.pi  # fica de frente para o próprio carro
        ped.moving = False
        self.peds.append(ped)

    def _update_crashed_traffic(self) -> None:
        """Faz o motorista descer quando o cronômetro de um carro batido zera, e
        recicla destroços antigos em tráfego novo para não acumular para sempre."""
        abandoned = [c for c in self.other_cars if c.abandoned]
        for car in self.other_cars:
            if car.crashed and not car.abandoned:
                car.crash_timer -= 1
                if car.crash_timer <= 0:
                    self._spawn_driver_checking(car)
                    car.abandoned = True

        if len(abandoned) > MAX_ABANDONED_CARS:
            oldest = abandoned[0]
            if oldest in self.other_cars:
                self.other_cars.remove(oldest)
            self.other_cars.append(self.make_traffic_car())

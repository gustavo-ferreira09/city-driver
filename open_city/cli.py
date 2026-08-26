"""Ponto de entrada usado pelo console-script ``open-city`` (ver pyproject.toml)."""

from .core import Game


def run() -> None:
    """Inicia uma nova partida e roda o laço principal até o jogador sair."""
    Game().run()

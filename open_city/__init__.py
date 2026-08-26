"""
Open City
=========

Um jogo top-down de ação em mundo aberto, inspirado no gênero popularizado
por GTA, escrito do zero em Python + Pygame. Não é afiliado nem reproduz
conteúdo de nenhum jogo comercial - é um projeto original, feito para estudo
e portfólio.

Uso básico::

    from open_city import Game

    Game().run()

Estrutura do pacote:

* ``open_city.settings``  - constantes globais (tela, mundo, ruas).
* ``open_city.palette``   - cores e arquétipos visuais.
* ``open_city.utils``     - funções utilitárias (geometria).
* ``open_city.world``     - geração e desenho da cidade.
* ``open_city.entities``  - veículos e pedestres.
* ``open_city.core``      - laço principal do jogo (classe ``Game``).
"""

from .core import Game

__all__ = ["Game"]
__version__ = "1.0.0"

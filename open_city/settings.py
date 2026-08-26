"""
Configurações globais do jogo.

Reúne, num só lugar, tudo que define a escala do jogo (tamanho de tela, do
mundo e da malha de ruas) para que essas constantes não fiquem espalhadas
pelo código. Ajustar o jogo (por exemplo, deixar o mundo maior ou as ruas
mais largas) deve começar - e, na maioria das vezes, terminar - aqui.
"""

# --- Janela / renderização -------------------------------------------------
SCREEN_W: int = 1000
SCREEN_H: int = 700
FPS: int = 60

# --- Mundo -------------------------------------------------------------
# Tamanho total do mundo, em pixels do "mundo" (não da tela).
WORLD_W: int = 4500
WORLD_H: int = 4500

# Malha urbana: cada quarteirão mede BLOCK x BLOCK pixels, dos quais ROAD_W
# pixels ao redor do quarteirão são reservados para a rua.
BLOCK: int = 360
ROAD_W: int = 150

# --- Aleatoriedade -------------------------------------------------------
# Semente fixa: mantém a geração do mundo (prédios, tráfego, pedestres)
# determinística entre execuções, o que ajuda tanto na depuração manual
# quanto nos testes automatizados. Defina como None para um mundo diferente
# a cada execução.
RANDOM_SEED: int = 7

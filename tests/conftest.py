"""
Configuração compartilhada dos testes.

Força o driver de vídeo/áudio "dummy" do SDL *antes* de qualquer import do
pygame, para que a suíte de testes rode sem precisar de um display real -
essencial em CI, containers e outros ambientes headless.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

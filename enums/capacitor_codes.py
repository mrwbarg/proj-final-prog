
from enum import Enum


class Action(Enum):
    """
        Enum com ações que podem ser realizadas em um banco de capacitores.

        Argumentos:
            None

        Atributos:
            StepUp (int): Código que representa a ligação de um estágio do banco.
            StepDown (int): Código que representa o desligamento de um estágio do banco.

        Métodos:
            None
    """
    StepUp = 1
    StepDown = 2

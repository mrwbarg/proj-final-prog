from enum import Enum


class Action(Enum):
    """
        Enum com ações que podem ser realizadas em um transformador.

        Argumentos:
            None

        Atributos:
            TapUp (int): Código que representa o aumento do tape do transformador.
            TapDown (int): Código que representa a redução do tape do transformador.

        Métodos:
            None
    """
    TapUp = 1
    TapDown = 2

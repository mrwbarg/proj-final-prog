from enum import Enum


class TerminalLocation(Enum):
    """
        Enum com os terminais das linhas que podem ser abertos.

        Argumentos:
            None

        Atributos:
            Start (int): Código que representa o terminal inicial da linha.
            End (int): Código que representa o terminal final da linha.
            Both (int): Código que ambos os terminais da linha.

        Métodos:
            None
    """
    Start = 1
    End = 2
    Both = 3

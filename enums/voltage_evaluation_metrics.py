from enum import Enum


class Metric(Enum):
    """
        Enum com métricas que podem ser utilizadas para avaliar a tensão do sistema.

        Argumentos:
            None

        Atributos:
            AVERAGE (int): Código que representa utilizar a média das tensões.

        Métodos:
            None
    """
    AVERAGE = 1

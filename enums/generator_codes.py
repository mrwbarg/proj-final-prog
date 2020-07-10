from enum import Enum


class Power(Enum):
    """
        Enum com as potências que podem ser alteradas nos geradores.

        Argumentos:
            None

        Atributos:
            Active (int): Código que representa a potência ativa do gerador.
            Reactive (int): Código que representa a potência reativa do gerador.

        Métodos:
            None
    """
    Active = 1
    Reactive = 2

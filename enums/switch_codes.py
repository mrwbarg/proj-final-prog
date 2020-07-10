from enum import Enum


class Action(Enum):
    """
        Enum com ações que podem ser realizadas em uma chave.

        Argumentos:
            None

        Atributos:
            None_ (int): Nenhuma ação.
            Open (int): Abrir a chave.
            Close (int): Fechar a chave.
            Reset (int): Resetar o estado da chave.
            Lock (int): Travar o estado da chave.
            Unlock (int): Destravar o estado da chave.

        Métodos:
            None
    """
    None_ = 0
    Open = 1
    Close = 2
    Reset = 3
    Lock = 4
    Unlock = 5


class State(Enum):
    """
        Enum com os estados que uma chave pode assumir.

        Argumentos:
            None

        Atributos:
            None_ (int): Estado desconhecido.
            Open (int): Chave aberta.
            Closed (int): Chave fechada.

        Métodos:
            None
    """
    None_ = 0
    Open = 1
    Closed = 2

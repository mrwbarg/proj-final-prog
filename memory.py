"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: memory.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""

import numpy as np

from collections import deque


class Memory(object):
    """
        Utilizada para armazenar as experiências passadas do agente. É implementada no formato de um deque.
        Quando o número de itens atinge o máximo, os mais antigos são descartados

        Argumentos:
            size (int): Tamanho da memória.

        Atributos:
            None

        Métodos:

            add(item)
                : Adiciona um item na memória.

            sample(batch_size)
                : Faz uma amostragem aleatória da memória.


    """

    def __init__(self, size):
        self._memory = deque(maxlen=size)

    def add(self, item):
        """
            Adiciona um item na memória.
            O item é adicionado no final.

            Parâmetros:
                item (any): Item a ser adicionado.

            Erros:
                None

            Retorna:
                None

        """
        self._memory.append(item)

    def sample(self, batch_size):
        """
            Faz uma amostragem aleatória da memória.
            Função utilizada no treinamento da rede.

            Parâmetros:
                barch_size (int): Número de amostras.

            Erros:
                None

            Retorna:
                Lista com itens aleatórios da memória.

        """
        random_indexes = np.random.choice(np.arange(len(self._memory)), size=int(batch_size), replace=False)
        return [self._memory[i] for i in random_indexes]

    def __len__(self):
        return len(self._memory)

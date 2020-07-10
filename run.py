"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: run.py
    Data de Criação: 11/03/2020
    Modificado em: 06/04/2020
"""

from environment import Environment


"""
    Arquivo responsável pelo treinamento e execução do modelo.
"""
train = True
env = Environment()
if train:
    env.train()
else:
    env.run()

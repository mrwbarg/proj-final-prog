"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: agent.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""

import pickle
import random
import matplotlib.pyplot as plt
import numpy as np
import operator as op
import joblib
import pandas as pd

from sklearn.preprocessing import StandardScaler, normalize
from statistics import mean
from tqdm import tqdm
from copy import deepcopy
from os import path

import enums.capacitor_codes as CapacitorCodes
import enums.transformer_codes as TransformerCodes

from memory import Memory
from dss_engine import OpenDssEngine
from neural_network import Network
from global_configuration import Configuration

# Local onde o arquivo está sendo executado
basepath = path.dirname(__file__)


class Agent(object):
    """
        Agente inteligente responsável por tomar as decisões inerentes ao reinforcement learning.
        Durante o treinamento, utiliza o protocolo epsilon-greedy.

        Argumentos:
            action_pool (dict): Ações que podem ser tomadas pelo agente. Cada ação possui um código numérico.

        Atributos:
            _action_pool (dict): Mapa de ações que pode ser tomadas ({'id':'ação'}).
            _last_action (str): Última ação tomada.
            _config (Configuration): Arquivo de configurações globais.
            _memory (Memory): Memória para armazenar as ações tomadas, mudanças de estado e recompensas. Os itens guardados na memporia tem o formato {'state': '', 'action': '', 'reward': '', 'next_state': ''}.
            _taken_actions (list(str)): Lista com todas as ações tomadas durante a execução.
            _weekdays_map (dict): Mapa com sigla de dias da semana para números.

        Métodos:

            take_action(model, environment, training, network, current_step, actions_taken)
                : O agente executa uma ação no ambiente seguindo o protocolo epsilon-greedy.

            reset()
                : Reinicia o agente.

            sample_memory()
                : Faz uma amostragem aleatória da memória do agente.

    """

    def __init__(self, action_pool={}):
        self._action_pool = action_pool
        self._last_action = None
        self._config = Configuration()
        self._memory = Memory(self._config.max_memory_size)
        self._taken_actions = []
        self._weekdays_map = {'MON': 1, 'TUE': 2, 'WED': 3, 'THU': 4, 'FRI': 5, 'SAT': 6, 'SUN': 7}

    def take_action(self, model, environment, training, network, current_step, actions_taken):
        """
            O agente executa uma ação no ambiente seguindo o protocolo epsilon-greedy.
            Durante a etapa de treino, o protocolo é seguido. Durante a execução normal a ação tomada é gulosa.

            Parâmetros:
                model (OpenDssEngine): Motor do OpenDSS utilizado para a simulação.
                environment (Environment): Ambiente onde serão executadas as ações.
                training (bool): Indica se está no processo de treinamento ou não.
                network (Network): Rede utilizada para escolher a ação.
                current_step (int): Passo atual da simulação (qual minuto do dia).
                actions_taken (int): Quantas ações foram tomadas no passo atual.

            Erros:
                None

            Retorna:
                None

        """
        alpha = environment.get_base_learning_rate()
        gamma = environment.get_discount_factor()

        initial_state = deepcopy(model.get_state())
        initial_state_voltages = deepcopy(model.get_voltages())

        p = np.random.random()
        # Greedy
        if (training and p < environment.get_epsilon()):
            a = random.choice(list(self._action_pool.keys()))
            _a = self._action_pool[a]
            if _a:
                model.take_action(_a)
            new_state = deepcopy(model.get_state())
            new_state_voltages = deepcopy(model.get_voltages())
            reward = environment.calculate_reward(initial_state_voltages,
                                                  new_state_voltages, _a, self._last_action)
            self._last_action = _a
            self._memory.add({
                'state': deepcopy(initial_state.state_space_repr(current_step, actions_taken, self._weekdays_map[model.get_weekday()])),
                'action': deepcopy(a),
                'reward': deepcopy(reward),
                'next_state': deepcopy(new_state.state_space_repr(current_step, actions_taken, self._weekdays_map[model.get_weekday()]))})
        # Optimal
        else:
            inputs = np.expand_dims(np.array(initial_state.state_space_repr(current_step, actions_taken, self._weekdays_map[model.get_weekday()]), dtype=np.float32), 0)
            a = np.squeeze(np.argmax(network.model(inputs), axis=-1))
            _a = self._action_pool[int(a)]
            if _a:
                model.take_action(_a)

            self._taken_actions.append(_a)

            if training:
                new_state = deepcopy(model.get_state())
                new_state_voltages = deepcopy(model.get_voltages())
                reward = environment.calculate_reward(initial_state_voltages, new_state_voltages, _a, self._last_action)
                self._last_action = _a
                self._memory.add({
                    'state': deepcopy(initial_state.state_space_repr(current_step, actions_taken, self._weekdays_map[model.get_weekday()])),
                    'action': deepcopy(a),
                    'reward': deepcopy(reward),
                    'next_state': deepcopy(new_state.state_space_repr(current_step, actions_taken, self._weekdays_map[model.get_weekday()]))})

    def reset(self):
        """
            Apaga a memória, ações tomadas e última ação tomada do agente.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None

        """
        self._last_action = None
        self._memory = Memory(self._config.max_memory_size)
        self._taken_actions = []

    def sample_memory(self):
        """
            Faz uma amostragem aleatória da memória do agente. 
            Função utilizada no treinamento da rede.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com itens aleatórios da memória.

        """
        return self._memory.sample(self._config.memory_batch_size)

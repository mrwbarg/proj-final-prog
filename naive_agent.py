"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: naive_agent.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""
import random
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from tqdm import tqdm
from copy import deepcopy
from statistics import mean
from os import path

from dss_engine import OpenDssEngine
from global_configuration import Configuration

basepath = path.dirname(__file__)


class NaiveAgent(object):
    """
        Classe responsável por criar um agente que atue no problema de controle de tensão de maneira gulosa,
        para efeitos de comparação.

        Argumentos:
            None

        Atributos:
            _model (OpenDssEngine):  Motor do OpenDSS utilizado para a simulação.
            _config (Configuration): Configurações globais do projeto.
            _max_episodes (int): Número máximo de episódios para treinamento.
            _experience (dict): Experiência adquirida pelo agente ao interagir com o sistema. Armazena o efeito na tensão em cada barra ao se tomar uma determinada ação.
            _steps_per_episode (int): Tamanho de cada episódio.
            _actions_per_step (int): Quantas ações podem ser tomadas em cada passo.
            _possible_actions (list(Tuple | None)): Ações que podem ser tomadas pelo agente no sistema.
            _cache_file (string): Caminho do arquivo utilizado para armazenar a experiência do agente.
            _current_episode (int): Episódio atual.
            _current_step (int): Passo dentro do episódio atual.
            _actions_taken (int): Quantas ações foram tomadas no passo atual.

        Métodos:

            train()
                : Executa o processo de treinamento do agente.

            run()
                : Inicia a execução do algoritmo utilizando o agente naive.

            get_voltage_targets()
                :

            take_action(train)
                :

            get_experience(voltages_before, voltages_after, action)
                :

            dump_experience()
                :

            load_experience()
    """

    def __init__(self):
        self._model = OpenDssEngine()
        self._config = Configuration()
        self._model.start()

        self._max_episodes = 100
        self._experience = {}

        self._steps_per_episode = self._model.get_episode_length()
        self._actions_per_step = self._model.get_actions_per_step()
        self._possible_actions = self._model.get_possible_actions() + [None]

        self._cache_file = "naive_xp_" + self._model.get_file_name() + '.cache'

        self._current_episode = 1
        self._current_step = 1
        self._actions_taken = 0

        self.load_experience()

    def train(self):
        """"
            Executa o processo de treinamento do agente. A cada passo da simulação, o agente toma uma decisão.
            A experiência é atualizada de acordo com o resultado das decisões tomadas.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """

        start_state = deepcopy(self._model.get_state())

        pbar = tqdm(total=self._max_episodes,
                    desc='Naive Train Episode: ', position=1, leave=True)

        while (self._current_episode <= self._max_episodes):
            self._model.start()
            self._current_step = 1
            self._model.set_state(deepcopy(start_state))

            while (self._current_step <= self._steps_per_episode):
                self._model.update_loads(self._current_step)
                self._actions_taken = 0
                while (self._actions_taken < self._actions_per_step):
                    voltages_before = self._model.get_voltages()
                    action = self.take_action(True)
                    voltages_after = self._model.get_voltages()
                    self._actions_taken += 1
                    self.get_experience(
                        voltages_before, voltages_after, action)
                self._current_step += 1
            self._current_episode += 1
            pbar.update(1)

        self.dump_experience()

        self._model.set_state(deepcopy(start_state))

    def run(self):
        """
            Inicia a execução do algoritmo utilizando o agente naive já treinado.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Tensão média controlada e tensão média controlada por barramento.
        """
        self._model.start(False)
        start_state = deepcopy(self._model.get_state())

        pbar = tqdm(total=self._steps_per_episode,
                    desc='Naive Run: ', position=0, leave=True)

        self._model.start(False)
        self._current_step = 1
        self._model.set_state(deepcopy(start_state))
        self.get_voltage_targets()
        load_profile = deepcopy(self._model.get_load_profile())

        naive_controlled_voltages = []
        naive_controlled_voltages_bus = []
        while (self._current_step <= self._steps_per_episode):
            self._model.update_loads(self._current_step)
            self._actions_taken = 0
            while (self._actions_taken < self._actions_per_step):
                action = self.take_action(False)
                naive_controlled_voltages.append(
                    self._model.evaluate_voltages())
                naive_controlled_voltages_bus.append(
                    self._model.get_voltages())
                self._actions_taken += 1
            self._current_step += 1
            pbar.update(1)

        self._model.start(False)
        self._current_step = 1
        self._actions_taken = 0
        self._model.set_state(deepcopy(start_state))
        self._model.update_load_profile(load_profile)

        self._model.set_state(deepcopy(start_state))

        return (naive_controlled_voltages, naive_controlled_voltages_bus)

    def get_voltage_targets(self):
        """
            Obtém os alvos de tensão de uma arquivo para cada barramento e cada minuto do dia.
            O arquivo tem o formato 'bus';'minute';'target'.
            Caso não exista o arquivo ou não haja dados para o alvo para um determinado barramento/minuto,
            o alvo padrão (1 p.u.) é utilizado.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Alvo de tensão ou none.
        """
        weekday = self._model.get_weekday()
        if path.isfile(path.join(basepath, "voltage_targets", weekday + ".csv")):
            self._targets = pd.read_csv(
                path.join(basepath, "voltage_targets", weekday + ".csv"), sep=";")
            self._targets.set_index(['bus', 'minute'], inplace=True)
        else:
            self._targets = None

    def take_action(self, train):
        """
            O agente executa uma ação no ambiente.
            Durante a etapa de treino, as ações tomadas são aleatórias de maneira a explorar o maior número de cenãrios.
            Durante a execução, a ação é escolhida da experiência de maneira gulosa através de um mecanismo de votação.
            Para cada barra, é avaliada se a tensão deve abaixar, aumentar ou se manter. Então a ação que mais teve o efeito desejado
            na barra recebe um voto. No final, a ação com mais votos é escolhida.


            Parâmetros:
                train (bool): Indica se está no processo de treinamento ou não.

            Erros:
                None

            Retorna:
                Ação escolhida.

        """
        if train:
            a = random.choice(self._possible_actions)
            self._model.take_action(a)
            return a

        else:
            v_direction = {}
            action_votes = {}
            for _bus in self._model.get_voltages():

                if self._targets is not None:
                    bus = _bus['bus']
                    query = f'bus == "{bus}" and minute == {self._current_step}'

                    target = self._targets.query(query)['target']

                    if not target.empty:
                        v_target = float(target)
                    else:
                        v_target = self._config.target_voltage

                else:
                    v_target = self._config.target_voltage

                if mean(_bus['voltages']) > v_target * 1.02:
                    v_direction[_bus['bus']] = 'down'

                elif mean(_bus['voltages']) < v_target * 0.98:
                    v_direction[_bus['bus']] = 'up'

                else:
                    v_direction[_bus['bus']] = 'same'

                for a, r in self._experience[_bus['bus']].items():
                    if a not in action_votes:
                        action_votes[a] = 0

                    total = r['up'] + r['down'] + r['same']

                    action_votes[a] += r[v_direction[_bus['bus']]] / total

            ranked_actions = {k: v for k, v in sorted(
                action_votes.items(), key=lambda i: i[1])}
            self._model.take_action(ranked_actions.popitem()[0])
            return a

    def get_experience(self, voltages_before, voltages_after, action):
        """
            Obtém a experiência sobre o efeito da ação tomada em cada barra.


            Parâmetros:
                voltages_before (dict): Dicionário com as tensões em cada barra na etapa anterior.
                voltages_after (dict): Dicionário com as tensões em cada barra na etapa atual após a ação ser tomada.
                action (tuple): Ação tomada.

            Erros:
                None

            Retorna:
                None

        """
        for bus_before, bus_after in zip(voltages_before, voltages_after):
            if bus_before['bus'] not in self._experience:
                self._experience[bus_before['bus']] = {}
                self._experience[bus_before['bus']][action] = {
                    'up': 0, 'down': 0, 'same': 0}

            elif action not in self._experience[bus_before['bus']]:
                self._experience[bus_before['bus']][action] = {
                    'up': 0, 'down': 0, 'same': 0}

            voltage_before = mean(bus_before['voltages'])
            voltage_after = mean(bus_after['voltages'])

            if voltage_after > voltage_before:
                self._experience[bus_before['bus']][action]['up'] += 1
            elif voltage_after < voltage_before:
                self._experience[bus_before['bus']][action]['down'] += 1
            else:
                self._experience[bus_before['bus']][action]['same'] += 1

    def dump_experience(self):
        """
            Salva a experiência no disco.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None

        """
        with open(str(path.join(basepath, "cache", self._cache_file)), 'wb') as cache:
            joblib.dump(self._experience, cache)

    def load_experience(self):
        """
            Carrega a experiência do disco.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None

        """
        if path.isfile(path.join(basepath, "cache", self._cache_file)):
            with open(str(path.join(basepath, "cache", self._cache_file)), 'rb') as cache:
                self._experience = joblib.load(cache)
        else:
            self._experience = {}


# a = NaiveAgent()
# a.train()

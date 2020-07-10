"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: environment.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from statistics import mean
from tqdm import tqdm
from copy import deepcopy
from os import path
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from math import sqrt

import enums.capacitor_codes as CapacitorCodes
import enums.transformer_codes as TransformerCodes

from dss_engine import OpenDssEngine
from neural_network import Network
from global_configuration import Configuration
from agent import Agent
from naive_agent import NaiveAgent

basepath = path.dirname(__file__)


class Environment(object):
    """
        Responsável por lidar com as interações com o modelo do circuito criado no OpenDSS.

        Argumentos:
            None

        Atributos:
            _model (OpenDssEngine):  Motor do OpenDSS utilizado para a simulação.
            _config (Configuration): Configurações globais do projeto.
            _max_episodes (int): Número máximo de episódios para treinamento.
            _steps_per_episode (int): Tamanho de cada episódio.
            _actions_per_step (int): Quantas ações podem ser tomadas em cada passo.
            _possible_actions (list(Tuple | None)): Ações que podem ser tomadas pelo agente no sistema.
            _possible_actions_map (dict): Mapeamento das ações para códigos.
            _weekdays_map (dict): Mapeamento dos dias da semana para números.
            _voltage_targets (dict): Alvos de tensão para cada barra.
            _current_episode (int): Episódio atual.
            _current_step (int): Passo dentro do episódio atual.
            _actions_taken (int): Quantas ações foram tomadas no passo atual.
            _training_steps (int): Número total de passos. Utilizado para iniciar o memory replay da rede.
            _agent (Agent): Agente que decide as ações a serem tomadas.
            _online_network (Network): Rede Neural online.
            _target_network (Network): Rede Neural offline.

        Métodos:

            train()
                : Executa o processo de treinamento do agente.

            run()
                : Inicia a execução do algoritmo.

            plot_run_results(by_bus_controlled_voltage, by_bus_normal_voltage, controlled_average_voltage, normal_average_voltage, naive_average_voltage, naive_by_bus_voltage)
                : Representa de maneira gráfica os resultados da execução do algoritmo.

            _check_action_undone(last_action, action)
                : Verifica se uma ação tomada em uma etapa do algoritmo é oposta a realizada na etapa anterior.

            get_voltage_targets()
                : Obtém os alvos de tensão de uma arquivo para cada barramento e cada minuto do dia.

            calculate_reward(previous_state, current_state, action, last_action)
                : Calcula o prêmio recebido pelo agente de acordo com a ação tomada e a mudança de estado gerada.

            get_epsilon()
                : Obtém o parâmetro epsilon a ser utilizado no passo atual.

            get_base_learning_rate()
                : Obtém a taxa de aprendizado a ser utilizada na rede neural.

            get_discount_factor()
                : Obtém a taxa de aprendizado a ser utilizada no reinforcement learning.

            sync_networks()
                : Sincroniza as redes online e offline, copiando os pesos de uma para outra.

            scaler_partial_fit(inputs)
                : Faz o fit parcial do normalizador utilizado na entrada das redes neurais com os dados disponíveis até a etapa atual.

            _train_network()
                : Treina a rede online através de uma amostragem aleatória da memória do agente.




    """

    def __init__(self):
        self._model = OpenDssEngine()
        self._config = Configuration()
        self._model.start()

        self._max_episodes = 1000
        self._steps_per_episode = self._model.get_episode_length()
        self._actions_per_step = self._model.get_actions_per_step()
        self._possible_actions = self._model.get_possible_actions() + [None]
        self._possible_actions_map = dict({(i, action) for i, action in enumerate(self._possible_actions)})
        self._weekdays_map = {'MON': 1, 'TUE': 2, 'WED': 3, 'THU': 4, 'FRI': 5, 'SAT': 6, 'SUN': 7}
        self._voltage_targets = None
        self._current_episode = 1
        self._current_step = 1
        self._actions_taken = 0
        self._training_steps = 0

        self._agent = Agent(self._possible_actions_map)

        self._online_network = Network(len(self._model.get_state().state_space_repr(self._current_step, self._actions_taken, self._weekdays_map[self._model.get_weekday()])), len(self._possible_actions), self._model.get_file_name())
        self._target_network = Network(len(self._model.get_state().state_space_repr(self._current_step, self._actions_taken, self._weekdays_map[self._model.get_weekday()])), len(self._possible_actions), self._model.get_file_name())
        self.sync_networks()

    def train(self, plot=True):
        """
            Executa o processo de treinamento do agente. A cada passo da simulação, o agente toma uma decisão.
            As redes são treinadas de acordo com o modo proposto pelo algoritmo.

            Parâmetros:
                plot (bool): Determina se a perda acumulada da rede será plotada após o treino.

            Erros:
                None

            Retorna:
                Perda média da rede online.
        """
        self._current_episode = 1
        self._current_step = 1
        self._actions_taken = 0
        self._training_steps = 0
        self._agent.reset()

        start_state = deepcopy(self._model.get_state())

        self._online_network._scaler.partial_fit(np.array(self._model.get_state().state_space_repr(self._current_step, self._actions_taken, self._weekdays_map[self._model.get_weekday()])).reshape(1, -1))
        self._target_network._scaler.partial_fit(np.array(self._model.get_state().state_space_repr(self._current_step, self._actions_taken, self._weekdays_map[self._model.get_weekday()])).reshape(1, -1))

        pbar = tqdm(total=self._max_episodes, desc='Episode: ', position=0, leave=True)

        while (self._current_episode <= self._max_episodes):
            self._model.start(False)
            self._current_step = 1
            self.get_voltage_targets()
            self._model.set_state(deepcopy(start_state))
            while (self._current_step <= self._steps_per_episode):
                self._model.update_loads(self._current_step)
                self._actions_taken = 0
                while (self._actions_taken < self._actions_per_step):
                    self._agent.take_action(
                        self._model, self, True, self._online_network, self._current_step, self._actions_taken)
                    self._actions_taken += 1
                    self._training_steps += 1

                    if self._training_steps > self._config.replay_start:
                        self._train_network()

                        if self._training_steps % self._config.target_update_frequency == 0:
                            self.sync_networks()

                self._current_step += 1
            self._current_episode += 1
            pbar.update(1)

        self.sync_networks()
        self._target_network.dump_weights()
        self._target_network.dump_scaler()

        self._model.set_state(deepcopy(start_state))

        # Plotar a perda da rede após o treino
        loss = self._online_network.get_loss()
        if plot:
            plt.plot([x for x in range(len(loss))], loss)
            plt.show()

        return sum(loss) / len(loss)

    def run(self):
        """
            Inicia a execução do algoritmo.
            São feitas três rodadas com o sistema na mesma condição inicial:
                -> Agente de RL atua sobre o sistema.
                -> Agente Naive atua sobre o sistema.
                -> O sistema roda sem nenhuma ação externa, com ou sem atuação dos reguladores automáticos (parâmetro da função start).

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Tensão média e por barramento, controlada e não controlada.
        """
        self._model.start(False)

        normal_average_voltage = []
        controlled_average_voltage = []
        by_bus_normal_voltage = []
        by_bus_controlled_voltage = []
        start_state = deepcopy(self._model.get_state())
        load_profile = deepcopy(self._model.get_load_profile())

        self._current_step = 1
        self._agent.reset()
        self._actions_taken = 0
        self._model.set_state(deepcopy(start_state))
        self._model.update_load_profile(load_profile)

        pbar = tqdm(total=self._steps_per_episode, desc='Smart Run Step: ', position=0, leave=True)
        while (self._current_step <= self._steps_per_episode):
            self._actions_taken = 0
            while (self._actions_taken < self._actions_per_step):
                self._model.update_loads(self._current_step)
                self._agent.take_action(
                    self._model, self, False, self._target_network, self._current_step, self._actions_taken)
                controlled_average_voltage.append(
                    self._model.evaluate_voltages())
                by_bus_controlled_voltage.append(self._model.get_voltages())
                self._actions_taken += 1
            self._current_step += 1
            pbar.update(1)

        print(self._agent._taken_actions)

        self._model.start(False)
        self._current_step = 1
        self._agent.reset()
        self._actions_taken = 0
        self._model.set_state(deepcopy(start_state))
        self._model.update_load_profile(load_profile)

        na = NaiveAgent()
        naive_average_voltages, naive_by_bus_voltages = na.run()

        self._model.start(True)
        self._current_step = 1
        self._agent.reset()
        self._actions_taken = 0
        self._model.set_state(deepcopy(start_state))
        self._model.update_load_profile(load_profile)

        pbar = tqdm(total=self._steps_per_episode,
                    desc='No-Action Run Step: ', position=0, leave=True)
        while (self._current_step <= self._steps_per_episode):
            self._actions_taken = 0
            while (self._actions_taken < self._actions_per_step):
                self._model.update_loads(self._current_step)
                normal_average_voltage.append(
                    self._model.evaluate_voltages())
                by_bus_normal_voltage.append(self._model.get_voltages())
                self._actions_taken += 1
            self._current_step += 1
            pbar.update(1)

        self.plot_run_results(by_bus_controlled_voltage, by_bus_normal_voltage, controlled_average_voltage, normal_average_voltage, naive_average_voltages, naive_by_bus_voltages)
        return (controlled_average_voltage, normal_average_voltage, by_bus_controlled_voltage, by_bus_normal_voltage)

    def plot_run_results(self, by_bus_controlled_voltage, by_bus_normal_voltage, controlled_average_voltage, normal_average_voltage, naive_average_voltage, naive_by_bus_voltage):
        """
            Representa de maneira gráfica os resultados da execução do algoritmo.

            Parâmetros:
                by_bus_controlled_voltage (list): Lista com as tensões controladas em cada barramento pelo agente de RL.
                by_bus_normal_voltage (list): Lista com as tensões não controladas em cada barramento.
                controlled_average_voltage (list): Lista com a tensão média controlada pelo agente de RL.
                normal_average_voltage (list): Lista com a tensão média não controlada.
                naive_average_voltage (list): Lista com a tensão média controlada pelo agente naive.
                naive_by_bus_voltage (list):  Lista com as tensões controladas em cada barramento pelo agente naive.

            Erros:
                None

            Retorna:
                None
        """
        smart_buses = {}
        base_buses = {}
        naive_buses = {}
        for smart_step, step, naive_step in zip(by_bus_controlled_voltage, by_bus_normal_voltage, naive_by_bus_voltage):
            for smart_bus, base_bus, naive_bus in zip(smart_step, step, naive_step):
                if smart_bus['bus'] in smart_buses:
                    smart_buses[smart_bus['bus']].append(mean(smart_bus['voltages']))
                else:
                    smart_buses[smart_bus['bus']] = [mean(smart_bus['voltages'])]

                if base_bus['bus'] in base_buses:
                    base_buses[base_bus['bus']].append(mean(base_bus['voltages']))
                else:
                    base_buses[base_bus['bus']] = [mean(base_bus['voltages'])]

                if naive_bus['bus'] in naive_buses:
                    naive_buses[naive_bus['bus']].append(mean(naive_bus['voltages']))
                else:
                    naive_buses[naive_bus['bus']] = [mean(naive_bus['voltages'])]

        fig10, ax10 = plt.subplots()
        ax10.set_title("Tensão Controlada (Reinforcement Learning) por Barramento")
        for k, v in smart_buses.items():
            ax10.plot([x for x in range(len(v))], v)

        colormap = plt.cm.nipy_spectral
        colors = [colormap(i) for i in np.linspace(0, 1, len(ax10.lines))]

        for i, j in enumerate(ax10.lines):
            j.set_color(colors[i])

        fig11, ax11 = plt.subplots()
        ax11.set_title("Tensão Normal por Barramento")
        for k, v in base_buses.items():
            ax11.plot([x for x in range(len(v))], v)

        for i, j in enumerate(ax11.lines):
            j.set_color(colors[i])

        fig12, ax12 = plt.subplots()
        ax12.set_title("Tensão Controlada (Naive) por Barramento")
        for k, v in naive_buses.items():
            ax12.plot([x for x in range(len(v))], v)

        for i, j in enumerate(ax12.lines):
            j.set_color(colors[i])

        fig, ax1 = plt.subplots()
        rms_normal = sqrt(mean_squared_error([1 for x in range(len(normal_average_voltage))], normal_average_voltage))
        rms_rl = sqrt(mean_squared_error([1 for x in range(len(controlled_average_voltage))], controlled_average_voltage))
        rms_naive = sqrt(mean_squared_error([1 for x in range(len(naive_average_voltage))], naive_average_voltage))

        p1, = ax1.plot([x for x in range(len(controlled_average_voltage))], controlled_average_voltage, color='blue', label=f"Reinforcement Learning (RMSE: {round(rms_rl, 4)})")
        p2, = ax1.plot([x for x in range(len(normal_average_voltage))], normal_average_voltage, color='red', label=f"Tensão Original (RMSE: {round(rms_normal, 4)})")
        p3, = ax1.plot([x for x in range(len(naive_average_voltage))], naive_average_voltage, color='green', label=f"Agente Naive (RMSE: {round(rms_naive, 4)})")
        lines = [p1, p2, p3]
        ax1.legend(lines, [l.get_label() for l in lines])
        ax1.axhspan(ymax=1.005, ymin=0.995, color='yellow', alpha=0.15)

        plt.title("Tensão Média no Sistema")
        plt.ylabel('Tensão (p.u.)')
        plt.xlabel('Minutos')
        plt.grid(linestyle='dashed')

        data_control = []
        for s in by_bus_controlled_voltage:
            for b in s:
                data_control.append(mean(b['voltages']))

        data_normal = []
        for s in by_bus_normal_voltage:
            for b in s:
                data_normal.append(mean(b['voltages']))

        data_naive = []
        for s in naive_by_bus_voltage:
            for b in s:
                data_naive.append(mean(b['voltages']))

        fig1, ax1 = plt.subplots()
        ax1.set_title('Distribuição das Tensões no Sistema')
        ax1.boxplot([data_control, data_naive, data_normal])
        plt.xticks([1, 2, 3], ['Tensão Controlada (RL)', 'Tensão Controlada (Naive)', 'Tensão Normal'])

        plt.show()

    def _check_action_undone(self, last_action, action):
        """
            Verifica se uma ação tomada em uma etapa do algoritmo é oposta a realizada na etapa anterior.

            Parâmetros:
                last_action (tuple): Ação tomada na etapa anterior.
                action (tuple): Ação tomada na etapa atual.

            Erros:
                None

            Retorna:
                Verdadeiro ou falso de acordo com o resultado.
        """
        if action and last_action:
            if (last_action[0] != action[0]):
                return False

            if (last_action[1] != action[1]):
                return False

            # Capactior
            if (action[0] == self._model.switch_capacitor.__name__):
                if ((action[2] == CapacitorCodes.Action.StepUp and last_action[2] == CapacitorCodes.Action.StepDown) or (action[2] == CapacitorCodes.Action.StepDown and last_action[2] == CapacitorCodes.Action.StepUp)):
                    return True
                else:
                    return False

            # Transformer
            elif (action[0] == self._model.change_tap.__name__):
                if ((action[2] == TransformerCodes.Action.TapUp and last_action[2] == TransformerCodes.Action.TapDown) or (action[2] == TransformerCodes.Action.TapDown and last_action[2] == TransformerCodes.Action.TapUp)):
                    return True
                else:
                    return False

            else:
                return False
        else:
            return False

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
            self._targets = pd.read_csv(path.join(basepath, "voltage_targets", weekday + ".csv"), sep=";")
            self._targets.set_index(['bus', 'minute'], inplace=True)
        else:
            self._targets = None

    def calculate_reward(self, previous_state, current_state, action, last_action):
        """
            Calcula o prêmio recebido pelo agente de acordo com a ação tomada e a mudança de estado gerada.

            Parâmetros:
                previous_state (dict): Dicionário com a tensão em cada barramento no estado anterior.
                current_state (dict): Dicionário com a tensão em cada barramento no estado atual.
                action (tuple): Ação tomada no estado atual.
                last_action (tuple): Ação tomada no estado anterior.

            Erros:
                None

            Retorna:
                Recompensa
        """
        reward = 0
        v_target = None

        for previous_voltage, current_voltage in zip(previous_state, current_state):
            if self._targets is not None:
                bus = current_voltage['bus']
                query = f'bus == "{bus}" and minute == {self._current_step}'

                target = self._targets.query(query)['target']
                if not target.empty:
                    v_target = float(target)
                else:
                    v_target = self._config.target_voltage
            else:
                v_target = self._config.target_voltage

            v_before = round(mean(previous_voltage['voltages']), 3)
            v_after = round(mean(current_voltage['voltages']), 3)

            if (abs(v_target - v_before) < abs(v_target - v_after)):
                reward += self._config.away_target_penalty_over

                if (self._config.lower_voltage_limit * v_target > v_after) or (v_after > self._config.upper_voltage_limit * v_target):
                    reward += self._config.out_of_limits_penalty

            elif (abs(v_target - v_before) > abs(v_target - v_after)):
                reward += self._config.toward_target_reward

            else:

                if (self._config.lower_voltage_limit * v_target > v_after) or (v_after > self._config.upper_voltage_limit * v_target):
                    reward += self._config.out_of_limits_penalty

                if not action:
                    reward += self._config.stand_still_reward_out_of_target

                else:
                    reward += self._config.meaningless_action_penalty

            if self._check_action_undone(last_action, action):
                reward += self._config.action_undone_penalty

        return reward

    def get_epsilon(self):
        """
            Obtém o parâmetro epsilon a ser utilizado no passo atual.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Epsilon (entre 0 e 1)
        """
        decay = ((self._max_episodes + 1 - self._current_episode) / self._max_episodes)
        return max(self._config.epsilon[0], self._config.epsilon[1] * decay)

    def get_base_learning_rate(self):
        """
            Obtém a taxa de aprendizado a ser utilizada na rede neural.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Taxa de aprendizado.
        """
        return self._config.base_learning_rate

    def get_discount_factor(self):
        """
            Obtém a taxa de aprendizado a ser utilizada no reinforcement learning.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Fator de desconto.
        """
        return self._config.discount_factor

    def sync_networks(self):
        """
            Sincroniza as redes online e offline, copiando os pesos de uma para outra.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._target_network = deepcopy(self._online_network)

    def scaler_partial_fit(self, inputs):
        """
            Faz o fit parcial do normalizador utilizado na entrada das redes neurais com os dados disponíveis até a etapa atual.

            Parâmetros:
                inputs (np.array): Array com as entradas que serão utilizadas.

            Erros:
                None

            Retorna:
                None
        """
        self._online_network._scaler.partial_fit(inputs)
        self._target_network._scaler.partial_fit(inputs)

    def _train_network(self):
        """
            Treina a rede online através de uma amostragem aleatória da memória do agente.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        train_batch = self._agent.sample_memory()
        inputs = np.array([sample["state"] for sample in train_batch], dtype=np.float32)

        self.scaler_partial_fit(inputs)
        actions = np.array([sample["action"] for sample in train_batch])
        rewards = np.array([sample["reward"] for sample in train_batch])
        next_inputs = np.array([sample["next_state"] for sample in train_batch], dtype=np.float32)
        self.scaler_partial_fit(next_inputs)
        encoded_actions = np.eye(len(self._possible_actions))[actions]

        best_actions = np.argmax(np.squeeze(self._online_network.model(next_inputs)), axis=-1)
        best_actions_values = np.squeeze(self._target_network.model(next_inputs))
        next_q_values = best_actions_values[np.arange(len(best_actions_values)), best_actions]

        targets = rewards + self._config.discount_factor * next_q_values

        self._online_network.update_weights(inputs, targets, encoded_actions)

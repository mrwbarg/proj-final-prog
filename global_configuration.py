"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: global_configuration.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""

from werkzeug.utils import cached_property


class Configuration(object):
    """
        Classe responsável por abrigar os parâmetros utilizados no projeto todo.

        Argumentos:
            use_lines_as_switches (bool): Define se todas as linhas podem ser chaveadas ou somente as que possue chaves explicítas no circuito.
            force_switch_state (bool): Permite ou não ignorar o estado de travamento das chaves.
            override_regulator_control (bool): Permite ou não que o algoritmo altere o estado dos reguladores de tensão.

        Atri:

            __USE_LINES_AS_SWITCHES (bool): Armazena o argumento definido acima.
            __FORCE_SWITCH_STATE (bool): Armazena o argumento definido acima.
            __OVERRIDE_REGULATOR_CONTROL (bool): Armazena o argumento definido acima.
            __CONST_DAILY_MINUTES (int): Quantidade de minutos considerados em um dia.
            __CONST_V_UPPER_LIMIT (float): Limite superior de tensão.
            __CONST_V_LOWER_LIMIT (float): Limite inferior de tensão.
            __CONST_V_TARGET (float): Alvo padrão de tensão.
            __OUT_OF_LIMITS_PENALTY (float): Penalidade por sair dos limites de tensão.
            __TOWARD_TARGET_REWARD (float): Recompensa por se aproximar do alvo.
            __AWAY_TARGET_PENALTY_OVER (float): Recompensa por se afastar do alvo e estar acima do alvo.
            __AWAY_TARGET_PENALTY_UNDER (float): Recompensa por se afastar do alvo e estar acima do alvo.
            __STAND_STILL_REWARD_OUT_OF_TARGET (float): Recompensa por não mudar o estado mas estar fora do alvo.
            __STAND_STILL_REWARD_ON_TARGET (float): Recompensa por não mudar o estado e estar no alvo.
            __STAND_STILL_PENALTY (float): Penalidade por não mudar o estado.
            __MEANINGLESS_ACTION_PENALTY (float): Penalidade por tomar uma ação sem efeito.
            __ACTION_UNDONE_PENALTY (float): Penalidade por desfazer uma ação.
            __DISCOUNT_FACTOR (float): Fator de desconto
            __BASE_LEARNING_RATE (float): Taxa de aprendizado.
            __MAX_EPSILON (float): Valor máximo de epsilon.
            __MIN_EPSILON (float): Valor mínimo de epsilon.
            __MEMORY_BATCH_SIZE (int): Tamanho do batch de amostragem da memória.
            __TARGET_UPDATE_FREQUENCY (int): A cada quantas iterações as redes são sincronizadas.
            __REPLAY_START (int): Após quantas iterações se inicia o treinamento das redes.
            __MAX_MEMORY_SIZE (int): Tamanho máximo da memória.

        Métodos:

            Todos os métodos desta classe são propriedades estáticas que servem apenas para evitar o acesso direto
            a seus atributos.
    """

    def __init__(self,
                 use_lines_as_switches=True,
                 force_switch_state=False,
                 override_regulator_control=True):

        # OpenDSS configurations
        self.__USE_LINES_AS_SWITCHES = use_lines_as_switches
        self.__FORCE_SWITCH_STATE = force_switch_state
        self.__OVERRIDE_REGULATOR_CONTROL = override_regulator_control

        # Constants
        self.__CONST_DAILY_MINUTES = 1440
        self.__CONST_V_UPPER_LIMIT = 1.05
        self.__CONST_V_LOWER_LIMIT = 0.92
        self.__CONST_V_TARGET = 1

        # Rewards and Penalties
        self.__OUT_OF_LIMITS_PENALTY = -1
        self.__TOWARD_TARGET_REWARD = 0.5
        self.__AWAY_TARGET_PENALTY_OVER = -0.95
        self.__AWAY_TARGET_PENALTY_UNDER = -0.75
        self.__STAND_STILL_REWARD_OUT_OF_TARGET = 0.1
        self.__STAND_STILL_REWARD_ON_TARGET = 0.9
        self.__STAND_STILL_PENALTY = -0.5
        self.__MEANINGLESS_ACTION_PENALTY = -0.8
        self.__ACTION_UNDONE_PENALTY = -1

        # DQL configuration
        self.__DISCOUNT_FACTOR = 0.9
        self.__BASE_LEARNING_RATE = 0.001
        self.__MAX_EPSILON = 1
        self.__MIN_EPSILON = 0.2
        self.__MEMORY_BATCH_SIZE = 512
        self.__TARGET_UPDATE_FREQUENCY = 2048
        self.__REPLAY_START = 512
        self.__MAX_MEMORY_SIZE = 8192

        if self.__REPLAY_START < self.__MEMORY_BATCH_SIZE:
            raise Exception(
                "Replay start must be bigger than or equal batch size!")

    @cached_property
    def stand_still_reward_on_target(self):
        return self.__STAND_STILL_REWARD_ON_TARGET

    @cached_property
    def replay_start(self):
        return self.__REPLAY_START

    @cached_property
    def max_memory_size(self):
        return self.__MAX_MEMORY_SIZE

    @cached_property
    def target_update_frequency(self):
        return self.__TARGET_UPDATE_FREQUENCY

    @cached_property
    def memory_batch_size(self):
        return self.__MEMORY_BATCH_SIZE

    @cached_property
    def use_lines_as_switches(self):
        return self.__USE_LINES_AS_SWITCHES

    @cached_property
    def force_switch_state(self):
        return self.__FORCE_SWITCH_STATE

    @cached_property
    def override_regulator_control(self):
        return self.__OVERRIDE_REGULATOR_CONTROL

    @cached_property
    def daily_minutes(self):
        return self.__CONST_DAILY_MINUTES

    @cached_property
    def upper_voltage_limit(self):
        return self.__CONST_V_UPPER_LIMIT

    @cached_property
    def lower_voltage_limit(self):
        return self.__CONST_V_LOWER_LIMIT

    @cached_property
    def target_voltage(self):
        return self.__CONST_V_TARGET

    @cached_property
    def out_of_limits_penalty(self):
        return self.__OUT_OF_LIMITS_PENALTY

    @cached_property
    def toward_target_reward(self):
        return self.__TOWARD_TARGET_REWARD

    @cached_property
    def away_target_penalty_over(self):
        return self.__AWAY_TARGET_PENALTY_OVER

    @cached_property
    def away_target_penalty_under(self):
        return self.__AWAY_TARGET_PENALTY_UNDER

    @cached_property
    def stand_still_penalty(self):
        return self.__STAND_STILL_PENALTY

    @cached_property
    def stand_still_reward_out_of_target(self):
        return self.__STAND_STILL_REWARD_OUT_OF_TARGET

    @cached_property
    def discount_factor(self):
        return self.__DISCOUNT_FACTOR

    @cached_property
    def epsilon(self):
        return (self.__MIN_EPSILON, self.__MAX_EPSILON)

    @cached_property
    def meaningless_action_penalty(self):
        return self.__MEANINGLESS_ACTION_PENALTY

    @cached_property
    def base_learning_rate(self):
        return self.__BASE_LEARNING_RATE

    @cached_property
    def action_undone_penalty(self):
        return self.__ACTION_UNDONE_PENALTY

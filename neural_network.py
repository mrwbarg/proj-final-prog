"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: neural_network.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""

import tensorflow as tf
import joblib

from os import path
from copy import deepcopy
from sklearn.preprocessing import StandardScaler, MinMaxScaler

from global_configuration import Configuration

# Local onde o arquivo está sendo executado
basepath = path.dirname(__file__)


class Network(object):

    """
        Responsável por criar as redes neurais e atualizar seus pesos durante o processo de treinamento.

        Argumentos:
            input_size (int): Tamanho da camada de entrada da rede neural. Varia com o tamanho do sistema.
            output_size (int): Tamanho da camada de saída da rede neural. Varia com o número de ações disponíveis no sistema.
            model_name (str): Nome do arquivo que está sendo executado, para fins de log.
            optimizer (tf.Optimizers): Otimizador que será utilizado na rede neural.

        Atributos:
            _input_size (int): Tamanho da camada de entrada da rede neural. Varia com o tamanho do sistema.
            _output_size (int): Tamanho da camada de saída da rede neural. Varia com o número de ações disponíveis no sistema.
            _optimizer (tf.optimizers): Nome do arquivo que está sendo executado, para fins de log.
            _loss (list(float)): Lista com as perdas acumuladas da rede. Disponível somente durante o processo de treinamento.
            _config (Configuration): Configurações globais.
            _hidden_layer_1_size (int): Tamanho da primeira camada oculta da rede.
            _hidden_layer_2_size (int): Tamanho da segunda camada oculta da rede.
            _value_layer_1_size (int): Tamanho da camada "value" da rede.
            _advantage_layer_1_size (int): Tamanho da camada "advantage" da rede.
            _cache_file (str): Nome do arquivo de cache dos pesos da rede.
            _scaler_file (str): Nome do arquivo de cache do scaler utilizado.
            _variables (list(tf.Variable)): Variáveis que podem ser otimizadas (pesos e bias).

        Métodos:

            initialize_weight_bias()
                : Inicializa os pesos e os bias da rede.

            load_scaler()
                : Carrega um scaler do disco se houver um arquivo de cache.

            model(inputs)
                : Modelo da rede.

            _dense_layer(x, weights, bias, activation=tf.identity, **activation_kwargs)
                : Modelo de uma camada densa da rede.

            update_weights(inputs, targets, actions)
                : Otimiza os pesos e bias da rede utilizando o otimizador definido.

            update_variables(variables)
                : Sobrescreve as variáveis da rede com novas variáveis.

            get_variables()
                : Obtém uma cópia das variáveis da rede.

            dump_weights()
                : Salva os pesos da rede em disco.

            get_loss()
                : Obtém as perdas cumulativas da rede. Disponível somente durante o treinamento.

            dump_scaler()
                : Salva os dados do scaler em disco.

    """

    def __init__(self, input_size, output_size, model_name, optimizer=tf.optimizers.Adam):
        self._input_size = input_size
        self._output_size = output_size
        self._optimizer = optimizer()
        self._loss = []
        self._config = Configuration()

        self._hidden_layer_1_size = 16
        self._hidden_layer_2_size = 32
        self._value_layer_1_size = 16
        self._advantage_layer_1_size = 16

        self._cache_file = "nn_" + model_name + ".cache"
        self._scaler_file = "scaler_" + model_name + ".cache"

        self._optimizer.learning_rate = self._config.base_learning_rate
        self.initialize_weights_bias()
        self.load_scaler()

    def initialize_weights_bias(self):
        """
            Inicializa os pesos e os bias da rede.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """

        weight_shapes = [
            [self._input_size, self._hidden_layer_1_size],
            [self._hidden_layer_1_size, self._hidden_layer_2_size],
            [self._hidden_layer_2_size, self._value_layer_1_size],
            [self._value_layer_1_size, 1],
            [self._hidden_layer_2_size, self._advantage_layer_1_size],
            [self._advantage_layer_1_size, self._output_size]]

        bias_shapes = [
            [1, self._hidden_layer_1_size],
            [1, self._hidden_layer_2_size],
            [1, self._value_layer_1_size],
            [1, 1],
            [1, self._advantage_layer_1_size],
            [1, self._output_size]]

        if not path.isfile(path.join(basepath, "cache", self._cache_file)):

            self._weights = [tf.Variable(initial_value=tf.initializers.glorot_uniform()(shape), trainable=True, dtype=tf.float32) for shape in weight_shapes]

            self._bias = [tf.Variable(initial_value=tf.initializers.zeros()(shape), trainable=True, dtype=tf.float32) for shape in bias_shapes]

            with open(str(path.join(basepath, "cache", self._cache_file)), 'wb') as nn_cache:
                joblib.dump({"weights": self._weights, "bias": self._bias}, nn_cache)

        else:
            with open(str(path.join(basepath, "cache", self._cache_file)), 'rb') as nn_cache:
                _d = joblib.load(nn_cache)
                self._weights = _d["weights"]
                self._bias = _d["bias"]

        self._variables = self._weights + self._bias

    def __eq__(self, other):
        for w1, w2 in zip(self._weights, other._weights):
            if not (w1.value().numpy() == w2.value().numpy()).all():
                return False
        return True

    def load_scaler(self):
        """
            Carrega um scaler do disco se houver um arquivo de cache. Caso contrário, cria um scaler novo.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        if not path.isfile(path.join(basepath, "cache", self._scaler_file)):
            # self._scaler = StandardScaler()
            self._scaler = MinMaxScaler()

        else:
            with open(str(path.join(basepath, "cache", self._scaler_file)), 'rb') as scaler_cache:
                self._scaler = joblib.load(scaler_cache)

    def model(self, inputs):
        """
            Modelo da rede. A entrada é normalizada utilizando-se o scaler.

            Parâmetros:
                inputs (np.array): Array com as entradas da rede.

            Erros:
                None

            Retorna:
                Resultado da rede.
        """

        inputs = self._scaler.transform(inputs)

        hidden_layer_1 = self._dense_layer(inputs, self._weights[0], self._bias[0], tf.nn.relu)
        hidden_layer_2 = self._dense_layer(hidden_layer_1, self._weights[1], self._bias[1], tf.nn.relu)
        value_layer = self._dense_layer(hidden_layer_2, self._weights[2], self._bias[2], tf.nn.relu)
        value_layer_output = self._dense_layer(value_layer, self._weights[3], self._bias[3], tf.nn.swish)
        advantage_layer = self._dense_layer(hidden_layer_2, self._weights[4], self._bias[4], tf.nn.relu)
        advantage_layer_output = self._dense_layer(advantage_layer, self._weights[5], self._bias[5], tf.nn.swish)
        output = value_layer_output + (advantage_layer_output - tf.math.reduce_mean(advantage_layer_output))

        return output

    def _dense_layer(self, x, weights, bias, activation=tf.identity, **activation_kwargs):
        """
            Modelo de uma camada densa da rede.

            Parâmetros:
                x (np.array): Entrada da camada.
                weights (list(tf.Variable)): Pesos da camada.
                bias (list(tf.Variable)): Bias da camada.
                activation (tf.nn): Função de ativação da camada.
                **activation_kwargs: Argumentos extras nomeados.

            Erros:
                None

            Retorna:
                Camada densa.
        """
        z = tf.matmul(x, weights) + bias
        return activation(z, **activation_kwargs)

    def update_weights(self, inputs, targets, actions):
        """
            Otimiza os pesos e bias da rede utilizando o otimizador definido.
            Gradient Clipping é utilizado conforme recomendação da literatura.

            Parâmetros:
                inputs (np.array): Array com as entradas da rede.
                targets (np.array): Array com alvos para as predições.
                actions (np.array): OneHotEncode das ações para cada entrada.

            Erros:
                None

            Retorna:
                None
        """
        with tf.GradientTape() as tape:
            q_values = tf.squeeze(self.model(inputs))
            predictions = tf.reduce_sum(q_values * actions, axis=1)
            loss = tf.losses.mean_squared_error(targets, predictions)
            self._loss.append(loss)

        gradients = tape.gradient(loss, self._variables)
        gradients = [(tf.clip_by_value(g, -1.0, 1.0)) for g in gradients]
        self._optimizer.apply_gradients(grads_and_vars=zip(gradients, self._variables))

        # self.dump_weights()

    def update_variables(self, variables):
        """
            Sobrescreve as variáveis da rede com novas variáveis.

            Parâmetros:
                variables (list(tf.Variable)): Lista com as novas variáveis.

            Erros:
                None

            Retorna:
                None
        """
        self._variables = variables

    def get_variables(self):
        """
            Obtém uma cópia das variáveis da rede.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com as variáveis.
        """
        return [tf.Variable(t) for t in self._variables]

    def dump_weights(self):
        """
            Salva os pesos da rede em disco.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        with open(str(path.join(basepath, "cache", self._cache_file)), 'wb') as nn_cache:
            joblib.dump({"weights": self._weights, "bias": self._bias}, nn_cache)

    def get_loss(self):
        """
            Obtém as perdas cumulativas da rede. Disponível somente durante o treinamento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com as perdas acumuladas.
        """
        return self._loss

    def dump_scaler(self):
        """
            Salva os dados do scaler em disco.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        with open(str(path.join(basepath, "cache", self._scaler_file)), 'wb') as scaler_cache:
            joblib.dump(self._scaler, scaler_cache)

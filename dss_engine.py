"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: dss_engine.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""

import win32com.client
import sys
import numpy as np
import random
import noise

from typing import List, Type
from win32com.client import makepy
from statistics import mean
from copy import deepcopy
from pathlib import Path
from os import listdir, path


import enums.capacitor_codes as CapacitorCodes
import enums.line_codes as LineCodes
import enums.transformer_codes as TransformerCodes
import enums.generator_codes as GeneratorCodes

from global_configuration import Configuration
from elements import Capacitor, Switch, Line, Transformer, RegulatorControl, Load, Generator, VSource, ISource, Bus
from enums.voltage_evaluation_metrics import Metric
from state import State


class OpenDssEngine(object):
    """
        Responsável por lidar com a conexão e obtenção de dados do OpenDSS,
        o programa de simulação utilizado.

        Argumentos:

            None

        Atributos:

            _config (Configuration): Configurações globais do projeto.
            _engine (COM Object): Lida com a interação com o software.
            _file (str): Caminho do arquivo sendo utilizado.
            _ckt (COM Object): Representa o circuito do modelo simulado. Permite acessar os elementos e funções do OpenDSS.
            _load_profile (dict): Guarda a curva de carga a ser utilizada, discretizada minuto a minuto.
            _capacitors (list(Capacitor)): Capacitores do circuito.
            _switches (list(Switch)): Chaves do circuito.
            _lines (list(Line)): Linhas do circuito.
            _transformers (list(Transformer)): Transformadores do circuito.
            _regulator_controls (list(RegulatorControl)): Controles dos Reguladores do circuito.
            _loads (list(Load)): Cargas presentes no circuito.
            _generators (list(Generator)): Geradores do circuito.
            _vsources (list(VSource)): Fontes de tensão do circuito.
            _isources (list(ISource)): Fontes de corrente do circuito.
            _buses (list(Bus)): Barramentos do circuito.
            _weekday (str): Dia da semana sendo simulado.

        Métodos:

            test_connection()
                : Testa a conexão com o software através do envio de um comando.

            open_file(path)
                : Abre e compila um arquivo '*.dss'.

            kill_session()
                : Elimina a conexão 'COM' com o software.

            load_capacitors()
                : Carrega os capacitores presentes no circuito.

            load_switches()
                : Carrega as chaves presentes no circuito.

            load_lines()
                : Carrega as linhas do circuito.

            load_transformers()
                : Carrega os transformadores do circuito.

            load_generators()
                : Carrega os geradores do circuito.

            load_vsources()
                : Carrega as fontes de tensão do circuito.

            load_isources()
                : Carrega as fontes de corrente do circuito.

            load_regulator_controls()
                : Carrega os controladores dos regulafores do circuito.

            load_loads()
                : Carrega as cargas do circuito.

            load_buses()
                : Carrega os barramentos do circuito.

            get_capacitor_names()
                : Obtém os nomes dos capacitores do circuito.

            get_switch_names()
                : Obtém os nomes das chaves do circuito.

            get_line_names()
                : Obtém os nomes das linhas do circuito.

            get_regulator_control_names()
                : Obtém os nomes dos controladores dos reguladores do circuito.

            get_load_names()
                : Obtém os nomes das cargas do circuito.

            get_generator_names()
                : Obtém o nome dos geradores do circuito.

            get_vsource_names()
                : Obtém o nome das fontes de tensão do circuito.

            get_isource_names()
                : Obtém o nome das fontes do corrente do circuito.

            lines_to_switches()
                : Converte as linhas do circuito para chaves, para que possam ser ligadas e desligadas.

            switch_capacitor(name, step=CapacitorCodes.Action.StepUp)
                : Ativa/desativa o próximo estágio/estágio anterior de um banco de capacitores.

            flip_switch(name, override_force_state=None, open_terminal=LineCodes.TerminalLocation.Both)
                : Altera o estado de uma chave do circuito.

            change_tap(name, step=TransformerCodes.Action.TapUp)
                : Altera o tape de um transformador do circuito.

            change_load_kw(name, kw)
                : Altera a potência real de uma carga do circuito.

            change_generator_power(name, value, power=GeneratorCodes.Power.Active)
                : Altera a potência de um gerador.

            change_vsource_voltage(name, v)
                : Altera a tensão de uma fonte de tensão.

            change_isource_amps(name, a)
                : Altera a corrente de uma fonte de corrente.

            get_possible_actions()
                : Obtém as ações que podem ser tomadas no sistema.

            get_voltages()
                : Obtém a tensão em cada barra do sistema.

            evaluate_voltages(metric=Metric.AVERAGE)
                : Avalia a tensão de acordo com alguma métrica.

            solve()
                : Envia o comando solve para o OpenDSS e atualiza os valores de tensão e potência.

            get_episode_length()
                : Obtém da curva de carga o tamanho de cada episódio do reinforcement learning.

            get_actions_per_step()
                : Obtém quantas ações podem ser tomadas a cada passo do reinforcement learning.

            set_load_profile(folder=PATH)
                : Carrega o perfil de carga.

            get_load_profile()
                : Obtém o perfil de carga carregado.

            update_load_profile(load_profile, weekday=None)
                : Atualiza o perfil de carga atual.

            start()
                : Executa uma série de funções necessárias para iniciar a simulação.

            update_loads(time_step)
                : Atualiza as cargas de acordo com o perfil de carga.

            get_state()
                : Atualiza as cargas de acordo com o perfil de carga.

            set_state(dumped)
                : Define o estado do sistema.

            take_action(args)
                : Executa uma ação no sistema.

            kill_engine()
                : Remove a 'engine' dos elementos.

            restore_engine(engine)
                : Restaura a 'engine' dos elementos.

            get_file_name()
                : Obtém o nome do arquivo do circuito aberto.

            get_weekday()
                : Obtém o nome do dia da semana correspondente ao perfil de carga atual.

    """

    def __init__(self) -> None:

        self._config = Configuration()

        sys.argv = ['makepy', 'OpenDSSEngine.dss']
        makepy.main()
        self._engine = win32com.client.Dispatch('OpenDSSEngine.dss')
        self._engine = win32com.client.gencache.EnsureDispatch(
            "OpenDSSEngine.dss")
        self._engine.Start(0)

        self._file = ''
        self._ckt = None
        self._load_profile = None
        self._weekday = None

        self._capacitors = None
        self._switches = None
        self._lines = None
        self._transformers = None
        self._regulator_controls = None
        self._loads = None
        self._generators = None
        self._vsources = None
        self._isources = None
        self._buses = None

    def test_connection(self) -> None:
        """
            Testa a conexão com o software através do envio de um comando.
            Se não existir um arquivo aberto, gera um erro.

            Parâmetros:
                None

            Erros:
                Excessão caso o envio do comando não seja bem sucedido.
                Excessão caso não haja um arquivo aberto.

            Retorna:
                None
        """

        if self._file and self._ckt:
            try:
                self._ckt.AllBusNames
            except Exception:
                raise Exception(
                    'Erro ao enviar comando! Problema na conexão.')
        else:
            raise Exception('Abra um arquivo para testar a conexão...')

    def open_file(self, path: str) -> None:
        """
            Abre e compila um arquivo '*.dss'.

            Parâmetros:
                path (str): Caminho do arquivo.

            Erros:
                Excessão quando ocorre um erro ao compilar o arquivo.

            Retorna:
                None
        """

        self._file = path
        try:
            self._engine.Text.Command = 'compile ' + self._file
            self._ckt = self._engine.ActiveCircuit
        except Exception:
            raise Exception('Erro ao compilar o arquivo')

    def kill_session(self) -> bool:
        """
            Elimina a conexão 'COM' com o software.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                True

        """

        self._engine = None
        self._ckt = None
        self._file = None

        return True

    def load_capacitors(self) -> None:
        """
            Carrega os capacitores presentes no circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """

        self._capacitors = [Capacitor(name=c, circuit=self._ckt, configuration=self._config)
                            for c in list(self._ckt.Capacitors.AllNames)]
        if (len(self._capacitors) == 1 and self._capacitors[0].get_name() == 'NONE'):
            self._capacitors = None

    def load_switches(self) -> None:
        """
            Carrega as chaves presentes no circuito.
            Caso não haja chaves, caso configurado, transforma todas as linhas em chaves.

            Parâmetros:
                None

            Erros:
                Excessão caso a configuração mande transformar as linhas em chaves mas não haja linhas.

            Retorna:
                None
        """

        self._switches = [Switch(name=s, circuit=self._ckt, configuration=self._config)
                          for s in list(self._ckt.SwtControls.AllNames)]
        if (len(self._switches) == 1 and self._switches[0].get_name() == 'NONE'):

            if self._config.use_lines_as_switches:
                if (len(self._lines) > 0):
                    self.lines_to_switches()
                else:
                    raise Exception(
                        'Nenhuma linha disponível ou linhas não foram carregadas')
            else:
                self._switches = None

    def load_lines(self) -> None:
        """
            Carrega as linhas do circuito.
            Caso não haja linhas, elimina a conexão 'COM' com o software, chamando a função 'kill_session()'.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._lines = [Line(name=l, circuit=self._ckt, configuration=self._config)
                       for l in list(self._ckt.Lines.AllNames)]

        if (len(self._lines) == 1 and self._switches[0].get_name() == 'NONE'):
            self.kill_session()

    def load_transformers(self) -> None:
        """
            Carrega os transformadores do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        if not self._config.override_regulator_control:
            self._transformers = [Transformer(name=t, circuit=self._ckt, configuration=self._config)
                                  for t in list(self._ckt.Transformers.AllNames) if t not in self.get_regulator_control_names()]
        else:
            self._transformers = [Transformer(name=t, circuit=self._ckt, configuration=self._config)
                                  for t in list(self._ckt.Transformers.AllNames)]

        if ((len(self._transformers) == 1 and self._transformers[0].get_name() == 'NONE') or (len(self._transformers) == 0)):
            self._transformers = None

    def load_generators(self) -> None:
        """
            Carrega os geradores do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._generators = [Generator(name=g, circuit=self._ckt, configuration=self._config)
                            for g in list(self._ckt.Generators.AllNames)]

        if ((len(self._generators) == 1 and self._generators[0].get_name() == 'NONE')):
            self._generators = None

    def load_vsources(self) -> None:
        """
            Carrega as fontes de tensão do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._vsources = [VSource(name=v, circuit=self._ckt, configuration=self._config)
                          for v in list(self._ckt.Vsources.AllNames)]

        if ((len(self._vsources) == 1 and self._vsources[0].get_name() == 'NONE')):
            self._vsources = None

    def load_isources(self) -> None:
        """
            Carrega as fontes de corrente do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._isources = [ISource(name=i, circuit=self._ckt, configuration=self._config)
                          for i in list(self._ckt.ISources.AllNames)]

        if ((len(self._isources) == 1 and self._isources[0].get_name() == 'NONE')):
            self._isources = None

    def load_regulator_controls(self) -> None:
        """
            Carrega os controladores dos reguladores do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """

        self._regulator_controls = [RegulatorControl(name=rc, circuit=self._ckt, configuration=self._config)
                                    for rc in list(self._ckt.RegControls.AllNames)]

        if (len(self._regulator_controls) == 1 and self._regulator_controls[0].get_name() == 'NONE'):
            self._regulator_controls = None

    def load_loads(self) -> None:
        """
            Carrega as cargas do circuito.
            Caso não haja cargas, elimina a conexão 'COM' com o software, chamando a função 'kill_session()'.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """

        self._loads = [Load(name=l, circuit=self._ckt, configuration=self._config)
                       for l in list(self._ckt.Loads.AllNames)]

        if (len(self._loads) == 1 and self._loads[0].get_name() == 'NONE'):
            self.kill_session()

    def load_buses(self) -> None:
        """
            Carrega os barramentos do circuito.
            Caso não haja barramentos, elimina a conexão 'COM' com o software, chamando a função 'kill_session()'.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """

        self._buses = [Bus(name=b, circuit=self._ckt, configuration=self._config)
                       for b in list(self._ckt.AllBusNames)]

        if (len(self._buses) == 1 and self._buses[0].get_name() == 'NONE'):
            self.kill_session()

    def get_capacitor_names(self) -> List[Type[Capacitor]]:
        """
            Obtém os nomes dos capacitores do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes dos capacitores.
        """
        return [capacitor.get_name() for capacitor in self._capacitors]

    def get_switch_names(self) -> List[Type[Switch]]:
        """
            Obtém os nomes das chaves do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes das chaves.
        """
        return [switch.get_name() for switch in self._switches]

    def get_line_names(self) -> List[Type[Line]]:
        """
            Obtém os nomes das linhas do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes das linhas.
        """
        return [line.get_name() for line in self._lines]

    def get_transformer_names(self) -> List[Type[Transformer]]:
        """
            Obtém os nomes dos transformadores do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes dos transformadores.
        """
        return [transformer.get_name() for transformer in self._transformers]

    def get_regulator_control_names(self) -> List[Type[RegulatorControl]]:
        """
            Obtém os nomes dos controladores dos reguladores do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes dos reguladores dos controladores.
        """
        return [regulator.get_name() for regulator in self._regulator_controls]

    def get_load_names(self) -> List[Type[Load]]:
        """
            Obtém os nomes das cargas do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes das cargas.
        """
        return [load.get_name() for load in self._loads]

    def get_generator_names(self) -> List[Type[Generator]]:
        """
            Obtém os nomes dos geradores do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes dos geradores.
        """
        return [generator.get_name() for generator in self._generators]

    def get_vsource_names(self) -> List[Type[VSource]]:
        """
            Obtém os nomes das fontes de tensão do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes das fontes de tensão.
        """
        return [vsource.get_name() for vsource in self._vsources]

    def get_isource_names(self) -> List[Type[ISource]]:
        """
            Obtém os nomes das fontes de corrente do circuito.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com os nomes das fontes de corrente.
        """
        return [isource.get_name() for isource in self._isources]

    def lines_to_switches(self) -> None:
        """
            Converte as linhas do circuito para chaves, para que possam ser ligadas e desligadas.
            Substitui as chaves originais do circuito.

            Parâmetros:
                None

            Erros:
                Excessão caso a conversão não esteja habilitada nas configurações.

            Retorna:
                None
        """

        if self._config.use_lines_as_switches:
            self._switches = [line.convert_to_switch() for line in self._lines]

        else:
            raise Exception(
                'Conversão não é permitida. USE_LINES_AS_SWITCHES está desabilitado.')

    def switch_capacitor(self, name, step=CapacitorCodes.Action.StepUp):
        """
            Ativa/desativa o próximo estágio/estágio anterior de um banco de capacitores.

            Parâmetros:
                name (str): Nome do capacitor
                step (CapacitorCodes.Action): StepUp ou StepDown. Ativar/Desativar o próximo estágio.

            Erros:
                Excessão caso o parâmetro 'step' não seja válido.
                Excessão caso o capacitor não exista.

            Retorna:
                None

        """
        capacitor = next(filter(lambda c: c.get_name() == name, self._capacitors), None)
        if capacitor:
            if(step == CapacitorCodes.Action.StepUp):
                return capacitor.switch_step(step)
            elif(step == CapacitorCodes.Action.StepDown):
                return capacitor.switch_step(step)
            else:
                raise Exception(f'Comando inválido <{step}>.')
        else:
            raise Exception(f'Capacitor <{name}> não existe.')

    def flip_switch(self, name, override_force_state=None, open_terminal=LineCodes.TerminalLocation.Both):
        """
            Altera o estado de uma chave do circuito.

            Parâmetros:
                name (str): Nome da chave.
                override_force_state (bool | None): Para as chaves não oriundas de linhas, força a mudança de estado caso a chave esteja travada
                open_terminal (LineCodes.TerminalLocation): Left, Right ou Both. Para as chaves oriundas de linhas, determina qual terminal abrir.

            Erros:
                Excessão caso a chave não exista.

            Retorna:
                None
        """
        switch = next(filter(lambda s: s.get_name() == name, self._switches), None)

        if switch:
            if not switch.get_from_line():
                switch.flip(override_force_state=override_force_state)

            else:
                switch.flip(open_terminal=open_terminal)
        else:
            raise Exception(f'Chave <{name}> não existe.')

    def change_tap(self, name, step=TransformerCodes.Action.TapUp):
        """
            Altera o tape de um transformador do circuito.

            Parâmetros:
                name (str): Nome do transformador.
                step (TransformerCodes.Action): TapUp ou TapDown. Aumenta ou diminui o tape do transformador.

            Erros:
                Excessão caso o transformador não exista.

            Retorna:
                None
        """
        transformer = next(filter(lambda t: t.get_name() == name, self._transformers), None)

        if transformer:
            transformer.change_tap(step)

        else:
            raise Exception(f'Transformador <{name}> não existe.')

    def change_load_kw(self, name, kw):
        """
            Altera a potência real de uma carga do circuito.

            Parâmetros:
                name (str): Nome da carga.
                kw (float): Novo valor da carga.

            Erros:
                Excessão caso a carga não exista.

            Retorna:
                None
        """
        load = next(filter(lambda l: l.get_name() == name, self._loads), None)

        if load:
            load.change_real_power(kw)

        else:
            raise Exception(f'Carga <{name}> não existe.')

    def change_generator_power(self, name, value, power=GeneratorCodes.Power.Active):
        """
            Altera a potência de um gerador.

            Parâmetros:
                name (str): Nome do gerador.
                value (float): Novo valor da potência.
                power (GeneratorCodes.Power): Active ou Reactive. Define se a potência alterada será a ativa ou a reativa.

            Erros:
                Excessão caso o gerador não exista.

            Retorna:
                None
        """
        generator = next(filter(lambda g: g.get_name() == name, self._generators), None)

        if generator:
            if (power == GeneratorCodes.Power.Active):
                generator.change_real_power(value)
            elif (power == GeneratorCodes.Power.Reactive):
                generator.change_reactive_power(value)
            else:
                raise Exception(f'Invalid option: {power}')

        else:
            raise Exception(f'Gerador <{name}> não existe.')

    def change_vsource_voltage(self, name, v):
        """
            Altera a tensão de uma fonte de tensão.

            Parâmetros:
                name (str): Nome da fonte.
                v (float): Novo valor de tensão.

            Erros:
                Excessão caso a fonte não exista.

            Retorna:
                None
        """
        vsource = next(filter(lambda vs: vs.get_name() == name, self._vsources), None)

        if vsource:
            vsource.change_vpu(v)

        else:
            raise Exception(f'VSource <{name}> não existe.')

    def change_isource_amps(self, name, a):
        """
            Altera a corrente de uma fonte de corrente.

            Parâmetros:
                name (str): Nome da fonte.
                a (float): Novo valor de corrente.

            Erros:
                Excessão caso a fonte não exista.

            Retorna:
                None
        """
        isource = next(filter(lambda i: i.get_name() == name, self._isources), None)

        if isource:
            isource.change_amps(a)

        else:
            raise Exception(f'ISource <{name}> does not exist.')

    def get_possible_actions(self):
        """
            Obtém as ações que podem ser tomadas no sistema.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista de ações que podem ser tomadas.
        """
        actions = []
        for capacitor in self._capacitors:
            for action in CapacitorCodes.Action:
                actions.append((self.switch_capacitor.__name__, capacitor.get_name(), action))

        for transformer in self._transformers:
            for action in TransformerCodes.Action:
                actions.append((self.change_tap.__name__, transformer.get_name(), action))

        return actions

    def get_voltages(self):
        """
            Obtém a tensão em cada barra do sistema. 
            Formato: {'bus': 'bus_name', 'voltages: (1.03, 1.03, 1.02)'}

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Lista com entidades no formato: {'bus': 'bus_name', 'voltages: (1.03, 1.03, 1.02)'} para cada barramento.
        """
        self.solve()
        return [bus.get_voltages() for bus in self._buses if len(bus.get_voltages()['voltages']) > 0]

    def evaluate_voltages(self, metric=Metric.AVERAGE):
        """
            Avalia a tensão de acordo com alguma métrica.

            Parâmetros:
                metric (Metric): Métrica que deve ser utilizada na avaliação.

            Erros:
                None

            Retorna:
                Resultado da avaliação.
        """
        self.solve()

        if (metric == Metric.AVERAGE):
            # Calcula a média da tensão de todos os barramentos. A tensão em cada barramento é a média de cada tensão fase-neutro.
            avg_v = []
            for element in self.get_voltages():
                avg_v.append(mean(element['voltages']))

            return mean(avg_v)

    def solve(self):
        """
            Envia o comando solve para o OpenDSS e atualiza os valores de tensão e potência.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
               None
        """
        self._engine.Text.Command = 'solve'

        for bus in self._buses:
            bus.update_state()

        for load in self._loads:
            load.update_state()

    def get_episode_length(self):
        """
            Obtém da curva de carga o tamanho de cada episódio do reinforcement learning.

            Parâmetros:
                None

            Erros:
                Excessão caso não haja um perfil de carga configurado.

            Retorna:
               Número de passos.
        """

        if self._load_profile:
            # return len(self._load_profile)
            return 180
        else:
            raise Exception('Perfil de carga não configurado!')

    def get_actions_per_step(self):
        """
            Obtém quantas ações podem ser tomadas a cada passo do reinforcement learning.
            Este valor é arbitrariamente uma ação por minuto.
            Assim, o valor retornado é o número de minutos em um dia dividido pelo tamanho do perfil de carga.

            Parâmetros:
                None

            Erros:
                Excessão caso não haja um perfil de carga configurado.

            Retorna:
               Número de ações.
        """
        if self._load_profile:
            return int(self._config.daily_minutes / len(self._load_profile))
        else:
            raise Exception('Perfil de carga não configurado!')

    def set_load_profile(self, folder='C:/Users/mauricio.barg/source/repos/drl-vcontrol/utils/load_profiles/real/'):
        """
            Carrega o perfil de carga.
            O formato do arquivo é: id_da_amostra;carga_normalizada. ex. 1;1.0323, 2;1.00 ...
            Os ultimos três caracteres do nome do arquivo devem ser os dias da semana em inglês: MON, TUE, ...
            Existe um processo aleatório que insere distúrbios com uma certa probabilidade, baseado em "Perlin Noise":    

            Parâmetros:
                folder (str): Caminho da pasta onde os arquivos das curvas de carga estão;

            Erros:
                Excessão caso não haja arquivos.

            Retorna:
               None
        """
        load_profiles = [f for f in listdir(folder) if path.isfile(path.join(folder, f))]
        load_profile = path.join(folder, random.choice(load_profiles))
        self._load_profile = {}
        try:
            with open(load_profile, 'r') as load_profile_data:
                for line in load_profile_data:
                    self._load_profile[int(line.strip().split(";")[0])] = float(line.strip().split(";")[1])
        except FileNotFoundError:
            raise Exception('Arquivos não encontrados!')

        self._weekday = Path(load_profile).stem[-3:]

        start = random.uniform(-10, 10)
        end = start + random.uniform(-4, 4)
        step = (end - start) / (len(self._load_profile) * 10)
        current = start
        n = []
        for i in range(len(self._load_profile)):
            n.append(noise.pnoise1(current, octaves=2))
            current += step

        for k in self._load_profile:
            self._load_profile[k] = self._load_profile[k] * (1 + n[k - 1])

    def get_load_profile(self):
        """
            Obtém o perfil de carga carregado.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Perfil de carga atual.

        """
        return self._load_profile

    def update_load_profile(self, load_profile, weekday=None):
        """
            Atualiza o perfil de carga atual.

            Parâmetros:
                load_profile (dict): Novo perfil de carga. Formato: {1: 1.0332, 2: 1.0399, ...}
                weekday (str): Dia da semana correspondente, abreviado em inglês.

            Erros:
                None

            Retorna:
                None
        """
        self._load_profile = deepcopy(load_profile)
        if weekday:
            self._weekday = weekday

    def start(self, tap_changes=False):
        """
            Executa uma série de funções necessárias para iniciar a simulação.

            Parâmetros:
                tap_changes (bool): Habilita ou não o controle automático inerente do circuito.

            Erros:
                None

            Retorna:
                None

        """
        if tap_changes:
            # self.open_file(
            #     'C:/Users/mauricio.barg/source/repos/drl-vcontrol/main/ckts/ieee13/IEEE13Nodeckt_AUTO.dss')
            # self.open_file(
            #     'C:/Users/mauricio.barg/source/repos/drl-vcontrol/main/ckts/ieee34/Run_IEEE34Mod2_AUTO.dss')
            self.open_file(
                'C:/Users/mauricio.barg/source/repos/drl-vcontrol/main/ckts/ieee123/Run_IEEE123Bus_AUTO.dss')
        else:
            # self.open_file(
            #     'C:/Users/mauricio.barg/source/repos/drl-vcontrol/main/ckts/ieee13/IEEE13Nodeckt.dss')
            # self.open_file(
            #     'C:/Users/mauricio.barg/source/repos/drl-vcontrol/main/ckts/ieee34/Run_IEEE34Mod2.dss')
            self.open_file(
                'C:/Users/mauricio.barg/source/repos/drl-vcontrol/main/ckts/ieee123/Run_IEEE123Bus.dss')

        self.test_connection()
        self.load_capacitors()
        self.load_lines()
        self.load_switches()
        self.load_regulator_controls()
        self.load_transformers()
        self.load_loads()
        self.load_generators()
        self.load_isources()
        self.load_vsources()
        self.load_buses()
        self.set_load_profile()
        self.lines_to_switches()
        self.update_loads(1)

    def update_loads(self, time_step):
        """
            Atualiza as cargas de acordo com o perfil de carga.

            Parâmetros:
                time_step (int): O momento da simulação. ex: se estiver minuto a minuto, é o minuto do dia.

            Erros:
                None

            Retorna:
                Estado atual (State).
        """
        for load in self._loads:
            load.change_real_power(
                load.original_kw * self._load_profile[time_step])

        self.solve()

    def get_state(self):
        """
            Obtém o estado atual do sistema.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None

        """
        self.solve()
        state = {
            'capacitors': self._capacitors,
            'lines': self._lines,
            'switches': self._switches,
            'regulator_controls': self._regulator_controls,
            'transformers': self._transformers,
            'loads': self._loads,
            'generators': self._generators,
            'i_sources': self._isources,
            'v_sources': self._vsources,
            'buses': self._buses
        }

        for class_ in state:
            if state[class_]:
                for element in state[class_]:
                    element.set_circuit_to_null()

        dump = deepcopy(State(self))

        for class_ in state:
            if state[class_]:
                for element in state[class_]:
                    element.set_circuit(self._ckt)

        return dump

    def set_state(self, dumped):
        """
            Define o estado do sistema.

            Parâmetros:
                dumped (State): O estado a ser definido.

            Erros:
                None

            Retorna:
                None
        """

        dumped = deepcopy(dumped)

        self._capacitors = dumped._capacitors
        self._switches = dumped._switches
        self._transformers = dumped._transformers
        self._loads = dumped._loads
        self._generators = dumped._generators
        self._isources = dumped._isources
        self._vsources = dumped._vsources

        elements = [self._capacitors, self._switches, self._transformers, self._loads,
                    self._generators, self._vsources, self._isources, self._buses]

        for element in elements:
            if element:
                for equip in element:
                    equip.set_circuit(self._ckt)

        self.solve()

        for element in elements:
            if element:
                for equip in element:
                    equip.update_state()

        self.solve()

    def take_action(self, args):
        """
            Executa uma ação no sistema.

            Parâmetros:
                args (tuple): Formato: ('nome_da_ação', argumento_1, argumento_2, argumento_n, ...)

            Erros:
                None

            Retorna:
                None
        """
        if args:
            getattr(self, args[0])(*args[1:])
        self.solve()

    def kill_engine(self):
        """
            Remove a 'engine' dos elementos.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        elements = [self._capacitors, self._switches, self._transformers, self._loads, self._regulator_controls, self._lines,
                    self._generators, self._vsources, self._isources, self._buses]

        for element in elements:
            if element:
                for equip in element:
                    equip.set_circuit_to_null()
        self._engine = None
        self._ckt = None

    def restore_engine(self, engine):
        """
            Restaura a 'engine' dos elementos.

            Parâmetros:
                engine (COM Object): Engine a ser configurada nos elementos.

            Erros:
                None

            Retorna:
                None
        """
        self._engine = engine
        self._ckt = self._engine.ActiveCircuit

        elements = [self._capacitors, self._switches, self._transformers, self._loads, self._regulator_controls, self._lines,
                    self._generators, self._vsources, self._isources, self._buses]

        for element in elements:
            if element:
                for equip in element:
                    equip.set_circuit(self._ckt)

    def get_file_name(self):
        """
            Obtém o nome do arquivo do circuito aberto.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do arquivo aberto.
        """
        return Path(self._file).stem

    def get_weekday(self):
        """
            Obtém o nome do dia da semana correspondente ao perfil de carga atual, abreviado em inglês.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do dia da semana.
        """
        return self._weekday

"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: elements.py
    Data de Criação: 11/03/2020
    Modificado em: 30/03/2020
"""

from werkzeug.utils import cached_property
from copy import deepcopy
from statistics import mean

import enums.switch_codes as SwitchCodes
import enums.capacitor_codes as CapacitorCodes
import enums.line_codes as LineCodes
import enums.transformer_codes as TransformerCodes

from global_configuration import Configuration


class Capacitor(object):
    """
        Classe que representa o elemento Capacitor no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _states (list): Lista com estados do do banco de capacitores.
            _hassteps (bool): Indica se o capacitor possui estágios disponíveis para serem ligados.
            _config (Configuration): Configurações globais do projeto.

        Métodos:

            _set_states()
                : Define o atributo "_states".

            _set_nsteps()
                : Define o atributo "_hassteps".

            get_name()
                : Obtém o nome do elemento.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

            switch_step(step=CapacitorCodes.Action.StepUp)
                : Liga/desliga o próximo/anterior estágio do capacitor.

            _switch_step_on()
                : Liga o próximo estágio do capacitor.

            _switch_step_off()
                : Desliga o estágio anterior do capacitor.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.
    """

    def __init__(self, name, circuit, configuration) -> None:
        self._name = name
        self._ckt = circuit
        self._states = None
        self._hassteps = None

        if (self._name != 'NONE'):
            if self._ckt:
                self._ckt.Capacitors.Name = self._name
                self._set_states()
                self._set_nsteps()

        self._config = configuration

    def __deepcopy__(self, memo):
        new = Capacitor(self._name, self._ckt, self._config)
        new._states = deepcopy(self._states)
        new._hassteps = deepcopy(self._hassteps)

        return new

    def __iter__(self):
        for attr in [self._name, self._states]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name and self._states == other._states

    def _set_states(self):
        """
            Define o atributo "_states".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._states = self._ckt.Capacitors.States

    def _set_nsteps(self):
        """
            Define o atributo "_hassteps".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._hassteps = self._ckt.Capacitors.AvailableSteps > 0

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Capacitors.Name = self._name
        self._ckt.Capacitors.States = self._states

    def switch_step(self, step=CapacitorCodes.Action.StepUp):
        """
            Liga/desliga o próximo/anterior estágio do capacitor.

            Parâmetros:
                step(CapacitorCodes.Action): Ligar ou desligar o estágio.

            Erros:
                None

            Retorna:
                None
        """
        if (step == CapacitorCodes.Action.StepUp):
            self._switch_step_on()
        elif (step == CapacitorCodes.Action.StepDown):
            self._switch_step_off()

    def _switch_step_on(self):
        """
            Liga o próximo estágio do capacitor.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                True em caso de sucesso, False caso contrário.
        """
        if self._hassteps:
            self._ckt.Capacitors.Name = self._name
            if self._ckt.Capacitors.AddStep():
                self._set_nsteps()
                self._set_states()

                return True
            else:
                return False
        else:
            return False

    def _switch_step_off(self):
        """
            Desliga o estágio anterior do capacitor.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                True em caso de sucesso, False caso contrário.
        """
        self._ckt.Capacitors.Name = self._name
        availableSteps = self._ckt.Capacitors.AvailableSteps
        totalSteps = self._ckt.Capacitors.NumSteps
        if (availableSteps != totalSteps):
            self._ckt.Capacitors.SubtractStep()
            self._set_nsteps()
            self._set_states()
            return True
        else:
            return False

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """

        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class Switch(object):
    """
        Classe que representa o elemento Switch no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.
            from_line (bool): Indica se a chave é um elemento chave ou se vem de uma linha.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.
            _from_line (bool): Indica se a chave é um elemento chave ou se vem de uma linha.
            _state (SwitchCodes.State): Indica o estado da chave.

        Métodos:

            _set_state()
                : Define o estado da chave.

            get_name()
                : Obtém o nome do elemento.

            get_state()
                : Obtém o estado da chave.

            get_from_line()
                : Obtém o atributo "_from_line.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

            _flip_switch_control(override_force_state=None)
                : Altera o estado de uma chave que não vem de uma linha.

            _flip_line_switch(open_terminal=LineCodes.TerminalLocation.Both)
                : Altera o estado de uma chave que vem de uma linha.

            flip(override_force_state=None, open_terminal=LineCodes.TerminalLocation.Both)
                : Altera o estado da chave.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.
    """

    def __init__(self, name, circuit, configuration, from_line=False) -> None:
        self._name = name
        self._ckt = circuit
        self._from_line = from_line
        self._state = None

        if (self._name != 'NONE'):
            if not self._from_line:
                self._ckt.SwtControls.Name = self._name
                self._set_state()
            else:
                self._state = SwitchCodes.State.Closed

        self._config = configuration

    def __iter__(self):
        for attr in [self._name, self._state]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name and self._state == other._state

    def _set_state(self, current_or_future='current'):
        """
            Define o estado da chave.

            Parâmetros:
                current_or_future (string): Obtém o estado atual ou o estado futuro programado por uma ação.

            Erros:
                Erro caso o parâmetro current_or_future seja diferente de "current" ou "future".

            Retorna:
                None
        """
        if (current_or_future == 'current'):
            self._state = SwitchCodes.State(self._ckt.SwtControls.State)
        elif (current_or_future == 'future'):
            if (self._ckt.SwtControls.Action == SwitchCodes.Action.Close.value or self._ckt.SwtControls.Action == SwitchCodes.Action.Open.value):
                self._state = SwitchCodes.State(self._ckt.SwtControls.Action)
            elif (self._ckt.SwtControls.Action == SwitchCodes.Action.Reset.value):
                self._state = SwitchCodes.State.Closed

        else:
            raise Exception(f'Invalid option: <{current_or_future}>')

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def get_state(self):
        """
            Obtém o estado da chave.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Estado da chave.
        """
        return self._state

    def get_from_line(self):
        """
            Obtém o atributo "_from_line.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Atributo "_from_line".
        """
        return self._from_line

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        if not self._from_line:
            self._ckt.SwtControls.Name = self._name
            self._ckt.SwtControls.State = self._state.value
        else:
            if (self._state == SwitchCodes.State.Closed):
                self._ckt.CktElements(f'Line.{self._name}').Close(1, 0)
                self._ckt.CktElements(f'Line.{self._name}').Close(2, 0)
            elif(self._state == SwitchCodes.State.Closed):
                self._ckt.CktElements(f'Line.{self._name}').Open(1, 0)
                self._ckt.CktElements(f'Line.{self._name}').Open(2, 0)

    def _flip_switch_control(self, override_force_state=None):
        """
            Altera o estado de uma chave que não vem de uma linha.

            Parâmetros:
                override_force_state (bool | None): Indica se o estado da chave deve ser forçado caso esteja travada.

            Erros:
                None

            Retorna:
                Estado da chave.
        """
        self._ckt.SwtControls.Name = self._name
        current_state = self._ckt.SwtControls.State

        if (self._ckt.SwtControls.IsLocked):
            if (self._config.force_switch_state() or override_force_state):
                if (current_state == SwitchCodes.State.Open.value):
                    self._ckt.SwtControls.State = SwitchCodes.State.Closed.value
                    self._set_state()
                    return SwitchCodes.State.Closed.value

                elif (current_state == SwitchCodes.State.Closed.value):
                    self._ckt.SwtControls.State = SwitchCodes.State.Open.value
                    self._set_state()
                    return SwitchStateActionCodes.Open.value
            else:
                return current_state

        if (current_state == SwitchCodes.State.Open.value):
            if (self._config.force_switch_state() or override_force_state):
                self._ckt.SwtControls.State = SwitchCodes.State.Closed.value
                self._set_state()

            else:
                self._ckt.SwtControls.Action = SwitchCodes.Action.Close.value
                self._set_state('future')

            return SwitchCodes.State.Closed.value

        elif (current_state == SwitchCodes.State.Closed.value):
            if (self._config.force_switch_state() or override_force_state):
                self._ckt.SwtControls.State = SwitchCodes.State.Open.value
                self._set_state()

            else:
                self._ckt.SwtControls.Action = SwitchCodes.Action.Open.value
                self._set_state('future')

            return SwitchCodes.State.Open.value

        else:
            return current_state

    def _flip_line_switch(self, open_terminal=LineCodes.TerminalLocation.Both):
        """
            Altera o estado de uma chave que vem de uma linha.

            Parâmetros:
                open_terminal (LineCodes.TerminalLocation): Indica qual terminal da linha deve ser aberto.

            Erros:
                Erro caso o parâmetro "open_terminal" possua um valor inválido.

            Retorna:
                Estado da chave.
        """
        if (self._state == SwitchCodes.State.Closed):
            if (open_terminal == LineCodes.TerminalLocation.Both):
                self._ckt.CktElements(f'Line.{self._name}').Open(1, 0)
                self._ckt.CktElements(f'Line.{self._name}').Open(2, 0)
                self._state = SwitchCodes.State.Open
            elif(open_terminal == LineCodes.TerminalLocation.Start):
                self._ckt.CktElements(f'Line.{self._name}').Open(1, 0)
                self._state = SwitchCodes.State.Open
            elif(open_terminal == LineCodes.TerminalLocation.End):
                self._ckt.CktElements(f'Line.{self._name}').Open(2, 0)
                self._state = SwitchCodes.State.Open
            else:
                raise Exception(f'Invalid option: <{open_terminal}>')

        elif (self._state == SwitchCodes.State.Open):
            self._ckt.CktElements(f'Line.{self._name}').Close(1, 0)
            self._ckt.CktElements(f'Line.{self._name}').Close(2, 0)
            self._state = SwitchCodes.State.Closed

        return self._state

    def flip(self, override_force_state=None, open_terminal=LineCodes.TerminalLocation.Both):
        """
            Altera o estado da chave.

            Parâmetros:
                override_force_state (bool | None): Indica se o estado da chave deve ser forçado caso esteja travada.
                open_terminal (LineCodes.TerminalLocation): Indica qual terminal da linha deve ser aberto.

            Erros:
                None

            Retorna:
                Chamada do método correspondente ao tipo da chave.
        """

        if not self._from_line:
            return self._flip_switch_control(override_force_state)
        else:
            return self._flip_line_switch(open_terminal)

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class Line(object):
    """
        Classe que representa o elemento Line no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            convert_to_switch()
                : Transforma a linha em uma chave para que possa ser aberta ou fechada.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit

        self._config = configuration

    def __iter__(self):
        for attr in [self._name]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def convert_to_switch(self):
        """
            Transforma a linha em uma chave para que possa ser aberta ou fechada.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Chave correspondente.
        """
        return Switch(name=self._name, circuit=self._ckt, from_line=True, configuration=self._config)

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class Transformer(object):
    """
        Classe que representa o elemento Transformer no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.
            _min_tap (float): Menor tape possível no transformador.
            _max_tap (float): Maior tape possível no transformador.
            _num_taps (int): Número total de tapes.
            _tap (int): Tape atual do transformador.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

            _set_tap()
                : Define o atributo "_tap".

            _set_num_taps()
                : Define o atributo "_num_taps".

            _set_max_tap()
                : Define o atributo "_min_tap".

            _set_min_tap()
                : Define o atributo "_min_tap".

            _tap_step_up()
                : Aumenta um tape do transformador.

            _tap_step_down()
                : Reduz um tape do transformador.

            change_tap()
                : Altera o tape do transformador.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit
        self._min_tap = None
        self._max_tap = None
        self._num_taps = None
        self._tap = None

        if (self._name != 'NONE'):
            self._ckt.Transformers.Name = self._name
            self._set_max_tap()
            self._set_min_tap()
            self._set_num_taps()
            self._set_tap()

        self._step_size = round(
            ((self._max_tap - self._min_tap) / self._num_taps), 10)

        self._config = configuration

    def __iter__(self):
        for attr in [self._name, self._tap]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name and self._tap == other._tap

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Transformers.Name = self._name
        self._ckt.Transformers.Tap = self._tap

    def _set_tap(self):
        """
            Define o atributo "_tap".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._tap = self._ckt.Transformers.Tap

    def _set_num_taps(self):
        """
            Define o atributo "_num_taps".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._num_taps = int(self._ckt.Transformers.NumTaps)

    def _set_max_tap(self):
        """
            Define o atributo "_max_tap".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._max_tap = self._ckt.Transformers.MaxTap

    def _set_min_tap(self):
        """
            Define o atributo "_min_tap".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._min_tap = self._ckt.Transformers.MinTap

    def _tap_step_up(self):
        """
            Aumenta um tape do transformador.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Tape atual.
        """
        if (self._tap < self._max_tap):
            self._ckt.Transformers.Name = self._name
            self._ckt.Transformers.Tap += float(self._step_size)
            self._set_tap()

        return self._tap

    def _tap_step_down(self):
        """
            Reduz um tape do transformador.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Tape atual.
        """
        if (self._tap > self._min_tap):
            self._ckt.Transformers.Name = self._name
            self._ckt.Transformers.Tap -= float(self._step_size)
            self._set_tap()

        return self._tap

    def change_tap(self, step=TransformerCodes.Action.TapUp):
        """
            Altera o tape do transformador.

            Parâmetros:
                step (TransformerCodes.Action): Indica se o tape será aumentado ou reduzido.

            Erros:
                Erro caso a opção "step" seja inválida.

            Retorna:
                Chamada da função correspondente a ação.
        """

        if (step == TransformerCodes.Action.TapUp):
            return self._tap_step_up()
        elif (step == TransformerCodes.Action.TapDown):
            return self._tap_step_down()
        else:
            raise Exception(f'Invalid option: {step}')

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class RegulatorControl(object):
    """
        Classe que representa o elemento RegulatorControl no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit

        self._config = configuration

    def __iter__(self):
        for attr in [self._name]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class Load(object):
    """
        Classe que representa o elemento Load no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.
            _kw (float): Potência ativa da carga.
            _original_kw (float): Potência ativa inicial da carga.
            _kvar (float): Potência reativa da carga.
            _pf (float): Fator de potência da carga.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

            original_kw()
                : Obtém o parâmetro "original_kw".

            _set_kw()
                : Define o parâmetro "_kw".

            _set_kvar()
                : Define o parâmetro "_kvar".

            _set_pf()
                : Define o parâmetro "_pf".

            _set_original_kw()
                : Define o parâmetro "_original_kw".

            _update_load_params()
                : Atualiza os parâmetros da carga.

            change_real_power(kw)
                : Altera a potência ativa da carga.

            change_power_factor(pf)
                : Altera o fator de potência da carga.

            change_reactive_power(kvar)
                : Altera a potência reativa da carga.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit
        self._kw = None
        self._original_kw = None
        self._kvar = None
        self._pf = None

        if (self._name != 'NONE'):
            self._ckt.Loads.Name = self._name
            self._set_kw()
            self._set_original_kw()
            self._set_kvar()
            self._set_pf()

        self._config = configuration

    def __iter__(self):
        for attr in [self._name, self._kw]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return (self._name == other._name and self._kw == other._kw)

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Loads.Name = self._name
        self._ckt.Loads.kW = self._kw
        self._ckt.Loads.PF = self._pf
        self._ckt.Loads.kvar = self._kvar

    @cached_property
    def original_kw(self):
        """
            Obtém o parâmetro "original_kw".
            Propriedade cacheada já que valor não é alterado ao longo da execução.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Parâmetro "original_kw"
        """
        return self._original_kw

    def _set_kw(self):
        """
            Define o parâmetro "_kw".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._kw = self._ckt.Loads.kW

    def _set_kvar(self):
        """
            Define o parâmetro "_kvar".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._kvar = self._ckt.Loads.kvar

    def _set_pf(self):
        """
            Define o parâmetro "_pf".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._pf = self._ckt.Loads.PF

    def _set_original_kw(self):
        """
            Define o parâmetro "_original_kw".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._original_kw = self._ckt.Loads.kW

    def _update_load_params(self):
        """
            Atualiza os parâmetros da carga.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._set_kw()
        self._set_kvar()
        self._set_pf()

    def change_real_power(self, kw):
        """
            Altera a potência ativa da carga.

            Parâmetros:
                kw (float): Novo valor de potência.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Loads.Name = self._name
        self._ckt.Loads.kW = kw
        self._update_load_params()

    def change_power_factor(self, pf):
        """
            Altera o fator de potência da carga.

            Parâmetros:
                pf (float): Novo valor de fator de potência.

            Erros:
                None

            Retorna:
                None
        """
        if (-1 <= pf <= 1):
            self._ckt.Loads.Name = self._name
            self._ckt.Loads.PF = pf
            self._update_load_params()

    def change_reactive_power(self, kvar):
        """
            Altera a potência reativa da carga.

            Parâmetros:
                kvar (float): Novo valor de potência reativa.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Loads.Name = self._name
        self._ckt.Loads.kvar = kvar
        self._update_load_params()

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class Generator(object):
    """
        Classe que representa o elemento Generator no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.
            _kw (float): Potência ativa do gerador.
            _kvar (float): Potência reativa do gerador.
            _pf (float): Fator de potência do gerador.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

            original_kw()
                : Obtém o parâmetro "original_kw".

            _set_kw()
                : Define o parâmetro "_kw".

            _set_kvar()
                : Define o parâmetro "_kvar".

            _set_pf()
                : Define o parâmetro "_pf".

            _update_generator_params()
                : Atualiza os parâmetros do gerador.

            change_real_power(kw)
                : Altera a potência ativa do gerador.

            change_power_factor(pf)
                : Altera o fator de potência do gerador.

            change_reactive_power(kvar)
                : Altera a potência reativa do gerador.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit
        self._kw = None
        self._kvar = None
        self._pf = None

        if (self._name != 'NONE'):
            self._ckt.Generators.Name = self._name
            self._set_kw()
            self._set_kvar()
            self._set_pf()

        self._config = configuration

    def __iter__(self):
        for attr in [self._name, self._kw, self._kvar, self._pf]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name and self._kw == other._kw and self._kvar == other._kvar and self._pf == other._pf

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Generators.Name = self._name
        self._ckt.Generators.kW = self._kw
        self._ckt.Generators.PF = self._pf
        self._ckt.Generators.kvar = self._kvar

    def _set_kw(self):
        """
            Define o parâmetro "_kw".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._kw = self._ckt.Generators.kW

    def _set_kvar(self):
        """
            Define o parâmetro "_kvar".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._kvar = self._ckt.Generators.kvar

    def _set_pf(self):
        """
            Define o parâmetro "_pf".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._pf = self._ckt.Generators.PF

    def _update_generator_params(self):
        """
            Atualiza os parâmetros do gerador.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._set_kw()
        self._set_kvar()
        self._set_pf()

    def change_real_power(self, kw):
        """
            Altera a potência ativa do gerador.

            Parâmetros:
                kw (float): Novo valor de potência.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Generators.Name = self._name
        self._ckt.Generators.kW = kw
        self._update_generator_params()

    def change_power_factor(self, pf):
        """
            Altera o fator de potência do gerador.

            Parâmetros:
                pf (float): Novo fator de potência.

            Erros:
                None

            Retorna:
                None
        """
        if (-1 <= pf <= 1):
            self._ckt.Generators.Name = self._name
            self._ckt.Generators.PF = pf
            self._update_generator_params()

    def change_reactive_power(self, kvar):
        """
            Altera a potência reativa do gerador.

            Parâmetros:
                kvar (float): Novo valor de potência.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Generators.Name = self._name
        self._ckt.Generators.kvar = kvar
        self._update_generator_params()

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class VSource(object):
    """
        Classe que representa o elemento VSource no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.
            _vpu (float): Tensão em p.u. da fonte.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

            _set_vpu()
                : Define o parâmetro "_vpu".

            _change_vpu()
                : Altera a tensão da fonte.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit
        self._vpu = None

        if (self._name != 'NONE'):
            self._ckt.Vsources.Name = self._name
            self._set_vpu()

        self._config = configuration

    def __iter__(self):
        for attr in [self._name, self._vpu]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name and self._vpu == other._vpu

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Vsources.Name = self._name
        self._ckt.Vsources.pu = self._vpu

    def _set_vpu(self):
        """
            Define o parâmetro "_vpu".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._vpu = self._ckt.Vsources.pu

    def change_vpu(self, v):
        """
            Altera a tensão da fonte.

            Parâmetros:
                v (float): Novo valor de tensão.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.Vsources.Name = self._name
        self._ckt.Vsources.pu = v
        self._set_vpu()

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class ISource(object):
    """
        Classe que representa o elemento ISource no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.
            _amps (float): Corrente da fonte.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

            _set_amps()
                : Define o parâmetro "_amps".

            _change_amps()
                : Altera a corrente da fonte.

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit
        self._amps = None

        if (self._name != 'NONE'):
            self._ckt.ISources.Name = self._name
            self._set_amps()

        self._config = configuration

    def __iter__(self):
        for attr in [self._name, self._amps]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name and self._amps == other._amps

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.ISources.Name = self._name
        self._ckt.ISources.Amps = self._amps

    def _set_amps(self):
        """
            Define o parâmetro "_amps".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._amps = self._ckt.ISources.Amps

    def change_amps(self, a):
        """
            Altera a corrente da fonte.

            Parâmetros:
                a (float): Novo valor de corrente.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.ISources.Name = self._name
        self._ckt.ISources.Amps = a

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit


class Bus(object):
    """
        Classe que representa o elemento Bus no OpenDSS.

        Argumentos:
            name (string): Nome do elemento.
            configuration (Configuration): Configurações globais do projeto.
            circuit (COM Object): Circuito no qual o elemento está inserido.

        Atributos:
            _name (string): Nome do elemento.
            _ckt (COM Object): Circuito no qual o elemento está inserido.
            _config (Configuration): Configurações globais do projeto.
            _vpu (float): Tensão em p.u. no barramento.

        Métodos:

            get_name()
                : Obtém o nome do elemento.

            get_voltages()
                : Obtém a tensão atual no barramento.

            _set_vpu()
                : Define o parâmetro "_vpu".

            set_circuit_to_null()
                : Remove o atributo "_circuit" do elemento.

            set_circuit(circuit)
                : Define o atributo "_circuit" do elemento.

            update_state()
                : Atualiza o estado do elemento no OpenDSS.

    """

    def __init__(self, name, circuit, configuration):
        self._name = name
        self._ckt = circuit
        self._vpu = None

        if (self._name != 'NONE'):
            self._ckt.SetActiveBus(self._name)
            self._set_vpu()

    def __iter__(self):
        for attr in [self._name, self._vpu]:
            yield attr

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        return self._name == other._name and round(mean(self._vpu), 3) == round(mean(other._vpu), 3)

    def get_name(self):
        """
            Obtém o nome do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                Nome do elemento.
        """
        return self._name

    def get_voltages(self):
        """
            Obtém a tensão atual no barramento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._set_vpu()
        return {'bus': self._name, 'voltages': self._vpu}

    def _set_vpu(self):
        """
            Define o parâmetro "_vpu".

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt.SetActiveBus(self._name)
        bus = self._ckt.ActiveBus
        self._vpu = tuple(bus.puVmagAngle[0:6:2])

    def set_circuit_to_null(self):
        """
            Remove o atributo "_circuit" do elemento.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = None

    def set_circuit(self, circuit):
        """
            Define o atributo "_circuit" do elemento.

            Parâmetros:
                circuit (COM Object): Circuito a ser definido para o elemento.

            Erros:
                None

            Retorna:
                None
        """
        self._ckt = circuit

    def update_state(self):
        """
            Atualiza o estado do elemento no OpenDSS.

            Parâmetros:
                None

            Erros:
                None

            Retorna:
                None
        """
        self._set_vpu()

"""
    Autor: Mauricio R. W. Barg
    Nome do Arquivo: state.py
    Data de Criação: 11/03/2020
    Modificado em: 03/04/2020
"""

from copy import deepcopy
from statistics import mean


class State(object):
    """
        Classe responsável por representar o estado do sistema simulado no OpenDSS.

        Argumentos:
            model (OpenDssEngine): A instância do modelo a ter o estado representado.

        Atributos:
            _capacitors (tuple(Capacitor)): Armazena os capacitores do modelo.
            _switches (tuple(Switch)): Armazena as chaves do modelo.
            _transformers (tuple(Transformer)): Armazena os transformadores do modelo.
            _loads (tuple(Load)): Armazena as cargas do modelo.
            _generators (tuple(Generator)): Armazena os geradores do modelo.
            _isources (tuple(ISource)): Armazena as fontes de corrente do modelo.
            _vsources (tuple(VSource)): Armazena as fontes de tensão do modelo.
            _buses (tuple(Bus)): Armazena os barramentos do modelo.
            _elements (list): Armazena os elementos citados acima.

        Métodos:

            state_space_repr()
                : Retorna uma representação de estado simplificada, usando somente tipos nativos para ser utilizada na entrada da rede neural.


    """

    def __init__(self, model=None):
        if model:
            self._capacitors = tuple(deepcopy(model._capacitors)) if model._capacitors else model._capacitors
            self._switches = tuple(deepcopy(model._switches)) if model._switches else model._switches
            self._transformers = tuple(deepcopy(model._transformers)) if model._transformers else model._transformers
            self._loads = tuple(deepcopy(model._loads)) if model._loads else model._loads
            self._generators = tuple(deepcopy(model._generators)) if model._generators else model._generators
            self._isources = tuple(deepcopy(model._isources)) if model._isources else model._isources
            self._vsources = tuple(deepcopy(model._vsources)) if model._vsources else model._vsources
            self._buses = tuple(deepcopy(model._buses)) if model._buses else model._buses  # A tensão nos barramentos não necessariamente representa o estado

            self._elements = [self._capacitors, self._switches, self._transformers, self._loads, self._generators, self._vsources, self._isources, self._buses]

            model = None

    def __deepcopy__(self, memo):
        """
            Override da função interna.
        """
        new = State()
        new._capacitors = deepcopy(self._capacitors)
        new._switches = deepcopy(self._switches)
        new._transformers = deepcopy(self._transformers)
        new._loads = deepcopy(self._loads)
        new._generators = deepcopy(self._generators)
        new._isources = deepcopy(self._isources)
        new._vsources = deepcopy(self._vsources)
        new._elements = deepcopy(self._elements)
        new._buses = deepcopy(self._buses)  # A tensão nos barramentos não necessariamente representa o estado

        return new

    def __iter__(self):
        """
            Override da função interna.
        """
        for attr in self._elements:
            yield attr

    def __hash__(self):
        """
            Override da função interna.
        """
        return hash(tuple(self))

    def __ne__(self, other):
        """
            Override da função interna.
        """
        return not self.__eq__(other)

    def __eq__(self, other):
        """
            Override da função interna.
        """
        if self._capacitors:
            for e in self._capacitors:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._capacitors), None)

                if e == other_e:
                    continue
                else:
                    return False

        elif other._capacitors:
            return False

        if self._switches:
            for e in self._switches:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._switches), None)
                if e == other_e:
                    continue
                else:
                    return False

        elif other._switches:
            return False

        if self._transformers:
            for e in self._transformers:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._transformers), None)
                if e == other_e:
                    continue
                else:
                    return False

        elif other._transformers:
            return False

        if self._loads:
            for e in self._loads:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._loads), None)
                if e == other_e:
                    continue
                else:
                    return False

        elif other._loads:
            return False

        if self._generators:
            for e in self._generators:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._generators), None)
                if e == other_e:
                    continue
                else:
                    return False

        elif other._generators:
            return False

        if self._isources:
            for e in self._isources:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._isources), None)
                if e == other_e:
                    continue
                else:
                    return False

        elif other._isources:
            return False

        if self._vsources:
            for e in self._vsources:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._vsources), None)
                if e == other_e:
                    continue
                else:
                    return False

        elif other._vsources:
            return False

        # A tensão nos barramentos não necessariamente representa o estado
        if self._buses:
            for e in self._buses:
                other_e = next(filter(lambda other_e: other_e.get_name() == e.get_name(), other._buses), None)
                if e == other_e:
                    continue
                else:
                    return False

        elif other._buses:
            return False

        return True

    def state_space_repr(self, current_step, actions_taken, weekday):
        """
            Retorna uma representação de estado simplificada,
            usando somente tipos nativos para ser utilizada na entrada da rede neural.

            Parâmetros:
                current_step (int): Etapa corrente da simulação (ex.: minuto do dia).
                actions_taken (int): Número de ações tomadas na etapa atual.
                weekday (int): Dia da semana. Número de 1 a 7, de acordo com o mapa:
                    {'MON': 1, 'TUE': 2, 'WED': 3, 'THU': 4, 'FRI': 5, 'SAT': 6, 'SUN': 7}

            Erros:
                None

            Retorna:
                Representação do estado em formato de lista, com tipos nativos.
        """

        representation = [current_step, actions_taken, weekday]

        if self._capacitors:
            for capacitor in self._capacitors:
                representation.append(sum(capacitor._states))

        #  Caso o estado das chaves não mude, o resultado é melhor se não forem incluidas na representação.
        # if self._switches:
        #     for switch in self._switches:
        #         representation.append(switch._state.value)

        if self._transformers:
            for transformer in self._transformers:
                representation.append(transformer._tap)

        if self._loads:
            total_kw = 0
            total_kvar = 0
            for load in self._loads:
                total_kw += load._kw
                total_kvar += load._kvar

            representation.append(total_kw)
            representation.append(total_kvar)

        if self._generators:
            for generator in self._generators:
                representation += [generator._kw, generator._kvar]

        if self._vsources:
            for vsource in self._vsources:
                representation.append(vsource._vpu)

        if self._isources:
            for isource in self._isources:
                representation.append(isource._amps)

        # A tensão não necessariamente representa o estado
        # if self._buses:
        #     for bus in self._buses:
        #         if len(bus._vpu) > 0:
        #             representation.append(mean(bus._vpu))
        #         else:
        #             representation.append(0)

        return representation

import datetime
from schema import Or
from experta import Fact, Field


class Paciente(Fact):
    """Fato que representa o paciente."""
    data_nascimento = Field(datetime.date, mandatory=True)

class Idade(Fact):
    """
    Fato com a idade calculada do paciente.
    Inclui data_nascimento para regras de agendamento futuro baseadas em idade.
    """
    anos = Field(int, mandatory=True)
    meses = Field(int, mandatory=True)
    dias = Field(int, mandatory=True)
    data_nascimento = Field(datetime.date, mandatory=True)

class DoseAplicada(Fact):
    """Fato que representa uma dose de vacina já administrada."""
    vacina_codigo = Field(str, mandatory=True)
    data_aplicacao = Field(datetime.date, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)

class RecomendacaoImediata(Fact):
    """Resultado: O paciente deve tomar esta vacina agora."""
    vacina = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)
    explicacao = Field(str, mandatory=True)

class AgendamentoFuturo(Fact):
    """Resultado: O paciente deve agendar esta vacina para o futuro."""
    vacina = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)
    data_minima = Field(datetime.date, mandatory=True)
    data_recomendada = Field(datetime.date, mandatory=True)
    explicacao = Field(str, mandatory=True)

class Contraindicacao(Fact):
    """Resultado: O paciente não pode tomar esta vacina."""
    vacina = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=False)
    motivo = Field(str, mandatory=True)
    explicacao = Field(str, mandatory=True)

class EsquemaCompleto(Fact):
    """Resultado: O esquema desta vacina está em dia."""
    vacina = Field(str, mandatory=True)
    explicacao = Field(str, mandatory=True)
    data_ultima_dose = Field(datetime.date, mandatory=False)

class ConflitoResolvido(Fact):
    """
    Fato interno para gerenciar a lógica de priorização
    (ex: SCR vs Febre Amarela).
    """
    vacinas = Field([str], mandatory=True)
import datetime
from schema import Or
from experta import Fact, Field


class Paciente(Fact):
    """Input fact representing the patient."""
    data_nascimento = Field(datetime.date, mandatory=True)

class Idade(Fact):
    """
    Input fact with the patient's computed age.
    Includes data_nascimento so future-scheduling rules can anchor dates to birth date.
    Note: `meses` stores total months (years * 12 + remaining months), not remainder alone.
    """
    anos = Field(int, mandatory=True)
    meses = Field(int, mandatory=True)
    dias = Field(int, mandatory=True)
    data_nascimento = Field(datetime.date, mandatory=True)

class DoseAplicada(Fact):
    """Input fact representing a previously administered vaccine dose."""
    vacina_codigo = Field(str, mandatory=True)
    data_aplicacao = Field(datetime.date, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)

class RecomendacaoImediata(Fact):
    """Output fact: the patient should receive this vaccine today."""
    vacina = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)
    explicacao = Field(str, mandatory=True)

class AgendamentoFuturo(Fact):
    """Output fact: the patient should schedule this vaccine for a future date."""
    vacina = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=True)
    data_minima = Field(datetime.date, mandatory=True)
    data_recomendada = Field(datetime.date, mandatory=True)
    explicacao = Field(str, mandatory=True)

class Contraindicacao(Fact):
    """Output fact: this vaccine is contraindicated for the patient."""
    vacina = Field(str, mandatory=True)
    dose = Field(Or(str, int), mandatory=False)
    motivo = Field(str, mandatory=True)
    explicacao = Field(str, mandatory=True)

class EsquemaCompleto(Fact):
    """Output fact: the vaccination schedule for this vaccine is complete/up to date."""
    vacina = Field(str, mandatory=True)
    explicacao = Field(str, mandatory=True)
    data_ultima_dose = Field(datetime.date, mandatory=False)

class ConflitoResolvido(Fact):
    """Internal fact used to track resolved live-virus conflicts (e.g. SCR vs Febre Amarela)."""
    vacinas = Field([str], mandatory=True)

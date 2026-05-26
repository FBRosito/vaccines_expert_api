import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

def to_date(d):
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RegrasDengue(_RegrasBase):
    """
    Rules for the Dengue vaccine - Qdenga (attenuated tetravalent DNG) - PNI / IN 2026.
    Target population: Adolescents aged 10 to 14 years, 11 months and 29 days.
    Schedule: 2 doses with a 90-day (3-month) interval.
    SIPNI code: 104.
    """

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 10),
        NOT(DoseAplicada(vacina_codigo='DENGUE'))
    )
    def rule_dengue_dose_1_schedule(self, dn):
        data_alvo = to_date(dn) + relativedelta(years=10)
        self.declare(AgendamentoFuturo(
            vacina="Dengue",
            dose=1,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao=(
                "Agendamento da 1ª dose da vacina Dengue (Qdenga), "
                "indicada a partir dos 10 anos de idade."
            )
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 10 and a < 15),
        NOT(DoseAplicada(vacina_codigo='DENGUE', dose=1)),
        NOT(DoseAplicada(vacina_codigo='DENGUE', dose=2))
    )
    def rule_dengue_dose_1_recommend(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Dengue",
            dose=1,
            explicacao=(
                f"Adolescente com {a} anos na faixa-alvo do PNI (10 a 14 anos, 11 meses e 29 dias). "
                "Recomenda-se a 1ª dose da vacina Dengue (Qdenga). "
                "A 2ª dose deve ser aplicada 90 dias após a 1ª."
            )
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 15),
        NOT(DoseAplicada(vacina_codigo='DENGUE', dose=1)),
        NOT(DoseAplicada(vacina_codigo='DENGUE', dose=2))
    )
    def rule_dengue_contraindicated_dose_1(self):
        self.declare(Contraindicacao(
            vacina="Dengue",
            dose=1,
            motivo="Janela etária para início do esquema encerrada.",
            explicacao=(
                "A vacina Dengue (Qdenga) na rotina do PNI é indicada apenas para "
                "adolescentes de 10 a 14 anos, 11 meses e 29 dias. "
                "Paciente fora desta janela etária."
            )
        ))

    @Rule(
        DoseAplicada(vacina_codigo='DENGUE', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='DENGUE', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(days=90)))
    )
    def rule_dengue_dose_2_schedule(self, d1):
        data_d2 = to_date(d1) + relativedelta(days=90)
        self.declare(AgendamentoFuturo(
            vacina="Dengue",
            dose=2,
            data_minima=data_d2,
            data_recomendada=data_d2,
            explicacao=(
                "A 2ª dose da vacina Dengue (Qdenga) deve ser aplicada "
                "90 dias (3 meses) após a 1ª dose."
            )
        ))

    @Rule(
        DoseAplicada(vacina_codigo='DENGUE', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='DENGUE', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(days=90)))
    )
    def rule_dengue_dose_2_recommend(self):
        self.declare(RecomendacaoImediata(
            vacina="Dengue",
            dose=2,
            explicacao=(
                "Intervalo de 90 dias após a 1ª dose cumprido. "
                "Recomenda-se a 2ª dose da vacina Dengue (Qdenga)."
            )
        ))

    @Rule(
        DoseAplicada(vacina_codigo='DENGUE', dose=2, data_aplicacao=MATCH.d2)
    )
    def rule_dengue_scheme_complete(self, d2):
        self.declare(EsquemaCompleto(
            vacina="Dengue",
            explicacao="Esquema de 2 doses da vacina Dengue (Qdenga) finalizado.",
            data_ultima_dose=to_date(d2)
        ))

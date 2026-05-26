import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, EsquemaCompleto

def to_date(d):
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RegrasPneumo23(_RegrasBase):
    """
    Rules for the Pneumococcal 23V vaccine (VPP23) - PNI / IN 2026.
    Target population: Elderly patients >= 60 years.
    Schedule: 2 doses with a minimum interval of 5 years between them.
    Especially indicated for sedentary and institutionalized individuals.
    SIPNI code: 21.
    """

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 60),
        NOT(DoseAplicada(vacina_codigo='PNEUMO23'))
    )
    def rule_pneumo23_dose_1_recommend(self):
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 23V",
            dose=1,
            explicacao=(
                "Idoso >= 60 anos sem registro de Pneumocócica 23V. "
                "A IN 2026 indica esta vacina especialmente para idosos sedentários "
                "e institucionalizados. Recomenda-se a 1ª dose."
            )
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 60),
        DoseAplicada(vacina_codigo='PNEUMO23', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='PNEUMO23', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(years=5)))
    )
    def rule_pneumo23_dose_2_schedule(self, d1):
        data_d2 = to_date(d1) + relativedelta(years=5)
        self.declare(AgendamentoFuturo(
            vacina="Pneumocócica 23V",
            dose=2,
            data_minima=data_d2,
            data_recomendada=data_d2,
            explicacao=(
                "A 2ª dose da Pneumocócica 23V é indicada com intervalo mínimo "
                "de 5 anos após a 1ª dose."
            )
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 60),
        DoseAplicada(vacina_codigo='PNEUMO23', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='PNEUMO23', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(years=5)))
    )
    def rule_pneumo23_dose_2_recommend(self):
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 23V",
            dose=2,
            explicacao=(
                "Intervalo de 5 anos desde a 1ª dose cumprido. "
                "Recomenda-se a 2ª dose da Pneumocócica 23V."
            )
        ))

    @Rule(
        DoseAplicada(vacina_codigo='PNEUMO23', dose=2, data_aplicacao=MATCH.d2)
    )
    def rule_pneumo23_scheme_complete(self, d2):
        self.declare(EsquemaCompleto(
            vacina="Pneumocócica 23V",
            explicacao="Esquema de 2 doses da Pneumocócica 23V finalizado.",
            data_ultima_dose=to_date(d2)
        ))

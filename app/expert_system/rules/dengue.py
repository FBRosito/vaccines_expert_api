import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, Contraindication, CompletedSchedule

def to_date(d):
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RulesDengue(_RegrasBase):
    """
    Rules for the Dengue vaccine - Qdenga (attenuated tetravalent DNG) - PNI / IN 2026.
    Target population: Adolescents aged 10 to 14 years, 11 months and 29 days.
    Schedule: 2 doses with a 90-day (3-month) interval.
    SIPNI code: 104.
    """

    @Rule(
        Age(years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a: a < 10),
        NOT(AppliedDose(vaccine_code='DENGUE'))
    )
    def rule_dengue_dose_1_schedule(self, dn):
        data_alvo = to_date(dn) + relativedelta(years=10)
        self.declare(FutureSchedule(
            vaccine="Dengue",
            dose=1,
            min_date=data_alvo,
            recommended_date=data_alvo,
            explanation=(
                "Agendamento da 1ª dose da vacina Dengue (Qdenga), "
                "indicada a partir dos 10 anos de idade."
            )
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 10 and a < 15),
        NOT(AppliedDose(vaccine_code='DENGUE', dose=1)),
        NOT(AppliedDose(vaccine_code='DENGUE', dose=2))
    )
    def rule_dengue_dose_1_recommend(self, a):
        self.declare(ImmediateRecommendation(
            vaccine="Dengue",
            dose=1,
            explanation=(
                f"Adolescente com {a} anos na faixa-alvo do PNI (10 a 14 anos, 11 meses e 29 dias). "
                "Recomenda-se a 1ª dose da vacina Dengue (Qdenga). "
                "A 2ª dose deve ser aplicada 90 dias após a 1ª."
            )
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 15),
        NOT(AppliedDose(vaccine_code='DENGUE', dose=1)),
        NOT(AppliedDose(vaccine_code='DENGUE', dose=2))
    )
    def rule_dengue_contraindicated_dose_1(self):
        self.declare(Contraindication(
            vaccine="Dengue",
            dose=1,
            reason="Janela etária para início do esquema encerrada.",
            explanation=(
                "A vacina Dengue (Qdenga) na rotina do PNI é indicada apenas para "
                "adolescentes de 10 a 14 anos, 11 meses e 29 dias. "
                "Patient fora desta janela etária."
            )
        ))

    @Rule(
        AppliedDose(vaccine_code='DENGUE', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='DENGUE', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(days=90)))
    )
    def rule_dengue_dose_2_schedule(self, d1):
        data_d2 = to_date(d1) + relativedelta(days=90)
        self.declare(FutureSchedule(
            vaccine="Dengue",
            dose=2,
            min_date=data_d2,
            recommended_date=data_d2,
            explanation=(
                "A 2ª dose da vacina Dengue (Qdenga) deve ser aplicada "
                "90 dias (3 meses) após a 1ª dose."
            )
        ))

    @Rule(
        AppliedDose(vaccine_code='DENGUE', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='DENGUE', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(days=90)))
    )
    def rule_dengue_dose_2_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="Dengue",
            dose=2,
            explanation=(
                "Intervalo de 90 dias após a 1ª dose cumprido. "
                "Recomenda-se a 2ª dose da vacina Dengue (Qdenga)."
            )
        ))

    @Rule(
        AppliedDose(vaccine_code='DENGUE', dose=2, date_applied=MATCH.d2)
    )
    def rule_dengue_scheme_complete(self, d2):
        self.declare(CompletedSchedule(
            vaccine="Dengue",
            explanation="Esquema de 2 doses da vacina Dengue (Qdenga) finalizado.",
            last_dose_date=to_date(d2)
        ))

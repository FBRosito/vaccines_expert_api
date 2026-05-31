import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, CompletedSchedule

def to_date(d):
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RulesPneumo23(_RegrasBase):
    """
    Rules for the Pneumococcal 23V vaccine (VPP23) - PNI / IN 2026.
    Target population: Elderly patients >= 60 years.
    Schedule: 2 doses with a minimum interval of 5 years between them.
    Especially indicated for sedentary and institutionalized individuals.
    SIPNI code: 21.
    """

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 60),
        NOT(AppliedDose(vaccine_code='PNEUMO23'))
    )
    def rule_pneumo23_dose_1_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="Pneumocócica 23V",
            dose=1,
            explanation=(
                "Idoso >= 60 anos sem registro de Pneumocócica 23V. "
                "A IN 2026 indica esta vacina especialmente para idosos sedentários "
                "e institucionalizados. Recomenda-se a 1ª dose."
            )
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 60),
        AppliedDose(vaccine_code='PNEUMO23', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='PNEUMO23', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(years=5)))
    )
    def rule_pneumo23_dose_2_schedule(self, d1):
        data_d2 = to_date(d1) + relativedelta(years=5)
        self.declare(FutureSchedule(
            vaccine="Pneumocócica 23V",
            dose=2,
            min_date=data_d2,
            recommended_date=data_d2,
            explanation=(
                "A 2ª dose da Pneumocócica 23V é indicada com intervalo mínimo "
                "de 5 anos após a 1ª dose."
            )
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 60),
        AppliedDose(vaccine_code='PNEUMO23', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='PNEUMO23', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(years=5)))
    )
    def rule_pneumo23_dose_2_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="Pneumocócica 23V",
            dose=2,
            explanation=(
                "Intervalo de 5 anos desde a 1ª dose cumprido. "
                "Recomenda-se a 2ª dose da Pneumocócica 23V."
            )
        ))

    @Rule(
        AppliedDose(vaccine_code='PNEUMO23', dose=2, date_applied=MATCH.d2)
    )
    def rule_pneumo23_scheme_complete(self, d2):
        self.declare(CompletedSchedule(
            vaccine="Pneumocócica 23V",
            explanation="Esquema de 2 doses da Pneumocócica 23V finalizado.",
            last_dose_date=to_date(d2)
        ))

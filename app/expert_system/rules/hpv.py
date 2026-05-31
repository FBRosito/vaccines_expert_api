import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, Contraindication, CompletedSchedule

class RulesHPV(_RegrasBase):
    """
    Rules for the HPV vaccine (Human Papillomavirus).
    Covers the single-dose schedule for the general population (ages 9-19).
    """

    # =================================================================
    # STANDARD SCHEDULE (SINGLE DOSE)
    # =================================================================

    @Rule(
        Age(years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a: a < 9),
        NOT(AppliedDose(vaccine_code='HPV'))
    )
    def rule_hpv_dose_1_schedule(self, dn):
        """
        (Scheduling) For children < 9 years, schedules the
        single dose for the exact date the child turns 9 years old.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_alvo = dn_data + relativedelta(years=9)

        self.declare(FutureSchedule(
            vaccine="HPV",
            dose="Única",
            min_date=data_alvo,
            recommended_date=data_alvo,
            explanation="Agendamento da dose única de HPV, recomendada aos 9 anos de idade."
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 9 and a < 20),
        NOT(AppliedDose(vaccine_code='HPV'))
    )
    def rule_hpv_dose_1_recommend_now_9to19_years(self, a):
        """
        (Recommendation) For persons aged 9 to 19 years with no dose,
        recommends applying the single dose.
        """
        explicacao = (
            f"Patient com {a} anos. Recomenda-se a dose única da vacina HPV."
            if a < 15
            else f"Patient com {a} anos. Recomenda-se resgate com dose única da vacina HPV."
        )
        self.declare(ImmediateRecommendation(
            vaccine="HPV",
            dose="Única",
            explanation=explicacao
        ))

    # =================================================================
    # COMPLETION AND CONTRAINDICATION RULES
    # =================================================================

    @Rule(
        AppliedDose(vaccine_code='HPV', date_applied=MATCH.data_dose)
    )
    def rule_hpv_scheme_complete(self, data_dose):
        """
        (Scheme Complete) If any HPV dose has been applied,
        marks the single-dose scheme as complete.
        """
        self.declare(CompletedSchedule(
            vaccine="HPV",
            explanation="Esquema de dose única finalizado.",
            last_dose_date=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 20),
        NOT(AppliedDose(vaccine_code='HPV'))
    )
    def rule_hpv_contraindicated_age(self):
        """
        (Contraindication) For persons >= 20 years with no dose,
        contraindicates the vaccine under PNI routine.
        """
        self.declare(Contraindication(
            vaccine="HPV",
            dose="Única",
            reason="Age superior à permitida.",
            explanation="A vacina HPV na rotina do PNI é recomendada apenas até os 19 anos, 11 meses e 29 dias."
        ))

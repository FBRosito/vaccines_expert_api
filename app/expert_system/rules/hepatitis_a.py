import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, Contraindication, CompletedSchedule

class RulesHepatitisA(_RegrasBase):
    """
    Vaccination rules for Hepatitis A (single dose at 15 months).
    """

    @Rule(
        Age(months=MATCH.m, years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 15),
        NOT(AppliedDose(vaccine_code='HEPATITE_A'))
    )
    def rule_hepatite_a_schedule(self, dn):
        """
        (Scheduling) For children < 15 months with no dose, schedules the
        single dose for the exact date the child turns 15 months old.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_alvo = dn_data + relativedelta(months=15)

        self.declare(FutureSchedule(
            vaccine="Hepatite A",
            dose="Única",
            min_date=data_alvo,
            recommended_date=data_alvo,
            explanation="Agendamento da dose única de Hepatite A, recomendada aos 15 meses de idade."
        ))

    @Rule(
        Age(months=MATCH.m, years=MATCH.a),
        TEST(lambda a, m: a < 5 and (a * 12 + m) >= 15),
        NOT(AppliedDose(vaccine_code='HEPATITE_A'))
    )
    def rule_hepatite_a_recommend_now(self):
        """
        (Recommendation) For children >= 15 months and < 5 years,
        recommends the single dose.
        """
        self.declare(ImmediateRecommendation(
            vaccine="Hepatite A",
            dose="Única",
            explanation="A vacina contra Hepatite A é recomendada em dose única aos 15 meses de idade. Pode ser aplicada até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 5),
        NOT(AppliedDose(vaccine_code='HEPATITE_A'))
    )
    def rule_hepatite_a_contraindicated_age(self):
        """
        (Contraindication) For children >= 5 years with no dose,
        contraindicates the vaccine per PNI routine.
        """
        self.declare(Contraindication(
            vaccine="Hepatite A",
            dose="Única",
            reason="Age superior à permitida.",
            explanation="A vacina Hepatite A na rotina do PNI é recomendada apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        AppliedDose(vaccine_code='HEPATITE_A', date_applied=MATCH.data_dose)
    )
    def rule_hepatite_a_scheme_complete(self, data_dose):
        """
        (Scheme Complete) If the single Hepatitis A dose
        has been applied, marks the scheme as complete.
        """
        self.declare(CompletedSchedule(
            vaccine="Hepatite A",
            explanation="Esquema de dose única finalizado.",
            last_dose_date=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

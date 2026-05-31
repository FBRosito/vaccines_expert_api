import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, Contraindication, CompletedSchedule

# --- HELPER FUNCTION ---
def to_date(d):
    """Converts datetime to date if necessary."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RulesInfluenza(_RegrasBase):
    """
    Rules for the Influenza (Flu) vaccine - PNI.

    Target population:
    - Children: 6 months to < 6 years (5 years, 11 months and 29 days).
    - Elderly: >= 60 years.

    Schedule:
    - Children (Primary vaccination): 2 doses with a 30-day interval.
    - Children (With prior history): Annual single dose.
    - Elderly: Annual single dose.
    """

    # =================================================================
    # UNDER 6 MONTHS - SCHEDULING
    # =================================================================
    # Schedule for the minimum age (6 months).

    @Rule(
        Age(months=MATCH.m, birth_date=MATCH.dn),
        TEST(lambda m: m < 6),
        NOT(AppliedDose(vaccine_code='INFLUENZA'))
    )
    def rule_influenza_schedule_6months(self, dn):
        data_alvo = to_date(dn) + relativedelta(months=6)
        self.declare(FutureSchedule(
            vaccine="Influenza",
            dose="1 (Primovacinação)",
            min_date=data_alvo,
            recommended_date=data_alvo,
            explanation="A vacina Influenza é indicada a partir dos 6 meses. Agendamento realizado para essa data."
        ))

    # =================================================================
    # CHILDREN - PRIMARY VACCINATION (DOSE 1)
    # =================================================================
    # If the child is between 6m and 6 years AND has never been vaccinated.

    @Rule(
        Age(months=MATCH.m, years=MATCH.a),
        TEST(lambda a, m: (a < 6) and (a * 12 + m >= 6)),
        NOT(AppliedDose(vaccine_code='INFLUENZA'))
    )
    def rule_influenza_child_primary_dose_1(self):
        self.declare(ImmediateRecommendation(
            vaccine="Influenza",
            dose="1 (Primovacinação)",
            explanation="Criança nunca vacinada contra Influenza. Recomenda-se iniciar esquema de primovacinação (1ª dose)."
        ))

    # =================================================================
    # CHILDREN - PRIMARY VACCINATION (DOSE 2)
    # =================================================================
    # If dose 1 was given THIS YEAR and it is the only lifetime dose, dose 2 is needed (30 days later).

    # CASE 1: SCHEDULE DOSE 2 (interval < 30 days)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 6),
        AppliedDose(vaccine_code='INFLUENZA', date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='INFLUENZA', dose=2)),
        TEST(lambda d1:
             (to_date(d1).year == datetime.date.today().year) and
             (datetime.date.today() < (to_date(d1) + relativedelta(days=30)))
        )
    )
    def rule_influenza_child_primary_dose_2_schedule(self, d1):
        data_base = to_date(d1)
        data_dose2 = data_base + relativedelta(days=30)

        self.declare(FutureSchedule(
            vaccine="Influenza",
            dose="2 (Primovacinação)",
            min_date=data_dose2,
            recommended_date=data_dose2,
            explanation="Primovacinação: A 2ª dose deve ser aplicada 30 dias após a 1ª dose."
        ))

    # CASE 2: IMMEDIATE RECOMMENDATION FOR DOSE 2 (30 days have passed)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 6),
        AppliedDose(vaccine_code='INFLUENZA', date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='INFLUENZA', dose=2)),
        TEST(lambda d1:
             (to_date(d1).year == datetime.date.today().year) and
             (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))
        )
    )
    def rule_influenza_child_primary_dose_2_recommend_now(self):
        self.declare(ImmediateRecommendation(
            vaccine="Influenza",
            dose="2 (Primovacinação)",
            explanation="Completar esquema de primovacinação. Intervalo de 30 dias cumprido."
        ))

    # =================================================================
    # CHILDREN - ANNUAL DOSE (WITH PRIOR HISTORY)
    # =================================================================
    # Child between 6m and 6y who was vaccinated in prior years.
    # This rule recommends the annual dose.
    # If the child has already received the dose this year, rule_cleanup_already_vaccinated_year
    # will fire and declare CompletedSchedule, resolving the conflict.

    @Rule(
        Age(months=MATCH.m, years=MATCH.a),
        TEST(lambda a, m: (a < 6) and (a * 12 + m >= 6)),
        AppliedDose(vaccine_code='INFLUENZA', date_applied=MATCH.d_antiga),
        TEST(lambda d_antiga: to_date(d_antiga).year < datetime.date.today().year),
        NOT(ImmediateRecommendation(vaccine="Influenza", dose="Anual"))
    )
    def rule_influenza_child_annual_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="Influenza",
            dose="Anual",
            explanation="Criança com histórico vacinal anterior. Recomenda-se dose única anual."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 6),
        AppliedDose(vaccine_code='INFLUENZA', date_applied=MATCH.d_atual),
        TEST(lambda d_atual: to_date(d_atual).year == datetime.date.today().year),
        OR(
            AppliedDose(vaccine_code='INFLUENZA', date_applied=MATCH.d_antiga,
                        test=lambda d_antiga: to_date(d_antiga).year < datetime.date.today().year),
            AppliedDose(vaccine_code='INFLUENZA', dose=2)
        )
    )
    def rule_cleanup_already_vaccinated_year(self, d_atual):
        self.declare(CompletedSchedule(
            vaccine="Influenza",
            explanation=f"Vacinação de Influenza ({datetime.date.today().year}) concluída.",
            last_dose_date=to_date(d_atual)
        ))

    # =================================================================
    # ELDERLY (>= 60 YEARS)
    # =================================================================

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 60),
        NOT(ImmediateRecommendation(vaccine="Influenza", dose="Anual"))
    )
    def rule_influenza_elderly_annual(self):
        self.declare(ImmediateRecommendation(
            vaccine="Influenza",
            dose="Anual",
            explanation="Idoso (>= 60 anos): Recomendada dose única anual."
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 60),
        AppliedDose(vaccine_code='INFLUENZA', date_applied=MATCH.d_atual),
        TEST(lambda d_atual: to_date(d_atual).year == datetime.date.today().year)
    )
    def rule_influenza_elderly_scheme_complete(self, d_atual):
        self.declare(CompletedSchedule(
            vaccine="Influenza",
            explanation=f"Dose anual de {datetime.date.today().year} realizada.",
            last_dose_date=to_date(d_atual)
        ))

    # =================================================================
    # ADOLESCENTS AND ADULTS (10 to 59 years) - ANNUAL DOSE
    # =================================================================

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: 10 <= a < 60),
        NOT(AppliedDose(vaccine_code='INFLUENZA',
                         date_applied=MATCH.d,
                         test=lambda d: to_date(d).year == datetime.date.today().year))
    )
    def rule_influenza_adolescent_adult_annual(self):
        self.declare(ImmediateRecommendation(
            vaccine="Influenza",
            dose="Anual",
            explanation=(
                "A IN 2026 inclui adolescentes (10-19 anos) e adultos (20-59 anos) "
                "no calendário de rotina da Influenza. Recomenda-se a dose anual."
            )
        ))

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: 10 <= a < 60),
        AppliedDose(vaccine_code='INFLUENZA', date_applied=MATCH.d_atual),
        TEST(lambda d_atual: to_date(d_atual).year == datetime.date.today().year)
    )
    def rule_influenza_adolescent_adult_scheme_complete(self, d_atual):
        self.declare(CompletedSchedule(
            vaccine="Influenza",
            explanation=f"Dose anual de Influenza ({datetime.date.today().year}) realizada.",
            last_dose_date=to_date(d_atual)
        ))

    # =================================================================
    # OUTSIDE TARGET POPULATION (Routine) — age gap 6-9 years in IN 2026
    # =================================================================

    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 6 and a < 10)
    )
    def rule_influenza_outside_target_group(self):
        self.declare(Contraindication(
            vaccine="Influenza",
            dose="Anual",
            reason="Fora da faixa etária de rotina.",
            explanation=(
                "A IN 2026 indica Influenza em rotina para crianças (6m a <6a), "
                "adolescentes e adultos (10-59a) e idosos (>=60a). "
                "Faixa etária 6-9 anos depende de comorbidades ou campanhas específicas."
            )
        ))

    # =================================================================
    # PRIMARY VACCINATION COMPLETION (CHILD)
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 6),
        AppliedDose(vaccine_code='INFLUENZA', dose=1, date_applied=MATCH.d1),
        AppliedDose(vaccine_code='INFLUENZA', dose=2, date_applied=MATCH.d2),
        TEST(lambda d1, d2:
             (to_date(d1).year == datetime.date.today().year) and
             (to_date(d2).year == datetime.date.today().year)
        )
    )
    def rule_influenza_primary_complete_year(self, d2):
        self.declare(CompletedSchedule(
            vaccine="Influenza",
            explanation=f"Primovacinação completa no ano de {datetime.date.today().year}.",
            last_dose_date=to_date(d2)
        ))

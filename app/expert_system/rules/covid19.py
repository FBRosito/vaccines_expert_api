import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, AND, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, CompletedSchedule, Contraindication

# --- HELPER FUNCTION ---
def to_date(d):
    """Converts datetime to date if necessary."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RulesCovid19(_RegrasBase):
    """
    Vaccination rules for COVID-19 (PNI).
    - Pfizer Pediatric (6m-4y): 3 doses (0, 4wk, 8wk).
    - Moderna Pediatric (6m-4y): 2 doses (0, 4wk).
    - Elderly (>=60y): Semi-annual booster.
    """

    # =================================================================
    # HELPERS
    # =================================================================

    def _schedule_specific_dose(self, vacina_nome, dose, data_base, semanas, motivo):
        data_base_date = to_date(data_base)
        data_alvo = data_base_date + relativedelta(weeks=semanas)

        self.declare(FutureSchedule(
            vaccine=vacina_nome,
            dose=dose,
            min_date=data_alvo,
            recommended_date=data_alvo,
            explanation=motivo
        ))

    # =================================================================
    # INITIAL INDICATION (NO PRIOR DOSE)
    # =================================================================

    @Rule(
        Age(months=MATCH.m, birth_date=MATCH.dn),
        TEST(lambda m: m < 6),
        NOT(AppliedDose(vaccine_code='COVID19_PFIZER')),
        NOT(AppliedDose(vaccine_code='COVID19_MODERNA'))
    )
    def rule_covid_general_schedule_6m(self, dn):
        data_alvo = to_date(dn) + relativedelta(months=6)
        self.declare(FutureSchedule(
            vaccine="COVID-19 (Pfizer ou Moderna)",
            dose=1,
            min_date=data_alvo,
            recommended_date=data_alvo,
            explanation="Agendamento da 1ª dose da COVID-19 pediátrica aos 6 meses."
        ))

    @Rule(
        Age(months=MATCH.m, years=MATCH.a),
        TEST(lambda m, a: (a * 12 + m) >= 6 and a < 5),
        NOT(AppliedDose(vaccine_code='COVID19_PFIZER')),
        NOT(AppliedDose(vaccine_code='COVID19_MODERNA'))
    )
    def rule_covid_general_recommend_start(self):
        self.declare(ImmediateRecommendation(
            vaccine="COVID-19 (Pfizer ou Moderna)",
            dose=1,
            explanation="Criança sem histórico de COVID-19. Iniciar esquema (Pfizer: 3 doses / Moderna: 2 doses)."
        ))

    # =================================================================
    # PFIZER TRACK - 3 DOSES
    # Schedule: D1 -> 4 wk -> D2 -> 8 wk -> D3
    # =================================================================

    # Pfizer D2 (Schedule)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='COVID19_PFIZER', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='COVID19_PFIZER', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(weeks=4)))
    )
    def rule_pfizer_dose_2_schedule(self, d1):
        self._schedule_specific_dose("COVID-19 (Pfizer)", 2, d1, 4, "Pfizer: 2ª dose agendada para 4 semanas após a 1ª.")

    # Pfizer D2 (Recommend Now)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='COVID19_PFIZER', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='COVID19_PFIZER', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(weeks=4)))
    )
    def rule_pfizer_dose_2_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="COVID-19 (Pfizer)", dose=2,
            explanation="2ª dose da Pfizer recomendada (intervalo de 4 semanas cumprido)."
        ))

    # Pfizer D3 (Schedule - 8 weeks after D2)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='COVID19_PFIZER', dose=2, date_applied=MATCH.d2),
        NOT(AppliedDose(vaccine_code='COVID19_PFIZER', dose=3)),
        TEST(lambda d2: datetime.date.today() < (to_date(d2) + relativedelta(weeks=8)))
    )
    def rule_pfizer_dose_3_schedule(self, d2):
        self._schedule_specific_dose("COVID-19 (Pfizer)", 3, d2, 8, "Pfizer: 3ª dose agendada para 8 semanas após a 2ª.")

    # Pfizer D3 (Recommend Now)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='COVID19_PFIZER', dose=2, date_applied=MATCH.d2),
        NOT(AppliedDose(vaccine_code='COVID19_PFIZER', dose=3)),
        TEST(lambda d2: datetime.date.today() >= (to_date(d2) + relativedelta(weeks=8)))
    )
    def rule_pfizer_dose_3_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="COVID-19 (Pfizer)", dose=3,
            explanation="3ª dose da Pfizer recomendada (intervalo de 8 semanas da D2 cumprido)."
        ))

    # Pfizer scheme complete
    @Rule(AppliedDose(vaccine_code='COVID19_PFIZER', dose=3, date_applied=MATCH.d3))
    def rule_pfizer_scheme_complete(self, d3):
        self.declare(CompletedSchedule(
            vaccine="COVID-19 (Pfizer)",
            explanation="Esquema Pfizer (3 doses) completo.",
            last_dose_date=to_date(d3)
        ))

    # =================================================================
    # MODERNA TRACK - 2 DOSES
    # Schedule: D1 -> 4 wk -> D2
    # =================================================================

    # Moderna D2 (Schedule)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='COVID19_MODERNA', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='COVID19_MODERNA', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(weeks=4)))
    )
    def rule_moderna_dose_2_schedule(self, d1):
        self._schedule_specific_dose("COVID-19 (Moderna)", 2, d1, 4, "Moderna: 2ª dose agendada para 4 semanas após a 1ª.")

    # Moderna D2 (Recommend Now)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='COVID19_MODERNA', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='COVID19_MODERNA', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(weeks=4)))
    )
    def rule_moderna_dose_2_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="COVID-19 (Moderna)", dose=2,
            explanation="2ª dose da Moderna recomendada (intervalo de 4 semanas cumprido)."
        ))

    # Moderna scheme complete (2 doses)
    @Rule(AppliedDose(vaccine_code='COVID19_MODERNA', dose=2, date_applied=MATCH.d2))
    def rule_moderna_scheme_complete(self, d2):
        self.declare(CompletedSchedule(
            vaccine="COVID-19 (Moderna)",
            explanation="Esquema Moderna (2 doses) completo.",
            last_dose_date=to_date(d2)
        ))

    # =================================================================
    # ELDERLY (>= 60 YEARS) - PERIODIC BOOSTER
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 60),
        OR(
            NOT(OR(AppliedDose(vaccine_code='COVID19_PFIZER'), AppliedDose(vaccine_code='COVID19_MODERNA'))),
            AND(
                OR(
                    AppliedDose(vaccine_code='COVID19_PFIZER', date_applied=MATCH.ult_dose),
                    AppliedDose(vaccine_code='COVID19_MODERNA', date_applied=MATCH.ult_dose)
                ),
                TEST(lambda ult_dose: datetime.date.today() >= (to_date(ult_dose) + relativedelta(months=6)))
            )
        ),
        NOT(ImmediateRecommendation(vacina__contains="COVID-19"))
    )
    def rule_covid_elderly_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="COVID-19 (Reforço)",
            dose="Periódica",
            explanation="Para idosos (>=60 anos), recomenda-se reforço semestral (bivalente ou disponível)."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 60),
        OR(
            AppliedDose(vaccine_code='COVID19_PFIZER', date_applied=MATCH.ult_dose),
            AppliedDose(vaccine_code='COVID19_MODERNA', date_applied=MATCH.ult_dose)
        ),
        TEST(lambda ult_dose: datetime.date.today() < (to_date(ult_dose) + relativedelta(months=6)))
    )
    def rule_covid_elderly_up_to_date(self, ult_dose):
        self.declare(CompletedSchedule(
            vaccine="COVID-19",
            explanation="Dose periódica em dia (intervalo de 6 meses vigente).",
            last_dose_date=to_date(ult_dose)
        ))

    # =================================================================
    # ADULTS (20-59 years) - ANNUAL PERIODIC DOSES
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: 20 <= a < 60),
        OR(
            NOT(OR(AppliedDose(vaccine_code='COVID19_PFIZER'),
                   AppliedDose(vaccine_code='COVID19_MODERNA'))),
            AND(
                OR(
                    AppliedDose(vaccine_code='COVID19_PFIZER', date_applied=MATCH.ult_dose),
                    AppliedDose(vaccine_code='COVID19_MODERNA', date_applied=MATCH.ult_dose)
                ),
                TEST(lambda ult_dose: datetime.date.today() >= (to_date(ult_dose) + relativedelta(months=12)))
            )
        ),
        NOT(ImmediateRecommendation(vacina__contains="COVID-19"))
    )
    def rule_covid_adult_recommend(self):
        self.declare(ImmediateRecommendation(
            vaccine="COVID-19 (Reforço)",
            dose="Periódica",
            explanation=(
                "A IN 2026 inclui adultos (20-59 anos) no calendário de rotina da COVID-19. "
                "Recomenda-se dose anual (Pfizer 0,3 mL ou Moderna 0,5 mL)."
            )
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: 20 <= a < 60),
        OR(
            AppliedDose(vaccine_code='COVID19_PFIZER', date_applied=MATCH.ult_dose),
            AppliedDose(vaccine_code='COVID19_MODERNA', date_applied=MATCH.ult_dose)
        ),
        TEST(lambda ult_dose: datetime.date.today() < (to_date(ult_dose) + relativedelta(months=12)))
    )
    def rule_covid_adult_scheme_complete(self, ult_dose):
        self.declare(CompletedSchedule(
            vaccine="COVID-19",
            explanation="Dose periódica anual em dia (intervalo de 12 meses vigente).",
            last_dose_date=to_date(ult_dose)
        ))

    # =================================================================
    # CONTRAINDICATION — age range 5-19 years (outside current target)
    # =================================================================
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 5 and a < 20),
        NOT(AppliedDose(vaccine_code='COVID19_PFIZER')),
        NOT(AppliedDose(vaccine_code='COVID19_MODERNA'))
    )
    def rule_covid_not_recommended_priority(self):
        self.declare(Contraindication(
            vaccine="COVID-19",
            dose="Rotina",
            reason="Fora do grupo prioritário na rotina atual.",
            explanation=(
                "Vacinação de rotina COVID-19 indicada para <5 anos, adultos (20-59 anos) "
                "e idosos (>=60 anos). Para faixa 5-19 anos, consultar orientações específicas."
            )
        ))

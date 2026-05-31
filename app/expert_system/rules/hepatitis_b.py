import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, Contraindication, CompletedSchedule

class RulesHepatitisB(_RegrasBase):
    """
    Rules for Hepatitis B (at birth and catch-up schedule for patients >= 7 years).
    The childhood primary schedule is covered by the Penta vaccine.
    """

    # =================================================================
    # AT-BIRTH SCHEDULE (0-30 DAYS)
    # =================================================================

    @Rule(Age(days=MATCH.d), TEST(lambda d: d <= 30), NOT(AppliedDose(vaccine_code='HEPATITE_B')))
    def rule_hep_b_at_birth_pending(self):
        self.declare(ImmediateRecommendation(
            vaccine="Hepatite B (ao nascer)",
            dose="Única",
            explanation="Dose única recomendada nas primeiras 24h de vida (preferencialmente 12h), podendo ser administrada até 30 dias após o nascimento."
        ))

    @Rule(AppliedDose(vaccine_code='HEPATITE_B', date_applied=MATCH.data_dose))
    def rule_hep_b_at_birth_ok(self, data_dose):
        self.declare(CompletedSchedule(
            vaccine="Hepatite B (ao nascer)",
            explanation="Dose ao nascer aplicada corretamente, conforme registro.",
            last_dose_date=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

    @Rule(Age(days=MATCH.d), TEST(lambda d: d > 30), NOT(AppliedDose(vaccine_code='HEPATITE_B')))
    def rule_hep_b_at_birth_contraindicated_age(self):
        self.declare(Contraindication(
            vaccine="Hepatite B (ao nascer)",
            dose="Única",
            reason="Age superior a 30 dias.",
            explanation="A dose monovalente da Hepatite B é recomendada apenas para os primeiros 30 dias de vida."
        ))

    # =================================================================
    # ADULT SCHEDULE (>= 7 YEARS)
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        NOT(AppliedDose(vaccine_code='HEPATITE_B')),
        NOT(AppliedDose(vaccine_code='PENTA')),
        NOT(CompletedSchedule(vaccine="Hepatite B (esquema adulto)"))
    )
    def rule_hep_b_over7_recommend_now(self, a):
        self.declare(ImmediateRecommendation(
            vaccine="Hepatite B (esquema adulto)",
            dose=1,
            explanation=f"Patient com {a} anos sem comprovação vacinal. Iniciar esquema de 3 doses (0, 1 e 6 meses)."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='HEPATITE_B', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='HEPATITE_B', dose=2)),
        NOT(CompletedSchedule(vaccine="Hepatite B (esquema adulto)"))
    )
    def rule_hep_b_over7_schedule_dose_2(self, d1):
        d1_data = d1.date() if isinstance(d1, datetime.datetime) else d1

        data_min = d1_data + relativedelta(weeks=4)
        data_rec = d1_data + relativedelta(days=30)
        hoje = datetime.date.today()

        if data_rec > hoje:
            self.declare(FutureSchedule(
                vaccine="Hepatite B (esquema adulto)",
                dose=2,
                min_date=data_min,
                recommended_date=data_rec,
                explanation="A 2ª dose é recomendada 30 dias após a primeira (mínimo de 4 semanas)."
            ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='HEPATITE_B', dose=1, date_applied=MATCH.d1),
        TEST(lambda d1: datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(weeks=4))),
        NOT(AppliedDose(vaccine_code='HEPATITE_B', dose=2)),
        NOT(CompletedSchedule(vaccine="Hepatite B (esquema adulto)"))
    )
    def rule_hep_b_over7_dose_2_recommend_late(self):
        self.declare(ImmediateRecommendation(
            vaccine="Hepatite B (esquema adulto)",
            dose=2,
            explanation="A 2ª dose da Hepatite B está atrasada. Aplicar agora (intervalo mínimo de 4 semanas respeitado)."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='HEPATITE_B', dose=1, date_applied=MATCH.d1),
        OR(
            'd2_ap' << AppliedDose(vaccine_code='HEPATITE_B', dose=2),
            'd2_ag' << FutureSchedule(vaccine="Hepatite B (esquema adulto)", dose=2),
            'd2_rec' << ImmediateRecommendation(vaccine="Hepatite B (esquema adulto)", dose=2)
        ),
        NOT(AppliedDose(vaccine_code='HEPATITE_B', dose=3)),
        NOT(FutureSchedule(vaccine="Hepatite B (esquema adulto)", dose=3)),
        NOT(CompletedSchedule(vaccine="Hepatite B (esquema adulto)"))
    )
    def rule_hep_b_over7_schedule_dose_3(self, d1, d2_ap=None, d2_ag=None, d2_rec=None):
        """
        (Scheduling) Dose 3: ideal 6 months after dose 1.
        Based on dose 2 (actual, planned, or currently recommended).
        """
        d1_data = d1.date() if isinstance(d1, datetime.datetime) else d1
        hoje = datetime.date.today()

        if d2_ap:
            val = d2_ap['date_applied']
            d2_base = val.date() if isinstance(val, datetime.datetime) else val
        elif d2_ag:
            d2_base = d2_ag['recommended_date']
        elif d2_rec:
            d2_base = hoje
        else:
            return

        # 1. Calculate mandatory minimums
        min_apos_d1 = d1_data + relativedelta(weeks=16)
        min_apos_d2 = d2_base + relativedelta(weeks=8)
        data_minima_final = max(min_apos_d1, min_apos_d2)

        # 2. Calculate the ideal (recommended) date
        data_ideal = d1_data + relativedelta(months=6)

        # 3. Prioritization logic (ideal vs minimum)
        data_recomendada_final = max(data_ideal, data_minima_final)

        if data_recomendada_final > hoje:
            self.declare(FutureSchedule(
                vaccine="Hepatite B (esquema adulto)",
                dose=3,
                min_date=data_minima_final,
                recommended_date=data_recomendada_final,
                explanation="Agendamento da 3ª dose (conclusão do esquema 0-1-6). Data respeita o prazo ideal de 6 meses após a 1ª dose e o intervalo mínimo de segurança de 8 semanas após a 2ª dose."
            ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='HEPATITE_B', dose=1, date_applied=MATCH.d1),
        AppliedDose(vaccine_code='HEPATITE_B', dose=2, date_applied=MATCH.d2),
        TEST(lambda d1, d2:
             datetime.date.today() >= ((d2.date() if isinstance(d2, datetime.datetime) else d2) + relativedelta(weeks=8)) and
             datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(weeks=16))
        ),
        NOT(AppliedDose(vaccine_code='HEPATITE_B', dose=3)),
        NOT(CompletedSchedule(vaccine="Hepatite B (esquema adulto)"))
    )
    def rule_hep_b_over7_dose_3_recommend_late(self):
        self.declare(ImmediateRecommendation(
            vaccine="Hepatite B (esquema adulto)",
            dose=3,
            explanation="A 3ª dose da Hepatite B está atrasada. Aplicar agora (todos os intervalos mínimos respeitados)."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='HEPATITE_B', dose=3, date_applied=MATCH.d3_data)
    )
    def rule_hep_b_over7_scheme_complete(self, d3_data):
        self.declare(CompletedSchedule(
            vaccine="Hepatite B (esquema adulto)",
            explanation="Esquema de 3 doses para Hepatite B finalizado.",
            last_dose_date=d3_data.date() if isinstance(d3_data, datetime.datetime) else d3_data
        ))

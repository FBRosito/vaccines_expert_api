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

class RulesPneumo10(_RegrasBase):
    """
    Rules for the Pneumococcal 10V vaccine.
    """

    # =================================================================
    # PRIMARY SCHEME (DOSE 1)
    # =================================================================

    @Rule(
        Age(months=MATCH.m, birth_date=MATCH.dn),
        TEST(lambda m: m < 2),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=1))
    )
    def rule_pneumo10_dose_1_schedule(self, dn):
        dn_data = to_date(dn)
        data_agendada = dn_data + relativedelta(months=2)

        self.declare(FutureSchedule(
            vaccine="Pneumocócica 10V",
            dose=1,
            min_date=data_agendada,
            recommended_date=data_agendada,
            explanation="Agendamento da 1ª dose, recomendada aos 2 meses de idade."
        ))

    @Rule(
        Age(months=MATCH.m, years=MATCH.a),
        TEST(lambda a, m: a == 0 and m >= 2),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=1))
    )
    def rule_pneumo10_dose_1_recommend_now_under_1y(self, m):
        self.declare(ImmediateRecommendation(
            vaccine="Pneumocócica 10V", dose=1,
            explanation=f"Patient com {m} meses. A 1ª dose da vacina Pneumocócica 10V é recomendada aos 2 meses."
        ))

    # =================================================================
    # PRIMARY SCHEME (DOSE 2)
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a < 5),
        OR(
            AppliedDose(vaccine_code='PNEUMO10', dose=1, date_applied=MATCH.d1_data),
            FutureSchedule(vaccine="Pneumocócica 10V", dose=1, recommended_date=MATCH.d1_data)
        ),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=2)),
        NOT(FutureSchedule(vaccine="Pneumocócica 10V", dose=2)),
        TEST(lambda d1_data:
            datetime.date.today() < (to_date(d1_data) + relativedelta(months=2))
        )
    )
    def rule_pneumo10_dose_2_schedule(self, d1_data):
        data_base = to_date(d1_data)

        self.declare(FutureSchedule(
            vaccine="Pneumocócica 10V", dose=2,
            min_date=data_base + relativedelta(days=30),
            recommended_date=data_base + relativedelta(months=2),
            explanation="A 2ª dose é agendada para 2 meses após a 1ª dose."
        ))

    @Rule(
        Age(years=MATCH.a, birth_date=MATCH.dn), TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='PNEUMO10', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=2)),
        TEST(lambda d1, dn:
            (
                (to_date(d1) >= (to_date(dn) + relativedelta(months=4)))
                and
                (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))
            )
            or
            (
                datetime.date.today() >= (to_date(d1) + relativedelta(months=2))
            )
        )
    )
    def rule_pneumo10_dose_2_recommend_now_late(self):
        self.declare(ImmediateRecommendation(
            vaccine="Pneumocócica 10V", dose=2,
            explanation="A 2ª dose da Pneumocócica 10V está recomendada (intervalo cumprido)."
        ))

    # =================================================================
    # BOOSTER (DOSE 3) - FULL LOGIC
    # =================================================================

    def _schedule_booster_generic(self, d2_data, dn):
        """Calculates booster: Max(12 months, D2 + 60 days)"""
        d2_resolvida = to_date(d2_data)
        dn_data = to_date(dn)

        data_12_meses = dn_data + relativedelta(months=12)
        data_intervalo_d2 = d2_resolvida + relativedelta(months=2)
        data_final = max(data_12_meses, data_intervalo_d2)

        self.declare(FutureSchedule(
            vaccine="Pneumocócica 10V",
            dose="Reforço",
            min_date=data_final,
            recommended_date=data_final,
            explanation="Reforço projetado para completá-lo até 12 meses de idade, ou 60 dias após a 2ª dose."
        ))

    @Rule(
        Age(years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a: a < 5),
        AppliedDose(vaccine_code='PNEUMO10', dose=2, date_applied=MATCH.d2),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=3)),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose="Reforço")),
        NOT(FutureSchedule(vaccine="Pneumocócica 10V", dose="Reforço"))
    )
    def rule_pneumo10_booster_after_applied_dose(self, d2, dn):
        self._schedule_booster_generic(d2, dn)

    @Rule(
        Age(years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a: a < 5),
        FutureSchedule(vaccine="Pneumocócica 10V", dose=2, recommended_date=MATCH.d2_prevista),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=2)),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=3)),
        NOT(FutureSchedule(vaccine="Pneumocócica 10V", dose="Reforço"))
    )
    def rule_pneumo10_booster_after_scheduled_dose(self, d2_prevista, dn):
        self._schedule_booster_generic(d2_prevista, dn)

    @Rule(
        Age(years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a: a < 5),
        ImmediateRecommendation(vaccine="Pneumocócica 10V", dose=2),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=2)),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=3)),
        NOT(FutureSchedule(vaccine="Pneumocócica 10V", dose="Reforço"))
    )
    def rule_pneumo10_booster_after_dose_2_recommendation(self, dn):
        self._schedule_booster_generic(datetime.date.today(), dn)

    @Rule(
        Age(months=MATCH.m, years=MATCH.a),
        AppliedDose(vaccine_code='PNEUMO10', dose=2, date_applied=MATCH.d2),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=3)),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose="Reforço")),
        TEST(lambda a, m, d2:
            (a >= 1) and
            (datetime.date.today() >= (to_date(d2) + relativedelta(months=2)))
        )
    )
    def rule_pneumo10_booster_recommend_now(self):
        self.declare(ImmediateRecommendation(
            vaccine="Pneumocócica 10V", dose="Reforço",
            explanation="Reforço recomendado: Criança maior que 1 ano com intervalo de 60 dias da 2ª dose cumprido."
        ))

    # =================================================================
    # CATCH-UP & COMPLETION
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        NOT(AppliedDose(vaccine_code='PNEUMO10')),
        NOT(FutureSchedule(vaccine="Pneumocócica 10V"))
    )
    def rule_pneumo10_catch_up_single_dose(self, a):
        self.declare(ImmediateRecommendation(
            vaccine="Pneumocócica 10V", dose="Única",
            explanation=f"Para crianças com {a} anos sem comprovação vacinal, recomenda-se dose única."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 5),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose=3)),
        NOT(AppliedDose(vaccine_code='PNEUMO10', dose="Única"))
    )
    def rule_pneumo10_contraindicated_age(self):
        self.declare(Contraindication(
            vaccine="Pneumocócica 10V", dose="Todas",
            reason="Age superior à permitida.",
            explanation="A vacina Pneumo10 na rotina do PNI é recomendada apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        OR(
            AppliedDose(vaccine_code='PNEUMO10', dose=3, date_applied=MATCH.data_dose),
            AppliedDose(vaccine_code='PNEUMO10', dose="Reforço", date_applied=MATCH.data_dose),
            AppliedDose(vaccine_code='PNEUMO10', dose="Única", date_applied=MATCH.data_dose)
        )
    )
    def rule_pneumo10_scheme_complete(self, data_dose):
        self.declare(CompletedSchedule(
            vaccine="Pneumocócica 10V",
            explanation="Esquema de vacinação da Pneumocócica 10V finalizado.",
            last_dose_date=to_date(data_dose)
        ))

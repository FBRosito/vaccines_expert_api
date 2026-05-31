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

class RulesMeningo(_RegrasBase):
    """
    Vaccination rules for Meningococcal C (infant)
    and Meningococcal ACWY (infant booster and adolescent).
    """

    # =================================================================
    # MENINGOCOCCAL C - PRIMARY SCHEME (3 AND 5 MONTHS)
    # =================================================================

    @Rule(
        Age(months=MATCH.m, days=MATCH.d, birth_date=MATCH.dn),
        TEST(lambda m: m < 3),
        NOT(AppliedDose(vaccine_code='MEN_C', dose=1))
    )
    def rule_menc_dose_1_schedule(self, dn):
        dn_data = to_date(dn)
        data_agendada = dn_data + relativedelta(months=3)

        self.declare(FutureSchedule(
            vaccine="Meningocócica C",
            dose=1,
            min_date=data_agendada,
            recommended_date=data_agendada,
            explanation="Agendamento da 1ª dose, recomendada aos 3 meses de idade."
        ))

    @Rule(
        Age(months=MATCH.m, years=MATCH.a),
        TEST(lambda a, m: a == 0 and m >= 3),
        NOT(AppliedDose(vaccine_code='MEN_C', dose=1))
    )
    def rule_menc_dose_1_recommend_now_under_1y(self, m):
        self.declare(ImmediateRecommendation(
            vaccine="Meningocócica C", dose=1,
            explanation=f"Patient com {m} meses. A 1ª dose da Meningocócica C é recomendada aos 3 meses."
        ))

    # Schedule dose 2 (future)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a == 0),
        OR(
            AppliedDose(vaccine_code='MEN_C', dose=1, date_applied=MATCH.d1_data),
            FutureSchedule(vaccine="Meningocócica C", dose=1, recommended_date=MATCH.d1_data)
        ),
        NOT(AppliedDose(vaccine_code='MEN_C', dose=2)),
        NOT(FutureSchedule(vaccine="Meningocócica C", dose=2)),
        TEST(lambda d1_data: datetime.date.today() < (to_date(d1_data) + relativedelta(months=2)))
    )
    def rule_menc_dose_2_schedule(self, d1_data):
        data_base = to_date(d1_data)
        self.declare(FutureSchedule(
            vaccine="Meningocócica C", dose=2,
            min_date=data_base + relativedelta(days=30),
            recommended_date=data_base + relativedelta(months=2),
            explanation="A 2ª dose da Meningocócica C é agendada 2 meses após a 1ª dose."
        ))

    # Recommend dose 2 now (only for < 12 months)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a == 0),
        AppliedDose(vaccine_code='MEN_C', dose=1, date_applied=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))),
        NOT(AppliedDose(vaccine_code='MEN_C', dose=2))
    )
    def rule_menc_dose_2_recommend_now_late(self):
        self.declare(ImmediateRecommendation(
            vaccine="Meningocócica C",
            dose=2,
            explanation="A 2ª dose da Meningocócica C está atrasada. Aplicar agora (intervalo mínimo de 30 dias)."
        ))

    # =================================================================
    # MENINGOCOCCAL ACWY - CATCH-UP / PRIMARY VACCINATION 1-4 YEARS
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        NOT(AppliedDose(vaccine_code='MEN_C')),
        NOT(AppliedDose(vaccine_code='MEN_ACWY'))
    )
    def rule_menacwy_catch_up_direct(self, a):
        """
        For ages 1-4 WITHOUT prior history: recommends ACWY single dose directly.
        This ensures protection against 4 serogroups and simplifies the late scheme.
        """
        self.declare(ImmediateRecommendation(
            vaccine="Meningocócica ACWY",
            dose="Dose Única",
            explanation=f"Criança de {a} anos sem vacina prévia. Administrar dose única de Meningocócica ACWY (proteção ampliada)."
        ))

    # =================================================================
    # MENINGOCOCCAL ACWY - INFANT BOOSTER (12 months - 4 years)
    # =================================================================

    # 1. Schedule ACWY booster (for patients < 12 months who already have Men-C dose 2)
    @Rule(
        Age(months=MATCH.m, years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 12),
        OR(
            AppliedDose(vaccine_code='MEN_C', dose=2, date_applied=MATCH.d2_data),
            FutureSchedule(vaccine="Meningocócica C", dose=2, recommended_date=MATCH.d2_data)
        ),
        NOT(AppliedDose(vaccine_code='MEN_ACWY')),
        NOT(FutureSchedule(vaccine="Meningocócica ACWY", dose="Reforço"))
    )
    def rule_menacwy_infant_schedule(self, d2_data, dn):
        d2_res = to_date(d2_data)
        dn_res = to_date(dn)

        data_12m = dn_res + relativedelta(months=12)
        data_int = d2_res + relativedelta(days=60)
        data_final = max(data_12m, data_int)

        self.declare(FutureSchedule(
            vaccine="Meningocócica ACWY",
            dose="Reforço",
            min_date=data_final,
            recommended_date=data_final,
            explanation="Reforço preferencial com Meningo ACWY aos 12 meses."
        ))

    # 2. Recommend ACWY NOW (booster for 1-4 years with Men-C history)
    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        OR(
            AppliedDose(vaccine_code='MEN_C', dose=1, date_applied=MATCH.d_antiga),
            AppliedDose(vaccine_code='MEN_C', dose=2, date_applied=MATCH.d_antiga),
            AppliedDose(vaccine_code='MEN_C', dose="Única", date_applied=MATCH.d_antiga)
        ),
        TEST(lambda d_antiga: datetime.date.today() >= (to_date(d_antiga) + relativedelta(days=30))),
        NOT(AppliedDose(vaccine_code='MEN_ACWY'))
    )
    def rule_menacwy_infant_recommend_now(self, a):
        self.declare(ImmediateRecommendation(
            vaccine="Meningocócica ACWY",
            dose="Reforço",
            explanation=f"Criança de {a} anos com histórico de Men-C. Recomendado reforço preferencial com ACWY."
        ))

    # =================================================================
    # MENINGOCOCCAL ACWY - ADOLESCENT (11-14 YEARS)
    # =================================================================

    # Schedule for 11 years
    @Rule(
        Age(years=MATCH.a, birth_date=MATCH.dn),
        TEST(lambda a: a >= 5 and a < 11),
        NOT(AppliedDose(vaccine_code='MEN_ACWY', dose=1))
    )
    def rule_menacwy_adolescent_schedule(self, dn):
        dn_data = to_date(dn)
        data_alvo = dn_data + relativedelta(years=11)

        self.declare(FutureSchedule(
            vaccine="Meningocócica ACWY",
            dose="Dose Única (Adolescente)",
            min_date=data_alvo,
            recommended_date=data_alvo,
            explanation="Agendamento da dose de rotina para adolescentes (11 a 14 anos)."
        ))

    # Immediate recommendation for adolescents (11-14 years)
    @Rule(
        Age(years=MATCH.a),
        TEST(lambda a: a >= 11 and a < 15),
        NOT(AppliedDose(vaccine_code='MEN_ACWY'))
    )
    def rule_menacwy_adolescent_recommend(self, a):
        self.declare(ImmediateRecommendation(
            vaccine="Meningocócica ACWY",
            dose="Dose Única (Adolescente)",
            explanation=f"Adolescente com {a} anos. Recomendada dose única de Meningo ACWY."
        ))

    # =================================================================
    # CONCLUSIONS
    # =================================================================

    @Rule(
        AppliedDose(vaccine_code='MEN_ACWY', date_applied=MATCH.d_acwy),
        Age(years=MATCH.a),
        TEST(lambda a: a >= 11)
    )
    def rule_menacwy_adolescent_scheme_complete(self, d_acwy):
        self.declare(CompletedSchedule(
            vaccine="Meningocócica ACWY",
            explanation="Esquema encerrado com a dose de Meningocócica ACWY.",
            last_dose_date=to_date(d_acwy)
        ))

    @Rule(
        AppliedDose(vaccine_code='MEN_ACWY', date_applied=MATCH.d_acwy),
        Age(years=MATCH.a),
        TEST(lambda a: a < 5)
    )
    def rule_menacwy_infant_scheme_complete(self, d_acwy):
        self.declare(CompletedSchedule(
            vaccine="Meningocócica C",
            explanation="Esquema encerrado com a dose de Meningocócica ACWY.",
            last_dose_date=to_date(d_acwy)
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 5 and a < 11),
        NOT(AppliedDose(vaccine_code='MEN_C', dose=3)),
        NOT(AppliedDose(vaccine_code='MEN_ACWY'))
    )
    def rule_menc_contraindicated_age(self):
        """Contraindication Men-C > 5 years (if booster was not given, the infant window was missed)."""
        self.declare(Contraindication(
            vaccine="Meningocócica C",
            dose="Reforço",
            reason="Age > 5 anos.",
            explanation="O reforço infantil é até 4 anos, 11 meses e 29 dias. Aguardar idade para ACWY adolescente (11 anos)."
        ))

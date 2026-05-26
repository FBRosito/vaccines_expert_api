import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

# --- HELPER FUNCTION ---
def to_date(d):
    """Converts datetime to date if necessary."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RegrasMeningo(_RegrasBase):
    """
    Vaccination rules for Meningococcal C (infant)
    and Meningococcal ACWY (infant booster and adolescent).
    """

    # =================================================================
    # MENINGOCOCCAL C - PRIMARY SCHEME (3 AND 5 MONTHS)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn),
        TEST(lambda m: m < 3),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=1))
    )
    def rule_menc_dose_1_schedule(self, dn):
        dn_data = to_date(dn)
        data_agendada = dn_data + relativedelta(months=3)

        self.declare(AgendamentoFuturo(
            vacina="Meningocócica C",
            dose=1,
            data_minima=data_agendada,
            data_recomendada=data_agendada,
            explicacao="Agendamento da 1ª dose, recomendada aos 3 meses de idade."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a == 0 and m >= 3),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=1))
    )
    def rule_menc_dose_1_recommend_now_under_1y(self, m):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da Meningocócica C é recomendada aos 3 meses."
        ))

    # Schedule dose 2 (future)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a == 0),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Meningocócica C", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2)),
        NOT(AgendamentoFuturo(vacina="Meningocócica C", dose=2)),
        TEST(lambda d1_data: datetime.date.today() < (to_date(d1_data) + relativedelta(months=2)))
    )
    def rule_menc_dose_2_schedule(self, d1_data):
        data_base = to_date(d1_data)
        self.declare(AgendamentoFuturo(
            vacina="Meningocócica C", dose=2,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 2ª dose da Meningocócica C é agendada 2 meses após a 1ª dose."
        ))

    # Recommend dose 2 now (only for < 12 months)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a == 0),
        DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2))
    )
    def rule_menc_dose_2_recommend_now_late(self):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C",
            dose=2,
            explicacao="A 2ª dose da Meningocócica C está atrasada. Aplicar agora (intervalo mínimo de 30 dias)."
        ))

    # =================================================================
    # MENINGOCOCCAL ACWY - CATCH-UP / PRIMARY VACCINATION 1-4 YEARS
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        NOT(DoseAplicada(vacina_codigo='MEN_C')),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def rule_menacwy_catch_up_direct(self, a):
        """
        For ages 1-4 WITHOUT prior history: recommends ACWY single dose directly.
        This ensures protection against 4 serogroups and simplifies the late scheme.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Dose Única",
            explicacao=f"Criança de {a} anos sem vacina prévia. Administrar dose única de Meningocócica ACWY (proteção ampliada)."
        ))

    # =================================================================
    # MENINGOCOCCAL ACWY - INFANT BOOSTER (12 months - 4 years)
    # =================================================================

    # 1. Schedule ACWY booster (for patients < 12 months who already have Men-C dose 2)
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 12),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=2, data_aplicacao=MATCH.d2_data),
            AgendamentoFuturo(vacina="Meningocócica C", dose=2, data_recomendada=MATCH.d2_data)
        ),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY')),
        NOT(AgendamentoFuturo(vacina="Meningocócica ACWY", dose="Reforço"))
    )
    def rule_menacwy_infant_schedule(self, d2_data, dn):
        d2_res = to_date(d2_data)
        dn_res = to_date(dn)

        data_12m = dn_res + relativedelta(months=12)
        data_int = d2_res + relativedelta(days=60)
        data_final = max(data_12m, data_int)

        self.declare(AgendamentoFuturo(
            vacina="Meningocócica ACWY",
            dose="Reforço",
            data_minima=data_final,
            data_recomendada=data_final,
            explicacao="Reforço preferencial com Meningo ACWY aos 12 meses."
        ))

    # 2. Recommend ACWY NOW (booster for 1-4 years with Men-C history)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d_antiga),
            DoseAplicada(vacina_codigo='MEN_C', dose=2, data_aplicacao=MATCH.d_antiga),
            DoseAplicada(vacina_codigo='MEN_C', dose="Única", data_aplicacao=MATCH.d_antiga)
        ),
        TEST(lambda d_antiga: datetime.date.today() >= (to_date(d_antiga) + relativedelta(days=30))),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def rule_menacwy_infant_recommend_now(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Reforço",
            explicacao=f"Criança de {a} anos com histórico de Men-C. Recomendado reforço preferencial com ACWY."
        ))

    # =================================================================
    # MENINGOCOCCAL ACWY - ADOLESCENT (11-14 YEARS)
    # =================================================================

    # Schedule for 11 years
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a >= 5 and a < 11),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY', dose=1))
    )
    def rule_menacwy_adolescent_schedule(self, dn):
        dn_data = to_date(dn)
        data_alvo = dn_data + relativedelta(years=11)

        self.declare(AgendamentoFuturo(
            vacina="Meningocócica ACWY",
            dose="Dose Única (Adolescente)",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da dose de rotina para adolescentes (11 a 14 anos)."
        ))

    # Immediate recommendation for adolescents (11-14 years)
    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11 and a < 15),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def rule_menacwy_adolescent_recommend(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Dose Única (Adolescente)",
            explicacao=f"Adolescente com {a} anos. Recomendada dose única de Meningo ACWY."
        ))

    # =================================================================
    # CONCLUSIONS
    # =================================================================

    @Rule(
        DoseAplicada(vacina_codigo='MEN_ACWY', data_aplicacao=MATCH.d_acwy),
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11)
    )
    def rule_menacwy_adolescent_scheme_complete(self, d_acwy):
        self.declare(EsquemaCompleto(
            vacina="Meningocócica ACWY",
            explicacao="Esquema encerrado com a dose de Meningocócica ACWY.",
            data_ultima_dose=to_date(d_acwy)
        ))

    @Rule(
        DoseAplicada(vacina_codigo='MEN_ACWY', data_aplicacao=MATCH.d_acwy),
        Idade(anos=MATCH.a),
        TEST(lambda a: a < 5)
    )
    def rule_menacwy_infant_scheme_complete(self, d_acwy):
        self.declare(EsquemaCompleto(
            vacina="Meningocócica C",
            explicacao="Esquema encerrado com a dose de Meningocócica ACWY.",
            data_ultima_dose=to_date(d_acwy)
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 11),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=3)),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def rule_menc_contraindicated_age(self):
        """Contraindication Men-C > 5 years (if booster was not given, the infant window was missed)."""
        self.declare(Contraindicacao(
            vacina="Meningocócica C",
            dose="Reforço",
            motivo="Idade > 5 anos.",
            explicacao="O reforço infantil é até 4 anos, 11 meses e 29 dias. Aguardar idade para ACWY adolescente (11 anos)."
        ))

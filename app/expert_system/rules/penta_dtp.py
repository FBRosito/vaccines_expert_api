import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

# --- HELPER FUNCTION ---
def to_date(d):
    """Converts datetime to date if necessary."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RegrasPentaDTP(_RegrasBase):
    """
    Rules for the sequential Penta (primary) and DTP (boosters) scheme - PNI.
    Penta: 2, 4, 6 months.
    DTP: 15 months (R1), 4 years (R2).
    """

    # =================================================================
    # HELPERS
    # =================================================================

    def _schedule_penta_generic(self, dose_atual, data_base_anterior, dn, d1_data=None):
        """
        Calculates the date for the next Penta dose (2 or 3).
        dose_atual: The dose being scheduled (2 or 3).
        data_base_anterior: Date of the previous dose (D1 for D2, D2 for D3).
        d1_data: Required only to calculate D3 (the 4-month rule).
        """
        data_base = to_date(data_base_anterior)
        dn_data = to_date(dn)

        data_ideal = data_base + relativedelta(months=2)

        data_minima_base = data_base + relativedelta(days=30)

        # Dose 3-specific rules
        if dose_atual == 3:
            data_idade_6m = dn_data + relativedelta(months=6)

            if d1_data:
                data_hepb_4m = to_date(d1_data) + relativedelta(months=4)
            else:
                data_hepb_4m = data_minima_base

            data_minima_final = max(data_minima_base, data_idade_6m, data_hepb_4m)
            data_recomendada_final = max(data_ideal, data_idade_6m, data_hepb_4m)
        else:
            # Dose 2
            data_minima_final = data_minima_base
            data_recomendada_final = data_ideal

        self.declare(AgendamentoFuturo(
            vacina="Penta",
            dose=dose_atual,
            data_minima=data_minima_final,
            data_recomendada=data_recomendada_final,
            explicacao=f"Agendamento da {dose_atual}ª dose da Penta (respeitando intervalos e idade mínima)."
        ))

    def _schedule_dtp_generic(self, dose_reforco, data_base_anterior, dn, idade_alvo_anos=None, idade_alvo_meses=None):
        """Calculates DTP boosters."""
        data_base = to_date(data_base_anterior)
        dn_data = to_date(dn)

        data_min_intervalo = data_base + relativedelta(months=6)

        if idade_alvo_anos:
            data_idade = dn_data + relativedelta(years=idade_alvo_anos)
        elif idade_alvo_meses:
            data_idade = dn_data + relativedelta(months=idade_alvo_meses)
        else:
            data_idade = data_min_intervalo

        data_final = max(data_idade, data_min_intervalo)

        self.declare(AgendamentoFuturo(
            vacina="DTP (Tríplice Bacteriana)",
            dose=dose_reforco,
            data_minima=data_final,
            data_recomendada=data_final,
            explicacao=f"Agendamento do {dose_reforco} DTP (respeitando idade e intervalo de 6 meses)."
        ))

    # =================================================================
    # PENTA - DOSE 1
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn),
        TEST(lambda m: m < 2),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=1))
    )
    def rule_penta_dose_1_schedule(self, dn):
        dn_data = to_date(dn)
        data_agendada = dn_data + relativedelta(months=2)

        self.declare(AgendamentoFuturo(
            vacina="Penta",
            dose=1,
            data_minima=data_agendada,
            data_recomendada=data_agendada,
            explicacao="Agendamento da 1ª dose da Penta aos 2 meses."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a < 7 and (a * 12 + m) >= 2),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=1))
    )
    def rule_penta_dose_1_recommend_now(self, m):
        self.declare(RecomendacaoImediata(
            vacina="Penta", dose=1,
            explicacao=f"Paciente com {m} meses. Penta 1ª dose recomendada."
        ))

    # =================================================================
    # PENTA - DOSE 2 (2 months after D1)
    # =================================================================

    # 1. Schedule (future)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 7),
        OR(
            DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Penta", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=2)),
        NOT(AgendamentoFuturo(vacina="Penta", dose=2)),
        TEST(lambda d1_data: datetime.date.today() < (to_date(d1_data) + relativedelta(months=2)))
    )
    def rule_penta_dose_2_schedule(self, d1_data, a):
        data_base = to_date(d1_data)
        self.declare(AgendamentoFuturo(
            vacina="Penta", dose=2,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="2ª dose Penta agendada para 2 meses após 1ª dose."
        ))

    # 2. Recommend now (routine or late)
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 7),
        DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=2)),
        TEST(lambda d1, dn:
            (
                (to_date(d1) >= (to_date(dn) + relativedelta(months=4))) and
                (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))
            )
            or
            (
                (datetime.date.today() >= (to_date(d1) + relativedelta(months=2)))
            )
        )
    )
    def rule_penta_dose_2_recommend_now(self):
        self.declare(RecomendacaoImediata(
            vacina="Penta", dose=2,
            explicacao="2ª dose da Penta recomendada (intervalo cumprido)."
        ))

    # =================================================================
    # PENTA - DOSE 3 (2 months after D2, >= 6 months of age, >= 4 months from D1)
    # =================================================================

    # Scenario 1: D2 applied -> Schedule D3
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 7),
        DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1),
        DoseAplicada(vacina_codigo='PENTA', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)),
        NOT(AgendamentoFuturo(vacina="Penta", dose=3)),
        TEST(lambda d2: datetime.date.today() < (to_date(d2) + relativedelta(months=2)))
    )
    def rule_penta_dose_3_schedule_after_dose(self, d2, d1, dn):
        self._schedule_penta_generic(3, d2, dn, d1_data=d1)

    # Scenario 2: D2 scheduled -> Project D3
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 7),
        DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1),
        AgendamentoFuturo(vacina="Penta", dose=2, data_recomendada=MATCH.d2_prevista),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=2)),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)),
        NOT(AgendamentoFuturo(vacina="Penta", dose=3))
    )
    def rule_penta_dose_3_schedule_after_scheduled(self, d2_prevista, d1, dn):
        self._schedule_penta_generic(3, d2_prevista, dn, d1_data=d1)

    # Scenario 3: D2 recommended now -> Project D3
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 7),
        DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1),
        RecomendacaoImediata(vacina="Penta", dose=2),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=2)),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)),
        NOT(AgendamentoFuturo(vacina="Penta", dose=3))
    )
    def rule_penta_dose_3_schedule_after_recommendation(self, d1, dn):
        # Assume application today
        self._schedule_penta_generic(3, datetime.date.today(), dn, d1_data=d1)

    # Recommend D3 now
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 7),
        DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1),
        DoseAplicada(vacina_codigo='PENTA', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)),
        TEST(lambda d1, d2, dn:
            (
                # Check age >= 6 months
                (datetime.date.today() >= (to_date(dn) + relativedelta(months=6))) and
                # Check D1-D3 interval >= 4 months
                (datetime.date.today() >= (to_date(d1) + relativedelta(months=4))) and
                # Check D2-D3 interval (30d catch-up or 60d routine)
                (
                   ((to_date(d2) >= (to_date(dn) + relativedelta(months=6))) and (datetime.date.today() >= (to_date(d2) + relativedelta(days=30))))
                   or
                   (datetime.date.today() >= (to_date(d2) + relativedelta(months=2)))
                )
            )
        )
    )
    def rule_penta_dose_3_recommend_now(self):
        self.declare(RecomendacaoImediata(
            vacina="Penta", dose=3,
            explicacao="3ª dose Penta recomendada (Idade >= 6m, D1->D3 >= 4m, D2->D3 ok)."
        ))

    @Rule(DoseAplicada(vacina_codigo='PENTA', dose=3, data_aplicacao=MATCH.d3))
    def rule_penta_scheme_complete(self, d3):
        self.declare(EsquemaCompleto(vacina="Penta", explicacao="Esquema primário completo.", data_ultima_dose=to_date(d3)))

    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a >= 7), NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)))
    def contraindicated_penta_age(self):
        self.declare(Contraindicacao(vacina="Penta", dose="Todas", motivo="Idade >= 7 anos.", explicacao="Penta contraindicada > 7 anos."))

    # =================================================================
    # DTP - 1ST BOOSTER (15 Months)
    # =================================================================

    # Scenario 1: D3 applied -> Schedule R1
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 15),
        DoseAplicada(vacina_codigo='PENTA', dose=3, data_aplicacao=MATCH.d3),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=1)),
        NOT(AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="1º Reforço"))
    )
    def rule_dtp_booster_1_schedule_after_dose(self, d3, dn):
        data_alvo = max(to_date(dn) + relativedelta(months=15), to_date(d3) + relativedelta(months=6))
        if datetime.date.today() < data_alvo:
            self._schedule_dtp_generic("1º Reforço", d3, dn, idade_alvo_meses=15)

    # Scenario 2: D3 scheduled/recommended -> Project R1
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        OR(
            AgendamentoFuturo(vacina="Penta", dose=3, data_recomendada=MATCH.d3_prevista),
            RecomendacaoImediata(vacina="Penta", dose=3)
        ),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=1)),
        NOT(AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="1º Reforço"))
    )
    def rule_dtp_booster_1_project(self, dn, d3_prevista=None):
        data_base = d3_prevista if d3_prevista else datetime.date.today()
        self._schedule_dtp_generic("1º Reforço", data_base, dn, idade_alvo_meses=15)

    # Recommend R1 now
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        DoseAplicada(vacina_codigo='PENTA', dose=3, data_aplicacao=MATCH.d3),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=1)),
        TEST(lambda a, m, d3:
            (a < 7) and
            (a * 12 + m >= 15) and
            (datetime.date.today() >= (to_date(d3) + relativedelta(months=6)))
        )
    )
    def rule_dtp_booster_1_recommend(self):
        self.declare(RecomendacaoImediata(
            vacina="DTP (Tríplice Bacteriana)", dose="1º Reforço",
            explicacao="1º Reforço DTP recomendado (Idade >= 15m, Intervalo 6m da Penta D3)."
        ))

    # =================================================================
    # DTP - 2ND BOOSTER (4 Years)
    # =================================================================

    # Scenario 1: R1 applied -> Schedule R2
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 4),
        DoseAplicada(vacina_codigo='DTP', dose=1, data_aplicacao=MATCH.r1),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=2)),
        NOT(AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="2º Reforço"))
    )
    def rule_dtp_booster_2_schedule_after_dose(self, r1, dn):
        data_alvo = max(to_date(dn) + relativedelta(years=4), to_date(r1) + relativedelta(months=6))
        if datetime.date.today() < data_alvo:
            self._schedule_dtp_generic("2º Reforço", r1, dn, idade_alvo_anos=4)

    # Scenario 2: R1 scheduled/recommended -> Project R2
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        OR(
            AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="1º Reforço", data_recomendada=MATCH.r1_prevista),
            RecomendacaoImediata(vacina="DTP (Tríplice Bacteriana)", dose="1º Reforço")
        ),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=1)),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=2)),
        NOT(AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="2º Reforço"))
    )
    def rule_dtp_booster_2_project(self, dn, r1_prevista=None):
        data_base = r1_prevista if r1_prevista else datetime.date.today()
        self._schedule_dtp_generic("2º Reforço", data_base, dn, idade_alvo_anos=4)

    # Recommend R2 now
    @Rule(
        Idade(anos=MATCH.a),
        DoseAplicada(vacina_codigo='DTP', dose=1, data_aplicacao=MATCH.r1),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=2)),
        TEST(lambda a, r1:
            (a >= 4 and a < 7) and
            (datetime.date.today() >= (to_date(r1) + relativedelta(months=6)))
        )
    )
    def rule_dtp_booster_2_recommend(self):
        self.declare(RecomendacaoImediata(
            vacina="DTP (Tríplice Bacteriana)", dose="2º Reforço",
            explicacao="2º Reforço DTP recomendado (Idade >= 4 anos, Intervalo 6m do R1)."
        ))

    # =================================================================
    # EXCEPTION AT AGE 6 (Missed opportunity for R2)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a == 6),
        DoseAplicada(vacina_codigo='DTP', dose=1, data_aplicacao=MATCH.r1),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=2)),
        TEST(lambda dn, r1: (to_date(r1) + relativedelta(months=6)) >= (to_date(dn) + relativedelta(years=7)))
    )
    def rule_dtp_missed_booster_2(self, r1):
        dt_data = to_date(r1) + relativedelta(years=10)
        self.declare(AgendamentoFuturo(
            vacina="dT (Dupla Adulto)", dose="Reforço",
            data_minima=dt_data, data_recomendada=dt_data,
            explicacao="R2 da DTP suspenso por idade (perda de oportunidade). Agendado reforço dT para 10 anos após R1."
        ))
        self.declare(EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)", explicacao="Esquema encerrado (R2 dispensado por idade).", data_ultima_dose=to_date(r1)))

    @Rule(DoseAplicada(vacina_codigo='DTP', dose=2, data_aplicacao=MATCH.r2))
    def rule_dtp_scheme_complete(self, r2):
        self.declare(EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)", explicacao="Esquema de reforços completo.", data_ultima_dose=to_date(r2)))

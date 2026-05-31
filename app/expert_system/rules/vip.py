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

class RegrasVip(_RegrasBase):
    """
    Vaccination rules for Poliomyelitis (VIP) - PNI.
    Schedule: 2, 4, 6 months (D1, D2, D3).
    Booster: 15 months.
    """

    # =================================================================
    # SCHEDULING HELPERS
    # =================================================================

    def _schedule_generic_dose(self, dose_num, data_base, meses_intervalo, motivo):
        """Schedules a future dose based on an interval."""
        data_base_date = to_date(data_base)
        data_ideal = data_base_date + relativedelta(months=meses_intervalo)

        # Minimum interval is generally 30 days for D1->D2->D3
        # For D3->Booster it is 6 months.
        if meses_intervalo == 6:
             data_minima = data_base_date + relativedelta(months=6)
        else:
             data_minima = data_base_date + relativedelta(days=30)

        self.declare(AgendamentoFuturo(
            vacina="VIP (Poliomielite)",
            dose=dose_num,
            data_minima=data_minima,
            data_recomendada=data_ideal,
            explicacao=motivo
        ))

    def _schedule_booster_logic(self, d3_data, dn):
        """Booster logic: MAX(15 months, D3 + 6 months)"""
        d3_resolvida = to_date(d3_data)
        dn_data = to_date(dn)

        data_15_meses = dn_data + relativedelta(months=15)
        data_intervalo_d3 = d3_resolvida + relativedelta(months=6)

        data_final = max(data_15_meses, data_intervalo_d3)

        self.declare(AgendamentoFuturo(
            vacina="VIP (Poliomielite)",
            dose="Reforço",
            data_minima=data_final,
            data_recomendada=data_final,
            explicacao="Reforço projetado para 15 meses ou 6 meses após a 3ª dose."
        ))

    # =================================================================
    # DOSE 1
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, data_nascimento=MATCH.dn),
        TEST(lambda m: m < 2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=1))
    )
    def rule_vip_dose_1_schedule(self, dn):
        dn_data = to_date(dn)
        data_agendada = dn_data + relativedelta(months=2)

        self.declare(AgendamentoFuturo(
            vacina="VIP (Poliomielite)",
            dose=1,
            data_minima=data_agendada,
            data_recomendada=data_agendada,
            explicacao="Agendamento da 1ª dose aos 2 meses."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a < 5 and (a * 12 + m) >= 2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=1))
    )
    def rule_vip_dose_1_recommend_now(self, m):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose=1,
            explicacao=f"Paciente com {m} meses sem vacina. Recomendada 1ª dose imediata."
        ))

    # =================================================================
    # DOSE 2 (2 months after D1)
    # =================================================================

    # Schedule D2 (future)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        OR(
            DoseAplicada(vacina_codigo='VIP', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=2)),
        TEST(lambda d1_data: datetime.date.today() < (to_date(d1_data) + relativedelta(months=2)))
    )
    def rule_vip_dose_2_schedule(self, d1_data):
        self._schedule_generic_dose(2, d1_data, 2, "2ª dose agendada para 2 meses após 1ª dose.")

    # Recommend D2 now (prioritizing routine)
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        TEST(lambda d1, dn:
            (
                # SITUATION 1: Late start (D1 given after 4 months of age)
                # Allows minimum 30-day interval for catch-up
                (to_date(d1) >= (to_date(dn) + relativedelta(months=4))) and
                (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))
            )
            or
            (
                # SITUATION 2: Routine (D1 given at the right age)
                # Requires ideal 2-month (60-day) interval
                (datetime.date.today() >= (to_date(d1) + relativedelta(months=2)))
            )
        )
    )
    def rule_vip_dose_2_recommend_now(self):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose=2,
            explicacao="2ª dose da VIP recomendada (intervalo adequado cumprido)."
        ))

    # =================================================================
    # DOSE 3 (2 months after D2)
    # =================================================================

    # Scenario 1: D2 applied -> Schedule D3
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3)),
        TEST(lambda d2: datetime.date.today() < (to_date(d2) + relativedelta(months=2)))
    )
    def rule_vip_dose_3_schedule_after_dose(self, d2):
        self._schedule_generic_dose(3, d2, 2, "3ª dose agendada para 2 meses após 2ª dose.")

    # Scenario 2: D2 scheduled -> Project D3
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=2, data_recomendada=MATCH.d2_prevista),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3))
    )
    def rule_vip_dose_3_schedule_after_scheduled(self, d2_prevista):
        self._schedule_generic_dose(3, d2_prevista, 2, "3ª dose projetada para 2 meses após 2ª dose.")

    # Scenario 3: D2 recommended now -> Project D3 from today
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        RecomendacaoImediata(vacina="VIP (Poliomielite)", dose=2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3))
    )
    def rule_vip_dose_3_schedule_after_recommendation(self):
        self._schedule_generic_dose(3, datetime.date.today(), 2, "3ª dose projetada para 2 meses após a 2ª dose (considerando aplicação hoje).")

    # Recommend D3 now (prioritizing routine)
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        TEST(lambda d2, dn:
            (
                # SITUATION 1: Accumulated delay (D2 given after 6 months of age)
                # Allows minimum 30-day interval for catch-up
                (to_date(d2) >= (to_date(dn) + relativedelta(months=6))) and
                (datetime.date.today() >= (to_date(d2) + relativedelta(days=30)))
            )
            or
            (
                # SITUATION 2: Routine
                # Requires ideal 2-month (60-day) interval
                (datetime.date.today() >= (to_date(d2) + relativedelta(months=2)))
            )
        )
    )
    def rule_vip_dose_3_recommend_now(self):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose=3,
            explicacao="3ª dose da VIP recomendada (intervalo adequado cumprido)."
        ))

    # =================================================================
    # BOOSTER - 15 Months
    # =================================================================

    # Scenario 1: D3 applied
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=3, data_aplicacao=MATCH.d3),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço")),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose="Reforço")),
        NOT(RecomendacaoImediata(vacina="VIP (Poliomielite)", dose="Reforço"))
    )
    def rule_vip_booster_after_dose(self, d3, dn):
        # Check if the target date is still in the future.
        d3_date = to_date(d3)
        dn_date = to_date(dn)
        data_alvo = max(dn_date + relativedelta(months=15), d3_date + relativedelta(months=6))

        if datetime.date.today() < data_alvo:
            self._schedule_booster_logic(d3, dn)

    # Scenario 2: D3 scheduled
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3, data_recomendada=MATCH.d3_prevista),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço")),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose="Reforço"))
    )
    def rule_vip_booster_after_scheduled(self, d3_prevista, dn):
        self._schedule_booster_logic(d3_prevista, dn)

    # Scenario 3: D3 recommended now
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        RecomendacaoImediata(vacina="VIP (Poliomielite)", dose=3),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço")),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose="Reforço"))
    )
    def rule_vip_booster_after_recommendation(self, dn):
        self._schedule_booster_logic(datetime.date.today(), dn)

    # Recommend booster now
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        DoseAplicada(vacina_codigo='VIP', dose=3, data_aplicacao=MATCH.d3),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço")),
        TEST(lambda a, m, d3:
            (a < 5) and
            (a * 12 + m >= 15) and
            (datetime.date.today() >= (to_date(d3) + relativedelta(months=6)))
        )
    )
    def rule_vip_booster_recommend_now(self):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose="Reforço",
            explicacao="Reforço recomendado: Idade >= 15 meses e intervalo de 6 meses da 3ª dose cumprido."
        ))

    # =================================================================
    # CONCLUSION
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço"))
    )
    def contraindicated_vip_age(self):
        self.declare(Contraindicacao(
            vacina="VIP (Poliomielite)",
            dose="Todas",
            motivo="Idade superior a 4 anos, 11 meses e 29 dias.",
            explicacao="O esquema infantil da VIP é recomendado apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='VIP', dose="Reforço", data_aplicacao=MATCH.d4_data)
    )
    def rule_vip_scheme_complete(self, d4_data):
        self.declare(EsquemaCompleto(
            vacina="VIP (Poliomielite)",
            explicacao="Esquema completo (3 doses + 1 reforço).",
            data_ultima_dose=to_date(d4_data)
        ))

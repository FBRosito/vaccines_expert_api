import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

# --- FUNÇÃO AUXILIAR ---
def to_date(d):
    """Converte datetime para date se necessário."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RegrasVip(_RegrasBase):
    """
    Regras de vacinação para a Poliomielite (VIP) - PNI.
    Esquema: 2, 4, 6 meses (D1, D2, D3).
    Reforço: 15 meses.
    """

    # =================================================================
    # AUXILIARES DE LÓGICA
    # =================================================================

    def _agendar_dose_generica(self, dose_num, data_base, meses_intervalo, motivo):
        """Agenda uma dose futura baseada em intervalo."""
        data_base_date = to_date(data_base)
        data_ideal = data_base_date + relativedelta(months=meses_intervalo)
        
        # Intervalo mínimo geralmente é 30 dias para D1->D2->D3
        # Para D3->Reforço é 6 meses.
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

    def _agendar_reforco_logica(self, d3_data, dn):
        """Lógica do Reforço: MAX(15 meses, D3 + 6 meses)"""
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
    def regra_vip_d1_agendar(self, dn):
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
    def regra_vip_d1_recomendar_agora(self, m):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose=1,
            explicacao=f"Paciente com {m} meses sem vacina. Recomendada 1ª dose imediata."
        ))

    # =================================================================
    # DOSE 2 (2 meses após D1)
    # =================================================================

    # Agendar D2 (Futuro)
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
    def regra_vip_d2_agendar(self, d1_data):
        self._agendar_dose_generica(2, d1_data, 2, "2ª dose agendada para 2 meses após 1ª dose.")

    # Recomendar D2 (Agora - Priorizando Rotina)
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        TEST(lambda d1, dn: 
            (
                # SITUAÇÃO 1: Início Tardio (D1 tomada após 4 meses de idade)
                # Permite intervalo mínimo de 30 dias para catch-up
                (to_date(d1) >= (to_date(dn) + relativedelta(months=4))) and 
                (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))
            )
            or
            (
                # SITUAÇÃO 2: Rotina (D1 tomada na idade certa)
                # Exige intervalo ideal de 2 meses (60 dias)
                (datetime.date.today() >= (to_date(d1) + relativedelta(months=2)))
            )
        )
    )
    def regra_vip_d2_recomendar_agora(self):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose=2,
            explicacao="2ª dose da VIP recomendada (intervalo adequado cumprido)."
        ))

    # =================================================================
    # DOSE 3 (2 meses após D2)
    # =================================================================

    # Cenário 1: D2 Aplicada -> Agendar D3
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3)),
        TEST(lambda d2: datetime.date.today() < (to_date(d2) + relativedelta(months=2)))
    )
    def regra_vip_d3_agendar_pos_dose(self, d2):
        self._agendar_dose_generica(3, d2, 2, "3ª dose agendada para 2 meses após 2ª dose.")

    # Cenário 2: D2 Agendada -> Projetar D3
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=2, data_recomendada=MATCH.d2_prevista),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3))
    )
    def regra_vip_d3_agendar_pos_agendamento(self, d2_prevista):
        self._agendar_dose_generica(3, d2_prevista, 2, "3ª dose projetada para 2 meses após 2ª dose.")

    # Cenário 3: D2 Recomendada Agora -> Projetar D3 a partir de hoje
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        RecomendacaoImediata(vacina="VIP (Poliomielite)", dose=2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3))
    )
    def regra_vip_d3_agendar_pos_recomendacao(self):
        self._agendar_dose_generica(3, datetime.date.today(), 2, "3ª dose projetada para 2 meses após a 2ª dose (considerando aplicação hoje).")

    # Recomendar D3 (Agora - Priorizando Rotina)
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        TEST(lambda d2, dn: 
            (
                # SITUAÇÃO 1: Atraso Acumulado (D2 tomada após 6 meses de idade)
                # Permite intervalo mínimo de 30 dias para catch-up
                (to_date(d2) >= (to_date(dn) + relativedelta(months=6))) and 
                (datetime.date.today() >= (to_date(d2) + relativedelta(days=30)))
            )
            or
            (
                # SITUAÇÃO 2: Rotina
                # Exige intervalo ideal de 2 meses (60 dias)
                (datetime.date.today() >= (to_date(d2) + relativedelta(months=2)))
            )
        )
    )
    def regra_vip_d3_recomendar_agora(self):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose=3,
            explicacao="3ª dose da VIP recomendada (intervalo adequado cumprido)."
        ))

    # =================================================================
    # REFORÇO - 15 Meses
    # =================================================================

    # Cenário 1: D3 Aplicada
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=3, data_aplicacao=MATCH.d3),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço")),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose="Reforço")),
        NOT(RecomendacaoImediata(vacina="VIP (Poliomielite)", dose="Reforço"))
    )
    def regra_vip_reforco_pos_dose(self, d3, dn):
        # Verifica se ainda é futuro.
        d3_date = to_date(d3)
        dn_date = to_date(dn)
        data_alvo = max(dn_date + relativedelta(months=15), d3_date + relativedelta(months=6))
        
        if datetime.date.today() < data_alvo:
            self._agendar_reforco_logica(d3, dn)

    # Cenário 2: D3 Agendada
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3, data_recomendada=MATCH.d3_prevista),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço")),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose="Reforço"))
    )
    def regra_vip_reforco_pos_agendamento(self, d3_prevista, dn):
        self._agendar_reforco_logica(d3_prevista, dn)

    # Cenário 3: D3 Recomendada Agora
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        RecomendacaoImediata(vacina="VIP (Poliomielite)", dose=3),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço")),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose="Reforço"))
    )
    def regra_vip_reforco_pos_recomendacao(self, dn):
        self._agendar_reforco_logica(datetime.date.today(), dn)

    # Recomendar Reforço (Agora)
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
    def regra_vip_reforco_recomendar_agora(self):
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose="Reforço",
            explicacao="Reforço recomendado: Idade >= 15 meses e intervalo de 6 meses da 3ª dose cumprido."
        ))

    # =================================================================
    # CONCLUSÃO
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5), 
        NOT(DoseAplicada(vacina_codigo='VIP', dose="Reforço"))
    )
    def contraindicacao_vip_idade(self):
        self.declare(Contraindicacao(
            vacina="VIP (Poliomielite)",
            dose="Todas",
            motivo="Idade superior a 4 anos, 11 meses e 29 dias.",
            explicacao="O esquema infantil da VIP é recomendado apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='VIP', dose="Reforço", data_aplicacao=MATCH.d4_data)
    )
    def regra_vip_esquema_completo(self, d4_data):
        self.declare(EsquemaCompleto(
            vacina="VIP (Poliomielite)",
            explicacao="Esquema completo (3 doses + 1 reforço).",
            data_ultima_dose=to_date(d4_data)
        ))
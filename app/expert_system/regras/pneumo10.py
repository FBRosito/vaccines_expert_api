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

class RegrasPneumo10(_RegrasBase):
    """
    Regras para a Pneumocócica 10V.
    """

    # =================================================================
    # ESQUEMA PRIMÁRIO (D1)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, data_nascimento=MATCH.dn), 
        TEST(lambda m: m < 2), 
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=1))
    )
    def regra_pneumo10_d1_agendar(self, dn):
        dn_data = to_date(dn)
        data_agendada = dn_data + relativedelta(months=2)
        
        self.declare(AgendamentoFuturo(
            vacina="Pneumocócica 10V",
            dose=1,
            data_minima=data_agendada,
            data_recomendada=data_agendada,
            explicacao="Agendamento da 1ª dose, recomendada aos 2 meses de idade."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a == 0 and m >= 2), 
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=1))
    )
    def regra_pneumo10_d1_recomendar_agora_menor1ano(self, m):
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V", dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da vacina Pneumocócica 10V é recomendada aos 2 meses."
        ))

    # =================================================================
    # ESQUEMA PRIMÁRIO (D2)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        OR(
            DoseAplicada(vacina_codigo='PNEUMO10', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Pneumocócica 10V", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=2)),
        NOT(AgendamentoFuturo(vacina="Pneumocócica 10V", dose=2)),
        TEST(lambda d1_data: 
            datetime.date.today() < (to_date(d1_data) + relativedelta(months=2))
        )
    )
    def regra_pneumo10_d2_agendar(self, d1_data):
        data_base = to_date(d1_data)
        
        self.declare(AgendamentoFuturo(
            vacina="Pneumocócica 10V", dose=2,
            data_minima=data_base + relativedelta(days=30), 
            data_recomendada=data_base + relativedelta(months=2), 
            explicacao="A 2ª dose é agendada para 2 meses após a 1ª dose."
        ))
    
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='PNEUMO10', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=2)),
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
    def regra_pneumo10_d2_recomendar_agora_atrasada(self):
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V", dose=2,
            explicacao="A 2ª dose da Pneumocócica 10V está recomendada (intervalo cumprido)."
        ))

    # =================================================================
    # REFORÇO (D3) - LÓGICA COMPLETA
    # =================================================================

    def _agendar_reforco_generico(self, d2_data, dn):
        """Calcula reforço: Max(12 meses, D2 + 60 dias)"""
        d2_resolvida = to_date(d2_data)
        dn_data = to_date(dn)
        
        data_12_meses = dn_data + relativedelta(months=12)
        data_intervalo_d2 = d2_resolvida + relativedelta(months=2)
        data_final = max(data_12_meses, data_intervalo_d2)
        
        self.declare(AgendamentoFuturo(
            vacina="Pneumocócica 10V",
            dose="Reforço",
            data_minima=data_final,
            data_recomendada=data_final,
            explicacao="Reforço projetado para completá-lo até 12 meses de idade, ou 60 dias após a 2ª dose."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='PNEUMO10', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3)),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose="Reforço")),
        NOT(AgendamentoFuturo(vacina="Pneumocócica 10V", dose="Reforço"))
    )
    def regra_pneumo10_reforco_pos_dose_aplicada(self, d2, dn):
        self._agendar_reforco_generico(d2, dn)

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        AgendamentoFuturo(vacina="Pneumocócica 10V", dose=2, data_recomendada=MATCH.d2_prevista),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=2)), 
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3)),
        NOT(AgendamentoFuturo(vacina="Pneumocócica 10V", dose="Reforço"))
    )
    def regra_pneumo10_reforco_pos_agendamento(self, d2_prevista, dn):
        self._agendar_reforco_generico(d2_prevista, dn)

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        RecomendacaoImediata(vacina="Pneumocócica 10V", dose=2),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=2)),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3)),
        NOT(AgendamentoFuturo(vacina="Pneumocócica 10V", dose="Reforço"))
    )
    def regra_pneumo10_reforco_pos_recomendacao_d2(self, dn):
        self._agendar_reforco_generico(datetime.date.today(), dn)

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        DoseAplicada(vacina_codigo='PNEUMO10', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3)),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose="Reforço")),
        TEST(lambda a, m, d2:
            (a >= 1) and 
            (datetime.date.today() >= (to_date(d2) + relativedelta(months=2)))
        )
    )
    def regra_pneumo10_reforco_aplicar_agora(self):
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V", dose="Reforço", 
            explicacao="Reforço recomendado: Criança maior que 1 ano com intervalo de 60 dias da 2ª dose cumprido."
        ))

    # =================================================================
    # CATCH-UP & CONCLUSÃO
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10')),
        NOT(AgendamentoFuturo(vacina="Pneumocócica 10V"))
    )
    def regra_pneumo10_catchup_dose_unica(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V", dose="Única",
            explicacao=f"Para crianças com {a} anos sem comprovação vacinal, recomenda-se dose única."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3)),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose="Única"))
    )
    def regra_pneumo10_contraindicacao_idade(self):
        self.declare(Contraindicacao(
            vacina="Pneumocócica 10V", dose="Todas",
            motivo="Idade superior à permitida.",
            explicacao="A vacina Pneumo10 na rotina do PNI é recomendada apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        OR(
            DoseAplicada(vacina_codigo='PNEUMO10', dose=3, data_aplicacao=MATCH.data_dose),
            DoseAplicada(vacina_codigo='PNEUMO10', dose="Reforço", data_aplicacao=MATCH.data_dose),
            DoseAplicada(vacina_codigo='PNEUMO10', dose="Única", data_aplicacao=MATCH.data_dose)
        )
    )
    def regra_pneumo10_esquema_completo(self, data_dose):
        self.declare(EsquemaCompleto(
            vacina="Pneumocócica 10V",
            explicacao="Esquema de vacinação da Pneumocócica 10V finalizado.",
            data_ultima_dose=to_date(data_dose)
        ))
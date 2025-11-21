import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasHepatiteB(_RegrasBase):
    """
    Regras para Hepatite B (ao nascer e esquema de catch-up >= 7 anos).
    O esquema primário infantil é coberto pela Penta.
    """

    # =================================================================
    # ESQUEMA AO NASCER (0-30 DIAS)
    # =================================================================

    @Rule(Idade(dias=MATCH.d), TEST(lambda d: d <= 30), NOT(DoseAplicada(vacina_codigo='HEPATITE_B')))
    def regra_hep_b_ao_nascer_pendente(self):
        self.declare(RecomendacaoImediata(
            vacina="Hepatite B (ao nascer)",
            dose="Única",
            explicacao="Dose única recomendada nas primeiras 24h de vida (preferencialmente 12h), podendo ser administrada até 30 dias após o nascimento."
        ))

    @Rule(DoseAplicada(vacina_codigo='HEPATITE_B', data_aplicacao=MATCH.data_dose))
    def regra_hep_b_ao_nascer_ok(self, data_dose):
        self.declare(EsquemaCompleto(
            vacina="Hepatite B (ao nascer)",
            explicacao="Dose ao nascer aplicada corretamente, conforme registro.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

    @Rule(Idade(dias=MATCH.d), TEST(lambda d: d > 30), NOT(DoseAplicada(vacina_codigo='HEPATITE_B')))
    def regra_hep_b_ao_nascer_contraindicacao_idade(self):
        self.declare(Contraindicacao(
            vacina="Hepatite B (ao nascer)",
            dose="Única",
            motivo="Idade superior a 30 dias.",
            explicacao="A dose monovalente da Hepatite B é recomendada apenas para os primeiros 30 dias de vida."
        ))

    # =================================================================
    # ESQUEMA ADULTO (>= 7 ANOS)
    # =================================================================
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B')),
        NOT(DoseAplicada(vacina_codigo='PENTA')),
        NOT(EsquemaCompleto(vacina="Hepatite B (esquema adulto)"))
    )
    def regra_hep_b_maior7_recomendar_agora(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Hepatite B (esquema adulto)",
            dose=1,
            explicacao=f"Paciente com {a} anos sem comprovação vacinal. Iniciar esquema de 3 doses (0, 1 e 6 meses)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=2)),
        NOT(EsquemaCompleto(vacina="Hepatite B (esquema adulto)"))
    )
    def regra_hep_b_maior7_agendar_d2(self, d1):
        d1_data = d1.date() if isinstance(d1, datetime.datetime) else d1
        
        data_min = d1_data + relativedelta(weeks=4)
        data_rec = d1_data + relativedelta(days=30)
        hoje = datetime.date.today()

        if data_rec > hoje:
            self.declare(AgendamentoFuturo(
                vacina="Hepatite B (esquema adulto)",
                dose=2,
                data_minima=data_min,
                data_recomendada=data_rec,
                explicacao="A 2ª dose é recomendada 30 dias após a primeira (mínimo de 4 semanas)."
            ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(weeks=4))),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=2)),
        NOT(EsquemaCompleto(vacina="Hepatite B (esquema adulto)"))
    )
    def regra_hep_b_maior7_d2_recomendar_atrasada(self):
        self.declare(RecomendacaoImediata(
            vacina="Hepatite B (esquema adulto)",
            dose=2,
            explicacao="A 2ª dose da Hepatite B está atrasada. Aplicar agora (intervalo mínimo de 4 semanas respeitado)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=1, data_aplicacao=MATCH.d1),
        OR(
            'd2_ap' << DoseAplicada(vacina_codigo='HEPATITE_B', dose=2),
            'd2_ag' << AgendamentoFuturo(vacina="Hepatite B (esquema adulto)", dose=2),
            'd2_rec' << RecomendacaoImediata(vacina="Hepatite B (esquema adulto)", dose=2)
        ),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=3)),
        NOT(AgendamentoFuturo(vacina="Hepatite B (esquema adulto)", dose=3)),
        NOT(EsquemaCompleto(vacina="Hepatite B (esquema adulto)"))
    )
    def regra_hep_b_maior7_agendar_d3_completo(self, d1, d2_ap=None, d2_ag=None, d2_rec=None):
        """
        (Agendamento) D3: Ideal 6 meses após D1.
        Baseia-se na D2 (Real, Planejada ou Recomendada Agora).
        """
        d1_data = d1.date() if isinstance(d1, datetime.datetime) else d1
        hoje = datetime.date.today()

        if d2_ap:
            val = d2_ap['data_aplicacao']
            d2_base = val.date() if isinstance(val, datetime.datetime) else val
        elif d2_ag:
            d2_base = d2_ag['data_recomendada']
        elif d2_rec:
            d2_base = hoje
        else:
            return

        # 1. Calcula os mínimos obrigatórios
        min_apos_d1 = d1_data + relativedelta(weeks=16)
        min_apos_d2 = d2_base + relativedelta(weeks=8)
        data_minima_final = max(min_apos_d1, min_apos_d2)

        # 2. Calcula a data ideal (recomendada)
        data_ideal = d1_data + relativedelta(months=6)

        # 3. Lógica de priorização (Ideal vs Mínimo)
        data_recomendada_final = max(data_ideal, data_minima_final)

        if data_recomendada_final > hoje:
            self.declare(AgendamentoFuturo(
                vacina="Hepatite B (esquema adulto)",
                dose=3,
                data_minima=data_minima_final,
                data_recomendada=data_recomendada_final,
                explicacao="Agendamento da 3ª dose (conclusão do esquema 0-1-6). Data respeita o prazo ideal de 6 meses após a 1ª dose e o intervalo mínimo de segurança de 8 semanas após a 2ª dose."
            ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=1, data_aplicacao=MATCH.d1),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=2, data_aplicacao=MATCH.d2),
        TEST(lambda d1, d2: 
             datetime.date.today() >= ((d2.date() if isinstance(d2, datetime.datetime) else d2) + relativedelta(weeks=8)) and
             datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(weeks=16))
        ),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=3)),
        NOT(EsquemaCompleto(vacina="Hepatite B (esquema adulto)"))
    )
    def regra_hep_b_maior7_d3_recomendar_atrasada(self):
        self.declare(RecomendacaoImediata(
            vacina="Hepatite B (esquema adulto)",
            dose=3,
            explicacao="A 3ª dose da Hepatite B está atrasada. Aplicar agora (todos os intervalos mínimos respeitados)."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=3, data_aplicacao=MATCH.d3_data)
    )
    def regra_hep_b_maior7_esquema_ok(self, d3_data):
        self.declare(EsquemaCompleto(
            vacina="Hepatite B (esquema adulto)",
            explicacao="Esquema de 3 doses para Hepatite B finalizado.",
            data_ultima_dose=d3_data.date() if isinstance(d3_data, datetime.datetime) else d3_data
        ))
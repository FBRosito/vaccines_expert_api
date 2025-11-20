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
        """
        (Recomendação) Para crianças <= 30 dias, recomenda a
        dose monovalente ao nascer.
        """
        self.declare(RecomendacaoImediata(
            vacina="Hepatite B (ao nascer)",
            dose="Única",
            explicacao="Dose única recomendada nas primeiras 24h de vida (preferencialmente 12h), podendo ser administrada até 30 dias após o nascimento."
        ))

    @Rule(DoseAplicada(vacina_codigo='HEPATITE_B', data_aplicacao=MATCH.data_dose))
    def regra_hep_b_ao_nascer_ok(self, data_dose):
        """
        (Esquema Completo) Considera a dose ao nascer como um
        esquema completo (para fins dessa dose específica).
        """
        self.declare(EsquemaCompleto(
            vacina="Hepatite B (ao nascer)",
            explicacao="Dose ao nascer aplicada corretamente, conforme registro.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

    @Rule(Idade(dias=MATCH.d), TEST(lambda d: d > 30), NOT(DoseAplicada(vacina_codigo='HEPATITE_B')))
    def regra_hep_b_ao_nascer_contraindicacao_idade(self):
        """
        (Contraindicação) Para crianças > 30 dias, contraindica a dose monovalente ao nascer.
        """
        self.declare(Contraindicacao(
            vacina="Hepatite B (ao nascer)",
            dose="Única",
            motivo="Idade superior a 30 dias.",
            explicacao="A dose monovalente da Hepatite B é recomendada apenas para os primeiros 30 dias de vida. Após essa idade, a proteção é conferida pelo esquema da vacina Penta."
        ))

    # =================================================================
    # ESQUEMA ADULTO (>= 7 ANOS)
    # =================================================================
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B')),
        NOT(DoseAplicada(vacina_codigo='PENTA'))
    )
    def regra_hep_b_maior7_recomendar_agora(self, a):
        """
        (Recomendação) Início do esquema 0, 1, 6 meses.
        """
        self.declare(RecomendacaoImediata(
            vacina="Hepatite B (esquema adulto)",
            dose=1,
            explicacao=f"Paciente com {a} anos sem comprovação vacinal. Iniciar esquema de 3 doses (0, 1 e 6 meses)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=2))
    )
    def regra_hep_b_maior7_agendar_d2(self, d1):
        """
        (Agendamento) D2: Ideal 30 dias após D1. Mínimo 4 semanas.
        """
        d1_data = d1.date() if isinstance(d1, datetime.datetime) else d1
        self.declare(AgendamentoFuturo(
            vacina="Hepatite B (esquema adulto)",
            dose=2,
            data_minima=d1_data + relativedelta(weeks=4),
            data_recomendada=d1_data + relativedelta(days=30),
            explicacao="A 2ª dose é recomendada 30 dias após a primeira (mínimo de 4 semanas)."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(weeks=4))),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=2))
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
            DoseAplicada(vacina_codigo='HEPATITE_B', dose=2, data_aplicacao=MATCH.d2_date),
            AgendamentoFuturo(vacina="Hepatite B (esquema adulto)", dose=2, data_recomendada=MATCH.d2_date)
        ),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=3)),
        NOT(AgendamentoFuturo(vacina="Hepatite B (esquema adulto)", dose=3))
    )
    def regra_hep_b_maior7_agendar_d3(self, d1, d2_date):
        """
        (Agendamento) D3: Ideal 6 meses após D1.
        Mínimos: 8 semanas após D2 (aplicada ou planejada) E 16 semanas após D1.
        """
        d1_data = d1.date() if isinstance(d1, datetime.datetime) else d1
        d2_resolvida = d2_date.date() if isinstance(d2_date, datetime.datetime) else d2_date

        # 1. Calcula os mínimos obrigatórios
        min_apos_d1 = d1_data + relativedelta(weeks=16)
        min_apos_d2 = d2_resolvida + relativedelta(weeks=8)
        data_minima_final = max(min_apos_d1, min_apos_d2)

        # 2. Calcula a data ideal (recomendada)
        data_ideal = d1_data + relativedelta(months=6)

        # 3. Lógica de priorização (Ideal vs Mínimo)
        data_recomendada_final = max(data_ideal, data_minima_final)

        self.declare(AgendamentoFuturo(
            vacina="Hepatite B (esquema adulto)",
            dose=3,
            data_minima=data_minima_final,
            data_recomendada=data_recomendada_final,
            explicacao="A 3ª dose é recomendada 6 meses após a 1ª dose, respeitando intervalos mínimos de 8 semanas após 2ª dose e 16 semanas após a 1ª dose."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=1, data_aplicacao=MATCH.d1),
        DoseAplicada(vacina_codigo='HEPATITE_B', dose=2, data_aplicacao=MATCH.d2),
        TEST(lambda d1, d2: 
             datetime.date.today() >= ((d2.date() if isinstance(d2, datetime.datetime) else d2) + relativedelta(weeks=8)) and
             datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(weeks=16))
        ),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_B', dose=3))
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
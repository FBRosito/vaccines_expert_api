import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo

class RegrasMeningo(_RegrasBase):
    """
    Regras de vacinação para Meningocócica C (infantil)
    e Meningocócica ACWY (adolescente).
    """

    # --- Vacina Meningocócica C ---
    @Rule(
        # Idade: >= 3 meses E < 12 meses (a == 0)
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a == 0 and m >= 3), 
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=1))
    )
    def regra_menc_d1_recomendar_agora_menor1ano(self, m):
        """
        Recomenda a D1 apenas para crianças de 3 a 11 meses
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da Meningocócica C é recomendada aos 3 meses."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1), 
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2))
    )
    def regra_menc_d2_agendar(self, d1):
        """
        Agenda a 2ª dose da Meningocócica C com base na data da 1ª dose.
        """
        self.declare(AgendamentoFuturo(
            vacina="Meningocócica C", dose=2,
            data_minima=(d1 + relativedelta(days=30)).isoformat(),
            data_recomendada=(d1 + relativedelta(months=2)).isoformat(),
            explicacao="A 2ª dose da Meningocócica C é agendada com intervalo recomendado de 60 dias (mínimo de 30 dias) após a 1ª dose."
        ))

    @Rule(
        # Criança com menos de 1 ano
        Idade(anos=MATCH.a), TEST(lambda a: a == 0),
        DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1),
        # Verifica se já passou o intervalo mínimo de 30 dias da D1
        TEST(lambda d1: (datetime.date.today() - d1.date()) >= relativedelta(days=30)),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2))
    )
    def regra_menc_d2_recomendar_agora_atrasada(self):
        """
        Recomenda a D2 (imediata) se a D1 foi dada, a D2 está atrasada 
        (>= 30 dias) e a criança ainda é menor de 12 meses.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", 
            dose=2,
            explicacao="A 2ª dose da Meningocócica C está atrasada. Aplicar agora (respeitado o intervalo mínimo de 30 dias da 1ª dose)."
        ))
    
    @Rule(
        # Requer que a D2 tenha sido aplicada
        DoseAplicada(vacina_codigo='MEN_C', dose=2, data_aplicacao=MATCH.d2), 
        Idade(meses=MATCH.m, anos=MATCH.a), 
        # Teste de idade E intervalo
        TEST(lambda a, m, d2:
            # Idade entre 12 meses e 4 anos 11m 29d
            (a < 5 and (a * 12 + m) >= 12) and
            # Intervalo mínimo de 60 dias após a D2
            ((datetime.date.today() - d2.date()) >= relativedelta(months=2))
        ), 
        # Reforço é a D3
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=3))
    )
    def regra_menc_reforco_recomendar_agora(self):
        """
        Recomenda o reforço da Meningocócica C a partir dos 12 meses, 
        respeitando o intervalo mínimo de 60 dias após a 2ª dose.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", 
            dose="Reforço", 
            explicacao="O reforço da Meningocócica C é recomendado a partir dos 12 meses, respeitando o intervalo mínimo de 60 dias da 2ª dose."
        ))

    @Rule(
        # Criança entre 1 e 4 anos (12m a 4a 11m 29d)
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        # Sem NENHUMA dose (Sem comprovação vacinal)
        NOT(DoseAplicada(vacina_codigo='MEN_C'))
    )
    def regra_menc_catchup_dose_unica(self, a):
        """
        Recomenda dose única para crianças de 1-4 anos sem a vacina.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C",
            dose="Única",
            explicacao=f"Para crianças com {a} anos sem comprovação vacinal, é recomendado a administração de dose única."
        ))

    @Rule(
        # Idade entre 12 meses e 4 anos 11m 29d
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a < 5 and (a * 12 + m) >= 12),
        
        # Comprovação de exatamente 1 dose
        DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2)),

        # Respeitar o intervalo mínimo de 60 dias da D1 (conforme P1)
        TEST(lambda d1: (datetime.date.today() - d1.date()) >= relativedelta(months=2))
    )
    def regra_menc_catchup_reforco_1dose(self):
        """
        Criança de 1-4 anos com apenas 1 dose recebe 1 dose de reforço
        (que funciona como D2), respeitando o intervalo de 60 dias.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C",
            dose="Reforço",
            explicacao="Criança com 1 dose prévia. Administrar dose de reforço (intervalo mínimo de 60 dias da dose anterior)."
        ))

    # --- Vacina Meningocócica ACWY ---
    @Rule(
        # Condição 1: Faixa etária de 11 a 14 anos
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11 and a < 15),
        
        # Condição 2: "Situação vacinal" -> Vacinado anteriormente com Meningo C
        # (Pressupõe que qualquer dose de MEN_C já conta como esquema prévio)
        DoseAplicada(vacina_codigo='MEN_C'),
        
        # Condição 3: Ainda não recebeu a MEN_ACWY
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_reforco_11a14_anos(self, a):
        """
        Recomenda a dose de reforço da ACWY para adolescentes de 11 a 14 anos
        que já possuem histórico vacinal da Meningocócica C.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Reforço",
            explicacao=f"Paciente com {a} anos e esquema prévio de Meningo C. Recomenda-se o reforço com Meningocócica ACWY."
        ))

    @Rule(
        # Condição 1: Faixa etária de 11 a 14 anos
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11 and a < 15),
        
        # Condição 2: "Situação vacinal" -> Sem histórico da Meningo C
        NOT(DoseAplicada(vacina_codigo='MEN_C')),
        
        # Condição 3: Ainda não recebeu a MEN_ACWY
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_dose_unica_11a14_anos(self, a):
        """
        Recomenda a dose única da ACWY para adolescentes de 11 a 14 anos
        sem histórico vacinal da Meningocócica C.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Única",
            explicacao=f"Paciente com {a} anos sem esquema prévio de Meningo C. Recomenda-se uma dose da vacina Meningocócica ACWY."
        ))
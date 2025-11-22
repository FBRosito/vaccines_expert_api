import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasMeningo(_RegrasBase):
    """
    Regras de vacinação para Meningocócica C (infantil)
    e Meningocócica ACWY (adolescente).
    """

    # =================================================================
    # MENINGOCÓCICA C - ESQUEMA PRIMÁRIO (3 E 5 MESES)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn), 
        TEST(lambda m: m < 3), 
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=1))
    )
    def regra_menc_d1_agendar(self, m, d, dn):
        """
        (Agendamento) Para crianças < 3 meses sem D1, agenda a
        primeira dose para a data exata dos 3 meses de idade.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
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
    def regra_menc_d1_recomendar_agora_menor1ano(self, m):
        """
        (Recomendação) Recomenda a D1 apenas para crianças
        de 3 a 11 meses.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da Meningocócica C é recomendada aos 3 meses."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a == 0),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Meningocócica C", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2)),
        NOT(AgendamentoFuturo(vacina="Meningocócica C", dose=2))
    )
    def regra_menc_d2_agendar(self, d1_data):
        """
        (Agendamento) Após D1, agenda D2.
        Define data mínima (30d) e recomendada (60d/2m).
        """
        data_base = d1_data.date() if isinstance(d1_data, datetime.datetime) else d1_data
        
        self.declare(AgendamentoFuturo(
            vacina="Meningocócica C", dose=2,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 2ª dose da Meningocócica C é agendada com intervalo recomendado de 60 dias (mínimo de 30 dias) após a 1ª dose."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a == 0),
        DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2))
    )
    def regra_menc_d2_recomendar_agora_atrasada(self):
        """
        (Recomendação) Recomenda a D2 (imediata) se a D1 foi dada, a D2 está atrasada 
        (>= 30 dias) e a criança ainda é menor de 12 meses.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", 
            dose=2,
            explicacao="A 2ª dose da Meningocócica C está atrasada. Aplicar agora (respeitado o intervalo mínimo de 30 dias da 1ª dose)."
        ))
    
    # =================================================================
    # MENINGOCÓCICA C - REFORÇO (12 MESES)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 12),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=2, data_aplicacao=MATCH.d2_data),
            AgendamentoFuturo(vacina="Meningocócica C", dose=2, data_recomendada=MATCH.d2_data)
        ),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=3)),
        NOT(AgendamentoFuturo(vacina="Meningocócica C", dose=3))
    )
    def regra_menc_reforco_agendar(self, d2_data, dn):
        """
        (Agendamento) Para < 12 meses com D2 (real ou planejada),
        agenda o reforço (D3) para a data ideal (12m) ou
        mínima (D2+60d), o que for mais tarde.
        """
        d2_resolvida = d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        
        data_rec_12m = dn_data + relativedelta(months=12)
        data_min_int = d2_resolvida + relativedelta(days=60)
        data_alvo = max(data_rec_12m, data_min_int)

        self.declare(AgendamentoFuturo(
            vacina="Meningocócica C",
            dose=3,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento do reforço da Men-C, recomendado aos 12 meses (respeitando o intervalo mínimo de 60 dias após a D2)."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='MEN_C', dose=2, data_aplicacao=MATCH.d2), 
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m, d2:
            (a < 5 and (a * 12 + m) >= 12) and
            (datetime.date.today() >= ((d2.date() if isinstance(d2, datetime.datetime) else d2) + relativedelta(months=2)))
        ), 
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=3))
    )
    def regra_menc_reforco_recomendar_agora(self):
        """
        (Recomendação) Recomenda o reforço da Meningocócica C a partir dos 12 meses, 
        respeitando o intervalo mínimo de 60 dias após a 2ª dose.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", 
            dose=3,
            explicacao="O reforço da Meningocócica C é recomendado a partir dos 12 meses, respeitando o intervalo mínimo de 60 dias da 2ª dose."
        ))

    # =================================================================
    # MENINGOCÓCICA C - CATCH-UP (1-4 ANOS)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        NOT(DoseAplicada(vacina_codigo='MEN_C'))
    )
    def regra_menc_catchup_dose_unica(self, a):
        """
        (Recomendação) Recomenda dose única para crianças de 1-4 anos sem a vacina.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C",
            dose="Única",
            explicacao=f"Para crianças com {a} anos sem comprovação vacinal, é recomendado a administração de dose única."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a < 5 and (a * 12 + m) >= 12),
        
        DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2)),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=3)),
        TEST(lambda d1: datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(months=2)))
    )
    def regra_menc_catchup_reforco_1dose(self):
        """
        (Recomendação) Criança de 1-4 anos com apenas 1 dose recebe 1 dose de reforço
        (que funciona como D2/Reforço), respeitando o intervalo de 60 dias.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C",
            dose=3,
            explicacao="Criança com 1 dose prévia. Administrar dose de reforço (intervalo mínimo de 60 dias da dose anterior)."
        ))

    # =================================================================
    # MENINGOCÓCICA C - CONCLUSÃO E CONTRAINDICAÇÃO
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=3)),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose="Única"))
    )
    def regra_menc_contraindicacao_idade(self):
        """
        (Contraindicação) Para crianças >= 5 anos sem esquema
        infantil completo, contraindica a Men-C.
        """
        self.declare(Contraindicacao(
            vacina="Meningocócica C",
            dose="Todas",
            motivo="Idade superior à permitida.",
            explicacao="O esquema infantil da Men-C é recomendado apenas até os 4 anos, 11 meses e 29 dias."
        ))
    
    @Rule(
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=3, data_aplicacao=MATCH.data_dose),
            DoseAplicada(vacina_codigo='MEN_C', dose="Única", data_aplicacao=MATCH.data_dose)
        )
    )
    def regra_menc_esquema_completo(self, data_dose):
        """
        (Esquema Completo) Finaliza o esquema da Men-C.
        """
        self.declare(EsquemaCompleto(
            vacina="Meningocócica C",
            explicacao="Esquema da Meningocócica C finalizado.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

    # =================================================================
    # MENINGOCÓCICA ACWY (ADOLESCENTE)
    # =================================================================
    
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 11),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY', dose=1))
    )
    def regra_menacwy_agendar(self, dn):
        """
        (Agendamento Proativo) Agenda a ACWY para o aniversário de 11 anos.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_alvo = dn_data + relativedelta(years=11)

        self.declare(AgendamentoFuturo(
            vacina="Meningocócica ACWY",
            dose=1,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da dose única de Meningo ACWY, recomendada aos 11 anos."
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11 and a < 15),
        DoseAplicada(vacina_codigo='MEN_C'),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_reforco_11a14_anos(self, a):
        """
        (Recomendação) Recomenda a dose de reforço da ACWY para 11-14 anos
        que já possuem histórico vacinal da Meningocócica C.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose=1,
            explicacao=f"Paciente com {a} anos e esquema prévio de Meningo C. Recomenda-se o reforço com Meningocócica ACWY."
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11 and a < 15),
        NOT(DoseAplicada(vacina_codigo='MEN_C')),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_dose_unica_11a14_anos(self, a):
        """
        (Recomendação) Recomenda a dose única da ACWY para 11-14 anos
        sem histórico vacinal da Meningocócica C.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose=1,
            explicacao=f"Paciente com {a} anos sem esquema prévio de Meningo C. Recomenda-se uma dose da vacina Meningocócica ACWY."
        ))
    
    @Rule(
        DoseAplicada(vacina_codigo='MEN_ACWY', dose=1, data_aplicacao=MATCH.data_dose)
    )
    def regra_menacwy_esquema_completo(self, data_dose):
        """
        (Esquema Completo) Finaliza o esquema da Men-ACWY.
        """
        self.declare(EsquemaCompleto(
            vacina="Meningocócica ACWY",
            explicacao="Dose de Meningocócica ACWY aplicada.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 15),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_contraindicacao_idade(self):
        """
        (Contraindicação) Para >= 15 anos, a ACWY não é rotina.
        """
        self.declare(Contraindicacao(
            vacina="Meningocócica ACWY",
            dose=1,
            motivo="Idade superior a 14 anos.",
            explicacao="A vacina Meningo ACWY é recomendada na rotina para adolescentes de 11 a 14 anos."
        ))
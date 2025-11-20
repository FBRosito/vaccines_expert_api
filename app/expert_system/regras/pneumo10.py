import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasPneumo10(_RegrasBase):
    """
    Regras para a Pneumocócica 10V, incluindo regras de catch-up.
    Atualizado com lógica proativa e tipos de data corretos.
    """

    @Rule(
        Idade(meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn), 
        TEST(lambda m: m < 2), 
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=1))
    )
    def regra_pneumo10_d1_agendar(self, m, d, dn):
        """
        (Agendamento) Para crianças < 2 meses sem D1, agenda a
        primeira dose para a data exata dos 2 meses de idade.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
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
        """
        (Recomendação) Recomenda a D1 apenas para crianças
        com menos de 1 ano (entre 2 e 11 meses).
        """
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V", dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da vacina Pneumocócica 10V é recomendada aos 2 meses."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        OR(
            DoseAplicada(vacina_codigo='PNEUMO10', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Pneumocócica 10V", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=2)),
        NOT(AgendamentoFuturo(vacina="Pneumocócica 10V", dose=2))
    )
    def regra_pneumo10_d2_agendar(self, d1_data):
        """
        (Agendamento) Após D1 (real ou planejada), agenda D2.
        Define data mínima (30d) e recomendada (60d/2m).
        """
        data_base = d1_data.date() if isinstance(d1_data, datetime.datetime) else d1_data
        
        self.declare(AgendamentoFuturo(
            vacina="Pneumocócica 10V", dose=2,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 2ª dose da Pneumocócica 10V é agendada com intervalo recomendado de 60 dias (mínimo de 30 dias) após a 1ª dose."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='PNEUMO10', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=2))
    )
    def regra_pneumo10_d2_recomendar_agora_atrasada(self):
        """
        (Recomendação) Recomenda a D2 (imediata) caso a D2
        esteja atrasada (>= 30 dias da D1) e < 5 anos.
        """
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V", 
            dose=2,
            explicacao="A 2ª dose da Pneumocócica 10V está atrasada. Aplicar agora (respeitado o intervalo mínimo de 30 dias da 1ª dose)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10'))
    )
    def regra_pneumo10_catchup_dose_unica(self, a):
        """
        (Recomendação) Recomenda dose única para crianças de 1 a 4
        anos sem nenhuma dose prévia.
        """
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V",
            dose="Única",
            explicacao=f"Para crianças com {a} anos sem comprovação vacinal, a IN 2024 recomenda a administração de dose única."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 12),
        OR(
            DoseAplicada(vacina_codigo='PNEUMO10', dose=2, data_aplicacao=MATCH.d2_data),
            AgendamentoFuturo(vacina="Pneumocócica 10V", dose=2, data_recomendada=MATCH.d2_data)
        ),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3)),
        NOT(AgendamentoFuturo(vacina="Pneumocócica 10V", dose="Reforço"))
    )
    def regra_pneumo10_reforco_agendar(self, d2_data, dn):
        """
        (Agendamento) Para < 12 meses com D2 (real ou planejada),
        agenda o reforço para a data ideal (12m) ou
        mínima (D2+60d), o que for mais tarde.
        """
        d2_resolvida = d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        
        data_rec_12m = dn_data + relativedelta(months=12)
        data_min_int = d2_resolvida + relativedelta(days=60)
        data_alvo = max(data_rec_12m, data_min_int)

        self.declare(AgendamentoFuturo(
            vacina="Pneumocócica 10V",
            dose="Reforço",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento do reforço da Pneumo10, recomendado aos 12 meses (respeitando o intervalo mínimo de 60 dias após a 2ª dose)."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='PNEUMO10', dose=2, data_aplicacao=MATCH.d2), 
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m, d2:
            (a < 5 and (a * 12 + m) >= 12) and
            (datetime.date.today() >= ((d2.date() if isinstance(d2, datetime.datetime) else d2) + relativedelta(months=2)))
        ), 
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3))
    )
    def regra_pneumo10_reforco_recomendar_agora(self):
        """
        (Recomendação) Recomenda o reforço da Pneumo10 a partir dos
        12 meses, respeitando o intervalo mínimo de 60 dias da D2.
        """
        self.declare(RecomendacaoImediata(
            vacina="Pneumocócica 10V", 
            dose="Reforço", 
            explicacao="O reforço da Pneumocócica 10V é recomendado a partir dos 12 meses, respeitando o intervalo mínimo de 60 dias da 2ª dose."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose=3)),
        NOT(DoseAplicada(vacina_codigo='PNEUMO10', dose="Única"))
    )
    def regra_pneumo10_contraindicacao_idade(self):
        """
        (Contraindicação) Para crianças >= 5 anos sem esquema
        completo, contraindica a vacina.
        """
        self.declare(Contraindicacao(
            vacina="Pneumocócica 10V",
            dose="Todas",
            motivo="Idade superior à permitida.",
            explicacao="A vacina Pneumo10 na rotina do PNI é recomendada apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        OR(
            DoseAplicada(vacina_codigo='PNEUMO10', dose=3, data_aplicacao=MATCH.data_dose),
            DoseAplicada(vacina_codigo='PNEUMO10', dose="Única", data_aplicacao=MATCH.data_dose)
        )
    )
    def regra_pneumo10_esquema_completo(self, data_dose):
        """
        (Esquema Completo) Considera o esquema completo se
        tomou o Reforço (D3) ou a Dose Única.
        """
        self.declare(EsquemaCompleto(
            vacina="Pneumocócica 10V",
            explicacao="Esquema de vacinação da Pneumocócica 10V finalizado.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))
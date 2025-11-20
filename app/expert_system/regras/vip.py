import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasVip(_RegrasBase):
    """
    Regras de vacinação para a Poliomielite (VIP).
    Atualizado com lógica proativa e tipos de data corretos.
    """

    @Rule(
        Idade(meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn), 
        TEST(lambda m: m < 2), 
        NOT(DoseAplicada(vacina_codigo='VIP', dose=1))
    )
    def regra_vip_d1_agendar(self, m, d, dn):
        """
        (Agendamento) Para crianças < 2 meses sem D1, agenda a
        primeira dose para a data exata dos 2 meses de idade.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_agendada = dn_data + relativedelta(months=2)
        
        self.declare(AgendamentoFuturo(
            vacina="VIP (Poliomielite)",
            dose=1,
            data_minima=data_agendada,
            data_recomendada=data_agendada,
            explicacao="Agendamento da 1ª dose, recomendada aos 2 meses de idade."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a < 5 and (a * 12 + m) >= 2), 
        NOT(DoseAplicada(vacina_codigo='VIP', dose=1))
    )
    def regra_vip_d1_recomendar_agora(self, m):
        """
        (Recomendação) Para crianças >= 2 meses e < 5 anos sem D1,
        recomenda a aplicação imediata.
        """
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da vacina VIP é recomendada aos 2 meses."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        OR(
            DoseAplicada(vacina_codigo='VIP', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=2))
    )
    def regra_vip_d2_agendar(self, d1_data):
        """
        (Agendamento) Após D1 (real ou planejada), agenda D2.
        Define data mínima (30d) e recomendada (60d/2m).
        """
        data_base = d1_data.date() if isinstance(d1_data, datetime.datetime) else d1_data
        
        self.declare(AgendamentoFuturo(
            vacina="VIP (Poliomielite)",
            dose=2,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 2ª dose da VIP é agendada com intervalo recomendado de 60 dias (mínimo de 30 dias) após a 1ª dose."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=2))
    )
    def regra_vip_d2_recomendar_agora_atrasada(self):
        """
        (Recomendação) Para crianças < 5 anos com D1 e D2 atrasada
        (>= 30 dias), recomenda a D2 imediata.
        """
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)",
            dose=2,
            explicacao="A 2ª dose da VIP está atrasada. Aplicar agora (respeitado o intervalo mínimo de 30 dias da D1)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        OR(
            DoseAplicada(vacina_codigo='VIP', dose=2, data_aplicacao=MATCH.d2_data),
            AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=2, data_recomendada=MATCH.d2_data)
        ),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3))
    )
    def regra_vip_d3_agendar(self, d2_data):
        """
        (Agendamento) Após D2 (real ou planejada), agenda D3.
        Define data mínima (30d) e recomendada (60d/2m).
        """
        data_base = d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data
        
        self.declare(AgendamentoFuturo(
            vacina="VIP (Poliomielite)",
            dose=3,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 3ª dose da VIP é agendada com intervalo recomendado de 60 dias (mínimo de 30 dias) após a 2ª dose."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='VIP', dose=2, data_aplicacao=MATCH.d2),
        TEST(lambda d2: (datetime.date.today() >= ((d2.date() if isinstance(d2, datetime.datetime) else d2) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=3))
    )
    def regra_vip_d3_recomendar_agora_atrasada(self):
        """
        (Recomendação) Para crianças < 5 anos com D2 e D3 atrasada
        (>= 30 dias), recomenda a D3 imediata.
        """
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)",
            dose=3,
            explicacao="A 3ª dose da VIP está atrasada. Aplicar agora (respeitado o intervalo mínimo de 30 dias da D2)."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 15),
        OR(
            DoseAplicada(vacina_codigo='VIP', dose=3, data_aplicacao=MATCH.d3_data),
            AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=3, data_recomendada=MATCH.d3_data)
        ),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=4)),
        NOT(AgendamentoFuturo(vacina="VIP (Poliomielite)", dose=4))
    )
    def regra_vip_reforco_agendar(self, d3_data, dn):
        """
        (Agendamento) Para < 15 meses com D3 (real ou planejada),
        agenda o reforço (D4) para a data ideal (15m) ou
        mínima (D3+6m), o que for mais tarde.
        """
        d3_resolvida = d3_data.date() if isinstance(d3_data, datetime.datetime) else d3_data
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        
        data_rec_15m = dn_data + relativedelta(months=15)
        data_min_int = d3_resolvida + relativedelta(months=6)
        data_alvo = max(data_rec_15m, data_min_int)

        self.declare(AgendamentoFuturo(
            vacina="VIP (Poliomielite)",
            dose=4,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento do reforço da VIP (4ª dose), recomendado aos 15 meses (respeitando o intervalo mínimo de 6 meses após a 3ª dose)."
        ))
    
    @Rule(
        DoseAplicada(vacina_codigo='VIP', dose=3, data_aplicacao=MATCH.d3_vip), 
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m, d3_vip:
            (a < 5 and (a * 12 + m) >= 15) and
            (datetime.date.today() >= ((d3_vip.date() if isinstance(d3_vip, datetime.datetime) else d3_vip) + relativedelta(months=6)))
        ),
        NOT(DoseAplicada(vacina_codigo='VIP', dose=4))
    )
    def regra_vip_reforco_recomendar_agora(self):
        """
        (Recomendação) Para crianças >= 15 meses com D3 da VIP
        e intervalo de 6 meses respeitado, recomenda o reforço (D4).
        """
        self.declare(RecomendacaoImediata(
            vacina="VIP (Poliomielite)", 
            dose=4,
            explicacao="O reforço da vacina VIP (4ª dose) é recomendado a partir dos 15 meses de idade, respeitando o intervalo mínimo de 6 meses após a 3ª dose."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5), 
        NOT(DoseAplicada(vacina_codigo='VIP', dose=4))
    )
    def contraindicacao_vip_idade(self):
        """
        (Contraindicação) Para >= 5 anos sem esquema completo,
        contraindica o esquema da VIP.
        """
        self.declare(Contraindicacao(
            vacina="VIP (Poliomielite)",
            dose="Todas",
            motivo="Idade superior a 4 anos, 11 meses e 29 dias.",
            explicacao="O esquema infantil da vacina contra a poliomielite (VIP) é recomendado até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='VIP', dose=4, data_aplicacao=MATCH.d4_data)
    )
    def regra_vip_esquema_completo(self, d4_data):
        """
        (Esquema Completo) Após a 4ª dose (reforço) da VIP,
        considera o esquema finalizado.
        """
        self.declare(EsquemaCompleto(
            vacina="VIP (Poliomielite)",
            explicacao="Esquema de 4 doses (3 + 1 reforço) da VIP finalizado.",
            data_ultima_dose=d4_data.date() if isinstance(d4_data, datetime.datetime) else d4_data
        ))
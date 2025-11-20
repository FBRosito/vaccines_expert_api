import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, EsquemaCompleto, Contraindicacao

class RegrasCovid19(_RegrasBase):
    """
    Regras de vacinação para a COVID-19 (esquema infantil).
    """

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda m, a: (a * 12 + m) < 6),
        NOT(DoseAplicada(vacina_codigo='COVID19', dose=1))
    )
    def regra_covid19_d1_agendar(self, dn):
        """
        (Agendamento) Para crianças < 6 meses sem D1, agenda a
        primeira dose para a data exata dos 6 meses de idade.
        """
        data_alvo = dn + relativedelta(months=6) 
        self.declare(AgendamentoFuturo(
            vacina="COVID-19",
            dose=1,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da 1ª dose da COVID-19, recomendada aos 6 meses de idade."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda m, a: (a * 12 + m) >= 6 and a < 5),
        TEST(lambda dn: (datetime.date.today() + relativedelta(weeks=4)) < (dn + relativedelta(years=5))),
        NOT(DoseAplicada(vacina_codigo='COVID19', dose=1))
    )
    def regra_covid19_d1_recomendar_agora(self):
        """
        (Recomendação) Recomenda a D1 para crianças entre 6 meses e < 5 anos,
        DESDE QUE haja tempo hábil (4 semanas) para a D2 antes dos 5 anos.
        """
        self.declare(RecomendacaoImediata(
            vacina="COVID-19",
            dose=1,
            explicacao="A 1ª dose da vacina COVID-19 é recomendada a partir dos 6 meses de idade."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), 
        TEST(lambda a: a < 5),
        OR(
            DoseAplicada(vacina_codigo='COVID19', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="COVID-19", dose=1, data_recomendada=MATCH.d1_data)
        ),
        TEST(lambda dn, d1_data: 
             ((d1_data.date() if isinstance(d1_data, datetime.datetime) else d1_data) + relativedelta(weeks=4)) 
             < (dn + relativedelta(years=5))
        ),
        NOT(DoseAplicada(vacina_codigo='COVID19', dose=2)),
        NOT(AgendamentoFuturo(vacina="COVID-19", dose=2))
    )
    def regra_covid19_d2_agendar(self, d1_data):
        """
        (Agendamento) Agenda a D2 com base na D1, se a 
        data resultante for menor que 5 anos de idade.
        """
        data_base = d1_data.date() if isinstance(d1_data, datetime.datetime) else d1_data
        data_alvo = data_base + relativedelta(weeks=4)
        
        self.declare(AgendamentoFuturo(
            vacina="COVID-19",
            dose=2,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="A 2ª dose da vacina COVID-19 é recomendada com intervalo de 4 semanas após a primeira."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), 
        TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() - d1) >= relativedelta(weeks=4)),
        TEST(lambda dn: datetime.date.today() < (dn + relativedelta(years=5))),
        NOT(DoseAplicada(vacina_codigo='COVID19', dose=2))
    )
    def regra_covid19_d2_recomendar_agora_atrasada(self):
        """
        (Recomendação) Recomenda D2 imediata se atrasada e < 5 anos.
        """
        self.declare(RecomendacaoImediata(
            vacina="COVID-19",
            dose=2,
            explicacao="A 2ª dose da COVID-19 está atrasada. Aplicar agora (respeitado o intervalo de 4 semanas da 1ª dose)."
        ))
        
    @Rule(
        DoseAplicada(vacina_codigo='COVID19', dose=2, data_aplicacao=MATCH.d2_data)
    )
    def regra_covid19_esquema_ok(self, d2_data):
        """
        (Esquema Completo) Após D2 da COVID-19, esquema finalizado.
        """
        self.declare(EsquemaCompleto(
            vacina="COVID-19",
            explicacao="Esquema primário de 2 doses da vacina COVID-19 finalizado.",
            data_ultima_dose=d2_data
        ))
    
    # =================================================================
    # REGRAS DE CONTRAINDICAÇÃO (IDADE E TEMPO HÁBIL)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5),
        NOT(DoseAplicada(vacina_codigo='COVID19', dose=2))
    )
    def regra_covid19_contraindicacao_idade_geral(self):
        """
        (Contraindicação) Geral para >= 5 anos sem esquema completo.
        """
        self.declare(Contraindicacao(
            vacina="COVID-19",
            dose="Todas",
            motivo="Idade superior à permitida.",
            explicacao="O esquema infantil da COVID-19 é recomendado apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        NOT(DoseAplicada(vacina_codigo='COVID19')),
        TEST(lambda dn: (datetime.date.today() + relativedelta(weeks=4)) >= (dn + relativedelta(years=5)))
    )
    def regra_covid19_contraindicacao_sem_tempo_inicio(self):
        """
        (Contraindicação) Não há tempo hábil para iniciar e terminar
        o esquema antes dos 5 anos.
        """
        self.declare(Contraindicacao(
            vacina="COVID-19",
            dose=1,
            motivo="Impossibilidade de completar o esquema na idade recomendada.",
            explicacao="Não há tempo hábil para administrar as duas doses necessárias (intervalo de 4 semanas) antes da criança completar 5 anos."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19', dose=1, data_aplicacao=MATCH.d1_data),
        NOT(DoseAplicada(vacina_codigo='COVID19', dose=2)),
        TEST(lambda dn, d1_data: (d1_data + relativedelta(weeks=4)) >= (dn + relativedelta(years=5)))
    )
    def regra_covid19_contraindicacao_sem_tempo_conclusao(self):
        """
        (Contraindicação) Criança tomou D1, mas não haverá tempo
        para a D2 antes dos 5 anos.
        """
        self.declare(Contraindicacao(
            vacina="COVID-19",
            dose=2,
            motivo="Idade limite excedida para conclusão do esquema.",
            explicacao="A segunda dose não poderá ser administrada no intervalo mínimo recomendado antes da criança completar 5 anos."
        ))
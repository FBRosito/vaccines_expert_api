import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasPentaDTP(_RegrasBase):
    """
    Regras para o esquema sequencial Penta (primário) e DTP (reforços).
    """

    @Rule(
        Idade(meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn), 
        TEST(lambda m: m < 2), 
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=1))
    )
    def regra_penta_d1_agendar(self, m, d, dn):
        """
        (Agendamento) Para crianças < 2 meses sem D1, agenda a
        primeira dose para a data exata dos 2 meses de idade.
        """
        data_agendada = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_agendada += relativedelta(months=2)
        
        self.declare(AgendamentoFuturo(
            vacina="Penta",
            dose=1,
            data_minima=data_agendada,
            data_recomendada=data_agendada,
            explicacao="Agendamento para a idade recomendada. A 1ª dose da vacina Penta deve ser aplicada aos 2 meses de idade."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a < 7 and (a * 12 + m) >= 2), 
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=1))
    )
    def regra_penta_d1_recomendar_agora(self, m):
        """
        (Recomendação) Para crianças >= 2 meses e < 7 anos sem D1,
        recomenda a aplicação imediata.
        """
        self.declare(RecomendacaoImediata(
            vacina="Penta",
            dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da vacina Penta, recomendada aos 2 meses, está pendente para aplicação."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 7),
        OR(
            DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Penta", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=2)),
        NOT(AgendamentoFuturo(vacina="Penta", dose=2))
    )
    def regra_penta_d2_agendar(self, d1_data):
        """
        (Agendamento) Após D1 (real ou planejada), agenda D2.
        Define data mínima (30d) e recomendada (60d/2m).
        """
        data_base = d1_data.date() if isinstance(d1_data, datetime.datetime) else d1_data
        
        self.declare(AgendamentoFuturo(
            vacina="Penta",
            dose=2,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 2ª dose é agendada com intervalo recomendado de 60 dias (mínimo de 30 dias) após a 1ª dose."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 7),
        DoseAplicada(vacina_codigo='PENTA', dose=1, data_aplicacao=MATCH.d1), 
        TEST(lambda d1: (datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=2))
    )
    def regra_penta_d2_recomendar_agora_atrasada(self):
        """
        (Recomendação) Para crianças < 7 anos com D1 e D2 atrasada
        (>= 30 dias), recomenda a D2 imediata.
        """
        self.declare(RecomendacaoImediata(
            vacina="Penta",
            dose=2,
            explicacao="A 2ª dose da Penta está atrasada. Aplicar agora (respeitado o intervalo mínimo de 30 dias da D1)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 7),
        OR(
            DoseAplicada(vacina_codigo='PENTA', dose=2, data_aplicacao=MATCH.d2_data),
            AgendamentoFuturo(vacina="Penta", dose=2, data_recomendada=MATCH.d2_data)
        ),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)),
        NOT(AgendamentoFuturo(vacina="Penta", dose=3))
    )
    def regra_penta_d3_agendar(self, d2_data):
        """
        (Agendamento) Após D2 (real ou planejada), agenda D3.
        Define data mínima (30d) e recomendada (60d/2m).
        """
        data_base = d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data
        
        self.declare(AgendamentoFuturo(
            vacina="Penta", dose=3,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 3ª dose é agendada com intervalo recomendado de 60 dias (mínimo de 30 dias) após a 2ª dose."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 7),
        DoseAplicada(vacina_codigo='PENTA', dose=2, data_aplicacao=MATCH.d2), 
        TEST(lambda d2: (datetime.date.today() >= ((d2.date() if isinstance(d2, datetime.datetime) else d2) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='PENTA', dose=3))
    )
    def regra_penta_d3_recomendar_agora_atrasada(self):
        """
        (Recomendação) Para crianças < 7 anos com D2 e D3 atrasada
        (>= 30 dias), recomenda a D3 imediata.
        """
        self.declare(RecomendacaoImediata(
            vacina="Penta",
            dose=3,
            explicacao="A 3ª dose da Penta está atrasada. Aplicar agora (respeitado o intervalo mínimo de 30 dias da D2)."
        ))
    
    @Rule(
        DoseAplicada(vacina_codigo='PENTA', dose=3, data_aplicacao=MATCH.d3_data)
    )
    def regra_penta_basico_ok(self, d3_data):
        """
        (Esquema Completo) Com 3 doses da Penta, considera o
        esquema primário finalizado e salva a data.
        """
        self.declare(EsquemaCompleto(
            vacina="Penta",
            explicacao="Esquema básico de 3 doses da vacina Penta foi finalizado. Os reforços seguem com a vacina DTP.",
            data_ultima_dose=d3_data.date() if isinstance(d3_data, datetime.datetime) else d3_data
        ))
    
    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a >= 7), NOT(DoseAplicada(vacina_codigo='PENTA', dose=3)))
    def contraindicacao_penta_idade(self):
        """
        (Contraindicação) Para >= 7 anos, contraindica a
        vacina Penta.
        """
        self.declare(Contraindicacao(
            vacina="Penta",
            dose="Todas",
            motivo="Idade superior a 6 anos, 11 meses e 29 dias.",
            explicacao="A vacina Penta é contraindicada para crianças com 7 anos ou mais."
        ))

    # =================================================================
    # REGRAS DTP (REFORÇOS)
    # =================================================================

    @Rule(
        OR(
            DoseAplicada(vacina_codigo='PENTA', dose=3, data_aplicacao=MATCH.d3_data),
            AgendamentoFuturo(vacina="Penta", dose=3, data_recomendada=MATCH.d3_data)
        ),
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 15),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=1)),
        NOT(AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="1º Reforço"))
    )
    def regra_dtp_reforco1_agendar(self, d3_data, dn):
        """
        (Agendamento Proativo) Para crianças < 15 meses com D3 da Penta
        (real ou planejada), agenda o 1º reforço (DTP).
        """
        data_base_d3 = d3_data.date() if isinstance(d3_data, datetime.datetime) else d3_data
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn

        data_rec_15m = dn_data + relativedelta(months=15)
        data_min_int = data_base_d3 + relativedelta(months=6)
        data_alvo = max(data_rec_15m, data_min_int)

        self.declare(AgendamentoFuturo(
            vacina="DTP (Tríplice Bacteriana)",
            dose="1º Reforço",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento do 1º reforço (DTP), recomendado aos 15 meses (respeitando o intervalo mínimo de 6 meses após a D3 da Penta)."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='PENTA', dose=3, data_aplicacao=MATCH.d3_penta),
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m, d3_penta:
            (a < 7 and (a * 12 + m) >= 15) and
            (datetime.date.today() >= ((d3_penta.date() if isinstance(d3_penta, datetime.datetime) else d3_penta) + relativedelta(months=6)))
        ),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=1))
    )
    def regra_dtp_reforco1_recomendar_agora(self):
        """
        (Recomendação) Para crianças >= 15 meses com D3 da Penta
        e intervalo de 6 meses respeitado, recomenda o 1º reforço.
        """
        self.declare(RecomendacaoImediata(
            vacina="DTP (Tríplice Bacteriana)",
            dose="1º Reforço",
            explicacao="O primeiro reforço com a vacina DTP é recomendado a partir dos 15 meses, respeitando o intervalo mínimo de 6 meses após a última dose da vacina Penta."
        ))

    @Rule(
        OR(
            DoseAplicada(vacina_codigo='DTP', dose=1, data_aplicacao=MATCH.r1_data),
            AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="1º Reforço", data_recomendada=MATCH.r1_data)
        ),
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 4),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=2)),
        NOT(AgendamentoFuturo(vacina="DTP (Tríplice Bacteriana)", dose="2º Reforço"))
    )
    def regra_dtp_reforco2_agendar(self, r1_data, dn):
        """
        (Agendamento) Para crianças < 4 anos com R1 da DTP
        (real ou planejada), agenda o 2º reforço.
        """
        data_base_r1 = r1_data.date() if isinstance(r1_data, datetime.datetime) else r1_data
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn

        data_rec_4a = dn_data + relativedelta(years=4)
        data_min_int = data_base_r1 + relativedelta(months=6)
        data_alvo = max(data_rec_4a, data_min_int)

        self.declare(AgendamentoFuturo(
            vacina="DTP (Tríplice Bacteriana)",
            dose="2º Reforço",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento do 2º reforço (DTP), recomendado aos 4 anos (respeitando o intervalo mínimo de 6 meses após o 1º reforço)."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='DTP', dose=1, data_aplicacao=MATCH.d1),
        Idade(anos=MATCH.a),
        TEST(lambda a, d1: a >= 4 and a < 7 and (datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(months=6)))),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=2))
    )
    def regra_dtp_reforco2_recomendar_agora(self):
        """
        (Recomendação) Para crianças >= 4 anos com 1º reforço DTP
        e intervalo de 6 meses respeitado, recomenda o 2º reforço.
        """
        self.declare(RecomendacaoImediata(
            vacina="DTP (Tríplice Bacteriana)",
            dose="2º Reforço",
            explicacao="O segundo reforço com a vacina DTP é recomendado aos 4 anos de idade, respeitando o intervalo mínimo de 6 meses do reforço anterior."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='DTP', dose=2, data_aplicacao=MATCH.r2_data)
    )
    def regra_dtp_esquema_completo(self, r2_data):
        """
        (Esquema Completo) Após o 2º reforço (DTP R2),
        finaliza o esquema infantil e salva a data.
        """
        self.declare(EsquemaCompleto(
            vacina="DTP (Tríplice Bacteriana)",
            explicacao="Esquema de reforços da DTP (infantil) finalizado.",
            data_ultima_dose=r2_data.date() if isinstance(r2_data, datetime.datetime) else r2_data
        ))

    @Rule(
        Idade(anos=MATCH.a, meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn),
        TEST(lambda a: a == 6),
        DoseAplicada(vacina_codigo='DTP', dose=1, data_aplicacao=MATCH.d1_dtp),
        NOT(DoseAplicada(vacina_codigo='DTP', dose=2)),
        TEST(lambda dn, d1_dtp:
            (dn + relativedelta(years=7))
            <=
            ((d1_dtp.date() if isinstance(d1_dtp, datetime.datetime) else d1_dtp) + relativedelta(months=6))
        ),
        salience=10
    )
    def regra_dtp_excecao_6_anos_agendar_dt(self, d1_dtp):
        """
        (Agendamento) Exceção para crianças de 6 anos que tomaram R1
        tão tarde que R2 cairia após os 7 anos. Libera do R2 e
        agenda dT para 10 anos no futuro.
        """
        data_base_r1 = d1_dtp.date() if isinstance(d1_dtp, datetime.datetime) else d1_dtp
        data_agendada_dt = data_base_r1 + relativedelta(years=10)
        
        self.declare(AgendamentoFuturo(
            vacina="dT (Dupla Adulto)",
            dose="Reforço",
            data_minima=data_agendada_dt,
            data_recomendada=data_agendada_dt,
            explicacao=f"Agendamento de reforço para 10 anos após a dose de DTP aplicada aos 6 anos, conforme IN 2024, já que o 2º reforço da DTP foi perdido por idade."
        ))
        
        self.declare(EsquemaCompleto(
            vacina="DTP (Tríplice Bacteriana)",
            explicacao="Esquema de reforços finalizado. A criança foi liberada do 2º reforço DTP por perda de oportunidade devido à idade, conforme IN 2024.",
            data_ultima_dose=data_base_r1
        ))
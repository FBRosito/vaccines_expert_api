import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, P, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, EsquemaCompleto

class RegrasDTAdulto(_RegrasBase):
    """
    Regras para a vacina dT (Dupla Adulto) a partir dos 7 anos.
    Cobre:
    1. Esquema de catch-up (3 doses) para não vacinados na infância.
    2. Reforços decenais (a cada 10 anos) para todos.
    """

    # =================================================================
    # REGRAS DE CATCH-UP (ESQUEMA PRIMÁRIO TARDIO)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        NOT(DoseAplicada(vacina_codigo='dT')),
        NOT(EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)"))
    )
    def regra_dt_catchup_d1_recomendar(self, a):
        """
        (Recomendação) Para >= 7 anos sem histórico vacinal básico
        (nem infantil, nem adulto), recomenda início imediato com dT.
        """
        self.declare(RecomendacaoImediata(
            vacina="dT (Dupla Adulto)",
            dose="1ª Dose (Esquema tardio)",
            explicacao=f"Paciente com {a} anos sem comprovação de esquema primário (Penta/DTP). Iniciar esquema de 3 doses com dT (0, 2, 8 meses)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='dT', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='dT', dose=2)),
        NOT(EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)"))
    )
    def regra_dt_catchup_d2_agendar(self, d1):
        """
        (Agendamento) Agenda D2 do catch-up.
        Intervalo Recomendado: 60 dias (2 meses).
        Intervalo Mínimo: 30 dias.
        """
        self.declare(AgendamentoFuturo(
            vacina="dT (Dupla Adulto)",
            dose="2ª Dose (Esquema tardio)",
            data_minima=d1.date() + relativedelta(days=30),
            data_recomendada=d1.date() + relativedelta(days=60),
            explicacao="A 2ª dose de dT é recomendada 60 dias após a primeira (mínimo de 30 dias)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='dT', dose=1, data_aplicacao=MATCH.d1),
        OR(
            DoseAplicada(vacina_codigo='dT', dose=2, data_aplicacao=MATCH.d2_data),
            AgendamentoFuturo(vacina="dT (Dupla Adulto)", dose="2ª Dose (Esquema tardio)", data_recomendada=MATCH.d2_data)
        ),
        NOT(DoseAplicada(vacina_codigo='dT', dose=3)),
        NOT(AgendamentoFuturo(vacina="dT (Dupla Adulto)", dose="3ª Dose (Esquema tardio)")),
        NOT(EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)"))
    )
    def regra_dt_catchup_d3_agendar_proativo(self, d2_data):
        """
        (Agendamento Proativo) Agenda D3 do catch-up com base na D2 (real ou planejada).
        Intervalo Recomendado: 60 dias após D2.
        Intervalo Mínimo: 30 dias após D2.
        """
        d2_resolvida = d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data

        self.declare(AgendamentoFuturo(
            vacina="dT (Dupla Adulto)",
            dose="3ª Dose (Esquema tardio)",
            data_minima=d2_resolvida + relativedelta(days=30),
            data_recomendada=d2_resolvida + relativedelta(days=60),
            explicacao="A 3ª dose de dT é recomendada 60 dias após a segunda (mínimo de 30 dias)."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='dT', dose=3, data_aplicacao=MATCH.d3_data),
        NOT(EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)"))
    )
    def regra_dt_catchup_esquema_completo(self, d3_data):
        """
        (Esquema Completo) Finaliza o esquema primário tardio
        após a 3ª dose de dT.
        """
        self.declare(EsquemaCompleto(
            vacina="dT (Dupla Adulto)",
            explicacao="Esquema primário tardio de 3 doses de dT finalizado.",
            data_ultima_dose=d3_data.date()
        ))

    # =================================================================
    # REGRAS DE REFORÇO DECENAL (A CADA 10 ANOS)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        OR(
            EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)", data_ultima_dose=MATCH.ult_dose_esquema),
            EsquemaCompleto(vacina="dT (Dupla Adulto)", data_ultima_dose=MATCH.ult_dose_esquema)
        ),
        NOT(DoseAplicada(vacina_codigo='dT', dose="Reforço")),
        NOT(DoseAplicada(vacina_codigo='dT', dose=4))
    )
    def regra_dt_primeiro_reforco_agendar(self, ult_dose_esquema):
        """
        (Agendamento) Agenda o primeiro reforço decenal 10 anos
        após a conclusão de qualquer esquema primário (infantil ou tardio).
        """
        data_alvo = ult_dose_esquema + relativedelta(years=10)
        
        self.declare(AgendamentoFuturo(
            vacina="dT (Dupla Adulto)",
            dose="Reforço Decenal",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao=f"Reforço recomendado 10 anos após a última dose do esquema básico ({ult_dose_esquema.strftime('%d/%m/%Y')})."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        OR(
            DoseAplicada(vacina_codigo='dT', dose="Reforço", data_aplicacao=MATCH.ult_reforco),
            DoseAplicada(vacina_codigo='dT', dose=MATCH.n, data_aplicacao=MATCH.ult_reforco),
        ),
        TEST(lambda n: isinstance(n, str) or (isinstance(n, int) and n >= 4)),
        NOT(DoseAplicada(vacina_codigo='dT', data_aplicacao=P(lambda d: d > ult_reforco))) # type: ignore
    )
    def regra_dt_reforco_subsequente_agendar(self, ult_reforco):
        """
        (Agendamento) Agenda o PRÓXIMO reforço decenal 10 anos
        após o último reforço aplicado.
        """
        data_base = ult_reforco.date() if isinstance(ult_reforco, datetime.datetime) else ult_reforco
        data_alvo = data_base + relativedelta(years=10)

        self.declare(AgendamentoFuturo(
            vacina="dT (Dupla Adulto)",
            dose="Reforço Decenal",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao=f"Reforço recomendado a cada 10 anos. Último foi em {data_base.strftime('%d/%m/%Y')}."
        ))
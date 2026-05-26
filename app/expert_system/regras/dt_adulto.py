import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, EsquemaCompleto

class RegrasDTAdulto(_RegrasBase):
    """
    Rules for the dT vaccine (Adult Double) from age 7 onwards.
    Covers:
    1. Catch-up schedule (3 doses) for individuals not vaccinated in childhood.
    2. Decennial boosters (every 10 years) for everyone.
    """

    # =================================================================
    # CATCH-UP RULES (LATE PRIMARY SCHEDULE)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        NOT(DoseAplicada(vacina_codigo='dT')),
        NOT(EsquemaCompleto(vacina="DTP (Tríplice Bacteriana)"))
    )
    def rule_dt_catch_up_dose_1_recommend(self, a):
        """
        (Recommendation) For patients >= 7 years with no basic vaccination history
        (neither childhood nor adult), recommends starting immediately with dT.
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
    def rule_dt_catch_up_dose_2_schedule(self, d1):
        """
        (Scheduling) Schedules dose 2 of the catch-up.
        Recommended interval: 60 days (2 months).
        Minimum interval: 30 days.
        """
        d1_base = d1.date() if isinstance(d1, datetime.datetime) else d1
        self.declare(AgendamentoFuturo(
            vacina="dT (Dupla Adulto)",
            dose="2ª Dose (Esquema tardio)",
            data_minima=d1_base + relativedelta(days=30),
            data_recomendada=d1_base + relativedelta(days=60),
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
    def rule_dt_catch_up_dose_3_schedule_proactive(self, d2_data):
        """
        (Proactive Scheduling) Schedules dose 3 of the catch-up based on dose 2 (actual or planned).
        Recommended interval: 60 days after dose 2.
        Minimum interval: 30 days after dose 2.
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
    def rule_dt_catch_up_scheme_complete(self, d3_data):
        """
        (Scheme Complete) Finalizes the late primary schedule
        after the 3rd dose of dT.
        """
        self.declare(EsquemaCompleto(
            vacina="dT (Dupla Adulto)",
            explicacao="Esquema primário tardio de 3 doses de dT finalizado.",
            data_ultima_dose=d3_data.date() if isinstance(d3_data, datetime.datetime) else d3_data
        ))

    # =================================================================
    # DECENNIAL BOOSTER RULES (EVERY 10 YEARS)
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
    def rule_dt_first_booster_schedule(self, ult_dose_esquema):
        """
        First decennial booster 10 years after the primary schedule.
        If the deadline has already passed, recommends immediately.
        """
        data_alvo = ult_dose_esquema + relativedelta(years=10)
        hoje = datetime.date.today()
        if data_alvo <= hoje:
            self.declare(RecomendacaoImediata(
                vacina="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                explicacao=f"Reforço decenal vencido. Último esquema básico concluído em {ult_dose_esquema.strftime('%d/%m/%Y')}."
            ))
        else:
            self.declare(AgendamentoFuturo(
                vacina="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                data_minima=data_alvo,
                data_recomendada=data_alvo,
                explicacao=f"Reforço recomendado 10 anos após a última dose do esquema básico ({ult_dose_esquema.strftime('%d/%m/%Y')})."
            ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 7),
        DoseAplicada(vacina_codigo='dT', dose="Reforço", data_aplicacao=MATCH.ult_reforco),
    )
    def rule_dt_subsequent_booster_schedule(self, ult_reforco):
        """
        Next decennial booster 10 years after the last applied booster.
        If overdue, recommends immediately.
        """
        data_base = ult_reforco.date() if isinstance(ult_reforco, datetime.datetime) else ult_reforco
        data_alvo = data_base + relativedelta(years=10)
        hoje = datetime.date.today()
        if data_alvo <= hoje:
            self.declare(RecomendacaoImediata(
                vacina="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                explicacao=f"Reforço decenal vencido. Último reforço aplicado em {data_base.strftime('%d/%m/%Y')}."
            ))
        else:
            self.declare(AgendamentoFuturo(
                vacina="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                data_minima=data_alvo,
                data_recomendada=data_alvo,
                explicacao=f"Reforço recomendado a cada 10 anos. Último foi em {data_base.strftime('%d/%m/%Y')}."
            ))

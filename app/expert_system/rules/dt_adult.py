import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Age, AppliedDose, ImmediateRecommendation, FutureSchedule, CompletedSchedule

class RulesDTAdult(_RegrasBase):
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
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        NOT(AppliedDose(vaccine_code='dT')),
        NOT(CompletedSchedule(vaccine="DTP (Tríplice Bacteriana)"))
    )
    def rule_dt_catch_up_dose_1_recommend(self, a):
        """
        (Recommendation) For patients >= 7 years with no basic vaccination history
        (neither childhood nor adult), recommends starting immediately with dT.
        """
        self.declare(ImmediateRecommendation(
            vaccine="dT (Dupla Adulto)",
            dose="1ª Dose (Esquema tardio)",
            explanation=f"Patient com {a} anos sem comprovação de esquema primário (Penta/DTP). Iniciar esquema de 3 doses com dT (0, 2, 8 meses)."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='dT', dose=1, date_applied=MATCH.d1),
        NOT(AppliedDose(vaccine_code='dT', dose=2)),
        NOT(CompletedSchedule(vaccine="DTP (Tríplice Bacteriana)"))
    )
    def rule_dt_catch_up_dose_2_schedule(self, d1):
        """
        (Scheduling) Schedules dose 2 of the catch-up.
        Recommended interval: 60 days (2 months).
        Minimum interval: 30 days.
        """
        d1_base = d1.date() if isinstance(d1, datetime.datetime) else d1
        self.declare(FutureSchedule(
            vaccine="dT (Dupla Adulto)",
            dose="2ª Dose (Esquema tardio)",
            min_date=d1_base + relativedelta(days=30),
            recommended_date=d1_base + relativedelta(days=60),
            explanation="A 2ª dose de dT é recomendada 60 dias após a primeira (mínimo de 30 dias)."
        ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='dT', dose=1, date_applied=MATCH.d1),
        OR(
            AppliedDose(vaccine_code='dT', dose=2, date_applied=MATCH.d2_data),
            FutureSchedule(vaccine="dT (Dupla Adulto)", dose="2ª Dose (Esquema tardio)", recommended_date=MATCH.d2_data)
        ),
        NOT(AppliedDose(vaccine_code='dT', dose=3)),
        NOT(FutureSchedule(vaccine="dT (Dupla Adulto)", dose="3ª Dose (Esquema tardio)")),
        NOT(CompletedSchedule(vaccine="DTP (Tríplice Bacteriana)"))
    )
    def rule_dt_catch_up_dose_3_schedule_proactive(self, d2_data):
        """
        (Proactive Scheduling) Schedules dose 3 of the catch-up based on dose 2 (actual or planned).
        Recommended interval: 60 days after dose 2.
        Minimum interval: 30 days after dose 2.
        """
        d2_resolvida = d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data

        self.declare(FutureSchedule(
            vaccine="dT (Dupla Adulto)",
            dose="3ª Dose (Esquema tardio)",
            min_date=d2_resolvida + relativedelta(days=30),
            recommended_date=d2_resolvida + relativedelta(days=60),
            explanation="A 3ª dose de dT é recomendada 60 dias após a segunda (mínimo de 30 dias)."
        ))

    @Rule(
        AppliedDose(vaccine_code='dT', dose=3, date_applied=MATCH.d3_data),
        NOT(CompletedSchedule(vaccine="DTP (Tríplice Bacteriana)"))
    )
    def rule_dt_catch_up_scheme_complete(self, d3_data):
        """
        (Scheme Complete) Finalizes the late primary schedule
        after the 3rd dose of dT.
        """
        self.declare(CompletedSchedule(
            vaccine="dT (Dupla Adulto)",
            explanation="Esquema primário tardio de 3 doses de dT finalizado.",
            last_dose_date=d3_data.date() if isinstance(d3_data, datetime.datetime) else d3_data
        ))

    # =================================================================
    # DECENNIAL BOOSTER RULES (EVERY 10 YEARS)
    # =================================================================

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        OR(
            CompletedSchedule(vaccine="DTP (Tríplice Bacteriana)", last_dose_date=MATCH.ult_dose_esquema),
            CompletedSchedule(vaccine="dT (Dupla Adulto)", last_dose_date=MATCH.ult_dose_esquema)
        ),
        NOT(AppliedDose(vaccine_code='dT', dose="Reforço")),
        NOT(AppliedDose(vaccine_code='dT', dose=4))
    )
    def rule_dt_first_booster_schedule(self, ult_dose_esquema):
        """
        First decennial booster 10 years after the primary schedule.
        If the deadline has already passed, recommends immediately.
        """
        data_alvo = ult_dose_esquema + relativedelta(years=10)
        hoje = datetime.date.today()
        if data_alvo <= hoje:
            self.declare(ImmediateRecommendation(
                vaccine="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                explanation=f"Reforço decenal vencido. Último esquema básico concluído em {ult_dose_esquema.strftime('%d/%m/%Y')}."
            ))
        else:
            self.declare(FutureSchedule(
                vaccine="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                min_date=data_alvo,
                recommended_date=data_alvo,
                explanation=f"Reforço recomendado 10 anos após a última dose do esquema básico ({ult_dose_esquema.strftime('%d/%m/%Y')})."
            ))

    @Rule(
        Age(years=MATCH.a), TEST(lambda a: a >= 7),
        AppliedDose(vaccine_code='dT', dose="Reforço", date_applied=MATCH.ult_reforco),
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
            self.declare(ImmediateRecommendation(
                vaccine="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                explanation=f"Reforço decenal vencido. Último reforço aplicado em {data_base.strftime('%d/%m/%Y')}."
            ))
        else:
            self.declare(FutureSchedule(
                vaccine="dT (Dupla Adulto)",
                dose="Reforço Decenal",
                min_date=data_alvo,
                recommended_date=data_alvo,
                explanation=f"Reforço recomendado a cada 10 anos. Último foi em {data_base.strftime('%d/%m/%Y')}."
            ))

import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasHPV(_RegrasBase):
    """
    Rules for the HPV vaccine (Human Papillomavirus).
    Covers the single-dose schedule for the general population (ages 9-19).
    """

    # =================================================================
    # STANDARD SCHEDULE (SINGLE DOSE)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 9),
        NOT(DoseAplicada(vacina_codigo='HPV'))
    )
    def rule_hpv_dose_1_schedule(self, dn):
        """
        (Scheduling) For children < 9 years, schedules the
        single dose for the exact date the child turns 9 years old.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_alvo = dn_data + relativedelta(years=9)

        self.declare(AgendamentoFuturo(
            vacina="HPV",
            dose="Única",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da dose única de HPV, recomendada aos 9 anos de idade."
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 9 and a < 20),
        NOT(DoseAplicada(vacina_codigo='HPV'))
    )
    def rule_hpv_dose_1_recommend_now_9to19_years(self, a):
        """
        (Recommendation) For persons aged 9 to 19 years with no dose,
        recommends applying the single dose.
        """
        explicacao = (
            f"Paciente com {a} anos. Recomenda-se a dose única da vacina HPV."
            if a < 15
            else f"Paciente com {a} anos. Recomenda-se resgate com dose única da vacina HPV."
        )
        self.declare(RecomendacaoImediata(
            vacina="HPV",
            dose="Única",
            explicacao=explicacao
        ))

    # =================================================================
    # COMPLETION AND CONTRAINDICATION RULES
    # =================================================================

    @Rule(
        DoseAplicada(vacina_codigo='HPV', data_aplicacao=MATCH.data_dose)
    )
    def rule_hpv_scheme_complete(self, data_dose):
        """
        (Scheme Complete) If any HPV dose has been applied,
        marks the single-dose scheme as complete.
        """
        self.declare(EsquemaCompleto(
            vacina="HPV",
            explicacao="Esquema de dose única finalizado.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 20),
        NOT(DoseAplicada(vacina_codigo='HPV'))
    )
    def rule_hpv_contraindicated_age(self):
        """
        (Contraindication) For persons >= 20 years with no dose,
        contraindicates the vaccine under PNI routine.
        """
        self.declare(Contraindicacao(
            vacina="HPV",
            dose="Única",
            motivo="Idade superior à permitida.",
            explicacao="A vacina HPV na rotina do PNI é recomendada apenas até os 19 anos, 11 meses e 29 dias."
        ))

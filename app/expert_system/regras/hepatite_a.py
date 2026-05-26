import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasHepatiteA(_RegrasBase):
    """
    Vaccination rules for Hepatitis A (single dose at 15 months).
    """

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 15),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_A'))
    )
    def rule_hepatite_a_schedule(self, dn):
        """
        (Scheduling) For children < 15 months with no dose, schedules the
        single dose for the exact date the child turns 15 months old.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_alvo = dn_data + relativedelta(months=15)

        self.declare(AgendamentoFuturo(
            vacina="Hepatite A",
            dose="Única",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da dose única de Hepatite A, recomendada aos 15 meses de idade."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a < 5 and (a * 12 + m) >= 15),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_A'))
    )
    def rule_hepatite_a_recommend_now(self):
        """
        (Recommendation) For children >= 15 months and < 5 years,
        recommends the single dose.
        """
        self.declare(RecomendacaoImediata(
            vacina="Hepatite A",
            dose="Única",
            explicacao="A vacina contra Hepatite A é recomendada em dose única aos 15 meses de idade. Pode ser aplicada até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_A'))
    )
    def rule_hepatite_a_contraindicated_age(self):
        """
        (Contraindication) For children >= 5 years with no dose,
        contraindicates the vaccine per PNI routine.
        """
        self.declare(Contraindicacao(
            vacina="Hepatite A",
            dose="Única",
            motivo="Idade superior à permitida.",
            explicacao="A vacina Hepatite A na rotina do PNI é recomendada apenas até os 4 anos, 11 meses e 29 dias."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='HEPATITE_A', data_aplicacao=MATCH.data_dose)
    )
    def rule_hepatite_a_scheme_complete(self, data_dose):
        """
        (Scheme Complete) If the single Hepatitis A dose
        has been applied, marks the scheme as complete.
        """
        self.declare(EsquemaCompleto(
            vacina="Hepatite A",
            explicacao="Esquema de dose única finalizado.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

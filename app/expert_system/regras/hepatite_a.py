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
    Regras de vacinação para a Hepatite A (dose única aos 15 meses).
    """

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 15),
        NOT(DoseAplicada(vacina_codigo='HEPATITE_A'))
    )
    def regra_hepatite_a_agendar(self, dn):
        """
        (Agendamento) Para crianças < 15 meses sem dose, agenda a
        dose única para a data exata dos 15 meses de idade.
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
    def regra_hepatite_a_recomendar_agora(self):
        """
        (Recomendação) Para crianças >= 15 meses e < 5 anos,
        recomenda a dose única.
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
    def regra_hepatite_a_contraindicacao_idade(self):
        """
        (Contraindicação) Para crianças >= 5 anos sem dose,
        contraindica a vacina conforme a rotina do PNI.
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
    def regra_hepatite_a_esquema_completo(self, data_dose):
        """
        (Esquema Completo) Se a dose única da Hepatite A
        foi aplicada, considera o esquema completo.
        """
        self.declare(EsquemaCompleto(
            vacina="Hepatite A",
            explicacao="Esquema de dose única finalizado.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))
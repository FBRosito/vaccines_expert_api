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
    Regras para a vacina HPV4 (Papilomavírus Humano).
    Cobre o esquema de dose única para a população geral (9-19 anos).
    """

    # =================================================================
    # ESQUEMA PADRÃO (DOSE ÚNICA)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 9),
        NOT(DoseAplicada(vacina_codigo='HPV'))
    )
    def regra_hpv_d1_agendar(self, dn):
        """
        (Agendamento) Para crianças < 9 anos, agenda a
        dose única para a data exata dos 9 anos de idade.
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_alvo = dn_data + relativedelta(years=9)
        
        self.declare(AgendamentoFuturo(
            vacina="HPV4", 
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
    def regra_hpv_d1_recomendar_agora_9a19_anos(self, a):
        """
        (Recomendação) Para pessoas de 9 a 19 anos sem dose,
        recomenda a aplicação da dose única.
        """
        explicacao = (
            f"Paciente com {a} anos. Recomenda-se a dose única da vacina HPV4."
            if a < 15
            else f"Paciente com {a} anos. Recomenda-se resgate com dose única da vacina HPV4."
        )
        self.declare(RecomendacaoImediata(
            vacina="HPV4",
            dose="Única",
            explicacao=explicacao
        ))

    # =================================================================
    # REGRAS DE CONCLUSÃO E CONTRAINDICAÇÃO
    # =================================================================

    @Rule(
        DoseAplicada(vacina_codigo='HPV', data_aplicacao=MATCH.data_dose)
    )
    def regra_hpv_esquema_completo(self, data_dose):
        """
        (Esquema Completo) Se qualquer dose de HPV foi aplicada,
        considera o esquema de dose única finalizado.
        """
        self.declare(EsquemaCompleto(
            vacina="HPV4",
            explicacao="Esquema de dose única finalizado.",
            data_ultima_dose=data_dose.date() if isinstance(data_dose, datetime.datetime) else data_dose
        ))

    @Rule(
        Idade(anos=MATCH.a), 
        TEST(lambda a: a >= 20),
        NOT(DoseAplicada(vacina_codigo='HPV'))
    )
    def regra_hpv_contraindicacao_idade(self):
        """
        (Contraindicação) Para pessoas >= 20 anos sem dose,
        contraindica a vacina na rotina do PNI.
        """
        self.declare(Contraindicacao(
            vacina="HPV4",
            dose="Única",
            motivo="Idade superior à permitida.",
            explicacao="A vacina HPV4 na rotina do PNI é recomendada apenas até os 19 anos, 11 meses e 29 dias."
        ))
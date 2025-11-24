import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, AND, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, EsquemaCompleto, Contraindicacao

# --- FUNÇÃO AUXILIAR ---
def to_date(d):
    """Converte datetime para date se necessário."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RegrasCovid19(_RegrasBase):
    """
    Regras de vacinação para a COVID-19 (PNI).
    - Pfizer Pediátrica (6m-4a): 3 doses (0, 4sem, 8sem).
    - Moderna Pediátrica (6m-4a): 2 doses (0, 4sem).
    - Idosos (>=60a): Reforço semestral.
    """

    # =================================================================
    # AUXILIARES
    # =================================================================
    
    def _agendar_dose_especifica(self, vacina_nome, dose, data_base, semanas, motivo):
        data_base_date = to_date(data_base)
        data_alvo = data_base_date + relativedelta(weeks=semanas)
        
        self.declare(AgendamentoFuturo(
            vacina=vacina_nome,
            dose=dose,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao=motivo
        ))

    # =================================================================
    # INDICAÇÃO INICIAL (NENHUMA DOSE)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, data_nascimento=MATCH.dn),
        TEST(lambda m: m < 6),
        NOT(DoseAplicada(vacina_codigo='COVID19_PFIZER')),
        NOT(DoseAplicada(vacina_codigo='COVID19_MODERNA'))
    )
    def regra_covid_geral_agendar_6m(self, dn):
        data_alvo = to_date(dn) + relativedelta(months=6) 
        self.declare(AgendamentoFuturo(
            vacina="COVID-19 (Pfizer ou Moderna)",
            dose=1,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da 1ª dose da COVID-19 pediátrica aos 6 meses."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda m, a: (a * 12 + m) >= 6 and a < 5),
        NOT(DoseAplicada(vacina_codigo='COVID19_PFIZER')),
        NOT(DoseAplicada(vacina_codigo='COVID19_MODERNA'))
    )
    def regra_covid_geral_recomendar_inicio(self):
        self.declare(RecomendacaoImediata(
            vacina="COVID-19 (Pfizer ou Moderna)",
            dose=1,
            explicacao="Criança sem histórico de COVID-19. Iniciar esquema (Pfizer: 3 doses / Moderna: 2 doses)."
        ))

    # =================================================================
    # TRILHA PFIZER - 3 DOSES
    # Esquema: D1 -> 4 sem -> D2 -> 8 sem -> D3
    # =================================================================

    # Pfizer D2 (Agendar)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(weeks=4)))
    )
    def regra_pfizer_d2_agendar(self, d1):
        self._agendar_dose_especifica("COVID-19 (Pfizer)", 2, d1, 4, "Pfizer: 2ª dose agendada para 4 semanas após a 1ª.")

    # Pfizer D2 (Recomendar Agora)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(weeks=4)))
    )
    def regra_pfizer_d2_recomendar(self):
        self.declare(RecomendacaoImediata(
            vacina="COVID-19 (Pfizer)", dose=2,
            explicacao="2ª dose da Pfizer recomendada (intervalo de 4 semanas cumprido)."
        ))

    # Pfizer D3 (Agendar - 8 semanas após D2)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=3)),
        TEST(lambda d2: datetime.date.today() < (to_date(d2) + relativedelta(weeks=8)))
    )
    def regra_pfizer_d3_agendar(self, d2):
        self._agendar_dose_especifica("COVID-19 (Pfizer)", 3, d2, 8, "Pfizer: 3ª dose agendada para 8 semanas após a 2ª.")

    # Pfizer D3 (Recomendar Agora)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=2, data_aplicacao=MATCH.d2),
        NOT(DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=3)),
        TEST(lambda d2: datetime.date.today() >= (to_date(d2) + relativedelta(weeks=8)))
    )
    def regra_pfizer_d3_recomendar(self):
        self.declare(RecomendacaoImediata(
            vacina="COVID-19 (Pfizer)", dose=3,
            explicacao="3ª dose da Pfizer recomendada (intervalo de 8 semanas da D2 cumprido)."
        ))

    # Pfizer Conclusão
    @Rule(DoseAplicada(vacina_codigo='COVID19_PFIZER', dose=3, data_aplicacao=MATCH.d3))
    def regra_pfizer_completa(self, d3):
        self.declare(EsquemaCompleto(
            vacina="COVID-19 (Pfizer)",
            explicacao="Esquema Pfizer (3 doses) completo.",
            data_ultima_dose=to_date(d3)
        ))

    # =================================================================
    # TRILHA MODERNA - 2 DOSES
    # Esquema: D1 -> 4 sem -> D2
    # =================================================================

    # Moderna D2 (Agendar)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19_MODERNA', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='COVID19_MODERNA', dose=2)),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(weeks=4)))
    )
    def regra_moderna_d2_agendar(self, d1):
        self._agendar_dose_especifica("COVID-19 (Moderna)", 2, d1, 4, "Moderna: 2ª dose agendada para 4 semanas após a 1ª.")

    # Moderna D2 (Recomendar Agora)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 5),
        DoseAplicada(vacina_codigo='COVID19_MODERNA', dose=1, data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='COVID19_MODERNA', dose=2)),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(weeks=4)))
    )
    def regra_moderna_d2_recomendar(self):
        self.declare(RecomendacaoImediata(
            vacina="COVID-19 (Moderna)", dose=2,
            explicacao="2ª dose da Moderna recomendada (intervalo de 4 semanas cumprido)."
        ))

    # Moderna Conclusão (2 doses)
    @Rule(DoseAplicada(vacina_codigo='COVID19_MODERNA', dose=2, data_aplicacao=MATCH.d2))
    def regra_moderna_completa(self, d2):
        self.declare(EsquemaCompleto(
            vacina="COVID-19 (Moderna)",
            explicacao="Esquema Moderna (2 doses) completo.",
            data_ultima_dose=to_date(d2)
        ))

    # =================================================================
    # IDOSOS (>= 60 ANOS) - REFORÇO PERIÓDICO
    # =================================================================
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 60),
        OR(
            NOT(OR(DoseAplicada(vacina_codigo='COVID19_PFIZER'), DoseAplicada(vacina_codigo='COVID19_MODERNA'))),
            AND(
                OR(
                    DoseAplicada(vacina_codigo='COVID19_PFIZER', data_aplicacao=MATCH.ult_dose),
                    DoseAplicada(vacina_codigo='COVID19_MODERNA', data_aplicacao=MATCH.ult_dose)
                ),
                TEST(lambda ult_dose: datetime.date.today() >= (to_date(ult_dose) + relativedelta(months=6)))
            )
        ),
        NOT(RecomendacaoImediata(vacina__contains="COVID-19"))
    )
    def regra_covid_idoso_recomendar(self):
        self.declare(RecomendacaoImediata(
            vacina="COVID-19 (Reforço)",
            dose="Periódica",
            explicacao="Para idosos (>=60 anos), recomenda-se reforço semestral (bivalente ou disponível)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 60),
        OR(
            DoseAplicada(vacina_codigo='COVID19_PFIZER', data_aplicacao=MATCH.ult_dose),
            DoseAplicada(vacina_codigo='COVID19_MODERNA', data_aplicacao=MATCH.ult_dose)
        ),
        TEST(lambda ult_dose: datetime.date.today() < (to_date(ult_dose) + relativedelta(months=6)))
    )
    def regra_covid_idoso_em_dia(self, ult_dose):
        self.declare(EsquemaCompleto(
            vacina="COVID-19",
            explicacao="Dose periódica em dia (intervalo de 6 meses vigente).",
            data_ultima_dose=to_date(ult_dose)
        ))

    # =================================================================
    # CONTRAINDICAÇÃO GERAL
    # =================================================================
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 60),
        NOT(DoseAplicada(vacina_codigo='COVID19_PFIZER')),
        NOT(DoseAplicada(vacina_codigo='COVID19_MODERNA'))
    )
    def regra_covid_fora_prioridade(self):
        self.declare(Contraindicacao(
            vacina="COVID-19",
            dose="Rotina",
            motivo="Fora do grupo prioritário.",
            explicacao="Vacinação de rotina indicada para <5 anos e >=60 anos."
        ))
import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

# --- FUNÇÃO AUXILIAR ---
def to_date(d):
    """Converte datetime para date se necessário."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

class RegrasInfluenza(_RegrasBase):
    """
    Regras para a Vacina Influenza (Gripe) - PNI.
    
    Público Alvo:
    - Crianças: 6 meses a < 6 anos (5 anos, 11 meses e 29 dias).
    - Idosos: >= 60 anos.
    
    Esquema:
    - Crianças (Primovacinação): 2 doses com intervalo de 30 dias.
    - Crianças (Com histórico): Dose única anual.
    - Idosos: Dose única anual.
    """

    # =================================================================
    # CONTRAINDICAÇÃO (MENORES DE 6 MESES)
    # =================================================================
    
    @Rule(
        Idade(meses=MATCH.m),
        TEST(lambda m: m < 6)
    )
    def regra_influenza_menor_6meses(self):
        self.declare(Contraindicacao(
            vacina="Influenza",
            dose="Qualquer",
            motivo="Idade inferior a 6 meses.",
            explicacao="A vacina da Influenza não é licenciada para crianças menores de 6 meses."
        ))

    # =================================================================
    # CRIANÇAS - PRIMOVACINAÇÃO (1ª DOSE)
    # =================================================================
    # Se a criança tem entre 6m e 6 anos E NUNCA tomou vacina na vida.

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: (a < 6) and (a * 12 + m >= 6)),
        NOT(DoseAplicada(vacina_codigo='INFLUENZA'))
    )
    def regra_influenza_crianca_primo_d1(self):
        self.declare(RecomendacaoImediata(
            vacina="Influenza",
            dose="1 (Primovacinação)",
            explicacao="Criança nunca vacinada contra Influenza. Recomenda-se iniciar esquema de primovacinação (1ª dose)."
        ))

    # =================================================================
    # CRIANÇAS - PRIMOVACINAÇÃO (2ª DOSE)
    # =================================================================
    # Se tomou a 1ª DOSE NESTE ANO, é a única dose da vida, e precisa da 2ª DOSE (30 dias depois).

    # CASO 1: AGENDAMENTO DA 2ª DOSE (Intervalo < 30 dias)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 6),
        DoseAplicada(vacina_codigo='INFLUENZA', data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='INFLUENZA', dose=2)),
        TEST(lambda d1: 
             (to_date(d1).year == datetime.date.today().year) and
             (datetime.date.today() < (to_date(d1) + relativedelta(days=30)))
        )
    )
    def regra_influenza_crianca_primo_d2_agendar(self, d1):
        data_base = to_date(d1)
        data_dose2 = data_base + relativedelta(days=30)
        
        self.declare(AgendamentoFuturo(
            vacina="Influenza",
            dose="2 (Primovacinação)",
            data_minima=data_dose2,
            data_recomendada=data_dose2,
            explicacao="Primovacinação: A 2ª dose deve ser aplicada 30 dias após a 1ª dose."
        ))

    # CASO 2: RECOMENDAÇÃO IMEDIATA DA 2ª DOSE (Já passou 30 dias)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 6),
        DoseAplicada(vacina_codigo='INFLUENZA', data_aplicacao=MATCH.d1),
        NOT(DoseAplicada(vacina_codigo='INFLUENZA', dose=2)),
        TEST(lambda d1: 
             (to_date(d1).year == datetime.date.today().year) and
             (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))
        )
    )
    def regra_influenza_crianca_primo_d2_aplicar(self):
        self.declare(RecomendacaoImediata(
            vacina="Influenza",
            dose="2 (Primovacinação)",
            explicacao="Completar esquema de primovacinação. Intervalo de 30 dias cumprido."
        ))

    # =================================================================
    # CRIANÇAS - DOSE ANUAL (COM HISTÓRICO)
    # =================================================================
    # Criança entre 6m e 6a que já tomou vacina em anos anteriores.
    # Esta regra recomenda a dose anual.
    # Se a criança já tiver tomado a dose deste ano, a regra 'regra_limpeza_ja_vacinado_ano'
    # irá disparar e declarar EsquemaCompleto, resolvendo o conflito.

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: (a < 6) and (a * 12 + m >= 6)),
        DoseAplicada(vacina_codigo='INFLUENZA', data_aplicacao=MATCH.d_antiga),
        TEST(lambda d_antiga: to_date(d_antiga).year < datetime.date.today().year),
        NOT(RecomendacaoImediata(vacina="Influenza", dose="Anual"))
    )
    def regra_influenza_crianca_anual_recomendar(self):
        self.declare(RecomendacaoImediata(
            vacina="Influenza",
            dose="Anual",
            explicacao="Criança com histórico vacinal anterior. Recomenda-se dose única anual."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 6),
        DoseAplicada(vacina_codigo='INFLUENZA', data_aplicacao=MATCH.d_atual),
        TEST(lambda d_atual: to_date(d_atual).year == datetime.date.today().year),
        OR(
            DoseAplicada(vacina_codigo='INFLUENZA', data_aplicacao=MATCH.d_antiga, 
                        test=lambda d_antiga: to_date(d_antiga).year < datetime.date.today().year),
            DoseAplicada(vacina_codigo='INFLUENZA', dose=2)
        )
    )
    def regra_limpeza_ja_vacinado_ano(self, d_atual):
        self.declare(EsquemaCompleto(
            vacina="Influenza",
            explicacao=f"Vacinação de Influenza ({datetime.date.today().year}) concluída.",
            data_ultima_dose=to_date(d_atual)
        ))

    # =================================================================
    # IDOSOS (>= 60 ANOS)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 60),
        NOT(RecomendacaoImediata(vacina="Influenza", dose="Anual"))
    )
    def regra_influenza_idoso_anual(self):
        self.declare(RecomendacaoImediata(
            vacina="Influenza",
            dose="Anual",
            explicacao="Idoso (>= 60 anos): Recomendada dose única anual."
        ))

    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 60),
        DoseAplicada(vacina_codigo='INFLUENZA', data_aplicacao=MATCH.d_atual),
        TEST(lambda d_atual: to_date(d_atual).year == datetime.date.today().year)
    )
    def regra_influenza_idoso_completo(self, d_atual):
        self.declare(EsquemaCompleto(
            vacina="Influenza",
            explicacao=f"Dose anual de {datetime.date.today().year} realizada.",
            data_ultima_dose=to_date(d_atual)
        ))

    # =================================================================
    # FORA DO PÚBLICO ALVO (Rotina)
    # =================================================================
    
    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 6 and a < 60)
    )
    def regra_influenza_fora_grupo(self):
        self.declare(Contraindicacao(
            vacina="Influenza",
            dose="Anual",
            motivo="Fora da faixa etária de rotina.",
            explicacao="No PNI, a Influenza é rotina para crianças (6m a <6a) e idosos (>=60). Outros grupos dependem de comorbidades."
        ))

    # =================================================================
    # CONCLUSÃO DE PRIMOVACINAÇÃO (CRIANÇA)
    # =================================================================
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 6),
        DoseAplicada(vacina_codigo='INFLUENZA', dose=1, data_aplicacao=MATCH.d1),
        DoseAplicada(vacina_codigo='INFLUENZA', dose=2, data_aplicacao=MATCH.d2),
        TEST(lambda d1, d2: 
             (to_date(d1).year == datetime.date.today().year) and 
             (to_date(d2).year == datetime.date.today().year)
        )
    )
    def regra_influenza_primo_completa_ano(self, d2):
        self.declare(EsquemaCompleto(
            vacina="Influenza",
            explicacao=f"Primovacinação completa no ano de {datetime.date.today().year}.",
            data_ultima_dose=to_date(d2)
        ))
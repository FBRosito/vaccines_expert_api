import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, AND, OR, TEST, P, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, EsquemaCompleto, ConflitoResolvido, Contraindicacao

# --- FUNÇÃO AUXILIAR ---
def to_date(d):
    """Converte datetime para date se necessário."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

def is_recente(d):
    """Verifica se a data é recente (< 30 dias atrás)."""
    d_obj = to_date(d)
    return 0 <= (datetime.date.today() - d_obj).days < 30

class RegrasVirusVivosAtenuados(_RegrasBase):
    """
    Contém regras para vacinas de vírus vivos atenuados que
    conflitam entre si: Febre Amarela, SCR, Tetraviral e Varicela.
    """

    # =================================================================
    # AUXILIARES
    # =================================================================

    def _agendar_reforco_fa_generico(self, data_base_d1, dn):
        d1_resolvida = to_date(data_base_d1)
        dn_resolvida = to_date(dn)
        data_4_anos = dn_resolvida + relativedelta(years=4)
        data_min_intervalo = d1_resolvida + relativedelta(days=30)
        data_final = max(data_4_anos, data_min_intervalo)
        
        self.declare(AgendamentoFuturo(
            vacina="Febre Amarela", 
            dose="Reforço",
            data_minima=data_final,
            data_recomendada=data_final,
            explicacao="Reforço de Febre Amarela recomendado aos 4 anos (ou 30 dias após a 1ª dose se iniciado tardiamente)."
        ))

    # =================================================================
    # ESQUEMA SCR (TRÍPLICE VIRAL)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 12),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v)))
    )
    def regra_scr_d1_agendar(self, dn):
        data_alvo = to_date(dn) + relativedelta(months=12)
        self.declare(AgendamentoFuturo(
            vacina="SCR (Tríplice Viral)", 
            dose=1,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da primeira dose, recomendada aos 12 meses de idade."
        ))

    # RECOMENDAÇÃO SCR D1 - Dividida

    # Caso 1: Criança >= 2 anos (Sem trava de Febre Amarela)
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a >= 2 and a < 5), 
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v)))
    )
    def regra_scr_d1_recomendar_maior2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", dose=1, 
            explicacao="A primeira dose da Tríplice Viral é recomendada."
        ))

    # Caso 2: Criança < 2 anos (Com trava: NÃO pode ter tomado FA recente)
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 12),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v))),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=P(is_recente)))
    )
    def regra_scr_d1_recomendar_menor2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", dose=1, 
            explicacao="A primeira dose da Tríplice Viral é recomendada aos 12 meses."
        ))
    
    # =================================================================
    # ESQUEMA TETRAVIRAL (SCR-V)
    # =================================================================

    @Rule(
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1),
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 15),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def regra_tetra_d1_agendar_pos_scr(self, d1, dn):
        d1_data = to_date(d1)
        dn_data = to_date(dn)
        data_rec_15m = dn_data + relativedelta(months=15)
        data_min_30d = d1_data + relativedelta(days=30)
        data_alvo = max(data_rec_15m, data_min_30d)

        self.declare(AgendamentoFuturo(
            vacina="Tetraviral (SCR-V)", 
            dose=1,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da 2ª dose de SCR (feita com Tetraviral), recomendada aos 15 meses."
        ))
    
    # RECOMENDAÇÃO TETRAVIRAL - Dividida

    # Caso 1: >= 2 Anos
    @Rule(
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1_scr), 
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m, d1_scr: 
            (a >= 2 and a < 5) and
            (datetime.date.today() >= (to_date(d1_scr) + relativedelta(days=30)))
        ), 
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def regra_scrv_recomendar_maior2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCRV (Tetraviral)", dose=1, 
            explicacao="A vacina Tetraviral (SCRV) é recomendada."
        ))

    # Caso 2: < 2 Anos (Trava FA)
    @Rule(
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1_scr), 
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m, d1_scr: 
            (a < 2 and (a * 12 + m) >= 15) and
            (datetime.date.today() >= (to_date(d1_scr) + relativedelta(days=30)))
        ), 
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1)),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=P(is_recente)))
    )
    def regra_scrv_recomendar_menor2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCRV (Tetraviral)", dose=1, 
            explicacao="Aos 15 meses, é recomendada a vacina Tetraviral (SCRV)."
        ))
    
    # =================================================================
    # ESQUEMA VARICELA
    # =================================================================

    @Rule(
        OR(
            DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1),
            DoseAplicada(vacina_codigo='VARICELA', dose=1)
        ),
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 4),
        NOT(DoseAplicada(vacina_codigo='VARICELA', dose=2))
    )
    def regra_varicela_d2_agendar(self, dn):
        dn_data = to_date(dn)
        data_alvo = dn_data + relativedelta(years=4)
        self.declare(AgendamentoFuturo(
            vacina="Varicela (atenuada)",
            dose=2,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da 2ª dose de Varicela, recomendada aos 4 anos."
        ))

    @Rule(
        OR(
            DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1),
            DoseAplicada(vacina_codigo='VARICELA', dose=1)
        ),
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 4 and a < 7),
        NOT(DoseAplicada(vacina_codigo='VARICELA', dose=2))
    )
    def regra_varicela_d2_recomendar_agora(self):
        self.declare(RecomendacaoImediata(
            vacina="Varicela (atenuada)",
            dose=2,
            explicacao="A segunda dose da vacina contra varicela é recomendada aos 4 anos."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: (a * 12 + m) < 9),
        NOT(DoseAplicada(vacina_codigo='VARICELA')),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL'))
    )
    def contraindicacao_varicela_idade_minima(self):
        self.declare(Contraindicacao(
            vacina="Varicela (atenuada)",
            dose=1,
            motivo="Idade inferior à permitida.",
            explicacao="A vacina Varicela (ou Tetraviral) é contraindicada para crianças menores de 9 meses."
        ))

    # =================================================================
    # REGRAS CATCH-UP SCR (5-29 ANOS)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 30),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v)))
    )
    def regra_scr_d1_recomendar_agora_catchup(self, a):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", 
            dose=1,
            explicacao=f"Paciente com {a} anos. Recomenda-se a 1ª dose da Tríplice Viral."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 30),
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() < (to_date(d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=2)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def regra_scr_d2_agendar_catchup(self, d1):
        d1_data = to_date(d1)
        data_alvo = d1_data + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina="SCR (Tríplice Viral)", 
            dose=2,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da 2ª dose da Tríplice Viral (intervalo mínimo de 30 dias)."
        ))

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 30),
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=2)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def regra_scr_d2_recomendar_agora_catchup(self):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", 
            dose=2,
            explicacao="Recomendação da 2ª dose da Tríplice Viral."
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 30),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=2)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def regra_scr_contraindicacao_idade_catchup(self):
        self.declare(Contraindicacao(
            vacina="SCR (Tríplice Viral)",
            dose=2,
            motivo="Idade superior à permitida para o esquema de 2 doses.",
            explicacao="A partir de 30 anos, considera-se dose única de SCR."
        ))

    # Conclusões de Esquema
    @Rule(
        OR(
            DoseAplicada(vacina_codigo='SCR', dose=2, data_aplicacao=MATCH.data_dose),
            DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1, data_aplicacao=MATCH.data_dose)
        )
    )
    def regra_scr_esquema_completo(self, data_dose):
        self.declare(EsquemaCompleto(vacina="SCR (Tríplice Viral)", explicacao="Esquema de 2 doses finalizado.", data_ultima_dose=to_date(data_dose)))
    
    @Rule(
        OR(
            DoseAplicada(vacina_codigo='VARICELA', dose=2, data_aplicacao=MATCH.data_dose),
            AND(
                OR(
                    DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1, data_aplicacao=MATCH.data_dose),
                    DoseAplicada(vacina_codigo='VARICELA', dose=1, data_aplicacao=MATCH.data_dose)
                ),
                Idade(anos=MATCH.a), TEST(lambda a: a >= 7)
            )
        )
    )
    def regra_varicela_esquema_completo(self, data_dose=None):
        data_final = to_date(data_dose) if data_dose else None
        self.declare(EsquemaCompleto(vacina="Varicela (atenuada)", explicacao="Esquema de Varicela finalizado.", data_ultima_dose=data_final))

    # =================================================================
    # VACINA FEBRE AMARELA
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: a == 0 and m < 9),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v)))
    )
    def regra_febre_amarela_d1_agendar(self, dn):
        dn_data = to_date(dn)
        data_alvo = dn_data + relativedelta(months=9)
        self.declare(AgendamentoFuturo(
            vacina="Febre Amarela", 
            dose=1,
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao="Agendamento da primeira dose, recomendada aos 9 meses."
        ))

    # RECOMENDAÇÃO FA D1 - Dividida

    # Caso 1: >= 2 Anos
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a >= 2 and a < 5), 
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v)))
    )
    def regra_febre_amarela_d1_recomendar_maior2(self):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose=1, 
            explicacao="A primeira dose da vacina contra Febre Amarela é recomendada."
        ))

    # Caso 2: < 2 Anos (Trava SCR/Tetra)
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 9),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v))),
        NOT(OR(
            DoseAplicada(vacina_codigo='SCR', data_aplicacao=P(is_recente)),
            DoseAplicada(vacina_codigo='TETRAVIRAL', data_aplicacao=P(is_recente))
        ))
    )
    def regra_febre_amarela_d1_recomendar_menor2(self):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose=1, 
            explicacao="A primeira dose da vacina contra Febre Amarela é recomendada."
        ))

    # Reforço FA
    @Rule(
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1, data_aplicacao=MATCH.d1),
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2)),
        NOT(AgendamentoFuturo(vacina="Febre Amarela", dose="Reforço"))
    )
    def regra_febre_amarela_reforco_pos_dose(self, d1, dn):
        d1_date = to_date(d1)
        dn_date = to_date(dn)
        data_alvo = max(dn_date + relativedelta(years=4), d1_date + relativedelta(days=30))
        if datetime.date.today() < data_alvo:
            self._agendar_reforco_fa_generico(d1, dn)

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        RecomendacaoImediata(vacina="Febre Amarela", dose=1),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2)),
        NOT(AgendamentoFuturo(vacina="Febre Amarela", dose="Reforço"))
    )
    def regra_febre_amarela_reforco_pos_recomendacao(self, dn):
        self._agendar_reforco_fa_generico(datetime.date.today(), dn)

    @Rule(
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1, data_aplicacao=MATCH.d1),
        Idade(anos=MATCH.a),
        TEST(lambda a, d1: a >= 4 and a < 5 and (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2))
    )
    def regra_febre_amarela_reforco_recomendar_agora(self):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose="Reforço",
            explicacao="Reforço da vacina contra Febre Amarela recomendado."
        ))

    # Catch-up FA
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 60),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v)))
    )
    def regra_febre_amarela_dose_unica_5a59(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose="Única",
            explicacao=f"Paciente com {a} anos sem comprovação vacinal. Administrar dose única."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a >= 5),
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda dn, d1: to_date(d1) < (to_date(dn) + relativedelta(years=5))),
        TEST(lambda d1: datetime.date.today() >= (to_date(d1) + relativedelta(days=30))),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2))
    )
    def regra_febre_amarela_catchup_reforco_pos_5anos_recomendar(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose="Reforço",
            explicacao=f"Paciente com {a} anos que recebeu a 1ª dose antes dos 5 anos. Administrar dose de reforço."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a >= 5),
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda dn, d1: to_date(d1) < (to_date(dn) + relativedelta(years=5))),
        TEST(lambda d1: datetime.date.today() < (to_date(d1) + relativedelta(days=30))),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2))
    )
    def regra_febre_amarela_catchup_reforco_pos_5anos_agendar(self, d1):
        d1_data = to_date(d1)
        data_alvo = d1_data + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina="Febre Amarela", dose="Reforço",
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao="Aguardar intervalo mínimo de 30 dias da 1ª dose."
        ))

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn), TEST(lambda a: a >= 5),
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda dn, d1: to_date(d1) >= (to_date(dn) + relativedelta(years=5)))
    )
    def regra_febre_amarela_esquema_completo_pos_5anos(self, d1):
        self.declare(EsquemaCompleto(vacina="Febre Amarela", explicacao="Esquema de 1 dose única aplicada após os 5 anos completo.", data_ultima_dose=to_date(d1)))

    @Rule(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2, data_aplicacao=MATCH.data_dose))
    def regra_febre_amarela_esquema_completo_2doses(self, data_dose):
        self.declare(EsquemaCompleto(vacina="Febre Amarela", explicacao="Esquema de 2 doses completo.", data_ultima_dose=to_date(data_dose)))
    
    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a >= 60), NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')))
    def regra_fa_contraindicacao_idade_geral(self):
        self.declare(Contraindicacao(vacina="Febre Amarela", dose="Única", motivo="Idade superior a 59 anos.", explicacao="Avaliar risco-benefício."))

    # =================================================================
    # REGRAS DE SIMULTANEIDADE (CONFLITOS VÍRUS VIVOS < 2 ANOS)
    # =================================================================

    # 1. PRIORIZAÇÃO: Faltam AMBAS (FA e SCR D1) -> Prioriza SCR
    @Rule(
        Idade(anos=MATCH.a, meses=MATCH.m),
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 12),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')),
        NOT(DoseAplicada(vacina_codigo='SCR')),
        salience=100
    )
    def regra_priorizacao_scr_sobre_vfa(self):
        self.declare(ConflitoResolvido(vacinas=['SCR (Tríplice Viral)', 'Febre Amarela']))
        self.declare(RecomendacaoImediata(
            vacina='SCR (Tríplice Viral)', dose=1,
            explicacao='Prioridade sobre Febre Amarela em < 2 anos. Aplicar SCR agora e agendar FA para 30 dias.'
        ))
        data_alvo = datetime.date.today() + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina='Febre Amarela', dose=1,
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao='Agendada para 30 dias após a SCR (intervalo obrigatório em < 2 anos).'
        ))

    # 2. PRIORIZAÇÃO: Faltam AMBAS (FA e TETRAVIRAL) -> Prioriza TETRAVIRAL
    @Rule(
        Idade(anos=MATCH.a, meses=MATCH.m),
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 15),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')),
        DoseAplicada(vacina_codigo='SCR', dose=1),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL')),
        salience=100
    )
    def regra_priorizacao_tetra_sobre_vfa(self):
        self.declare(ConflitoResolvido(vacinas=['Tetraviral (SCR-V)', 'Febre Amarela']))
        self.declare(RecomendacaoImediata(
            vacina='Tetraviral (SCR-V)', dose=1,
            explicacao='Prioridade sobre Febre Amarela em < 2 anos. Aplicar Tetraviral agora e agendar FA para 30 dias.'
        ))
        data_alvo = datetime.date.today() + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina='Febre Amarela', dose=1,
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao='Agendada para 30 dias após a Tetraviral (intervalo obrigatório em < 2 anos).'
        ))

    # 3. INTERVALO: FA recente -> Adiar SCR ou TETRA
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 2),
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=MATCH.data_fa),
        TEST(lambda data_fa: 0 <= (datetime.date.today() - to_date(data_fa)).days < 30),
        OR(
            NOT(DoseAplicada(vacina_codigo='SCR')),
            NOT(DoseAplicada(vacina_codigo='TETRAVIRAL'))
        )
    )
    def regra_atraso_sarampo_por_fa_recente(self, data_fa):
        data_alvo = to_date(data_fa) + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina="SCR/Tetraviral", dose="Dose Pendente",
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao="Aguardar 30 dias após Febre Amarela (conflito de vírus vivo < 2 anos)."
        ))

    # 4. INTERVALO: SCR ou TETRA recente -> Adiar FA
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 2),
        OR(
            DoseAplicada(vacina_codigo='SCR', data_aplicacao=MATCH.data_viva),
            DoseAplicada(vacina_codigo='TETRAVIRAL', data_aplicacao=MATCH.data_viva)
        ),
        TEST(lambda data_viva: 0 <= (datetime.date.today() - to_date(data_viva)).days < 30),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA'))
    )
    def regra_atraso_fa_por_sarampo_recente(self, data_viva):
        data_alvo = to_date(data_viva) + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina="Febre Amarela", dose=1,
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao="Aguardar 30 dias após SCR/Tetraviral (conflito de vírus vivo < 2 anos)."
        ))

    # =================================================================
    # REGRAS GERAIS DE SIMULTANEIDADE (VARICELA vs OUTRAS)
    # =================================================================
    # Aplica-se a todas as idades se não forem simultâneas.
    # Intervalo diferenciado para Varicela (Min 15 / Rec 30).

    # 1. FA TOMADA RECENTEMENTE -> AGENDAR VARICELA
    @Rule(
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=MATCH.data_fa),
        TEST(lambda data_fa: 0 <= (datetime.date.today() - to_date(data_fa)).days < 30),
        Idade(anos=MATCH.a),
        OR(NOT(DoseAplicada(vacina_codigo='VARICELA')), 
           NOT(DoseAplicada(vacina_codigo='SCR')))
    )
    def regra_geral_agendada_por_febre_amarela(self, data_fa, a):
        data_fa_data = to_date(data_fa)
        data_rec = data_fa_data + relativedelta(days=30)
        data_min_varicela = data_fa_data + relativedelta(days=15)
        
        # Varicela (Intervalo Min 15, Rec 30)
        if not self.get_dose_aplicada('VARICELA'):
             self.declare(AgendamentoFuturo(
                vacina="Varicela", dose=1,
                data_minima=data_min_varicela, 
                data_recomendada=data_rec,
                explicacao="Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após a Febre Amarela."
            ))
        
        # SCR (Mantém 30 dias se criança >= 2 anos, pois < 2 já é tratado acima)
        if a >= 2 and not self.get_dose_aplicada('SCR'):
            self.declare(AgendamentoFuturo(
                vacina="SCR (Tríplice Viral)", dose=1,
                data_minima=data_rec, 
                data_recomendada=data_rec,
                explicacao="Aguardar 30 dias após a Febre Amarela (intervalo de vírus vivos)."
            ))

    # 2. VARICELA OU SCR TOMADAS RECENTEMENTE -> AGENDAR FEBRE AMARELA
    @Rule(
        OR(
            'dose_fact' << DoseAplicada(vacina_codigo='SCR'),
            'dose_fact' << DoseAplicada(vacina_codigo='VARICELA')
        ),
        TEST(lambda dose_fact: 0 <= (datetime.date.today() - to_date(dose_fact['data_aplicacao'])).days < 30),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v))),
        Idade(anos=MATCH.a)
    )
    def regra_febre_amarela_agendada_por_outras(self, dose_fact, a):
        vacina_codigo_origem = dose_fact['vacina_codigo']
        data_viva = to_date(dose_fact['data_aplicacao'])
        
        data_rec = data_viva + relativedelta(days=30)
        
        # Se a vacina anterior foi Varicela, FA pode ser 15 dias (Min)
        if vacina_codigo_origem == 'VARICELA':
             data_min = data_viva + relativedelta(days=15)
             explicacao = f"Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após {vacina_codigo_origem}."
        else: # SCR
             data_min = data_rec # 30 dias
             explicacao = f"Agendada para 30 dias após {vacina_codigo_origem} (intervalo de vírus vivos)."

        if a < 2 and vacina_codigo_origem == 'SCR':
            pass # Já tratado em regra específica de < 2 anos
        else:
            self.declare(AgendamentoFuturo(
                vacina="Febre Amarela", 
                dose=1,
                data_minima=data_min,
                data_recomendada=data_rec,
                explicacao=explicacao
            ))

    # 3. SCR RECENTE -> AGENDAR VARICELA (15 min / 30 rec)
    @Rule(
        DoseAplicada(vacina_codigo='SCR', data_aplicacao=MATCH.data_scr),
        TEST(lambda data_scr: 0 <= (datetime.date.today() - to_date(data_scr)).days < 30),
        NOT(DoseAplicada(vacina_codigo='VARICELA', dose=1)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def regra_varicela_agendada_por_scr(self, data_scr):
        data_scr_data = to_date(data_scr)
        data_rec = data_scr_data + relativedelta(days=30)
        data_min = data_scr_data + relativedelta(days=15)
        
        self.declare(AgendamentoFuturo(
            vacina="Varicela", dose=1,
            data_minima=data_min, 
            data_recomendada=data_rec,
            explicacao="Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após a SCR."
        ))

    # 4. VARICELA RECENTE -> AGENDAR SCR (15 min / 30 rec)
    @Rule(
        DoseAplicada(vacina_codigo='VARICELA', data_aplicacao=MATCH.data_var),
        TEST(lambda data_var: 0 <= (datetime.date.today() - to_date(data_var)).days < 30),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def regra_scr_agendada_por_varicela(self, data_var):
        data_var_data = to_date(data_var)
        data_rec = data_var_data + relativedelta(days=30)
        data_min = data_var_data + relativedelta(days=15)
        
        self.declare(AgendamentoFuturo(
            vacina="SCR (Tríplice Viral)", dose=1,
            data_minima=data_min, 
            data_recomendada=data_rec,
            explicacao="Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após a Varicela."
        ))

    # Helper para verificar se dose existe no contexto (já que Experta não tem 'exists' fácil dentro do RHS sem passar pelo LHS)
    def get_dose_aplicada(self, codigo):
        for fact in self.facts.values():
            if isinstance(fact, DoseAplicada) and fact['vacina_codigo'] == codigo:
                return True
        return False

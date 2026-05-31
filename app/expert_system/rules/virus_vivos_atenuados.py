import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, AND, OR, TEST, P, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, EsquemaCompleto, ConflitoResolvido, Contraindicacao

# --- HELPER FUNCTIONS ---
def to_date(d):
    """Converts datetime to date if necessary."""
    if isinstance(d, datetime.datetime):
        return d.date()
    return d

def is_recente(d):
    """Checks whether the date is recent (< 30 days ago)."""
    d_obj = to_date(d)
    return 0 <= (datetime.date.today() - d_obj).days < 30

class RegrasVirusVivosAtenuados(_RegrasBase):
    """
    Contains rules for live attenuated virus vaccines that
    conflict with each other: Yellow Fever, MMR (SCR), Varicella (and legacy Tetraviral).
    """

    # =================================================================
    # HELPERS
    # =================================================================

    def _schedule_fa_booster_generic(self, data_base_d1, dn):
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
    # MMR (SCR) SCHEME - DOSE 1 (12 MONTHS)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 12),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v)))
    )
    def rule_scr_dose_1_schedule(self, dn):
        data_alvo = to_date(dn) + relativedelta(months=12)
        self.declare(AgendamentoFuturo(
            vacina="SCR (Tríplice Viral)",
            dose=1,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da 1ª dose (SCR), recomendada aos 12 meses."
        ))

    # MMR DOSE 1 RECOMMENDATION

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a >= 2 and a < 5),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v)))
    )
    def rule_scr_dose_1_recommend_over_2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", dose=1,
            explicacao="A primeira dose da Tríplice Viral é recomendada."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 12),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v))),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=P(is_recente)))
    )
    def rule_scr_dose_1_recommend_under_2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", dose=1,
            explicacao="A primeira dose da Tríplice Viral é recomendada aos 12 meses."
        ))

    # =================================================================
    # MMR SCHEME - DOSE 2 (15 MONTHS)
    # =================================================================

    # Case 1: D1 applied -> Schedule D2
    @Rule(
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1),
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda m: m < 15),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=2)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL'))
    )
    def rule_scr_dose_2_schedule(self, d1, dn):
        d1_data = to_date(d1)
        dn_data = to_date(dn)
        data_rec_15m = dn_data + relativedelta(months=15)
        data_min_30d = d1_data + relativedelta(days=30)
        data_alvo = max(data_rec_15m, data_min_30d)

        self.declare(AgendamentoFuturo(
            vacina="SCR (Tríplice Viral)",
            dose=2,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da 2ª dose de SCR, recomendada aos 15 meses."
        ))

    # Case 2: D1 scheduled -> Project D2
    @Rule(
        AgendamentoFuturo(vacina="SCR (Tríplice Viral)", dose=1, data_recomendada=MATCH.d1_prevista),
        Idade(data_nascimento=MATCH.dn),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=2)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL')),
        NOT(AgendamentoFuturo(vacina="SCR (Tríplice Viral)", dose=2))
    )
    def rule_scr_dose_2_project(self, d1_prevista, dn):
        d1_data = to_date(d1_prevista)
        dn_data = to_date(dn)
        data_rec_15m = dn_data + relativedelta(months=15)
        data_min_30d = d1_data + relativedelta(days=30)
        data_alvo = max(data_rec_15m, data_min_30d)

        self.declare(AgendamentoFuturo(
            vacina="SCR (Tríplice Viral)",
            dose=2,
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Projeção da 2ª dose de SCR para os 15 meses."
        ))

    # --- MMR DOSE 2 RECOMMENDATION ---

    # Case 1: Over 2 years (no YF lock)
    @Rule(
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1_scr),
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m, d1_scr:
            (a >= 2 and a < 5) and
            (datetime.date.today() >= (to_date(d1_scr) + relativedelta(days=30)))
        ),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=2)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL'))
    )
    def rule_scr_dose_2_recommend_over_2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", dose=2,
            explicacao="A 2ª dose da Tríplice Viral é recomendada."
        ))

    # Case 2: Under 2 years (YF lock)
    @Rule(
        DoseAplicada(vacina_codigo='SCR', dose=1, data_aplicacao=MATCH.d1_scr),
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m, d1_scr:
            (a < 2 and (a * 12 + m) >= 15) and
            (datetime.date.today() >= (to_date(d1_scr) + relativedelta(days=30)))
        ),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=2)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL')),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=P(is_recente)))
    )
    def rule_scr_dose_2_recommend_under_2(self):
        self.declare(RecomendacaoImediata(
            vacina="SCR (Tríplice Viral)", dose=2,
            explicacao="A 2ª dose da Tríplice Viral é recomendada aos 15 meses."
        ))

    # =================================================================
    # VARICELLA SCHEME - DOSE 1 (15 MONTHS)
    # =================================================================

    # Case 1: Schedule by age (< 15 months)
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda m: m < 15),
        NOT(DoseAplicada(vacina_codigo='VARICELA')),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL')),
        NOT(AgendamentoFuturo(vacina="Varicela (atenuada)", dose=1))
    )
    def rule_varicela_dose_1_schedule_by_age(self, dn):
        data_15m = to_date(dn) + relativedelta(months=15)
        self.declare(AgendamentoFuturo(
            vacina="Varicela (atenuada)",
            dose=1,
            data_minima=data_15m,
            data_recomendada=data_15m,
            explicacao="A 1ª dose de Varicela é recomendada aos 15 meses (junto com a 2ª dose da Tríplice Viral)."
        ))

    # Case 2: Schedule because MMR D1 was already given
    @Rule(
        Idade(data_nascimento=MATCH.dn),
        DoseAplicada(vacina_codigo='SCR', dose=1),
        NOT(DoseAplicada(vacina_codigo='VARICELA')),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL')),
        NOT(AgendamentoFuturo(vacina="Varicela (atenuada)", dose=1))
    )
    def rule_varicela_dose_1_schedule_after_mmr(self, dn):
        data_15m = to_date(dn) + relativedelta(months=15)
        if datetime.date.today() < data_15m:
            self.declare(AgendamentoFuturo(
                vacina="Varicela (atenuada)",
                dose=1,
                data_minima=data_15m,
                data_recomendada=data_15m,
                explicacao="A 1ª dose de Varicela é recomendada aos 15 meses."
            ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: (a < 5 and (a * 12 + m) >= 15)),
        NOT(DoseAplicada(vacina_codigo='VARICELA')),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL')),
        NOT(DoseAplicada(vacina_codigo='SCR', data_aplicacao=P(is_recente))),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=P(is_recente)))
    )
    def rule_varicela_dose_1_recommend(self):
        self.declare(RecomendacaoImediata(
            vacina="Varicela (atenuada)", dose=1,
            explicacao="A 1ª dose de Varicela (monovalente) é recomendada aos 15 meses."
        ))

    # =================================================================
    # VARICELLA SCHEME - DOSE 2 (4 YEARS)
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
    def rule_varicela_dose_2_schedule(self, dn):
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
        NOT(DoseAplicada(vacina_codigo='VARICELA', dose=2)),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=P(is_recente)))
    )
    def rule_varicela_dose_2_recommend_now(self):
        self.declare(RecomendacaoImediata(
            vacina="Varicela (atenuada)",
            dose=2,
            explicacao="A segunda dose da vacina contra varicela é recomendada aos 4 anos."
        ))

    # =================================================================
    # MMR CATCH-UP RULES (5-29 YEARS)
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 30),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'SCR (Tríplice Viral)' in v)))
    )
    def rule_scr_dose_1_recommend_now_catch_up(self, a):
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
    def rule_scr_dose_2_schedule_catch_up(self, d1):
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
    def rule_scr_dose_2_recommend_now_catch_up(self):
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
    def rule_scr_contraindicated_age_catch_up(self):
        self.declare(Contraindicacao(
            vacina="SCR (Tríplice Viral)",
            dose=2,
            motivo="Idade superior à permitida para o esquema de 2 doses.",
            explicacao="A partir de 30 anos, considera-se dose única de SCR."
        ))

    # Scheme completions
    @Rule(
        OR(
            DoseAplicada(vacina_codigo='SCR', dose=2, data_aplicacao=MATCH.data_dose),
            DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1, data_aplicacao=MATCH.data_dose)
        )
    )
    def rule_scr_scheme_complete(self, data_dose):
        self.declare(EsquemaCompleto(vacina="SCR (Tríplice Viral)", explicacao="Esquema de 2 doses finalizado.", data_ultima_dose=to_date(data_dose)))

    @Rule(DoseAplicada(vacina_codigo='VARICELA', dose=2, data_aplicacao=MATCH.data_dose))
    def rule_varicela_scheme_complete_2_doses(self, data_dose):
        self.declare(EsquemaCompleto(vacina="Varicela (atenuada)", explicacao="Esquema de Varicela finalizado (2 doses).", data_ultima_dose=to_date(data_dose)))

    @Rule(
        OR(
            DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1, data_aplicacao=MATCH.data_dose),
            DoseAplicada(vacina_codigo='VARICELA', dose=1, data_aplicacao=MATCH.data_dose)
        ),
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 7),
        NOT(DoseAplicada(vacina_codigo='VARICELA', dose=2))
    )
    def rule_varicela_scheme_complete_by_age(self, data_dose):
        self.declare(EsquemaCompleto(
            vacina="Varicela (atenuada)",
            explicacao="Esquema encerrado com 1 dose (idade > 7 anos, perdeu 2ª dose de rotina).",
            data_ultima_dose=to_date(data_dose)
        ))

    # =================================================================
    # YELLOW FEVER VACCINE
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: a == 0 and m < 9),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v)))
    )
    def rule_febre_amarela_dose_1_schedule(self, dn):
        dn_data = to_date(dn)
        data_alvo = dn_data + relativedelta(months=9)
        self.declare(AgendamentoFuturo(
            vacina="Febre Amarela",
            dose=1,
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao="Agendamento da primeira dose, recomendada aos 9 meses."
        ))

    # YF DOSE 1 RECOMMENDATION - Split

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a >= 2 and a < 5),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v)))
    )
    def rule_febre_amarela_dose_1_recommend_over_2(self):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose=1,
            explicacao="A primeira dose da vacina contra Febre Amarela é recomendada."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a),
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 9),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v))),
        NOT(DoseAplicada(vacina_codigo='SCR', data_aplicacao=P(is_recente))),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', data_aplicacao=P(is_recente))),
        NOT(DoseAplicada(vacina_codigo='VARICELA', data_aplicacao=P(is_recente)))
    )
    def rule_febre_amarela_dose_1_recommend_under_2(self):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose=1,
            explicacao="A primeira dose da vacina contra Febre Amarela é recomendada."
        ))

    # YF Booster
    @Rule(
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1, data_aplicacao=MATCH.d1),
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2)),
        NOT(AgendamentoFuturo(vacina="Febre Amarela", dose="Reforço"))
    )
    def rule_febre_amarela_booster_after_dose(self, d1, dn):
        d1_date = to_date(d1)
        dn_date = to_date(dn)
        data_alvo = max(dn_date + relativedelta(years=4), d1_date + relativedelta(days=30))
        if datetime.date.today() < data_alvo:
            self._schedule_fa_booster_generic(d1, dn)

    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a < 5),
        RecomendacaoImediata(vacina="Febre Amarela", dose=1),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1)),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2)),
        NOT(AgendamentoFuturo(vacina="Febre Amarela", dose="Reforço"))
    )
    def rule_febre_amarela_booster_after_recommendation(self, dn):
        self._schedule_fa_booster_generic(datetime.date.today(), dn)

    @Rule(
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=1, data_aplicacao=MATCH.d1),
        Idade(anos=MATCH.a),
        TEST(lambda a, d1: a >= 4 and a < 5 and (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2))
    )
    def rule_febre_amarela_booster_recommend_now(self):
        self.declare(RecomendacaoImediata(
            vacina="Febre Amarela", dose="Reforço",
            explicacao="Reforço da vacina contra Febre Amarela recomendado."
        ))

    # YF Catch-up
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 60),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')),
        NOT(ConflitoResolvido(vacinas=P(lambda v: 'Febre Amarela' in v)))
    )
    def rule_febre_amarela_single_dose_5_to_59(self, a):
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
    def rule_febre_amarela_catch_up_booster_after_5y_recommend(self, a):
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
    def rule_febre_amarela_catch_up_booster_after_5y_schedule(self, d1):
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
    def rule_febre_amarela_scheme_complete_after_5y(self, d1):
        self.declare(EsquemaCompleto(vacina="Febre Amarela", explicacao="Esquema de 1 dose única aplicada após os 5 anos completo.", data_ultima_dose=to_date(d1)))

    @Rule(DoseAplicada(vacina_codigo='FEBRE_AMARELA', dose=2, data_aplicacao=MATCH.data_dose))
    def rule_febre_amarela_scheme_complete_2_doses(self, data_dose):
        self.declare(EsquemaCompleto(vacina="Febre Amarela", explicacao="Esquema de 2 doses completo.", data_ultima_dose=to_date(data_dose)))

    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a >= 60), NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')))
    def rule_fa_contraindicated_elderly(self):
        self.declare(Contraindicacao(
            vacina="Febre Amarela",
            dose="Única",
            motivo="Não recomendada em rotina para idosos >= 60 anos.",
            explicacao=(
                "A vacina Febre Amarela não é indicada em rotina para idosos >= 60 anos "
                "devido ao risco aumentado de eventos adversos graves. "
                "Para residentes em áreas com circulação viral ativa, é necessária avaliação "
                "individual de comorbidades e risco-benefício pela equipe de saúde."
            )
        ))

    # =================================================================
    # SIMULTANEOUS USE RULES (LIVE VIRUS CONFLICTS < 2 YEARS)
    # =================================================================

    # 1. PRIORITIZATION: BOTH missing (YF and MMR D1) -> Prioritize MMR
    @Rule(
        Idade(anos=MATCH.a, meses=MATCH.m),
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 12),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')),
        NOT(DoseAplicada(vacina_codigo='SCR')),
        salience=100
    )
    def rule_prioritize_scr_over_yf(self):
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

    # 2. PRIORITIZATION: BOTH missing (YF and Varicella) -> Prioritize Varicella
    @Rule(
        Idade(anos=MATCH.a, meses=MATCH.m),
        TEST(lambda a, m: a < 2 and (a * 12 + m) >= 15),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA')),
        DoseAplicada(vacina_codigo='SCR', dose=1),
        NOT(DoseAplicada(vacina_codigo='VARICELA')),
        salience=100
    )
    def rule_prioritize_varicela_over_yf(self):
        self.declare(ConflitoResolvido(vacinas=['Varicela (atenuada)', 'Febre Amarela']))
        self.declare(RecomendacaoImediata(
            vacina='Varicela (atenuada)', dose=1,
            explicacao='Prioridade sobre Febre Amarela em < 2 anos. Aplicar Varicela agora e agendar FA para 30 dias.'
        ))
        data_alvo = datetime.date.today() + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina='Febre Amarela', dose=1,
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao='Agendada para 30 dias após a Varicela (intervalo obrigatório em < 2 anos).'
        ))

    # 3. INTERVAL: Recent YF -> Delay MMR or Varicella (or Tetraviral)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 2),
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=MATCH.data_fa),
        TEST(lambda data_fa: 0 <= (datetime.date.today() - to_date(data_fa)).days < 30),
        OR(
            NOT(DoseAplicada(vacina_codigo='SCR')),
            NOT(DoseAplicada(vacina_codigo='VARICELA')),
            NOT(DoseAplicada(vacina_codigo='TETRAVIRAL'))
        )
    )
    def rule_delay_mmr_due_to_recent_yf(self, data_fa):
        data_alvo = to_date(data_fa) + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina="SCR/Varicela", dose="Dose Pendente",
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao="Aguardar 30 dias após Febre Amarela (conflito de vírus vivo < 2 anos)."
        ))

    # 4. INTERVAL: Recent MMR or Varicella -> Delay YF
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a < 2),
        OR(
            DoseAplicada(vacina_codigo='SCR', data_aplicacao=MATCH.data_viva),
            DoseAplicada(vacina_codigo='VARICELA', data_aplicacao=MATCH.data_viva),
            DoseAplicada(vacina_codigo='TETRAVIRAL', data_aplicacao=MATCH.data_viva)
        ),
        TEST(lambda data_viva: 0 <= (datetime.date.today() - to_date(data_viva)).days < 30),
        NOT(DoseAplicada(vacina_codigo='FEBRE_AMARELA'))
    )
    def rule_delay_yf_due_to_recent_mmr(self, data_viva):
        data_alvo = to_date(data_viva) + relativedelta(days=30)
        self.declare(AgendamentoFuturo(
            vacina="Febre Amarela", dose=1,
            data_minima=data_alvo, data_recomendada=data_alvo,
            explicacao="Aguardar 30 dias após SCR/Varicela (conflito de vírus vivo < 2 anos)."
        ))

    # =================================================================
    # GENERAL SIMULTANEOUS USE RULES (VARICELLA vs OTHERS)
    # =================================================================

    # 1. RECENT YF -> SCHEDULE VARICELLA
    @Rule(
        DoseAplicada(vacina_codigo='FEBRE_AMARELA', data_aplicacao=MATCH.data_fa),
        TEST(lambda data_fa: 0 <= (datetime.date.today() - to_date(data_fa)).days < 30),
        Idade(anos=MATCH.a),
        OR(NOT(DoseAplicada(vacina_codigo='VARICELA')),
           NOT(DoseAplicada(vacina_codigo='SCR')))
    )
    def rule_general_scheduled_due_to_yf(self, data_fa, a):
        data_fa_data = to_date(data_fa)
        data_rec = data_fa_data + relativedelta(days=30)
        data_min_varicela = data_fa_data + relativedelta(days=15)

        if not self.get_dose_aplicada('VARICELA'):
             self.declare(AgendamentoFuturo(
                vacina="Varicela", dose=1,
                data_minima=data_min_varicela,
                data_recomendada=data_rec,
                explicacao="Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após a Febre Amarela."
            ))

        if a >= 2 and not self.get_dose_aplicada('SCR'):
            self.declare(AgendamentoFuturo(
                vacina="SCR (Tríplice Viral)", dose=1,
                data_minima=data_rec,
                data_recomendada=data_rec,
                explicacao="Aguardar 30 dias após a Febre Amarela (intervalo de vírus vivos)."
            ))

    # 2. RECENT VARICELLA OR MMR -> SCHEDULE YELLOW FEVER
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
    def rule_yf_scheduled_due_to_others(self, dose_fact, a):
        vacina_codigo_origem = dose_fact['vacina_codigo']
        data_viva = to_date(dose_fact['data_aplicacao'])

        data_rec = data_viva + relativedelta(days=30)

        if vacina_codigo_origem == 'VARICELA':
             data_min = data_viva + relativedelta(days=15)
             explicacao = f"Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após {vacina_codigo_origem}."
        else: # SCR
             data_min = data_rec  # 30 days
             explicacao = f"Agendada para 30 dias após {vacina_codigo_origem} (intervalo de vírus vivos)."

        if a < 2 and vacina_codigo_origem == 'SCR':
            pass  # Already handled by the specific < 2 year rule
        else:
            self.declare(AgendamentoFuturo(
                vacina="Febre Amarela",
                dose=1,
                data_minima=data_min,
                data_recomendada=data_rec,
                explicacao=explicacao
            ))

    # 3. RECENT MMR -> SCHEDULE VARICELLA (15 days min / 30 days recommended)
    @Rule(
        DoseAplicada(vacina_codigo='SCR', data_aplicacao=MATCH.data_scr),
        TEST(lambda data_scr: 0 <= (datetime.date.today() - to_date(data_scr)).days < 30),
        NOT(DoseAplicada(vacina_codigo='VARICELA', dose=1)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def rule_varicela_scheduled_due_to_mmr(self, data_scr):
        data_scr_data = to_date(data_scr)
        data_rec = data_scr_data + relativedelta(days=30)
        data_min = data_scr_data + relativedelta(days=15)

        self.declare(AgendamentoFuturo(
            vacina="Varicela", dose=1,
            data_minima=data_min,
            data_recomendada=data_rec,
            explicacao="Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após a SCR."
        ))

    # 4. RECENT VARICELLA -> SCHEDULE MMR (15 days min / 30 days recommended)
    @Rule(
        DoseAplicada(vacina_codigo='VARICELA', data_aplicacao=MATCH.data_var),
        TEST(lambda data_var: 0 <= (datetime.date.today() - to_date(data_var)).days < 30),
        NOT(DoseAplicada(vacina_codigo='SCR', dose=1)),
        NOT(DoseAplicada(vacina_codigo='TETRAVIRAL', dose=1))
    )
    def rule_mmr_scheduled_due_to_varicela(self, data_var):
        data_var_data = to_date(data_var)
        data_rec = data_var_data + relativedelta(days=30)
        data_min = data_var_data + relativedelta(days=15)

        self.declare(AgendamentoFuturo(
            vacina="SCR (Tríplice Viral)", dose=1,
            data_minima=data_min,
            data_recomendada=data_rec,
            explicacao="Aguardar intervalo recomendado de 30 dias (mínimo 15 dias) após a Varicela."
        ))

    # =================================================================
    # YELLOW FEVER — CONTRAINDICATION FOR ELDERLY (>= 60 years)
    # =================================================================

    # Helper to check whether a dose exists in the current context
    def get_dose_aplicada(self, codigo):
        for fact in self.facts.values():
            if isinstance(fact, DoseAplicada) and fact['vacina_codigo'] == codigo:
                return True
        return False

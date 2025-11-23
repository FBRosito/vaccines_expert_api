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

class RegrasMeningo(_RegrasBase):
    """
    Regras de vacinação para Meningocócica C (infantil)
    e Meningocócica ACWY (reforço infantil e adolescente).
    """

    # =================================================================
    # MENINGOCÓCICA C - ESQUEMA PRIMÁRIO (3 E 5 MESES)
    # =================================================================

    @Rule(
        Idade(meses=MATCH.m, dias=MATCH.d, data_nascimento=MATCH.dn), 
        TEST(lambda m: m < 3), 
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=1))
    )
    def regra_menc_d1_agendar(self, dn):
        dn_data = to_date(dn)
        data_agendada = dn_data + relativedelta(months=3)
        
        self.declare(AgendamentoFuturo(
            vacina="Meningocócica C",
            dose=1,
            data_minima=data_agendada,
            data_recomendada=data_agendada,
            explicacao="Agendamento da 1ª dose, recomendada aos 3 meses de idade."
        ))

    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a), 
        TEST(lambda a, m: a == 0 and m >= 3), 
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=1))
    )
    def regra_menc_d1_recomendar_agora_menor1ano(self, m):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", dose=1,
            explicacao=f"Paciente com {m} meses. A 1ª dose da Meningocócica C é recomendada aos 3 meses."
        ))

    # Agendar D2 (Futuro)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a == 0),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Meningocócica C", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2)),
        NOT(AgendamentoFuturo(vacina="Meningocócica C", dose=2)),
        TEST(lambda d1_data: datetime.date.today() < (to_date(d1_data) + relativedelta(months=2)))
    )
    def regra_menc_d2_agendar(self, d1_data):
        data_base = to_date(d1_data)
        self.declare(AgendamentoFuturo(
            vacina="Meningocócica C", dose=2,
            data_minima=data_base + relativedelta(days=30),
            data_recomendada=data_base + relativedelta(months=2),
            explicacao="A 2ª dose da Meningocócica C é agendada 2 meses após a 1ª dose."
        ))

    # Recomendar D2 (Agora - Apenas para < 12 meses)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a == 0),
        DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d1),
        TEST(lambda d1: (datetime.date.today() >= (to_date(d1) + relativedelta(days=30)))),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=2))
    )
    def regra_menc_d2_recomendar_agora_atrasada(self):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica C", 
            dose=2,
            explicacao="A 2ª dose da Meningocócica C está atrasada. Aplicar agora (intervalo mínimo de 30 dias)."
        ))
    
    # =================================================================
    # MENINGOCÓCICA ACWY - CATCH-UP / PRIMOVACINAÇÃO 1-4 ANOS
    # =================================================================

    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        NOT(DoseAplicada(vacina_codigo='MEN_C')),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_catchup_direto(self, a):
        """
        Para 1-4 anos SEM histórico: Recomenda ACWY Dose Única diretamente.
        Isso garante proteção contra 4 sorogrupos e simplifica o esquema tardio.
        """
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Dose Única",
            explicacao=f"Criança de {a} anos sem vacina prévia. Administrar dose única de Meningocócica ACWY (proteção ampliada)."
        ))

    # =================================================================
    # MENINGOCÓCICA ACWY - REFORÇO INFANTIL (12 meses - 4 anos)
    # =================================================================
    
    # 1. Agendar Reforço ACWY (Para quem tem < 12 meses e já tem Men-C D2)
    @Rule(
        Idade(meses=MATCH.m, anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a, m: (a * 12 + m) < 12),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=2, data_aplicacao=MATCH.d2_data),
            AgendamentoFuturo(vacina="Meningocócica C", dose=2, data_recomendada=MATCH.d2_data)
        ),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY')),
        NOT(AgendamentoFuturo(vacina="Meningocócica ACWY", dose="Reforço"))
    )
    def regra_menacwy_infantil_agendar(self, d2_data, dn):
        d2_res = to_date(d2_data)
        dn_res = to_date(dn)
        
        data_12m = dn_res + relativedelta(months=12)
        data_int = d2_res + relativedelta(days=60)
        data_final = max(data_12m, data_int)
        
        self.declare(AgendamentoFuturo(
            vacina="Meningocócica ACWY",
            dose="Reforço",
            data_minima=data_final,
            data_recomendada=data_final,
            explicacao="Reforço preferencial com Meningo ACWY aos 12 meses."
        ))

    # 2. Recomendar ACWY AGORA (Reforço para 1-4 anos com histórico de Men-C)
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 1 and a < 5),
        OR(
            DoseAplicada(vacina_codigo='MEN_C', dose=1, data_aplicacao=MATCH.d_antiga),
            DoseAplicada(vacina_codigo='MEN_C', dose=2, data_aplicacao=MATCH.d_antiga),
            DoseAplicada(vacina_codigo='MEN_C', dose="Única", data_aplicacao=MATCH.d_antiga)
        ),
        TEST(lambda d_antiga: datetime.date.today() >= (to_date(d_antiga) + relativedelta(days=30))), 
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_infantil_recomendar_agora(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Reforço",
            explicacao=f"Criança de {a} anos com histórico de Men-C. Recomendado reforço preferencial com ACWY."
        ))

    # =================================================================
    # MENINGOCÓCICA ACWY - ADOLESCENTE (11-14 ANOS)
    # =================================================================
    
    # Agendar para 11 anos
    @Rule(
        Idade(anos=MATCH.a, data_nascimento=MATCH.dn),
        TEST(lambda a: a >= 5 and a < 11),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY', dose=1))
    )
    def regra_menacwy_adolescente_agendar(self, dn):
        dn_data = to_date(dn)
        data_alvo = dn_data + relativedelta(years=11)

        self.declare(AgendamentoFuturo(
            vacina="Meningocócica ACWY",
            dose="Dose Única (Adolescente)",
            data_minima=data_alvo,
            data_recomendada=data_alvo,
            explicacao="Agendamento da dose de rotina para adolescentes (11 a 14 anos)."
        ))

    # Recomendação Imediata Adolescente (11-14 anos)
    @Rule(
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11 and a < 15),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menacwy_adolescente_recomendar(self, a):
        self.declare(RecomendacaoImediata(
            vacina="Meningocócica ACWY",
            dose="Dose Única (Adolescente)",
            explicacao=f"Adolescente com {a} anos. Recomendada dose única de Meningo ACWY."
        ))

    # =================================================================
    # CONCLUSÕES
    # =================================================================

    @Rule(
        DoseAplicada(vacina_codigo='MEN_ACWY', data_aplicacao=MATCH.d_acwy),
        Idade(anos=MATCH.a),
        TEST(lambda a: a >= 11)
    )
    def regra_menacwy_adolescente_completo(self, d_acwy):
        self.declare(EsquemaCompleto(
            vacina="Meningocócica ACWY",
            explicacao="Esquema encerrado com a dose de Meningocócica ACWY.",
            data_ultima_dose=to_date(d_acwy)
        ))

    @Rule(
        DoseAplicada(vacina_codigo='MEN_ACWY', data_aplicacao=MATCH.d_acwy),
        Idade(anos=MATCH.a),
        TEST(lambda a: a < 5)
    )
    def regra_menacwy_infantil_completo(self, d_acwy):
        self.declare(EsquemaCompleto(
            vacina="Meningocócica C", 
            explicacao="Esquema encerrado com a dose de Meningocócica ACWY.",
            data_ultima_dose=to_date(d_acwy)
        ))
    
    @Rule(
        Idade(anos=MATCH.a), TEST(lambda a: a >= 5 and a < 11),
        NOT(DoseAplicada(vacina_codigo='MEN_C', dose=3)),
        NOT(DoseAplicada(vacina_codigo='MEN_ACWY'))
    )
    def regra_menc_contraindicacao_idade(self):
        """Contraindicação Men-C > 5 anos (se não tomou reforço, perdeu oportunidade infantil)."""
        self.declare(Contraindicacao(
            vacina="Meningocócica C",
            dose="Reforço",
            motivo="Idade > 5 anos.",
            explicacao="O reforço infantil é até 4 anos, 11 meses e 29 dias. Aguardar idade para ACWY adolescente (11 anos)."
        ))
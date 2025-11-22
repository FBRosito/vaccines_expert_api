import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasRotavirus(_RegrasBase):
    """
    Regras para o Rotavírus (VORH), com fortes restrições de idade.
    """

    @Rule(
        Idade(dias=MATCH.d, data_nascimento=MATCH.dn), 
        TEST(lambda d: d < 45),
        NOT(DoseAplicada(vacina_codigo='VORH', dose=1))
    )
    def regra_vorh_d1_agendar(self, dn):
        """
        (Agendamento) Para crianças < 1m15d, agenda a D1
        para a data mínima (1m15d) e recomendada (2m).
        """
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        data_min = dn_data + relativedelta(days=45)
        data_rec = dn_data + relativedelta(months=2)
        
        self.declare(AgendamentoFuturo(
            vacina="Rotavírus (VORH)", 
            dose=1,
            data_minima=data_min,
            data_recomendada=data_rec,
            explicacao="Agendamento da 1ª dose, recomendada aos 2 meses (idade mínima de 1 mês e 15 dias)."
        ))

    @Rule(
        Idade(dias=MATCH.d), TEST(lambda d: d >= 45 and d <= 105), 
        NOT(DoseAplicada(vacina_codigo='VORH', dose=1))
    )
    def regra_vorh_d1_recomendar_agora(self):
        """
        (Recomendação) Recomenda a D1 se a criança está na janela
        de idade correta (1m 15d a 3m 15d).
        """
        self.declare(RecomendacaoImediata(
            vacina="Rotavírus (VORH)", dose=1,
            explicacao="A 1ª dose da vacina Rotavírus é recomendada aos 2 meses, e o paciente está na janela de idade permitida para aplicação (1 mês e 15 dias a 3 meses e 15 dias)."
        ))

    @Rule(
        Idade(dias=MATCH.dias_atuais, data_nascimento=MATCH.dn),
        TEST(lambda dias_atuais: dias_atuais <= 240),
        OR(
            DoseAplicada(vacina_codigo='VORH', dose=1, data_aplicacao=MATCH.d1_data),
            AgendamentoFuturo(vacina="Rotavírus (VORH)", dose=1, data_recomendada=MATCH.d1_data)
        ),
        NOT(DoseAplicada(vacina_codigo='VORH', dose=2)),
        NOT(AgendamentoFuturo(vacina="Rotavírus (VORH)", dose=2))
    )
    def regra_vorh_d2_agendar(self, d1_data, dn):
        """
        (Agendamento) Após D1, agenda D2.
        Respeita intervalos e a idade mínima da D2 (3m 15d).
        """
        d1_base = d1_data.date() if isinstance(d1_data, datetime.datetime) else d1_data
        dn_data = dn.date() if isinstance(dn, datetime.datetime) else dn
        
        data_min_int = d1_base + relativedelta(days=30)
        data_min_idade = dn_data + relativedelta(days=105)
        data_min_final = max(data_min_int, data_min_idade)

        data_rec_int = d1_base + relativedelta(months=2)
        data_rec_idade = dn_data + relativedelta(months=4)
        data_rec_final = max(data_rec_int, data_rec_idade, data_min_final)
        
        data_limite = dn_data + relativedelta(months=7, days=29)

        if data_min_final <= data_limite:
            self.declare(AgendamentoFuturo(
                vacina="Rotavírus (VORH)", dose=2,
                data_minima=data_min_final,
                data_recomendada=data_rec_final,
                explicacao="A 2ª dose da VORH é agendada com intervalo mínimo de 30 dias após a 1ª dose e deve ser aplicada a partir de 3 meses e 15 dias até os 7 meses e 29 dias de idade."
            ))

    @Rule(
        DoseAplicada(vacina_codigo='VORH', dose=1, data_aplicacao=MATCH.d1),
        Idade(dias=MATCH.dias_atuais),
        TEST(lambda dias_atuais, d1:
            (dias_atuais >= 105 and dias_atuais <= 240) and
            (datetime.date.today() >= ((d1.date() if isinstance(d1, datetime.datetime) else d1) + relativedelta(days=30)))
        ),
        NOT(DoseAplicada(vacina_codigo='VORH', dose=2))
    )
    def regra_vorh_d2_recomendar_agora_atrasada(self):
        """
        (Recomendação) Recomenda D2 imediata se na janela de idade
        (3m 15d a 7m 29d) e intervalo mínimo (30d) respeitado.
        """
        self.declare(RecomendacaoImediata(
            vacina="Rotavírus (VORH)", 
            dose=2,
            explicacao="A 2ª dose da VORH está na janela de aplicação (3m15d a 7m29d) e o intervalo mínimo de 30 dias da 1ª dose foi respeitado."
        ))

    @Rule(
        Idade(dias=MATCH.d), TEST(lambda d: d > 105), 
        NOT(DoseAplicada(vacina_codigo='VORH', dose=1))
    )
    def contraindicacao_vorh_idade_inicio(self, d):
        """
        (Contraindicação) Contraindica D1 se a criança
        tem > 3 meses e 15 dias.
        """
        self.declare(Contraindicacao(
            vacina="Rotavírus (VORH)",
            dose=1,
            motivo="Idade superior à permitida para a 1ª dose.",
            explicacao=f"A 1ª dose da vacina Rotavírus só pode ser aplicada até os 3 meses e 15 dias de vida. A idade do paciente ultrapassou este limite."
        ))
        
    @Rule(
        DoseAplicada(vacina_codigo='VORH', dose=1), 
        Idade(dias=MATCH.d), NOT(DoseAplicada(vacina_codigo='VORH', dose=2)), 
        TEST(lambda d: d > 240)
    )
    def contraindicacao_vorh_idade_dose2(self, d):
        """
        (Contraindicação) Contraindica D2 se a criança
        tem > 7 meses e 29 dias.
        """
        self.declare(Contraindicacao(
            vacina="Rotavírus (VORH)",
            dose=2,
            motivo="Idade superior à permitida para a 2ª dose.",
            explicacao=f"A 2ª dose da vacina Rotavírus só pode ser aplicada até os 7 meses e 29 dias de vida. A idade do paciente ultrapassou este limite."
        ))

    @Rule(
        DoseAplicada(vacina_codigo='VORH', dose=2, data_aplicacao=MATCH.d2_data)
    )
    def regra_vorh_esquema_completo(self, d2_data):
        """
        (Esquema Completo) Após a D2 da VORH,
        considera o esquema completo.
        """
        self.declare(EsquemaCompleto(
            vacina="Rotavírus (VORH)",
            explicacao="Esquema de 2 doses finalizado.",
            data_ultima_dose=d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data
        ))
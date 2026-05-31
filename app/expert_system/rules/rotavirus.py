import datetime
from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, OR, TEST, KnowledgeEngine
from dateutil.relativedelta import relativedelta

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .facts import Idade, DoseAplicada, RecomendacaoImediata, AgendamentoFuturo, Contraindicacao, EsquemaCompleto

class RegrasRotavirus(_RegrasBase):
    """
    Rules for Rotavirus (VORH), with strict age restrictions.
    """

    @Rule(
        Idade(dias=MATCH.d, data_nascimento=MATCH.dn),
        TEST(lambda d: d < 45),
        NOT(DoseAplicada(vacina_codigo='VORH', dose=1))
    )
    def rule_vorh_dose_1_schedule(self, dn):
        """
        (Scheduling) For children < 1m15d, schedules dose 1
        with minimum date (1m15d) and recommended date (2m).
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
    def rule_vorh_dose_1_recommend_now(self):
        """
        (Recommendation) Recommends dose 1 if the child is within the
        correct age window (1m 15d to 3m 15d).
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
    def rule_vorh_dose_2_schedule(self, d1_data, dn):
        """
        (Scheduling) After dose 1, schedules dose 2.
        Respects intervals and the minimum age for dose 2 (3m 15d).
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
    def rule_vorh_dose_2_recommend_now_late(self):
        """
        (Recommendation) Recommends immediate dose 2 if within the age window
        (3m 15d to 7m 29d) and the minimum interval (30d) has been respected.
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
    def contraindicated_vorh_start_age(self, d):
        """
        (Contraindication) Contraindicates dose 1 if the child
        is older than 3 months and 15 days.
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
    def contraindicated_vorh_dose_2_age(self, d):
        """
        (Contraindication) Contraindicates dose 2 if the child
        is older than 7 months and 29 days.
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
    def rule_vorh_scheme_complete(self, d2_data):
        """
        (Scheme Complete) After dose 2 of VORH,
        marks the scheme as complete.
        """
        self.declare(EsquemaCompleto(
            vacina="Rotavírus (VORH)",
            explicacao="Esquema de 2 doses finalizado.",
            data_ultima_dose=d2_data.date() if isinstance(d2_data, datetime.datetime) else d2_data
        ))

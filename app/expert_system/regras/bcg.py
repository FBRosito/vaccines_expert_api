from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, Contraindicacao, EsquemaCompleto

class RegrasBCG(_RegrasBase):
    """Vaccination rules for BCG (IN 2026 §1). Single-dose, birth to 4y 11m 29d."""

    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a < 5), NOT(DoseAplicada(vacina_codigo='BCG')))
    def rule_bcg_recommend_now(self):
        """(Recommendation) Child < 5 years with no prior BCG dose: recommend immediate application."""
        self.declare(RecomendacaoImediata(
            vacina="BCG",
            dose="Única",
            explicacao="Dose única recomendada o mais precocemente possível após o nascimento para proteger contra as formas graves de tuberculose (miliar e meníngea)."
        ))

    @Rule(DoseAplicada(vacina_codigo='BCG'))
    def rule_bcg_scheme_complete(self):
        """(Schedule complete) BCG dose on record: mark scheme as finished."""
        self.declare(EsquemaCompleto(
            vacina="BCG",
            explicacao="Esquema de dose única finalizado. Crianças vacinadas que não apresentam cicatriz não devem ser revacinadas."
        ))

    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a >= 5), NOT(DoseAplicada(vacina_codigo='BCG')))
    def rule_bcg_contraindicated_by_age(self):
        """(Contraindication) Child >= 5 years with no prior BCG dose: contraindicated by age limit."""
        self.declare(Contraindicacao(
            vacina="BCG",
            dose="Única",
            motivo="Idade superior a 4 anos, 11 meses e 29 dias.",
            explicacao="A vacina BCG é recomendada na rotina para crianças até 4 anos, 11 meses e 29 dias. Após essa idade, a aplicação não é mais indicada."
        ))

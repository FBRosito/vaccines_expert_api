from typing import TYPE_CHECKING
from experta import Rule, MATCH, NOT, TEST, KnowledgeEngine

if TYPE_CHECKING:
    _RegrasBase = KnowledgeEngine
else:
    _RegrasBase = object

from .fatos import Idade, DoseAplicada, RecomendacaoImediata, Contraindicacao, EsquemaCompleto

class RegrasBCG(_RegrasBase):
    """
    Regras de vacinação para a BCG.
    """

    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a < 5), NOT(DoseAplicada(vacina_codigo='BCG')))
    def regra_bcg_recomendar_agora(self):
        """
        (Recomendação) Para crianças < 5 anos sem dose, recomenda a aplicação imediata.
        """
        self.declare(RecomendacaoImediata(
            vacina="BCG",
            dose="Única",
            explicacao="Dose única recomendada o mais precocemente possível após o nascimento para proteger contra as formas graves de tuberculose (miliar e meníngea)."
        ))

    @Rule(DoseAplicada(vacina_codigo='BCG'))
    def regra_bcg_esquema_ok(self):
        """
        (Esquema Completo) Se a dose de BCG foi aplicada, considera o esquema completo.
        """
        self.declare(EsquemaCompleto(
            vacina="BCG",
            explicacao="Esquema de dose única finalizado. Crianças vacinadas que não apresentam cicatriz não devem ser revacinadas."
        ))

    @Rule(Idade(anos=MATCH.a), TEST(lambda a: a >= 5), NOT(DoseAplicada(vacina_codigo='BCG')))
    def regra_bcg_contraindicacao_idade(self):
        """
        (Contraindicação) Para crianças >= 5 anos sem dose, contraindica a aplicação.
        """
        self.declare(Contraindicacao(
            vacina="BCG",
            dose="Única",
            motivo="Idade superior a 4 anos, 11 meses e 29 dias.",
            explicacao="A vacina BCG é recomendada na rotina para crianças até 4 anos, 11 meses e 29 dias. Após essa idade, a aplicação não é mais indicada."
        ))
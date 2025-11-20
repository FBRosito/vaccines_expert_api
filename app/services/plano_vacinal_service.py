from typing import Optional
from datetime import datetime
from experta import KnowledgeEngine, DefFacts
from dateutil.relativedelta import relativedelta

from app.expert_system.regras.fatos import *

from app.expert_system.regras.bcg import RegrasBCG
from app.expert_system.regras.hepatite_b import RegrasHepatiteB
from app.expert_system.regras.penta_dtp import RegrasPentaDTP
from app.expert_system.regras.vip import RegrasVip
from app.expert_system.regras.rotavirus import RegrasRotavirus
from app.expert_system.regras.pneumo10 import RegrasPneumo10
from app.expert_system.regras.meningo import RegrasMeningo
from app.expert_system.regras.covid19 import RegrasCovid19
from app.expert_system.regras.hepatite_a import RegrasHepatiteA
from app.expert_system.regras.virus_vivos_atenuados import RegrasVirusVivosAtenuados
from app.expert_system.regras.dt_adulto import RegrasDTAdulto
from app.expert_system.regras.hpv import RegrasHPV

from app.repositories import log_repository
from app.repositories.models import PlanoVacinalLogModel

from app.utils.helpers import converter_datas_para_string


class PlanoVacinalService:
    def _montar_motor(self, data_nascimento: datetime.date) -> Optional[KnowledgeEngine]:
        """
        Seleciona os módulos de regras apropriados e monta uma classe de
        KnowledgeEngine dinamicamente para o paciente.
        """
        hoje = datetime.date.today()
        idade_anos = relativedelta(hoje, data_nascimento).years

        modulos_de_regras = [
            RegrasBCG,
            RegrasHepatiteB,
            RegrasPentaDTP,
            RegrasVip,
            RegrasRotavirus,
            RegrasPneumo10,
            RegrasMeningo,
            RegrasCovid19,
            RegrasHepatiteA,
            RegrasVirusVivosAtenuados,
            RegrasDTAdulto,
            RegrasHPV
        ]

        if not modulos_de_regras:
            return None

        MotorDinamico = type(
            'MotorDinamico',
            (*modulos_de_regras, KnowledgeEngine),
            {}
        )

        @DefFacts()
        def _fatos_iniciais(self):
            dn = self.paciente_dados['data_nascimento']
            hoje = datetime.date.today()
            yield Paciente(data_nascimento=dn)

            delta = relativedelta(hoje, dn)
            idade_meses_completos = delta.years * 12 + delta.months
            idade_dias_totais = (hoje - dn).days

            yield Idade(
                dias=idade_dias_totais, 
                meses=idade_meses_completos, 
                anos=delta.years,
                data_nascimento=dn
            )

            for vacina in self.carteira_dados:
                yield DoseAplicada(
                    vacina_codigo=vacina['vacina_codigo'],
                    data_aplicacao=vacina['data_aplicacao'],
                    dose=vacina.get('dose')
                )
        
        MotorDinamico._fatos_iniciais = _fatos_iniciais

        return MotorDinamico()

    def _coletar_resultados(self, engine: KnowledgeEngine) -> dict:
        """
        Coleta os fatos categorizados do motor, incluindo __factid__ para logging.
        """
        recomendadas = []
        aprazadas = []
        contraindicadas = []
        em_dia = []

        for fact in engine.facts.values():
            if isinstance(fact, RecomendacaoImediata):
                recomendadas.append(dict(fact))
            elif isinstance(fact, AgendamentoFuturo):
                aprazadas.append(dict(fact))
            elif isinstance(fact, Contraindicacao):
                contraindicadas.append(dict(fact))
            elif isinstance(fact, EsquemaCompleto):
                em_dia.append(dict(fact))
        
        aprazadas.sort(key=lambda x: x.get('data_recomendada', ''))

        return {
            "vacinas_recomendadas": recomendadas,
            "vacinas_aprazadas": aprazadas,
            "vacinas_contraindicadas": contraindicadas,
            "vacinas_em_dia": em_dia
        }

    def gerar_plano_e_auditar(self, dados_paciente: dict) -> dict:
        """
        Gera o plano vacinal e audita com logs.
        """
        paciente_info = dados_paciente['paciente']
        carteira_info = dados_paciente.get('carteira_vacinacao', [])
        
        self._paciente_dados = paciente_info
        self._carteira_dados = carteira_info

        engine = self._montar_motor(paciente_info['data_nascimento'])

        if not engine:
            return {"erro": "Nenhum calendário vacinal aplicável para a idade informada."}

        setattr(engine, 'paciente_dados', self._paciente_dados)
        setattr(engine, 'carteira_dados', self._carteira_dados)
        
        engine.reset()
        engine.run()

        # 1. Coleta os resultados completos, com o __factid__
        plano_gerado_completo = self._coletar_resultados(engine)

        # 2. Usa os resultados completos para o log de auditoria
        try:
            input_serializavel = converter_datas_para_string(dados_paciente)
            # A saída para o log contém o __factid__
            output_serializavel = converter_datas_para_string(plano_gerado_completo)
            
            log_params = {
                'paciente_sexo': paciente_info['sexo'],
                'numero_doses_recebidas': len(carteira_info),
                'request_input': input_serializavel,
                'response_output': output_serializavel
            }
            if paciente_info.get('data_nascimento'):
                log_params['paciente_data_nascimento'] = paciente_info['data_nascimento']
            novo_log = PlanoVacinalLogModel(**log_params)
            log_repository.salvar_log(novo_log)
        except Exception as e:
            print(f"ERRO ao salvar o log de auditoria: {e}")
        
        # 3. Prepara a resposta para o cliente, REMOVENDO o __factid__
        plano_para_cliente = {}
        for categoria, lista_de_fatos in plano_gerado_completo.items():
            lista_limpa = []
            for fato_dict in lista_de_fatos:
                fato_limpo = fato_dict.copy()
                fato_limpo.pop('__factid__', None)
                lista_limpa.append(fato_limpo)
            plano_para_cliente[categoria] = lista_limpa

        # 4. Retorna a versão limpa
        return plano_para_cliente

from typing import Optional
from datetime import datetime
from experta import KnowledgeEngine, DefFacts
from dateutil.relativedelta import relativedelta
import uuid

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
from app.expert_system.regras.influenza import RegrasInfluenza

from app.repositories import log_repository
from app.repositories.models import PlanoVacinalLogModel

from app.utils.helpers import converter_datas_para_string

# --- MAPA DE NOMES DE VACINAS (DO EXPERTA) PARA CÓDIGOS SIPNI (RNDS) ---
MAPA_NOME_PARA_SIPNI = {
    "BCG": "01",
    "Hepatite B": "06",
    "Penta": "42",
    "DTP (Tríplice Bacteriana)": "14",
    "VIP (Poliomielite)": "22",
    "Rotavírus (VORH)": "41",
    "Pneumocócica 10V": "17",
    "Meningocócica C": "29",
    "Meningocócica ACWY": "54",
    "Influenza": "33",
    "Febre Amarela": "05",
    "SCR (Tríplice Viral)": "21",
    "Tetraviral (SCR-V)": "30",
    "SCRV (Tetraviral)": "30",
    "Varicela": "13",
    "Varicela (atenuada)": "13",
    "Hepatite A": "15",
    "HPV": "49",
    "dT (Dupla Adulto)": "37",
    "COVID-19": "103", 
    "COVID-19 (Pfizer)": "103",
    "COVID-19 (Moderna)": "107",
    "COVID-19 (Pfizer ou Moderna)": "103",
    "COVID-19 (Reforço)": "103"
}

# --- MAPA DE DOSES PARA ESQUEMAS COMPLETOS (FALLBACK) ---
MAPA_DOSE_PADRAO_COMPLETA = {
    "BCG": "Única",
    "Hepatite B (ao nascer)": "Única",
    "Hepatite B (esquema adulto)": "3",
    "Penta": "3",
    "DTP (Tríplice Bacteriana)": "2º Reforço",
    "VIP (Poliomielite)": "Reforço",
    "Rotavírus (VORH)": "2",
    "Pneumocócica 10V": "Reforço",
    "Meningocócica C": "Reforço",
    "Meningocócica ACWY": "Única",
    "Influenza": "Anual",
    "Febre Amarela": "Reforço",
    "SCR (Tríplice Viral)": "2",
    "Tetraviral (SCR-V)": "Única",
    "Varicela (atenuada)": "2",
    "Hepatite A": "Única",
    "HPV": "Única",
    "dT (Dupla Adulto)": "Reforço",
    "COVID-19": "Completo",
    "COVID-19 (Pfizer)": "3",
    "COVID-19 (Moderna)": "2"
}

class PlanoVacinalService:
    def _montar_motor(self) -> Optional[KnowledgeEngine]:
        hoje = datetime.date.today()

        modulos_de_regras = [
            RegrasBCG, RegrasHepatiteB, RegrasPentaDTP, RegrasVip, RegrasRotavirus,
            RegrasPneumo10, RegrasMeningo, RegrasCovid19, RegrasHepatiteA,
            RegrasVirusVivosAtenuados, RegrasDTAdulto, RegrasHPV, RegrasInfluenza
        ]

        if not modulos_de_regras:
            return None

        MotorDinamico = type('MotorDinamico', (*modulos_de_regras, KnowledgeEngine), {})

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

    def _converter_para_fhir_bundle(self, plano_interno: dict) -> dict:
        bundle_id = str(uuid.uuid4())
        fhir_bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "collection",
            "timestamp": datetime.datetime.now().isoformat(),
            "entry": []
        }

        def criar_recurso_recommendation(item, status_fhir, data_criterio=None):
            nome_vacina = item.get('vacina', 'Desconhecida')
            codigo_sipni = MAPA_NOME_PARA_SIPNI.get(nome_vacina, "99")

            dose_str = str(item.get('dose', 'Unknown'))
            if (dose_str == 'Unknown' or dose_str == 'None') and status_fhir == 'complete':
                dose_str = MAPA_DOSE_PADRAO_COMPLETA.get(nome_vacina, "Completo")

            resource = {
                "resourceType": "ImmunizationRecommendation",
                "date": datetime.date.today().isoformat(),
                "recommendation": [{
                    "vaccineCode": {
                        "coding": [{
                            "system": "http://www.saude.gov.br/fhir/rnds/CodeSystem/br-imunobiologico",
                            "code": codigo_sipni,
                            "display": nome_vacina
                        }]
                    },
                    "forecastStatus": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status",
                            "code": status_fhir,
                            "display": status_fhir.capitalize()
                        }]
                    },
                    "doseNumberString": dose_str,
                    "description": item.get('explicacao') or item.get('motivo')
                }]
            }

            if data_criterio:
                resource["recommendation"][0]["dateCriterion"] = data_criterio

            return {"resource": resource}

        # 1. Recomendadas (Imediata)
        for item in plano_interno["vacinas_recomendadas"]:
            data_criterio = [{
                "code": {"coding": [{"system": "http://loinc.org", "code": "30980-7", "display": "Date forecast"}]},
                "value": datetime.date.today().isoformat()
            }]
            fhir_bundle["entry"].append(criar_recurso_recommendation(item, "due", data_criterio))

        # 2. Aprazadas (Futuro)
        for item in plano_interno["vacinas_aprazadas"]:
            data_min = item.get('data_minima')
            data_rec = item.get('data_recomendada')
            
            criterios = []
            if data_rec:
                criterios.append({
                    "code": {"coding": [{"system": "http://loinc.org", "code": "30980-7", "display": "Date forecast"}]},
                    "value": data_rec.isoformat() if hasattr(data_rec, 'isoformat') else str(data_rec)
                })
            if data_min:
                criterios.append({
                    "code": {"coding": [{"system": "http://loinc.org", "code": "30981-5", "display": "Earliest date"}]},
                    "value": data_min.isoformat() if hasattr(data_min, 'isoformat') else str(data_min)
                })
            
            fhir_bundle["entry"].append(criar_recurso_recommendation(item, "due", criterios))

        # 3. Contraindicadas
        for item in plano_interno["vacinas_contraindicadas"]:
            fhir_bundle["entry"].append(criar_recurso_recommendation(item, "contraindicated"))

        # 4. Em Dia
        for item in plano_interno["vacinas_em_dia"]:
            fhir_bundle["entry"].append(criar_recurso_recommendation(item, "complete"))

        return fhir_bundle

    def gerar_plano_e_auditar(self, dados_paciente: dict) -> dict:
        paciente_info = dados_paciente['paciente']
        carteira_info = dados_paciente.get('carteira_vacinacao', [])
        
        self._paciente_dados = paciente_info
        self._carteira_dados = carteira_info

        engine = self._montar_motor()

        if not engine:
            return {"erro": "Nenhum calendário vacinal aplicável."}

        setattr(engine, 'paciente_dados', self._paciente_dados)
        setattr(engine, 'carteira_dados', self._carteira_dados)
        
        engine.reset()
        engine.run()

        plano_interno = self._coletar_resultados(engine)

        try:
            plano_fhir = self._converter_para_fhir_bundle(plano_interno)
        except Exception as e:
            print(f"Erro na conversão FHIR: {e}")
            return {"erro": f"Falha ao converter resposta para FHIR: {str(e)}"}

        try:
            input_str = converter_datas_para_string(dados_paciente)
            output_str = converter_datas_para_string(plano_fhir)
            
            log_params = {
                'paciente_sexo': paciente_info['sexo'],
                'numero_doses_recebidas': len(carteira_info),
                'request_input': input_str,
                'response_output': output_str
            }
            if paciente_info.get('data_nascimento'):
                log_params['paciente_data_nascimento'] = paciente_info['data_nascimento']
            
            novo_log = PlanoVacinalLogModel(**log_params)
            log_repository.salvar_log(novo_log)
        except Exception as e:
            print(f"ERRO ao salvar log: {e}")
        
        return plano_fhir

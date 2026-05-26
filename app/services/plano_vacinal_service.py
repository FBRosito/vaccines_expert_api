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
from app.expert_system.regras.pneumo23 import RegrasPneumo23
from app.expert_system.regras.meningo import RegrasMeningo
from app.expert_system.regras.covid19 import RegrasCovid19
from app.expert_system.regras.hepatite_a import RegrasHepatiteA
from app.expert_system.regras.virus_vivos_atenuados import RegrasVirusVivosAtenuados
from app.expert_system.regras.dt_adulto import RegrasDTAdulto
from app.expert_system.regras.hpv import RegrasHPV
from app.expert_system.regras.influenza import RegrasInfluenza
from app.expert_system.regras.dengue import RegrasDengue

from app.repositories import log_repository
from app.repositories.models import PlanoVacinalLogModel

import logging
from app.utils.helpers import convert_dates_to_str

logger = logging.getLogger(__name__)

# --- Vaccine name → SIPNI code mapping (internal Experta names → RNDS/SIPNI codes) ---
# Reference: http://www.saude.gov.br/fhir/r4/CodeSystem/BRImunobiologico
MAPA_NOME_PARA_SIPNI = {
    "BCG": "15",
    "Hepatite B": "9",
    "Hepatite B (ao nascer)": "9",
    "Hepatite B (esquema adulto)": "9",
    "Penta": "42",
    "DTP (Tríplice Bacteriana)": "46",
    "VIP (Poliomielite)": "22",
    "Rotavírus (VORH)": "45",
    "Pneumocócica 10V": "26",
    "Pneumocócica 23V": "21",
    "Meningocócica C": "41",
    "Meningocócica ACWY": "74",
    "Influenza": "33",
    "Febre Amarela": "14",
    "SCR (Tríplice Viral)": "24",
    "Tetraviral (SCR-V)": "56",
    "SCRV (Tetraviral)": "56",
    "Varicela": "34",
    "Varicela (atenuada)": "34",
    "Hepatite A": "55",
    "HPV": "67",
    "dT (Dupla Adulto)": "25",
    "Dengue": "104",
    "COVID-19": "102",
    "COVID-19 (Pfizer)": "102",
    "COVID-19 (Pfizer ou Moderna)": "102",
    "COVID-19 (Moderna)": "97",
    "COVID-19 (Reforço)": "87",
}

# --- Default dose label for completed schedules (used as FHIR fallback) ---
MAPA_DOSE_PADRAO_COMPLETA = {
    "BCG": "Única",
    "Hepatite B (ao nascer)": "Única",
    "Hepatite B (esquema adulto)": "3",
    "Penta": "3",
    "DTP (Tríplice Bacteriana)": "2º Reforço",
    "VIP (Poliomielite)": "Reforço",
    "Rotavírus (VORH)": "2",
    "Pneumocócica 10V": "Reforço",
    "Pneumocócica 23V": "2",
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
    "Dengue": "2",
    "COVID-19": "Completo",
    "COVID-19 (Pfizer)": "3",
    "COVID-19 (Moderna)": "2"
}

class PlanoVacinalService:
    def _build_engine(self) -> Optional[KnowledgeEngine]:
        """Assemble all 15 rule modules into a single Experta KnowledgeEngine instance."""
        rule_modules = [
            RegrasBCG, RegrasHepatiteB, RegrasPentaDTP, RegrasVip, RegrasRotavirus,
            RegrasPneumo10, RegrasPneumo23, RegrasMeningo, RegrasCovid19, RegrasHepatiteA,
            RegrasVirusVivosAtenuados, RegrasDTAdulto, RegrasHPV, RegrasInfluenza,
            RegrasDengue
        ]

        if not rule_modules:
            return None

        DynamicEngine = type('DynamicEngine', (*rule_modules, KnowledgeEngine), {})

        @DefFacts()
        def _initial_facts(self):
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

        DynamicEngine._initial_facts = _initial_facts
        return DynamicEngine()

    def _collect_results(self, engine: KnowledgeEngine) -> dict:
        """Collect all output facts from the engine into a structured dict."""
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

    def _to_fhir_bundle(self, plano_interno: dict) -> dict:
        """Convert the internal vaccination plan dict to an HL7 FHIR Bundle."""
        bundle_id = str(uuid.uuid4())
        fhir_bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "collection",
            "timestamp": datetime.datetime.now().isoformat(),
            "entry": []
        }

        def build_recommendation_resource(item, status_fhir, data_criterio=None):
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
                            "system": "http://www.saude.gov.br/fhir/r4/CodeSystem/BRImunobiologico",
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

        # 1. Immediate recommendations
        for item in plano_interno["vacinas_recomendadas"]:
            data_criterio = [{
                "code": {"coding": [{"system": "http://loinc.org", "code": "30980-7", "display": "Date forecast"}]},
                "value": datetime.date.today().isoformat()
            }]
            fhir_bundle["entry"].append(build_recommendation_resource(item, "due", data_criterio))

        # 2. Scheduled (future doses)
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
            
            fhir_bundle["entry"].append(build_recommendation_resource(item, "due", criterios))

        # 3. Contraindicated
        for item in plano_interno["vacinas_contraindicadas"]:
            fhir_bundle["entry"].append(build_recommendation_resource(item, "contraindicated"))

        # 4. Up to date
        for item in plano_interno["vacinas_em_dia"]:
            fhir_bundle["entry"].append(build_recommendation_resource(item, "complete"))

        return fhir_bundle

    def generate_plan_and_audit(self, dados_paciente: dict) -> dict:
        """Run the inference engine for a patient and persist an audit log entry."""
        paciente_info = dados_paciente['paciente']
        carteira_info = dados_paciente.get('carteira_vacinacao', [])

        self._paciente_dados = paciente_info
        self._carteira_dados = carteira_info

        engine = self._build_engine()

        if not engine:
            return {"erro": "Nenhum calendário vacinal aplicável."}

        setattr(engine, 'paciente_dados', self._paciente_dados)
        setattr(engine, 'carteira_dados', self._carteira_dados)

        engine.reset()
        engine.run()

        plano_interno = self._collect_results(engine)

        try:
            plano_fhir = self._to_fhir_bundle(plano_interno)
        except Exception as e:
            logger.error("FHIR conversion error: %s", e)
            return {"erro": f"Falha ao converter resposta para FHIR: {str(e)}"}

        try:
            input_str = convert_dates_to_str(dados_paciente)
            output_str = convert_dates_to_str(plano_fhir)

            log_params = {
                'paciente_sexo': paciente_info['sexo'],
                'numero_doses_recebidas': len(carteira_info),
                'request_input': input_str,
                'response_output': output_str
            }
            if paciente_info.get('data_nascimento'):
                log_params['paciente_data_nascimento'] = paciente_info['data_nascimento']

            novo_log = PlanoVacinalLogModel(**log_params)
            log_repository.save_log(novo_log)
        except Exception as e:
            logger.error("Failed to save audit log: %s", e)

        return plano_fhir

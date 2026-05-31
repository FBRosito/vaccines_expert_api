from typing import Optional
from datetime import datetime
from experta import KnowledgeEngine, DefFacts
from dateutil.relativedelta import relativedelta
import uuid

from app.expert_system.rules.facts import *

from app.expert_system.rules.bcg import RulesBCG
from app.expert_system.rules.hepatitis_b import RulesHepatitisB
from app.expert_system.rules.penta_dtp import RulesPentaDTP
from app.expert_system.rules.vip import RulesVip
from app.expert_system.rules.rotavirus import RulesRotavirus
from app.expert_system.rules.pneumo10 import RulesPneumo10
from app.expert_system.rules.pneumo23 import RulesPneumo23
from app.expert_system.rules.meningo import RulesMeningo
from app.expert_system.rules.covid19 import RulesCovid19
from app.expert_system.rules.hepatitis_a import RulesHepatitisA
from app.expert_system.rules.live_attenuated_viruses import RulesLiveAttenuatedViruses
from app.expert_system.rules.dt_adult import RulesDTAdult
from app.expert_system.rules.hpv import RulesHPV
from app.expert_system.rules.influenza import RulesInfluenza
from app.expert_system.rules.dengue import RulesDengue

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

class VaccinationPlanService:
    def _build_engine(self) -> Optional[KnowledgeEngine]:
        """Assemble all 15 rule modules into a single Experta KnowledgeEngine instance."""
        rule_modules = [
            RulesBCG, RulesHepatitisB, RulesPentaDTP, RulesVip, RulesRotavirus,
            RulesPneumo10, RulesPneumo23, RulesMeningo, RulesCovid19, RulesHepatitisA,
            RulesLiveAttenuatedViruses, RulesDTAdult, RulesHPV, RulesInfluenza,
            RulesDengue
        ]

        if not rule_modules:
            return None

        DynamicEngine = type('DynamicEngine', (*rule_modules, KnowledgeEngine), {})

        @DefFacts()
        def _initial_facts(self):
            dn = self.paciente_dados['birth_date']
            hoje = datetime.date.today()
            yield Patient(birth_date=dn)

            delta = relativedelta(hoje, dn)
            idade_meses_completos = delta.years * 12 + delta.months
            idade_dias_totais = (hoje - dn).days

            yield Age(
                days=idade_dias_totais,
                months=idade_meses_completos,
                years=delta.years,
                birth_date=dn
            )

            for vacina in self.carteira_dados:
                yield AppliedDose(
                    vaccine_code=vacina['vaccine_code'],
                    date_applied=vacina['date_applied'],
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
            if isinstance(fact, ImmediateRecommendation):
                recomendadas.append(dict(fact))
            elif isinstance(fact, FutureSchedule):
                aprazadas.append(dict(fact))
            elif isinstance(fact, Contraindication):
                contraindicadas.append(dict(fact))
            elif isinstance(fact, CompletedSchedule):
                em_dia.append(dict(fact))
        
        aprazadas.sort(key=lambda x: x.get('recommended_date', ''))

        return {
            "recommended_vaccines": recomendadas,
            "scheduled_vaccines": aprazadas,
            "contraindicated_vaccines": contraindicadas,
            "up_to_date_vaccines": em_dia
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
            nome_vacina = item.get('vaccine', 'Desconhecida')
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
                    "description": item.get('explanation') or item.get('reason')
                }]
            }

            if data_criterio:
                resource["recommendation"][0]["dateCriterion"] = data_criterio

            return {"resource": resource}

        # 1. Immediate recommendations
        for item in plano_interno["recommended_vaccines"]:
            data_criterio = [{
                "code": {"coding": [{"system": "http://loinc.org", "code": "30980-7", "display": "Date forecast"}]},
                "value": datetime.date.today().isoformat()
            }]
            fhir_bundle["entry"].append(build_recommendation_resource(item, "due", data_criterio))

        # 2. Scheduled (future doses)
        for item in plano_interno["scheduled_vaccines"]:
            data_min = item.get('min_date')
            data_rec = item.get('recommended_date')
            
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
        for item in plano_interno["contraindicated_vaccines"]:
            fhir_bundle["entry"].append(build_recommendation_resource(item, "contraindicated"))

        # 4. Up to date
        for item in plano_interno["up_to_date_vaccines"]:
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
                'paciente_sexo': paciente_info['sex'],
                'numero_doses_recebidas': len(carteira_info),
                'request_input': input_str,
                'response_output': output_str
            }
            if paciente_info.get('birth_date'):
                log_params['paciente_data_nascimento'] = paciente_info['birth_date']

            novo_log = PlanoVacinalLogModel(**log_params)
            log_repository.save_log(novo_log)
        except Exception as e:
            logger.error("Failed to save audit log: %s", e)

        return plano_fhir

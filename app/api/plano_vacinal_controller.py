import logging
from flask import jsonify, request
from app import limiter
from marshmallow import ValidationError
from . import api_bp
from datetime import date, datetime

logger = logging.getLogger(__name__)

from app.schemas.plano_vacinal_schema import FHIRBundleSchema
from app.services.plano_vacinal_service import PlanoVacinalService

# --- SIPNI (RNDS) code → internal rule engine code translation map ---
# Reference: http://www.saude.gov.br/fhir/r4/CodeSystem/BRImunobiologico
DE_PARA_SIPNI_INTERNO = {
    # ======================================================================
    # Official SIPNI codes (BRImunobiologico code system)
    # ======================================================================
    "15": "BCG",                # BCG
    "9":  "HEPATITE_B",         # Hepatite B recombinante
    "42": "PENTA",              # Penta (DTP/HB/Hib)
    "46": "DTP",                # DTP (Tríplice Bacteriana)
    "22": "VIP",                # Poliomielite Inativada
    "45": "VORH",               # Rotavírus Humano G1P[8]
    "26": "PNEUMO10",           # Pneumocócica 10V conjugada
    "41": "MEN_C",              # Meningocócica C conjugada
    "74": "MEN_ACWY",           # Meningocócica ACWY conjugada
    "33": "INFLUENZA",          # Influenza trivalente
    "14": "FEBRE_AMARELA",      # Febre Amarela atenuada
    "24": "SCR",                # Tríplice Viral (SCR)
    "56": "TETRAVIRAL",         # Tetraviral (SCR-V)
    "34": "VARICELA",           # Varicela atenuada
    "55": "HEPATITE_A",         # Hepatite A inativada infantil
    "67": "HPV",                # HPV quadrivalente (6, 11, 16, 18)
    "25": "dT",                 # Difteria e Tétano adulto
    "21": "PNEUMO23",           # Pneumocócica 23V (VPP23)
    "104": "DENGUE",            # Dengue atenuada (Qdenga)
    # COVID-19 — multiple formulations mapped to a unified internal code
    "102": "COVID19_PFIZER",    # COVID-19 Pfizer pediátrica <5 anos
    "87":  "COVID19_PFIZER",    # COVID-19 Pfizer adulto (Comirnaty)
    "103": "COVID19_PFIZER",    # COVID-19 Pfizer bivalente
    "97":  "COVID19_MODERNA",   # COVID-19 Moderna (Spikevax)
    "105": "COVID19_MODERNA",   # COVID-19 Moderna bivalente
    # ======================================================================
    # Legacy codes (backward compatibility — no key conflicts)
    # ======================================================================
    "01": "BCG",                # legado: usar "15"
    "06": "HEPATITE_B",         # legado: usar "9"
    "05": "FEBRE_AMARELA",      # legado: usar "14"
    "17": "PNEUMO10",           # legado: usar "26"
    "29": "MEN_C",              # legado: usar "41"
    "54": "MEN_ACWY",           # legado: usar "74"
    "30": "TETRAVIRAL",         # legado: usar "56"
    "13": "VARICELA",           # legado: usar "34"
    "49": "HPV",                # legado: usar "67"
    "37": "dT",                 # legado: usar "25"
    # Removidos (conflito com código oficial de outra vacina):
    # "21" era SCR → SCR usa "24"; "21" agora é PNEUMO23
    # "107" era COVID19_MODERNA → "107" é VPC20 (Pneumo20); Moderna usa "97"
    # "41" era VORH → "41" agora é MEN_C; VORH usa "45"
    # "14" era DTP → "14" agora é FEBRE_AMARELA; DTP usa "46"
    # "15" era HEPATITE_A → "15" agora é BCG; Hepatite A usa "55"
}

def _parse_data_iso(data_str):
    """Parse an ISO date string (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) to a date object."""
    if not data_str:
        return None
    if isinstance(data_str, (date, datetime)):
        return data_str if isinstance(data_str, date) else data_str.date()
        
    try:
        return date.fromisoformat(str(data_str)[:10])
    except ValueError:
        return None

def _adaptar_fhir_para_interno(fhir_data):
    """
    Anti-Corruption Layer: convert an RNDS-compliant FHIR Bundle to the flat internal
    dict format that PlanoVacinalService expects. Performs explicit date parsing (str → date).
    """
    paciente = None
    carteira = []

    for entry in fhir_data.get('entry', []):
        resource = entry.get('resource', {})
        r_type = resource.get('resourceType')

        if r_type == 'Patient':
            # Map FHIR Patient → internal patient dict
            sexo_map = {
                'male': 'Masculino', 
                'female': 'Feminino', 
                'other': 'Outro', 
                'unknown': 'Outro'
            }
            
            data_nasc_obj = _parse_data_iso(resource.get('birthDate'))

            paciente = {
                'data_nascimento': data_nasc_obj,
                'sexo': sexo_map.get(resource.get('gender'), 'Outro')
            }
        
        elif r_type == 'Immunization':
            # Map FHIR Immunization → internal DoseAplicada dict
            
            codings = resource.get('vaccineCode', {}).get('coding', [])
            codigo_sipni = codings[0].get('code') if codings else None
            
            codigo_interno = None
            if codigo_sipni:
                codigo_interno = DE_PARA_SIPNI_INTERNO.get(str(codigo_sipni))

            protocolos = resource.get('protocolApplied', [])
            dose_info = protocolos[0] if protocolos else {}
            dose_valor = dose_info.get('doseNumberPositiveInt') or dose_info.get('doseNumberString')

            data_aplicacao_obj = _parse_data_iso(resource.get('occurrenceDateTime'))

            if codigo_interno and dose_valor and data_aplicacao_obj:
                carteira.append({
                    'vacina_codigo': codigo_interno,
                    'data_aplicacao': data_aplicacao_obj,
                    'dose': dose_valor
                })

    return {'paciente': paciente, 'carteira_vacinacao': carteira}

@limiter.limit("10 per minute")
@api_bp.route('/simulador/plano-vacinal', methods=['POST'])
def get_vaccination_plan():
    """FHIR-compliant endpoint (RNDS). Accepts a FHIR Bundle and returns an ImmunizationRecommendation Bundle."""
    logger.info("POST /simulador/plano-vacinal accessed.")

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erros": "Nenhum dado fornecido."}), 400

    # 1. Structural validation (FHIR schema)
    schema = FHIRBundleSchema()
    try:
        dados_fhir_validos = schema.load(json_data)
    except ValidationError as err:
        return jsonify({"erros": err.messages, "tipo": "Erro de Validação FHIR"}), 400

    # 2. Adapt FHIR Bundle → internal Python object model
    try:
        dados_internos = _adaptar_fhir_para_interno(dados_fhir_validos)
        
        if not dados_internos['paciente']:
            return jsonify({"erros": "O Bundle deve conter pelo menos um recurso 'Patient'."}), 400
        
        if not dados_internos['paciente']['data_nascimento']:
             return jsonify({"erros": "Data de nascimento inválida ou ausente no recurso Patient."}), 400
            
    except Exception as e:
        return jsonify({"erros": f"Erro ao processar dados FHIR: {str(e)}"}), 400

    # 3. Run the inference engine
    servico = PlanoVacinalService()
    plano = servico.generate_plan_and_audit(dados_internos)

    if not plano:
        return jsonify({"erros": "Erro interno ao gerar o plano."}), 500

    logger.info("Vaccination plan generated successfully.")
    return jsonify(plano)

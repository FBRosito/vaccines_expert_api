from flask import jsonify, request
from app import limiter
from marshmallow import ValidationError
from . import api_bp
from datetime import date, datetime

from app.schemas.plano_vacinal_schema import FHIRBundleSchema
from app.services.plano_vacinal_service import PlanoVacinalService

# --- MAPA DE TRADUÇÃO: CÓDIGOS SIPNI (RNDS) -> CÓDIGOS INTERNOS (REGRAS) ---
DE_PARA_SIPNI_INTERNO = {
    "01": "BCG",
    "06": "HEPATITE_B",
    "42": "PENTA",
    "14": "DTP",
    "22": "VIP",
    "41": "VORH",
    "17": "PNEUMO10",
    "29": "MEN_C",
    "54": "MEN_ACWY",
    "33": "INFLUENZA",
    "05": "FEBRE_AMARELA",
    "21": "SCR",
    "30": "TETRAVIRAL",
    "13": "VARICELA",
    "15": "HEPATITE_A",
    "49": "HPV",
    "37": "dT",
    # Vacinas COVID-19 Específicas
    "103": "COVID19_PFIZER",
    "107": "COVID19_MODERNA"
}

def _parse_data_iso(data_str):
    """Converte string ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS) para objeto date."""
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
    Função Adaptadora (Anti-Corruption Layer).
    Converte o Bundle FHIR (padrão RNDS) para o formato plano interno que o Service espera.
    Realiza o parsing explícito de datas (String -> Date Object).
    """
    paciente = None
    carteira = []

    for entry in fhir_data.get('entry', []):
        resource = entry.get('resource', {})
        r_type = resource.get('resourceType')

        if r_type == 'Patient':
            # Mapeia Patient FHIR -> Objeto Paciente Interno
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
            # Mapeia Immunization FHIR -> DoseAplicada Interna
            
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
def obter_plano_vacinal():
    """
    Endpoint FHIR-Compliant (RNDS).
    """
    print(f"Rota /simulador/plano-vacinal (FHIR RNDS) acessada.")

    json_data = request.get_json()
    if not json_data:
        return jsonify({"erros": "Nenhum dado fornecido."}), 400

    # 1. Validação Estrutural (FHIR Schema)
    schema = FHIRBundleSchema()
    try:
        dados_fhir_validos = schema.load(json_data)
    except ValidationError as err:
        return jsonify({"erros": err.messages, "tipo": "Erro de Validação FHIR"}), 400
    
    # 2. Adaptação (FHIR -> Modelo Interno com objetos Python)
    try:
        dados_internos = _adaptar_fhir_para_interno(dados_fhir_validos)
        
        if not dados_internos['paciente']:
            return jsonify({"erros": "O Bundle deve conter pelo menos um recurso 'Patient'."}), 400
        
        if not dados_internos['paciente']['data_nascimento']:
             return jsonify({"erros": "Data de nascimento inválida ou ausente no recurso Patient."}), 400
            
    except Exception as e:
        return jsonify({"erros": f"Erro ao processar dados FHIR: {str(e)}"}), 400

    # 3. Execução do Serviço (Motor de Regras)
    servico = PlanoVacinalService()
    plano = servico.gerar_plano_e_auditar(dados_internos)

    if not plano:
        return jsonify({"erros": "Erro interno ao gerar o plano."}), 500

    print(f"Plano vacinal gerado com sucesso.")
    
    return jsonify(plano)

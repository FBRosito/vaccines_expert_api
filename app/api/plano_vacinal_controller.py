from flask import jsonify, request
from marshmallow import ValidationError
from . import api_bp # Supondo que o blueprint seja definido em app/api/__init__.py

# Importe o novo schema e o serviço
from app.schemas.plano_vacinal_schema import PlanoVacinalInputSchema
from app.services.plano_vacinal_service import PlanoVacinalService

@api_bp.route('/simulador/plano-vacinal', methods=['POST'])
def obter_plano_vacinal():
    """
    Endpoint para receber dados do paciente e retornar o plano vacinal.
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"erros": "Nenhum dado de entrada fornecido."}), 400

    # Instancia e usa o schema para validação
    schema = PlanoVacinalInputSchema()
    try:
        dados_validados = schema.load(json_data)
    except ValidationError as err:
        # Se a validação falhar, retorna um erro 400 com os detalhes
        return jsonify({"erros": err.messages}), 400
    
    # Se a validação for bem-sucedida, prossegue para a camada de serviço
    if not isinstance(dados_validados, dict):
        return jsonify({"erros": "Dados do paciente devem ser um objeto JSON."}), 400

    servico = PlanoVacinalService()
    plano = servico.gerar_plano_e_auditar(dados_validados)

    if not plano:
        return jsonify({"erros": "Erro ao gerar o plano vacinal."}), 500

    print(f"Plano vacinal gerado com sucesso para o paciente.")

    return jsonify(plano)
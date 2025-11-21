from flask import jsonify
from . import api_bp
from app import limiter

from app.services.auditoria_service import AuditoriaService

@limiter.limit("30 per minute")
@api_bp.route('/auditoria', methods=['GET'])
def obter_todos_registros():
    """
    Endpoint para obter todos os registros de auditoria.
    """

    print(f"Rota /auditoria acessada.")

    servico = AuditoriaService()
    plano = servico.listar_registros()

    if not plano:
        return jsonify({"erros": "Erro ao retornar registros de auditoria."}), 500

    print(f"Registros de auditoria retornados com sucesso.")

    return jsonify(plano)
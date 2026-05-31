import logging
from flask import jsonify
from . import api_bp
from app import limiter

from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


@limiter.limit("30 per minute")
@api_bp.route('/auditoria', methods=['GET'])
def get_all_audit_records():
    """Return the 50 most recent audit log entries."""
    logger.info("GET /auditoria accessed.")

    service = AuditService()
    records = service.list_records()

    if not records:
        return jsonify({"erros": "Erro ao retornar registros de auditoria."}), 500

    logger.info("Audit records returned successfully.")
    return jsonify(records)

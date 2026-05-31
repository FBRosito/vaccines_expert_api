
from flask import jsonify

from app.repositories import log_repository
from app.repositories.models import PlanoVacinalLogModel


class AuditoriaService:
    def list_records(self):
        """Return the 50 most recent audit log entries, ordered by timestamp descending."""
        try:
            logs = PlanoVacinalLogModel.query.order_by(PlanoVacinalLogModel.timestamp.desc()).limit(50).all()
            return [log.to_dict() for log in logs]
        except Exception:
            return None
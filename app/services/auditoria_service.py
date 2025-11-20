
from flask import jsonify

from app.repositories import log_repository
from app.repositories.models import PlanoVacinalLogModel


class AuditoriaService:
    def listar_registros(self):
        """
        Lista todos os registros de auditoria do banco de dados.
        """

        try:
            logs = PlanoVacinalLogModel.query.order_by(PlanoVacinalLogModel.timestamp.desc()).limit(50).all()
            lista_em_dict = [log.to_dict() for log in logs]
            return lista_em_dict
        except Exception as e:
            return None
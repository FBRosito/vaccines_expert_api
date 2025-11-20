from app import db
from .models import PlanoVacinalLogModel

def salvar_log(log: PlanoVacinalLogModel):
    """
    Salva uma nova entrada de log de simulação no banco de dados.
    """
    db.session.add(log)
    db.session.commit()
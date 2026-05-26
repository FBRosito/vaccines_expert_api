from app import db
from .models import PlanoVacinalLogModel

def save_log(log: PlanoVacinalLogModel):
    """Persist a new simulation log entry to the database."""
    db.session.add(log)
    db.session.commit()
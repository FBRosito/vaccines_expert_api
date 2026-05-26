from app import db
import datetime
from sqlalchemy.dialects.postgresql import JSONB

class PlanoVacinalLogModel(db.Model):
    __tablename__ = 'plano_vacinal_logs'

    # --- Audit columns ---
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now())

    # --- Analytical columns (indexed for query performance) ---
    paciente_data_nascimento = db.Column(db.Date, nullable=False, index=True)
    paciente_sexo = db.Column(db.String(20))
    numero_doses_recebidas = db.Column(db.Integer)

    # --- Traceability columns (raw FHIR payloads) ---
    request_input = db.Column(JSONB, nullable=False)
    response_output = db.Column(JSONB, nullable=False)

    def __repr__(self):
        return f'<Log id={self.id} at={self.timestamp}>'

    def to_dict(self):
        """Serialise the model instance to a JSON-compatible dict."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "paciente_data_nascimento": self.paciente_data_nascimento.isoformat() if self.paciente_data_nascimento else None,
            "paciente_sexo": self.paciente_sexo,
            "numero_doses_recebidas": self.numero_doses_recebidas,
            "request_input": self.request_input,
            "response_output": self.response_output
        }

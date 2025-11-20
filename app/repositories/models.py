from app import db
import datetime
from sqlalchemy.dialects.postgresql import JSONB # Para PostgreSQL

class PlanoVacinalLogModel(db.Model):
    __tablename__ = 'plano_vacinal_logs'

    # --- Colunas de Auditoria ---
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    # Poderíamos adicionar: request_source_ip, user_id, api_version, etc.

    # --- Colunas para Análise de Dados (Indexadas e Otimizadas para Queries) ---
    # Armazenamos campos chave do paciente fora do JSON para buscas rápidas.
    paciente_data_nascimento = db.Column(db.Date, nullable=False, index=True)
    paciente_sexo = db.Column(db.String(20))
    numero_doses_recebidas = db.Column(db.Integer)

    # --- Colunas para Rastreabilidade (Armazenamento Bruto) ---
    # Guardamos a "foto" exata da entrada e da saída para rastreabilidade perfeita.
    # Use db.JSON para SQLite/MySQL ou JSONB para PostgreSQL para melhor performance.
    request_input = db.Column(JSONB, nullable=False)
    response_output = db.Column(JSONB, nullable=False)

    def __repr__(self):
        return f'<Log ID: {self.id} em {self.timestamp}>'
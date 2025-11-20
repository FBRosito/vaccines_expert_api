from flask import Blueprint

# Criação do Blueprint para a API
api_bp = Blueprint('api', __name__)

# Importa os controllers ao final para evitar importações circulares.
# O Blueprint "aprende" sobre as rotas definidas nos controllers.
from . import plano_vacinal_controller, auditoria_controller
from flask import Flask
from config import config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Instancia as extensões
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    """
    Função Fábrica da Aplicação (Application Factory).
    Cria e configura uma instância da aplicação Flask.
    """
    app = Flask(__name__)

    # 1. Carregar a configuração a partir do objeto importado
    app.config.from_object(config[config_name])

    # 2. Inicializar extensões (ex: banco de dados)
    db.init_app(app)
    migrate.init_app(app, db) # Inicializa o Migrate

    # 3. Registrar os Blueprints (nossas rotas)
    from .api import api_bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Adicionar uma rota raiz simples para teste
    @app.route('/')
    def index():
        return "Servidor do Sistema Especialista está no ar! Acesse /api/health para o health check."

    return app
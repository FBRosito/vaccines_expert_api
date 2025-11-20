from config import config
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template


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
    migrate.init_app(app, db)

    # 3. Registrar os Blueprints (nossas rotas)
    from .api import api_bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health')
    def health():
        return "Servidor do Sistema Especialista está no ar!", 200

    return app
import os
from app import create_app

# Obtém o nome da configuração do ambiente ou usa 'default'
config_name = os.getenv('FLASK_CONFIG', 'default')

app = create_app(config_name)

if __name__ == '__main__':
    app.run()
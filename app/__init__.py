from flask import Flask
import os

def create_app(config=None):
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='../static'
    )
    
    # Configuración básica
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  
        JSON_AS_ASCII=False 
    )
    
    # Aplicar configuración personalizada si se proporciona
    if config:
        app.config.update(config)
    
    # Variable global para archivos de configuración
    app.config['CONFIG_FILES_CONTENT'] = {}
    
    # Registrar blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    return app
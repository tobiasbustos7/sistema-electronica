from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder.'
login_manager.login_message_category = 'warning'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @app.context_processor
    def inject_globals():
        from app.models import Configuracion, Caja
        def configuracion(clave):
            try:
                return Configuracion.get(clave)
            except Exception:
                return ''
        def caja_abierta():
            try:
                return Caja.query.filter_by(estado='Abierta').first() is not None
            except Exception:
                return False
        return dict(configuracion=configuracion, caja_abierta=caja_abierta)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/')

    from app.usuarios import bp as usuarios_bp
    app.register_blueprint(usuarios_bp, url_prefix='/usuarios')

    from app.productos import bp as productos_bp
    app.register_blueprint(productos_bp, url_prefix='/productos')

    from app.proveedores import bp as proveedores_bp
    app.register_blueprint(proveedores_bp, url_prefix='/proveedores')

    from app.compras import bp as compras_bp
    app.register_blueprint(compras_bp, url_prefix='/compras')

    from app.ventas import bp as ventas_bp
    app.register_blueprint(ventas_bp, url_prefix='/ventas')

    from app.caja import bp as caja_bp
    app.register_blueprint(caja_bp, url_prefix='/caja')

    from app.inventario import bp as inventario_bp
    app.register_blueprint(inventario_bp, url_prefix='/inventario')

    from app.reportes import bp as reportes_bp
    app.register_blueprint(reportes_bp, url_prefix='/reportes')

    from app.historia import bp as historia_bp
    app.register_blueprint(historia_bp, url_prefix='/historial')

    from app.configuracion import bp as configuracion_bp
    app.register_blueprint(configuracion_bp, url_prefix='/configuracion')

    with app.app_context():
        from app.models import Usuario, Rol
        db.create_all()
        Rol.inicializar_roles()
        Usuario.crear_admin_default()

    return app

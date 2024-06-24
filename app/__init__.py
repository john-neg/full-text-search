from flask import Flask

from app.main import bp as main_bp
from config import FlaskConfig


def register_blueprints(app):
    """Регистрирует модули (blueprints)."""
    app.register_blueprint(main_bp)


def create_app(config_class=FlaskConfig):
    """Создает приложение Flask."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    with app.app_context():
        register_blueprints(app)

    return app

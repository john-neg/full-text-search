from flask import Flask

from config import FlaskConfig
from .main import bp as main_bp


def register_blueprints(app):
    """Регистрирует модули (blueprints)."""
    app.register_blueprint(main_bp)


def create_app(config_class=FlaskConfig):
    """Создает приложение Flask."""

    # # Создание директорий если отсутствуют
    # for local_directory in (
    #     FlaskConfig.TEMP_FILE_DIR,
    #     FlaskConfig.EXPORT_FILE_DIR,
    #     FlaskConfig.UPLOAD_FILE_DIR,
    #     FlaskConfig.LOG_FILE_DIR,
    # ):
    #     if not os.path.exists(local_directory):
    #         os.mkdir(local_directory, 0o755)
    #
    # # Очистка временных директорий
    # for temp_directory in (
    #     FlaskConfig.EXPORT_FILE_DIR,
    #     FlaskConfig.UPLOAD_FILE_DIR,
    # ):
    #     for file in os.listdir(temp_directory):
    #         try:
    #             os.remove(os.path.join(temp_directory, file))
    #         except FileNotFoundError:
    #             pass

    app = Flask(__name__)
    app.config.from_object(config_class)

    with app.app_context():
        register_blueprints(app)

    return app

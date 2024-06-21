import logging
import os

from flask import render_template, send_from_directory, flash
from werkzeug.exceptions import HTTPException

from common.db_service import get_mongo_db_document_service
from config import DocumentStatusType, FlaskConfig
from . import bp


# @bp.route('/favicon.ico')
# def favicon():
#     return send_from_directory(
#         os.path.join(FlaskConfig.STATIC_FILE_DIR, 'img/favicons'),
#         'favicon.ico',
#         mimetype='image/vnd.microsoft.icon',
#     )


@bp.route("/")
@bp.route("/index")
def index():
    database = get_mongo_db_document_service()
    # Общее количество обработанных статей
    total_articles = database.repository.collection.count_documents(
        {
            "parse_status": DocumentStatusType.COMPLETED,
            "processing_status": DocumentStatusType.COMPLETED,
            "lemmatization_status": DocumentStatusType.COMPLETED,
        }
    )
    return render_template("index.html", total_articles=total_articles)


# @bp.app_errorhandler(Exception)
# def handle_exception(error):
#     """Обработка и вывод всех ошибок (кроме HTTP) в виде flash-сообщений."""
#     if isinstance(error, HTTPException):
#         return error
#     message = f"Произошла ошибка - {type(error).__name__} - {error}"
#     flash(message, category='danger')
#     logging.error(message)
#     return render_template("errors/500_generic.html"), 500

import datetime

from flask import render_template, request

from common.db_service import get_mongo_db_document_service
from common.func import get_nlp_model
from common.models import ArticleDocument
from common.processors import (
    KeywordsProcessor,
    LanguageProcessor,
    SearchPrepareProcessor,
)
from config import BaseConfig, DocumentStatusType
from ml_models.models import TfIdfModel, Word2VecModel
from . import bp
from .forms import SearchForm

tfidf_model = TfIdfModel()
tfidf_model.load(BaseConfig.TF_IDF_MODEL_FILE)

w2v_model = Word2VecModel()
w2v_model.load(BaseConfig.WORD2VEC_MODEL_FILE)

language_processor = LanguageProcessor(target_language="russian")
language_processor.load_translations(BaseConfig.TRANSLATIONS_CACHE_FILE)

words_processor = SearchPrepareProcessor(
    nlp_model=get_nlp_model(),
    prediction_model=w2v_model,
    vocabulary=tfidf_model.vectorizer.vocabulary,
    processor=KeywordsProcessor(language_processor),
)

db = get_mongo_db_document_service()


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    form = SearchForm()
    date = datetime.date.today().strftime("%d.%m.%Y")
    articles, addon_words, search_request = {}, "", ""
    # Положение переключателей
    switch_autocomplete = request.form.get("switch_autocomplete") is not None
    switch_more_results = request.form.get("switch_more_results") is not None

    # Общее количество обработанных статей
    total_articles = db.repository.collection.count_documents(
        {
            "parse_status": DocumentStatusType.COMPLETED,
            "processing_status": DocumentStatusType.COMPLETED,
            "lemmatization_status": DocumentStatusType.COMPLETED,
        }
    )

    if request.method == "POST" and form.validate_on_submit():
        search_string = request.form.get("search_string")
        search_results_number = BaseConfig.SEARCH_RESULTS
        search_request = words_processor.process_text(search_string)
        if request.form.get("switch_autocomplete"):
            addon_words = words_processor.add_similar_words(search_string)
            search_request = f"{search_request} {addon_words}"
        if request.form.get("switch_more_results"):
            search_results_number += 10
        similar_articles = tfidf_model.search_similar(
            search_request, search_results_number
        )
        for _id, percent in similar_articles.items():
            article = ArticleDocument(**db.get_by_id(_id))
            data, url = article.reference.split(" URL: ")
            url = url.replace(" (дата обращения:).", "")
            percent = f"{percent * 100:.2f}%"
            article.reference = data
            articles[_id] = [article, url, date, percent]

    return render_template(
        "index.html",
        total_articles=total_articles,
        form=form,
        articles=articles,
        search_request=search_request,
        addon_words=addon_words,
        switch_autocomplete=switch_autocomplete,
        switch_more_results=switch_more_results,
    )


# @bp.app_errorhandler(Exception)
# def handle_exception(error):
#     """Обработка и вывод всех ошибок (кроме HTTP) в виде flash-сообщений."""
#     if isinstance(error, HTTPException):
#         return error
#     message = f"Произошла ошибка - {type(error).__name__} - {error}"
#     flash(message, category='danger')
#     logging.error(message)
#     return render_template("errors/500_generic.html"), 500

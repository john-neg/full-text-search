from common.db_service import get_mongo_db_document_service
from config import BaseConfig
from ml_models.func import get_db_list, get_lemmas_count, get_tfidf_vectorizer
from ml_models.models import ArticlesLemmasIterator, TfIdfModel

if __name__ == "__main__":
    db = get_mongo_db_document_service()

    # Считаем количество повторений каждой леммы в текстах
    lemmas_counter = get_lemmas_count(get_db_list(db), show_progress=True)
    # Создаем словарь наиболее часто встречаемых слов
    lemmas_vocabulary = [
        word for word, _ in lemmas_counter.most_common(BaseConfig.VOCABULARY_SIZE)
    ]
    # Итератор по леммам
    lemmas_iterator = ArticlesLemmasIterator(
        get_db_list(db), ["text", "abstract", "keywords", "title"]
    )
    # Создаем и обучаем TF-IDF модель
    tfidf_vectorizer = get_tfidf_vectorizer(vocabulary=lemmas_vocabulary)
    tfidf_model = TfIdfModel(tfidf_vectorizer)
    tfidf_model.fit_and_build_matrix(lemmas_iterator, show_progress=True)
    # Сохраняем модель
    tfidf_model.save(BaseConfig.TF_IDF_MODEL_FILE)

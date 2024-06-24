from common.db_service import get_mongo_db_document_service
from config import BaseConfig
from ml_models.func import get_db_list, get_tfidf_vectorizer
from ml_models.models import ArticlesLemmasIterator, TfIdfModel

if __name__ == "__main__":
    db = get_mongo_db_document_service()

    # Словарь лем
    with open(BaseConfig.LEM_VOCAB_FILE, encoding="utf-8") as file:
        lemmas_vocabulary = [item.strip() for item in file.readlines()]

    # Итератор по леммам
    lemmas_iterator = ArticlesLemmasIterator(
        get_db_list(db), ["text", "abstract", "keywords", "title"]
    )

    # Создаем и обучаем TF-IDF модель
    tfidf_vectorizer = get_tfidf_vectorizer(vocabulary=lemmas_vocabulary)
    tfidf_model = TfIdfModel(vectorizer=tfidf_vectorizer)
    tfidf_model.fit_and_build_matrix(lemmas_iterator, show_progress=True)
    # Сохраняем модель
    tfidf_model.save(BaseConfig.TF_IDF_MODEL_FILE)

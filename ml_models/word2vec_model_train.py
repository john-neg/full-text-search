from common.db_service import get_mongo_db_document_service
from config import BaseConfig
from ml_models.func import get_db_list
from ml_models.models import ArticlesLemmasIterator, Word2VecModel

if __name__ == "__main__":
    db = get_mongo_db_document_service()

    # Итератор по леммам
    lemmas_iterator = ArticlesLemmasIterator(
        get_db_list(db), ["abstract", "keywords", "title"]
    )
    # Создаем и обучаем Word2Vec модель
    w2v_model = Word2VecModel()
    w2v_model.fit(lemmas_iterator, show_progress=True)
    # Сохраняем модель
    w2v_model.save(BaseConfig.WORD2VEC_MODEL_FILE)

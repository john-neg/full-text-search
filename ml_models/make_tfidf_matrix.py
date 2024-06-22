import os
import pickle
from dataclasses import dataclass, field
from zipfile import ZIP_DEFLATED, ZipFile

from bson import json_util
from pymongo.cursor import Cursor
from tqdm import tqdm

from common.db_repository import DocumentType
from common.db_service import get_mongo_db_document_service
from common.models import ArticleDocument
from config import BaseConfig
from ml_models.func import get_db_list, get_lemmas_count
from ml_models.models import TfIdfModel, get_tfidf_vectorizer


@dataclass
class ArticlesLemmasIterator:
    """Класс для итерации по аттрибутам коллекции документов."""

    db_list: Cursor[DocumentType]
    lemmas_fields: list
    _stack: list = field(default_factory=list)
    objects_ids: dict = field(default_factory=dict)
    counter = 0

    def __iter__(self):
        return self

    def __next__(self):
        article = ArticleDocument(**self.db_list.next())
        self.objects_ids[self.counter] = article._id
        self.counter += 1
        lemmas = " ".join(
            [val for key, val in article.lemmas.items() if key in self.lemmas_fields]
        )
        return lemmas


if __name__ == "__main__":
    db = get_mongo_db_document_service()

    # Считаем количество повторений каждой леммы в текстах
    lemmas_counter = get_lemmas_count(tqdm(get_db_list(db)))
    # Создаем словарь наиболее часто встречаемых слов
    lemmas_vocabulary = [word for word, _ in lemmas_counter.most_common(7500)]
    # Итератор по леммам
    lemmas_iterator = ArticlesLemmasIterator(
        get_db_list(db), ["text", "abstract", "keywords", "title"]
    )
    # Создаем и обучаем TF-IDF модель
    tfidf_vectorizer = get_tfidf_vectorizer(lemmas_vocabulary)
    tfidf_model = TfIdfModel(tfidf_vectorizer)
    tfidf_matrix = tfidf_model.fit_and_make_tfidf_matrix(tqdm(lemmas_iterator))

    # Сохраняем модель
    with ZipFile(
        os.path.join(BaseConfig.DATA_DIR, "tfidf_matrix.zip"),
        mode="w",
        compression=ZIP_DEFLATED,
        compresslevel=9,
    ) as zip_file:
        with zip_file.open("tfidf_model.pkl", "w") as file:
            pickle.dump(tfidf_model, file, protocol=pickle.HIGHEST_PROTOCOL)
        with zip_file.open("tfidf_matrix.pkl", "w") as file:
            pickle.dump(tfidf_matrix, file, protocol=pickle.HIGHEST_PROTOCOL)
        zip_file.writestr(
            "tfidf_matrix_objects.json",
            data=json_util.dumps(
                lemmas_iterator.objects_ids, ensure_ascii=False, indent=3
            ),
        )

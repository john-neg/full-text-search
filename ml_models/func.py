from collections import Counter
from typing import Iterable

from pymongo.cursor import Cursor
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm

from common.db_repository import DocumentType
from common.db_service import MongoDbCrudService
from config import DocumentStatusType


def get_lemmas_count(
    data: Iterable[DocumentType],
    field_name="lemmas",
    show_progress: bool = False,
) -> Counter:
    """Счетчик количества слов."""
    counter = Counter()
    if show_progress:
        data = tqdm(data)
    for document in data:
        for key, val in document[field_name].items():
            words = val.split()
            for word in words:
                counter[word] += 1
    return counter


def get_db_list(db: MongoDbCrudService) -> Cursor[DocumentType]:
    """Возвращает итератор по полностью обработанным документам."""
    db_list = db.list(
        {
            "parse_status": DocumentStatusType.COMPLETED,
            "processing_status": DocumentStatusType.COMPLETED,
            "lemmatization_status": DocumentStatusType.COMPLETED,
        }
    )
    return db_list


def get_tfidf_vectorizer(vocabulary: list[str]) -> TfidfVectorizer:
    return TfidfVectorizer(
        ngram_range=(1, 1),
        encoding="utf-8",
        vocabulary=vocabulary,
    )

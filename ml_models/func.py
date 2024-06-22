from collections import Counter
from typing import Iterable

import numpy as np
from pymongo.cursor import Cursor
from sklearn.feature_extraction.text import TfidfVectorizer

from common.db_repository import DocumentType
from common.db_service import MongoDbCrudService
from config import DocumentStatusType


def get_lemmas_count(data: Iterable[DocumentType], field_name="lemmas") -> Counter:
    """Счетчик количества слов."""
    counter = Counter()
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



from dataclasses import dataclass, field
from typing import Iterable

from bson import ObjectId
from pymongo.cursor import Cursor
from tqdm import tqdm

from common.db_service import get_mongo_db_document_service
from common.func import get_nlp_model, lemmatization
from common.models import ArticleDocument
from common.processors import TitleProcessor
from config import DocumentStatusType

nlp = get_nlp_model()
database = get_mongo_db_document_service()

# Процессор названий статей
title_processor = TitleProcessor()


@dataclass
class ArticlesIterator:
    db_list: Cursor[ArticleDocument]
    _stack: list = field(default_factory=list)

    def __iter__(self):
        return self

    def __next__(self):
        if not self._stack:
            article = ArticleDocument(**self.db_list.next())
            for attr in ["text", "abstract", "keywords", "title"]:
                value = getattr(article, attr)
                if value:
                    if isinstance(value, list):
                        value = " ".join(value)
                    if attr == "title":
                        value = title_processor.filter_letters(value)
                    self._stack.append((value, {"_id": article._id, "attr": attr}))
        return self._stack.pop()


def lemmatize_articles(
    text_data: Iterable[tuple[str, dict[str, ObjectId | str, str]]],
    batch_size: int = 50,
    n_process: int = 2,
):
    for value, context in nlp.pipe(
        text_data,
        batch_size=batch_size,
        n_process=n_process,
        disable=["parser", "ner"],
        as_tuples=True,
    ):
        lemmas = lemmatization(value)
        lemmas = title_processor.fix_letters(" ".join(lemmas))
        _id = context.get("_id")
        attr = context.get("attr")

        database.update(
            {"_id": _id},
            {
                "$set": {
                    f"lemmas.{attr}": lemmas,
                    "lemmatization_status": DocumentStatusType.COMPLETED,
                }
            },
        )


if __name__ == "__main__":
    db = get_mongo_db_document_service()
    db_list = db.list(
        {
            "parse_status": DocumentStatusType.COMPLETED,
            "processing_status": DocumentStatusType.COMPLETED,
            "lemmatization_status": DocumentStatusType.WAITING,
        }
    )
    db_iterable = ArticlesIterator(db_list)
    lemmatize_articles(tqdm(db_iterable), batch_size=10, n_process=1)

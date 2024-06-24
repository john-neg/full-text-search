import os
import time
from dataclasses import dataclass
from datetime import datetime
from functools import singledispatchmethod, wraps
from typing import Any, Mapping, Optional

from bson import ObjectId
from pymongo import MongoClient
from pymongo.cursor import Cursor
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from pymongo.results import DeleteResult, InsertOneResult, UpdateResult

from config import BaseConfig, MongoDBSettings
from .db_repository import DocumentType, MongoDbRepository


def task_retry_processor(retry_count: int = 5):
    """Декоратор для повтора действия в случае ошибок соединения."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for retry in range(retry_count):
                try:
                    return func(*args, **kwargs)
                except ConnectionFailure:
                    print("ConnectionFailure: retry", retry + 1)
                    with open(
                        os.path.join(BaseConfig.LOGS_DIR, "mongo_db.log"),
                        "a",
                        encoding="UTF8",
                    ) as err:
                        err.write(
                            f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')} {err}\n"
                        )
                    time.sleep(1)
            else:
                raise ConnectionFailure

        return wrapper

    return decorator


@dataclass
class MongoDbCrudService:
    """Базовый класс CRUD операций для базы данных MongoDB."""

    repository: MongoDbRepository

    @task_retry_processor()
    def list(self, *args, **kwargs) -> Cursor[DocumentType]:
        return self.repository.list(*args, **kwargs)

    @task_retry_processor()
    def get(self, query_filter, *args, **kwargs) -> Optional[DocumentType]:
        return self.repository.get(query_filter, *args, **kwargs)

    @singledispatchmethod
    @task_retry_processor()
    def get_by_id(self, _id: str, *args, **kwargs) -> Optional[DocumentType]:
        return self.repository.get({"_id": ObjectId(_id)}, *args, **kwargs)

    @get_by_id.register(ObjectId)
    @task_retry_processor()
    def _(self, _id: ObjectId, *args, **kwargs):
        return self.repository.get({"_id": _id}, *args, **kwargs)

    @task_retry_processor()
    def create(self, document, **kwargs) -> InsertOneResult:
        return self.repository.create(document, **kwargs)

    @task_retry_processor()
    def update(self, query_filter, update, **kwargs) -> UpdateResult:
        return self.repository.update(query_filter, update, **kwargs)

    @task_retry_processor()
    def delete(self, query_filter, *args, **kwargs) -> DeleteResult:
        return self.repository.delete(query_filter, *args, **kwargs)


def get_mongo_db(
    dbname: str = MongoDBSettings.DB_NAME,
) -> Database[Mapping[str, Any]]:
    """Подключение к базе данных MongoDB."""

    client = MongoClient(MongoDBSettings.CONNECTION_STRING)
    return client[dbname]


def get_mongo_db_document_service(
    mongo_db: Database = get_mongo_db(),
    collection_name: str = MongoDBSettings.COLLECTION_NAME,
) -> MongoDbCrudService:
    return MongoDbCrudService(repository=MongoDbRepository(mongo_db, collection_name))

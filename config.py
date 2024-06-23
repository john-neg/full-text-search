import os
from enum import Enum

from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))


class BaseConfig(object):
    # Директория с моделями и данными
    DATA_DIR = os.path.join(BASEDIR, "data")
    # Директория с логами
    LOGS_DIR = os.path.join(BASEDIR, "logs")
    # Название файла с кешем переводов
    TRANSLATIONS_CACHE_FILE = os.path.join(DATA_DIR, "keyword_translations.json")
    # Название файла модели TF-IDF
    TF_IDF_MODEL_FILE = os.path.join(DATA_DIR, "tfidf_model.zip")
    # Название файла модели TF-IDF
    WORD2VEC_MODEL_FILE = os.path.join(DATA_DIR, "word2vec.model")
    # Размер автодополнения поисковых запросов
    AUTOCOMPLETE_SIZE = 2
    # Размер словаря модели
    VOCABULARY_SIZE = 10000
    # Кол-во результатов поиска
    SEARCH_RESULTS = 5


class FlaskConfig(object):
    """Конфигурация Flask."""

    SECRET_KEY = os.getenv("SECRET_KEY", "DEFAULT_SECRET_KEY")
    STATIC_FILE_DIR = os.path.join(BASEDIR, "app/static/")


class CrawlerConfig(object):
    """Crawler config data."""

    # Базовая ссылка на сайт
    LINK = "https://cyberleninka.ru"
    # Ссылка на страницу категории
    CATEGORY_LINK = f"{LINK}/article/c/"
    # Селектор для адреса категории
    CATEGORY_LINK_XPATH = "//*[contains(@href, '/article/c/')]"
    # Ссылка на страницу статьи
    ARTICLE_LINK = f"{LINK}/article/n/"
    # Селектор для адреса статьи
    ARTICLE_LINK_XPATH = "//*[contains(@href, '/article/n/')]"
    # Название лог файла
    LOG_FILE = "crawler.log"
    # Количество статей на странице
    ARTICLES_PER_PAGE = 20
    # Смещение для номера начальной страницы
    PAGE_OFFSET = 38


class MongoDBSettings(object):
    """Database settings"""

    # Имя пользователя БД
    MONGO_DB_USER = os.getenv("MONGO_DB_USER")
    # Пароль
    MONGO_DB_PASS = os.getenv("MONGO_DB_PASS")
    # Адрес сервера БД
    MONGO_DB_URL = os.getenv("MONGO_DB_URL")
    # Строка подключения к БД
    CONNECTION_STRING = f"mongodb://{MONGO_DB_USER}:{MONGO_DB_PASS}@{MONGO_DB_URL}"
    # Имя базы данных
    DB_NAME = "cyberleninka"
    # Имя коллекции
    COLLECTION_NAME = "mathematics"
    # COLLECTION_NAME = 'test'


class DocumentStatusType(str, Enum):
    """Класс статусов состояния документа."""

    WAITING = "waiting"
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"
    DELETE = "delete"
    ERROR = "error"

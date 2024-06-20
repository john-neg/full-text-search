import os

from dotenv import load_dotenv

BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"))


class BaseConfig(object):
    DATASET_DIR = os.path.join(BASEDIR, "dataset")
    MODEL_DIR = os.path.join(BASEDIR, "models")


class FlaskConfig(object):
    """Конфигурация Flask."""

    SECRET_KEY = os.getenv("SECRET_KEY", "DEFAULT_SECRET_KEY")
    STATIC_FILE_DIR = os.path.join(BASEDIR, "app/static/")


class CrawlerConfig(object):
    """Crawler config data."""

    # Базовая ссылка на сайт
    LINK = 'https://cyberleninka.ru'
    # Ссылка на страницу категории
    CATEGORY_LINK = f"{LINK}/article/c/"
    # Селектор для адреса категории
    CATEGORY_LINK_XPATH = "//*[contains(@href, '/article/c/')]"
    # Ссылка на страницу статьи
    ARTICLE_LINK = f"{LINK}/article/n/"
    # Селектор для адреса статьи
    ARTICLE_LINK_XPATH = "//*[contains(@href, '/article/n/')]"
    # Название лог файла
    LOG_FILE = 'crawler.log'
    # Количество статей на странице
    ARTICLES_PER_PAGE = 20
    # Смещение для начальной страницы
    PAGE_OFFSET = -40


class DbSettings(object):
    """Database settings"""

    # Имя пользователя БД
    MONGO_DB_USER = os.getenv('MONGO_DB_USER')
    # Пароль
    MONGO_DB_PASS = os.getenv('MONGO_DB_PASS')
    # Адрес сервера БД
    MONGO_DB_URL = os.getenv('MONGO_DB_URL')
    # Строка подключения к БД
    CONNECTION_STRING = f"mongodb://{MONGO_DB_USER}:{MONGO_DB_PASS}@{MONGO_DB_URL}"
    # Имя базы данных
    DB_NAME = 'cyberleninka'

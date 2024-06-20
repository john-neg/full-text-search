import random
import time
from datetime import datetime
from typing import Any, Mapping

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By

from config import CrawlerConfig, DbSettings
from base.functions import get_language, get_language_detector
from pages.article_page import ArticlePage
from pages.category_page import CategoryPage


def get_browser() -> webdriver.Chrome:
    """Открывает браузер."""
    browser_options = webdriver.ChromeOptions()
    # Режим без показа браузера
    browser_options.add_argument("--headless")
    # Загрузка страниц без картинок
    browser_options.add_argument("--blink-settings=imagesEnabled=false")
    return webdriver.Chrome(options=browser_options)


def get_database(dbname: str = DbSettings.DB_NAME) -> Database[Mapping[str, Any]]:
    """Подключает к базе данных."""
    client = MongoClient(DbSettings.CONNECTION_STRING)
    return client[dbname]


def parse_data(article_slug, article_page: ArticlePage) -> dict:
    """Возвращает данные парсинга страницы."""
    data = {
        "article_slug": article_slug,
        "authors": article_page.get_authors(),
        "title": article_page.get_title(),
        "year": article_page.get_year(),
        "magazine": article_page.get_magazine(),
        "magazine_issue": article_page.get_magazine_issue(),
        "magazine_volume": article_page.get_magazine_volume(),
        "keywords": article_page.get_keywords(),
        "abstract": article_page.get_abstract(),
        "scopus": article_page.get_status("scopus"),
        "vak": article_page.get_status("vak"),
        "reference": article_page.get_reference_data(),
        "text": article_page.get_text(),
    }
    return data


def check_captcha(browser):
    """Проверяет наличие капчи."""
    try:
        browser.find_element(By.ID, "g-recaptcha-response")
        return True
    except NoSuchElementException:
        return False


def check_nginx_error(browser):
    """Проверяет наличие ошибки Nginx."""
    try:
        element = browser.find_element(By.TAG_NAME, 'h1')
        if element.text == "502 Bad Gateway":
            return True
    except NoSuchElementException:
        return False
    else:
        return False


def check_empty(browser):
    """Проверяет наличие данных на странице."""
    try:
        element = browser.find_element(By.TAG_NAME, 'body')
        if not element.text:
            return True
    except NoSuchElementException:
        return False
    else:
        return False


def parse_links(collection):
    """Функция для сбора ссылок на статьи."""

    # Открываем браузер
    browser = get_browser()
    # Подключаемся к базе данных
    db = get_database()
    # Переходим на страницу категории
    category_page = CategoryPage(browser, collection)
    # Получаем количество страниц
    pages = category_page.get_pages_number()
    # Подключаемся к коллекции статей в базе данных
    db_collection = db[collection]
    # Определяем стартовую страницу с которой нужно начать собирать ссылки
    start_page = db[collection].count_documents({}) // CrawlerConfig.ARTICLES_PER_PAGE
    # Запускаем постраничный цикл
    for page in range(start_page + 1 - CrawlerConfig.PAGE_OFFSET, pages + 1):
        category_page.get_articles_page(page)
        while check_nginx_error(category_page.browser):
            time.sleep(5)
            category_page.get_articles_page(page)
        articles = category_page.get_articles()
        # Проверяем наличие капчи на странице
        if check_captcha(category_page.browser):
            with open(CrawlerConfig.LOG_FILE, "a", encoding="UTF8") as log:
                log.write(
                    f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')} "
                    f"!#{collection} page:{page} CAPTCHA\n"
                )
            # Устанавливаем длительное ожидание
            time.sleep(1000)
            # Завершаем программу
            exit()
        else:
            print(f"#{collection} page:{page}")
            for article_slug in articles:
                article_data = {"article_slug": article_slug}
                # Проверяем наличие уникального идентификатора статьи в базе данных
                record = db_collection.find_one(article_data)
                # Если записи нет устанавливаем True для переменной нужно записать в базу
                need_to_write = False if record else True
                # Пока переменная need_to_write = True делается попытка записать
                # идентификатор в базу данных
                while need_to_write:
                    try:
                        article_data["parse_status"] = "waiting"
                        db_collection.insert_one(article_data)
                        need_to_write = False
                    # Обрабатываем исключение «ошибка соединения» делаем запись в лог
                    except ConnectionFailure as error:
                        print(error)
                        need_to_write = True
                        with open(CrawlerConfig.LOG_FILE, "a", encoding="UTF8") as err:
                            err.write(
                                f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')} "
                                f"{error} ({collection}, {category_page}, {article_slug})\n"
                            )
                time.sleep(0.1)
        time.sleep(random.choice([1]))
    browser.quit()


def parse_articles(collection):
    """Функция для сбора данных о статьях."""

    # Открываем браузер
    browser = get_browser()
    # Подключаемся к базе данных
    db = get_database()
    # Выбираем коллекцию
    db_collection = db[collection]
    # Получаем экземпляр класса определения языка текста
    lang_detector = get_language_detector()

    # Пока на странице отсутствует капча выполняем парсинг данных
    while not check_captcha(browser):
        # Ищем статью со статусом waiting
        cursor = db_collection.find({"parse_status": "waiting"})
        db_record = cursor.next()
        article_slug = db_record.get("article_slug")
        db_collection.find_one_and_update(
            db_record, {"$set": {"parse_status": "in progress"}}
        )
        # Устанавливаем интервал между запросами для соблюдения этики сбора данных
        time.sleep(3)
        article_page = ArticlePage(browser, article_slug)
        # Если страница по ссылке пустая, значит ресурс был удален
        if check_empty(article_page.browser):
            db_collection.find_one_and_update(
                db_record, {"$set": {"parse_status": "delete"}}
            )
        else:
            # Обработка ошибок сайта
            while check_nginx_error(article_page.browser):
                time.sleep(5)
                print("Nginx Error")
                article_page = ArticlePage(browser, article_slug)
            if article_page.check_captcha():
                db_collection.find_one_and_update(
                    {"_id": db_record.get("_id")}, {"$set": {"parse_status": "waiting"}}
                )
                with open(CrawlerConfig.LOG_FILE, "a", encoding="UTF8") as log:
                    log.write(
                        f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')} "
                        f"!#{collection} article:{article_slug} CAPTCHA\n"
                    )
                print("CAPTCHA")
                time.sleep(60)
                exit()
            else:
                try:
                    # Парсим данные текущей статьи
                    article_data = parse_data(article_slug, article_page)
                    # Добавляем данные о языке
                    article_data["language"] = get_language(
                        article_data.get("text"), lang_detector
                    )
                    article_data["parse_status"] = "completed"
                    # Заменяем существующую запись в базе на новую с данными
                    db_collection.find_one_and_replace(
                        {"_id": db_record.get("_id")}, article_data
                    )
                # В случае отсутствия необходимых элементов устанавливаем статус error
                except NoSuchElementException:
                    db_collection.find_one_and_update(
                        {"_id": db_record.get("_id")}, {"$set": {"parse_status": "error"}}
                    )


if __name__ == "__main__":
    category = "mathematics"
    # Получаем идентификаторы статей
    parse_links(category)
    # Получаем данные по каждому идентификатору
    parse_articles(category)

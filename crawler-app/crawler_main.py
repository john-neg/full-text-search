import os
import random
import time
from datetime import datetime

from selenium.common import NoSuchElementException, TimeoutException

from config import BaseConfig, CrawlerConfig, DocumentStatusType, MongoDBSettings
from func import check_captcha, check_empty, check_nginx_error, get_browser
from pages.article_page import ArticlePage
from pages.category_page import CategoryPage
from common.db_service import MongoDbCrudService, get_mongo_db_document_service
from common.func import get_language, get_language_detector
from common.models import ArticleDocument


def parse_data(
    article_slug: str, article_page: ArticlePage, article: ArticleDocument
) -> ArticleDocument:
    """Возвращает документ с данными парсинга страницы."""

    article.article_slug = article_slug
    article.authors = article_page.get_authors()
    article.title = article_page.get_title()
    article.year = article_page.get_year()
    article.magazine = article_page.get_magazine()
    article.magazine_issue = article_page.get_magazine_issue()
    article.magazine_volume = article_page.get_magazine_volume()
    article.keywords = article_page.get_keywords()
    article.abstract = article_page.get_abstract()
    article.scopus = article_page.get_status("scopus")
    article.vak = article_page.get_status("vak")
    article.reference = article_page.get_reference_data()
    article.text = article_page.get_text()
    return article


def parse_links(collection: str, database: MongoDbCrudService):
    """Функция для сбора ссылок на статьи."""

    # Открываем браузер
    browser = get_browser()
    # Переходим на страницу категории
    category_page = CategoryPage(browser, collection)
    # Получаем количество страниц
    pages = category_page.get_pages_number()
    # Определяем стартовую страницу с которой нужно начать собирать ссылки
    start_page = (
        database.repository.collection.count_documents({})
        // CrawlerConfig.ARTICLES_PER_PAGE
    )
    # Запускаем постраничный цикл
    for page in range(start_page + 1 - CrawlerConfig.PAGE_OFFSET, pages + 1):
        category_page.get_articles_page(page)
        while check_nginx_error(category_page.browser):
            time.sleep(5)
            category_page.get_articles_page(page)
        articles = category_page.get_articles()
        # Проверяем наличие капчи на странице
        if check_captcha(category_page.browser):
            with open(
                os.path.join(BaseConfig.LOGS_DIR, CrawlerConfig.LOG_FILE),
                "a",
                encoding="UTF8",
            ) as log:
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
                # Проверяем наличие уникального идентификатора статьи в базе данных
                record = database.get({"article_slug": article_slug})
                # Если нет записи добавляем в базу данных
                if not record:
                    article_data = ArticleDocument(article_slug=article_slug)
                    database.create(article_data.to_dict())
                time.sleep(0.1)
        time.sleep(random.choice([1, 1.5, 2]))
    browser.quit()


def parse_articles(collection: str, database: MongoDbCrudService):
    """Функция для сбора данных о статьях."""

    # Открываем браузер
    browser = get_browser()
    # Получаем экземпляр класса определения языка текста
    lang_detector = get_language_detector()

    # Пока на странице отсутствует капча выполняем парсинг данных
    while not check_captcha(browser):
        # Ищем статью со статусом waiting
        cursor = database.list({"parse_status": DocumentStatusType.WAITING})
        db_record = cursor.next()
        article_slug = db_record.get("article_slug")
        database.update(
            db_record, {"$set": {"parse_status": DocumentStatusType.IN_PROGRESS}}
        )
        # Устанавливаем интервал между запросами для соблюдения этики сбора данных
        time.sleep(3)
        article_page = ArticlePage(browser, article_slug)
        # Если страница по ссылке пустая, значит ресурс был удален
        if check_empty(article_page.browser):
            database.update(
                db_record, {"$set": {"parse_status": DocumentStatusType.DELETE}}
            )
        else:
            # Обработка ошибок сайта
            while check_nginx_error(article_page.browser):
                time.sleep(5)
                print("Nginx Error")
                article_page = ArticlePage(browser, article_slug)
            if article_page.check_captcha():
                database.update(
                    {"_id": db_record.get("_id")},
                    {"$set": {"parse_status": DocumentStatusType.WAITING}},
                )
                with open(
                    os.path.join(BaseConfig.LOGS_DIR, CrawlerConfig.LOG_FILE),
                    "a",
                    encoding="UTF8",
                ) as log:
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
                    article_data = parse_data(
                        article_slug, article_page, ArticleDocument(**db_record)
                    )
                    # Добавляем данные о языке
                    article_data.language = get_language(
                        article_data.text, lang_detector
                    )
                    article_data.parse_status = DocumentStatusType.COMPLETED
                    # Обновляем запись в базе данных
                    database.update(
                        {"_id": db_record.get("_id")},
                        {"$set": article_data.to_dict()},
                    )
                # В случае таймаута возвращаем статус в ожидании
                except TimeoutException:
                    database.update(
                        {"_id": db_record.get("_id")},
                        {"$set": {"parse_status": DocumentStatusType.WAITING}},
                    )
                # В случае отсутствия необходимых элементов устанавливаем статус error
                except NoSuchElementException:
                    database.update(
                        {"_id": db_record.get("_id")},
                        {"$set": {"parse_status": DocumentStatusType.ERROR}},
                    )


if __name__ == "__main__":
    # Подключаемся к базе данных
    db = get_mongo_db_document_service()
    category = MongoDBSettings.COLLECTION_NAME
    # Получаем идентификаторы статей
    parse_links(category, db)
    # Получаем данные по каждому идентификатору
    parse_articles(category, db)

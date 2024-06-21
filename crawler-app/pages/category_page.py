from dataclasses import dataclass

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from config import CrawlerConfig
from .base_page import BasePage


@dataclass
class CategoryPage(BasePage):
    """Класс для работы со страницей категорий."""

    category_slug: str
    url: str = CrawlerConfig.CATEGORY_LINK

    def __post_init__(self):
        self.open(self.url + self.category_slug)

    def get_pages_number(self) -> int:
        """Возвращает количество страниц в категории."""
        try:
            WebDriverWait(self.browser, 10).until(
                expected_conditions.visibility_of_element_located(
                    (By.CLASS_NAME, "paginator")
                )
            )
            paginator = self.browser.find_element(By.CLASS_NAME, "paginator")
            elements = paginator.find_elements(By.TAG_NAME, "a")
            last_element = elements.pop().get_attribute("href")
            page_number = last_element.replace(
                f"{CrawlerConfig.CATEGORY_LINK}{self.category_slug}/", ""
            )
            return int(page_number)
        except NoSuchElementException:
            return 1

    def get_articles_page(self, page: int):
        """Открывает указанную страницу."""
        if page and page != 1:
            self.open(f"{CrawlerConfig.CATEGORY_LINK}{self.category_slug}/{page}")

    def get_articles(self) -> dict:
        """Возвращает ссылки на статьи со страницы."""
        links = self.browser.find_elements(
            By.XPATH,
            CrawlerConfig.ARTICLE_LINK_XPATH,
        )
        articles = {
            link.get_attribute("href")
            .replace(CrawlerConfig.ARTICLE_LINK, ""): link.find_element(
                By.CLASS_NAME, "title"
            )
            .text
            for link in links
        }
        return articles

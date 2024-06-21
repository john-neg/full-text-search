import re
from dataclasses import dataclass

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from config import CrawlerConfig
from .base_page import BasePage


@dataclass
class ArticlePage(BasePage):
    """Класс для работы со страницей статьи."""

    article_slug: str
    url: str = CrawlerConfig.ARTICLE_LINK

    def __post_init__(self):
        self.open(self.url + self.article_slug)

    def get_authors(self) -> list:
        """Возвращает авторов."""
        obj = self.browser.find_element(By.CLASS_NAME, "author-list")
        return obj.text.split("\n")

    def get_title(self) -> str:
        """Возвращает название."""
        return self.browser.find_element(
            By.XPATH, "//i[contains(@itemprop, 'headline')]"
        ).text

    def get_year(self) -> str:
        """Возвращает год."""
        return self.browser.find_element(By.CLASS_NAME, "year").text

    def get_magazine(self) -> str:
        """Возвращает название журнала."""
        return self.browser.find_element(
            By.NAME, "citation_journal_title"
        ).get_attribute("content")

    def get_magazine_issue(self) -> str:
        """Возвращает выпуск журнала."""
        return self.browser.find_element(By.NAME, "citation_issue").get_attribute(
            "content"
        )

    def get_magazine_volume(self) -> str:
        """Возвращает том журнала."""
        return self.browser.find_element(By.NAME, "citation_volume").get_attribute(
            "content"
        )

    def get_status(self, status) -> str:
        """Возвращает статус статьи 'scopus', 'vak' и т.д."""
        try:
            self.browser.find_element(By.CLASS_NAME, status)
            return "1"
        except NoSuchElementException:
            return "0"

    def get_abstract(self) -> str:
        """Возвращает аннотацию."""
        try:
            return self.browser.find_element(
                By.XPATH, "//p[contains(@itemprop, 'description')]"
            ).text
        except NoSuchElementException:
            return ""

    def get_keywords(self) -> str:
        """Возвращает ключевые слова."""
        return (
            self.browser.find_element(By.NAME, "citation_keywords")
            .get_attribute("content")
            .lower()
            .split(", ")
        )

    def get_text(self) -> str:
        """Возвращает OCR текст статьи."""
        return self.browser.find_element(By.CLASS_NAME, "ocr").text

    def get_reference_data(self) -> str:
        """Возвращает ссылку для цитирования."""
        button = self.browser.find_element(By.ID, "btn-quote")
        button.click()
        WebDriverWait(self.browser, 10).until(
            expected_conditions.visibility_of_element_located((By.ID, "quote-text"))
        )
        text = self.browser.find_element(By.ID, "quote-text").text
        text = re.sub(
            r"дата обращения: \d{1,2}\W\d{1,2}\W\d{4}", "дата обращения:", text
        )
        button = self.browser.find_element(By.CLASS_NAME, "close")
        button.click()
        return text

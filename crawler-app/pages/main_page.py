from dataclasses import dataclass

from selenium.webdriver.common.by import By

from config import CrawlerConfig
from .base_page import BasePage


@dataclass
class MainPage(BasePage):
    """Класс действий на главной странице."""

    url: str = CrawlerConfig.LINK

    def __post_init__(self):
        self.open(self.url)

    def get_categories(self) -> dict:
        links = self.browser.find_elements(By.XPATH, CrawlerConfig.CATEGORY_LINK_XPATH)
        categories = {
            link.get_attribute("href").replace(CrawlerConfig.CATEGORY_LINK, ""): link.text
            for link in links
        }
        return categories

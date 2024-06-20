from dataclasses import dataclass

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


@dataclass
class BasePage:
    """Базовый класс для сайта."""

    browser: webdriver

    def open(self, link: str):
        """Открывает страницу."""
        self.browser.get(link)

    def scroll_down(self):
        """Пролистывает страницу до конца."""
        self.browser.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )

    def check_captcha(self):
        """Проверяет наличие капчи на странице."""
        try:
            self.browser.find_element(
                By.ID, 'g-recaptcha-response'
            )
            return True
        except NoSuchElementException:
            return False

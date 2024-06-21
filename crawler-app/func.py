from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By


def get_browser(headless: bool = False, no_images: bool = True) -> webdriver.Chrome:
    """Открывает браузер."""
    browser_options = webdriver.ChromeOptions()
    if headless:
        # Режим без показа браузера
        browser_options.add_argument("--headless")
    if no_images:
        # Загрузка страниц без картинок
        browser_options.add_argument("--blink-settings=imagesEnabled=false")
    return webdriver.Chrome(options=browser_options)


def check_captcha(browser: webdriver.Chrome) -> bool:
    """Проверяет наличие капчи."""
    try:
        browser.find_element(By.ID, "g-recaptcha-response")
        return True
    except NoSuchElementException:
        return False


def check_nginx_error(browser: webdriver.Chrome) -> bool:
    """Проверяет наличие ошибки Nginx."""
    try:
        element = browser.find_element(By.TAG_NAME, "h1")
        if element.text == "502 Bad Gateway":
            return True
    except NoSuchElementException:
        return False
    else:
        return False


def check_empty(browser: webdriver.Chrome) -> bool:
    """Проверяет наличие данных на странице."""
    try:
        element = browser.find_element(By.TAG_NAME, "body")
        if not element.text:
            return True
    except NoSuchElementException:
        return False
    else:
        return False

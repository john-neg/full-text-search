import json
import re
import time
from dataclasses import dataclass, field


import translators as ts
from lingua import LanguageDetector

from base.functions import get_language_detector


@dataclass
class LanguageProcessor:
    """Процессор для определения языка и перевода текста."""

    target_language: str
    language_detector: LanguageDetector = get_language_detector()
    translations: dict[str, str] = field(default_factory=dict)

    def get_language(self, text: str) -> str:
        """Возвращает язык текста."""
        try:
            return self.language_detector.detect_language_of(text).name.lower()
        except AttributeError:
            return ""

    def translate(self, text: str):
        """Осуществляет перевод текста на указанный язык."""
        text = text.lower()
        if text not in self.translations:
            translation = ts.translate_text(
                text, translator="bing", to_language=self.target_language[:2]
            )
            print(f"Translation request -> {text}")
            self.translations[text] = translation.lower()
            time.sleep(1)
            return translation
        return self.translations[text]

    def load_translations(self, filename: str):
        with open(filename, "r", encoding="utf8") as trans_file:
            self.translations = json.loads(trans_file.read())

    def save_translations(self, filename: str):
        with open(filename, "w", encoding="utf8") as trans_file:
            trans_file.write(
                json.dumps(self.translations, ensure_ascii=False, indent=3)
            )


@dataclass
class BaseTextProcessor:
    """Базовый процессор для обработки текста."""

    REPLACE_DICT = {
        "c": "с",
        "a": "а",
        "e": "е",
        "p": "р",
        "y": "у",
        "o": "о",
        "ё": "е",
        "m": "м",
        "k": "к",
        "b": "в",
        "h": "н",
        "3": "з",
        "0": "о",
        "x": "х",
    }

    def __post_init__(self):
        self.translate_table = {ord(k): ord(v) for k, v in self.REPLACE_DICT.items()}

    def fix_letters(self, text: str) -> str:
        """Замена символов в тексте."""

        return text.translate(self.translate_table)


@dataclass
class KeywordsProcessor(BaseTextProcessor):
    """Процессор для ключевых слов."""

    lang_processor: LanguageProcessor

    RE_FILTER_SYMBOLS = re.compile(r"[^а-яьъёa-zА-ЯA-Z\s\-]")

    def translate(self, keywords_list: list) -> list:
        """Переводит иностранные слова."""
        result = []
        for word in keywords_list:
            if word:
                if self.lang_processor.get_language(word) != self.lang_processor.target_language:
                    word = self.lang_processor.translate(word)
                result.append(word)
        return result

    def filter_symbols(self, keywords_list: list) -> list:
        """Фильтрует символы и переводит в нижний регистр."""

        keyword_list = [
            re.sub(self.RE_FILTER_SYMBOLS, "", keyword.lower())
            for keyword in keywords_list
            if keyword
        ]
        return keyword_list


class AbstractProcessor(BaseTextProcessor):
    """Процессор для аннотаций статей."""


class ArticleProcessor(BaseTextProcessor):
    """Процессор для текстов статей."""

    # Ищет все символы, которые не являются буквами кириллицы
    # (от "а" до "я" и от "А" до "Я"), запятой, пробелом,
    # точкой, двоеточием или дефисом.
    RE_FILTER_TEXT = re.compile(r"([^а-яА-Я ,.:\-]+)")

    # Ищет любой символ, который не является кириллической
    # буквой "аАяЯвВсСуУиИкКоО" или дефисом,
    # и который находится между двумя пробелами.
    RE_SINGLE_LETTERS = re.compile(r"\s[^аАяЯвВсСуУиИкКоО\-]\s")

    # Ищет запятую, за которой следует граница слова
    RE_COMMA_FIX = re.compile(r"[,]\b")

    # Ищет точку, за которой следует граница слова
    RE_POINT_FIX = re.compile(r"[.]\b")

    #  Ищет один или несколько символов, которые не
    #  являются буквами, цифрами или знаками подчеркивания,
    #  за которыми следует последовательность из двух
    #  или более таких символов
    RE_PUNCTUATION_REMOVE = re.compile(r"\W(\W{2,})")

    # Ищет один или более пробельных символа подряд
    RE_SPACES = re.compile(r"\s+")

    def cleanup(self, text: str) -> str:
        """Очистка текста при помощи регулярных выражений."""

        pipeline = {
            self.RE_FILTER_TEXT: r" ",
            self.RE_SINGLE_LETTERS: r" ",
            self.RE_COMMA_FIX: r", ",
            self.RE_POINT_FIX: r". ",
            self.RE_PUNCTUATION_REMOVE: r" ",
            self.RE_SINGLE_LETTERS: r" ",
            self.RE_SPACES: r" ",
        }

        for pattern, repl in pipeline.items():
            text = re.sub(pattern, repl, text)
        return text

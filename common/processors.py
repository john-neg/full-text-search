import json
import os
import re
import time
from copy import copy
from dataclasses import dataclass, field

import translators as ts
from lingua import LanguageDetector
from requests import HTTPError
from spacy import Language
from translators.server import TranslatorError

from common.func import get_language_detector, lemmatization
from config import BaseConfig
from ml_models.models import Word2VecModel


@dataclass
class LanguageProcessor:
    """Процессор для определения языка и перевода текста.

    Attributes:
        target_language (str): язык ("russian", "english" и т.д.)
        language_detector (LanguageDetector): объект определителя языка
        translations (dict[str, str]): словарь переводов
    """

    target_language: str = "russian"
    language_detector: LanguageDetector = get_language_detector()
    translations: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        try:
            self.load_translations(BaseConfig.TRANSLATIONS_CACHE_FILE)
        except FileNotFoundError:
            pass

    def get_language(self, text: str) -> str:
        """Возвращает язык текста."""
        try:
            return self.language_detector.detect_language_of(text).name.lower()
        except AttributeError:
            return ""

    def _translator(self, text_data, service):
        """Осуществляет перевод."""

        return ts.translate_text(
            text_data,
            translator=service,
            to_language=self.target_language[:2],
            sleep_seconds=1,
        )

    def translate_keyword(self, word: str):
        """Осуществляет перевод слова или выражения на указанный язык."""
        word = word.lower()
        if word not in self.translations:
            translation = self._translator(word, "bing")
            print(f"Translation request -> {word}")
            self.translations[word] = translation.lower()
            time.sleep(1)
            return translation
        return self.translations[word]

    def translate_text(self, text: str):
        """Осуществляет перевод текста на указанный язык."""

        if text:
            from_language = self.get_language(text)
            if from_language and from_language != self.target_language:
                print(f"Translation request -> {text[:25]}")
                try:
                    translation = self._translator(text, "yandex")
                except HTTPError:
                    translation = self._translator(text, "bing")
                except TranslatorError:
                    translation = self._translator(text, "google")
                return translation
        return text

    def load_translations(self, filename: str):
        if os.path.exists(filename):
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

    RE_FILTER_SYMBOLS = re.compile(r"[^а-яьъёa-zА-ЯA-Z\s\-]")
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

    def filter_letters(self, text: str) -> str:
        """Фильтр символов."""
        return re.sub(self.RE_FILTER_SYMBOLS, "", text.lower())

    def fix_letters(self, text: str) -> str:
        """Замена символов в OCR тексте."""
        return text.translate(self.translate_table)


class TitleProcessor(BaseTextProcessor):
    """Процессор для названий статей."""


@dataclass
class KeywordsProcessor(BaseTextProcessor):
    """Процессор для ключевых слов."""

    lang_processor: LanguageProcessor

    def translate(self, keywords_list: list) -> list:
        """Переводит иностранные слова."""
        result = []
        for word in keywords_list:
            if word:
                if (
                    self.lang_processor.get_language(word)
                    != self.lang_processor.target_language
                ):
                    word = self.lang_processor.translate_keyword(word)
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


class TextProcessor(BaseTextProcessor):
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


@dataclass
class SearchPrepareProcessor:
    """Класс для добавления предсказанных слов к тексту."""

    nlp_model: Language
    prediction_model: Word2VecModel
    vocabulary: list
    processor: KeywordsProcessor

    def process_text(self, text: str) -> str:
        """Формирует поисковый запрос."""
        text = self.processor.filter_letters(text)
        words = lemmatization(self.nlp_model(text))
        words = self.processor.translate(words)
        return " ".join(words)

    def add_similar_words(self, text: str) -> str:
        """Дополняет поисковый запрос."""
        words = self.process_text(text).split()
        addon = []
        for word in copy(words):
            if word in self.vocabulary:
                try:
                    similar_words = self.prediction_model.most_similar(
                        word, qty=BaseConfig.AUTOCOMPLETE_SIZE
                    )
                    addon.extend(
                        [
                            w for w, percent in similar_words
                            if w not in words and percent > 0.4
                        ]
                    )
                except KeyError:
                    pass
        return " ".join(addon)

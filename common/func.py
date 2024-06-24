import string

import spacy
from lingua import LanguageDetector, LanguageDetectorBuilder
from spacy import Language
from spacy.tokens import Doc
from spacy.lang.ru import stop_words

from config import BaseConfig

with open(BaseConfig.STOP_WORDS_FILE) as file:
    stopwords = set([word.strip() for word in file.readlines()])
    stopwords.update(stop_words.STOP_WORDS)


def get_language_detector() -> LanguageDetector:
    """Возвращает объект класса LanguageDetector для определения языка."""
    return (
        LanguageDetectorBuilder.from_all_languages()
        .with_preloaded_language_models()
        .build()
    )


def get_nlp_model(name: str = "ru_core_news_lg") -> Language:
    """Возвращает Pipeline NLP модели SpaCy."""

    model = spacy.load(name)
    return model


def lemmatization(sentence: Doc):

    # Лемматизация
    sentence = [
        word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_
        for word in sentence
    ]
    # Фильтры
    sentence = [
        word
        for word in sentence
        if all(
            [
                # Нет в стоп словах
                word not in stopwords,
                # Не пунктуация
                word not in string.punctuation,
                # Только буквы
                word.isalpha(),
                # Не латинские буквы
                not word.isascii(),
                # Длина больше 2
                len(word) > 2,
            ]
        )
    ]
    return sentence

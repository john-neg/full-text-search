import string

from lingua import LanguageDetector
from lingua import LanguageDetectorBuilder
from spacy.lang.ru import stop_words
from spacy.tokens import Doc


def get_language_detector() -> LanguageDetector:
    """Возвращает объект класса LanguageDetector для определения языка."""
    return (
        LanguageDetectorBuilder.from_all_languages()
        .with_preloaded_language_models()
        .build()
    )


def get_language(text, detector) -> str:
    """Возвращает язык текста."""
    try:
        return detector.detect_language_of(text).name.lower()
    except AttributeError:
        return ""


def lemmatization(sentence: Doc):

    # Лемматизация
    sentence = [
        word.lemma_.lower().strip() if word.lemma_ != "-PRON-"
        else word.lower_ for word in sentence
    ]
    # Фильтры
    sentence = [
        word for word in sentence if all(
            [
                # Нет в стоп словах
                word not in stop_words.STOP_WORDS,
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

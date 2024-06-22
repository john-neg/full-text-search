from dataclasses import dataclass
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass
class TfIdfModel:
    tfidf_vectorizer: TfidfVectorizer

    def fit_and_make_tfidf_matrix(self, data: Iterable[str]):
        """Обучает модель, возвращает TfIdf матрицу."""
        return self.tfidf_vectorizer.fit_transform(data)

    def get_new_vector(self, search_lemma: str):
        """Создает новый вектор."""
        return self.tfidf_vectorizer.transform([search_lemma]).toarray()

    @staticmethod
    def search_similar(new_vector, size: int, tfidf_matrix):
        """Находит ближайшие документы."""

        def cosine_sim(a, b):
            """Рассчитывает косинусное сходство."""
            cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            return cos_sim

        cosines = enumerate(
            [
                cosine_sim(vector.reshape(-1), new_vector.reshape(-1))
                for vector in tfidf_matrix.toarray()
            ]
        )
        return sorted(cosines, key=lambda x: x[1], reverse=True)[:size]


def get_tfidf_vectorizer(vocabulary: list[str]) -> TfidfVectorizer:
    return TfidfVectorizer(
        ngram_range=(1, 1),
        encoding="utf-8",
        vocabulary=vocabulary,
    )

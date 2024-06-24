import pickle
from dataclasses import dataclass, field
from zipfile import ZIP_DEFLATED, ZipFile

from bson import ObjectId, json_util
from gensim.models import Word2Vec
from pymongo.cursor import Cursor
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm

from common.db_repository import DocumentType
from common.models import ArticleDocument


@dataclass
class ArticlesLemmasIterator:
    """Класс для итерации по аттрибутам коллекции документов."""

    db_list: Cursor[DocumentType]
    lemmas_fields: list
    _stack: list = field(default_factory=list)
    objects_ids: dict = field(default_factory=dict)
    counter = 0

    def __iter__(self):
        return self

    def __next__(self):
        article = ArticleDocument(**self.db_list.next())
        self.objects_ids[self.counter] = article._id
        self.counter += 1
        lemmas = " ".join(
            [val for key, val in article.lemmas.items() if key in self.lemmas_fields]
        )
        return lemmas


@dataclass
class TfIdfModel:
    """Класс для работы с TF-IDF моделью."""

    vectorizer: TfidfVectorizer = None
    matrix: sparse.csr_matrix = None
    matrix_objects: dict = field(default_factory=dict)

    def fit_and_build_matrix(
        self, data: ArticlesLemmasIterator, show_progress: bool = False
    ) -> None:
        """Обучает модель, создает TfIdf матрицу."""
        if self.vectorizer is None:
            raise ValueError("В модели отсутствует TfidfVectorizer")
        self.matrix = self.vectorizer.fit_transform(
            tqdm(data) if show_progress else data
        )
        self.matrix_objects = data.objects_ids

    def search_similar(self, search_lemma: str, n: int) -> dict[ObjectId, float]:
        """Находит ближайшие документы."""
        if self.matrix is None:
            raise ValueError("В модели отсутствует Tf-Idf матрица")
        new_vector = self.vectorizer.transform([search_lemma]).transpose()
        cos_similarity = self.matrix.dot(new_vector).toarray()
        sorted_objects = sorted(
            enumerate(cos_similarity), key=lambda x: x[1], reverse=True
        )[:n]
        return {self.matrix_objects[key]: sum(val) for key, val in sorted_objects}

    def save(self, filename) -> None:
        with ZipFile(
            filename, mode="w", compression=ZIP_DEFLATED, compresslevel=9
        ) as zip_file:
            with zip_file.open("vectorizer.pkl", "w") as vector_file:
                pickle.dump(
                    self.vectorizer,
                    vector_file,
                    protocol=pickle.HIGHEST_PROTOCOL,
                )
            with zip_file.open("matrix.npz", "w") as matrix_file:
                sparse.save_npz(matrix_file, self.matrix)
            zip_file.writestr(
                "matrix_objects.json",
                json_util.dumps(self.matrix_objects, ensure_ascii=False, indent=3),
            )

    def load(self, filename: str) -> None:
        with ZipFile(filename) as zip_file:
            with zip_file.open("vectorizer.pkl") as vector_file:
                self.vectorizer = pickle.load(vector_file)
            with zip_file.open("matrix.npz") as matrix_file:
                self.matrix = sparse.load_npz(matrix_file)
            with zip_file.open("matrix_objects.json") as obj_file:
                data = json_util.loads(obj_file.read())
                self.matrix_objects = {int(k): v for k, v in data.items()}


@dataclass
class Word2VecModel:
    """Класс для работы с Word2Vec моделью."""

    model: Word2Vec = None

    def fit(
        self,
        data: ArticlesLemmasIterator,
        vector_size: int = 300,
        show_progress: bool = False,
        **kwargs
    ) -> None:
        if show_progress:
            data = tqdm(data)
        texts = [abstract.split() for abstract in data]
        self.model = Word2Vec(sentences=texts, vector_size=vector_size, **kwargs)

    def load(self, filename: str) -> None:
        """Загружает модель из файла."""
        self.model = Word2Vec.load(filename)

    def save(self, filename: str) -> None:
        """Сохраняет модель в файл."""
        if self.model is not None:
            self.model = self.model.save(filename)
        else:
            raise ValueError("Отсутствует объект модели Word2Vec.")

    def most_similar(self, word: str, qty: int = 5) -> list[tuple[str, float]]:
        """Метод нахождения ближайших слов."""
        if self.model is not None:
            return self.model.wv.most_similar(word, topn=qty)
        raise ValueError("Отсутствует объект модели Word2Vec.")

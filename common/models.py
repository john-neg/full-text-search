from dataclasses import dataclass, field

from bson import ObjectId

from config import DocumentStatusType


@dataclass
class ArticleDocument:
    _id: ObjectId
    article_slug: str = ""
    authors: list[str] = field(default_factory=list)
    title: str = ""
    year: str = ""
    magazine: str = ""
    magazine_issue: str = ""
    magazine_volume: str = ""
    keywords: list = field(default_factory=list)
    abstract: str = ""
    scopus: str = ""
    vak: str = ""
    reference: str = ""
    text: str = ""
    language: str = ""
    parse_status: DocumentStatusType = DocumentStatusType.WAITING
    processing_status: DocumentStatusType = DocumentStatusType.WAITING
    lemmatization_status: DocumentStatusType = DocumentStatusType.WAITING
    lemmas: dict = field(default_factory=dict)

    def to_dict(self):
        return self.__dict__

    def __iter__(self):
        yield from self.__dict__.items()

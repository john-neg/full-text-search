import os.path

from tqdm import tqdm

from config import BaseConfig, DocumentStatusType
from common.db_service import get_mongo_db_document_service
from common.models import ArticleDocument
from common.processors import (
    AbstractProcessor,
    KeywordsProcessor,
    LanguageProcessor,
    TextProcessor,
)

# Языковой процессор
language_processor = LanguageProcessor(target_language="russian")
# Ранее сделанные переводы
language_processor.load_translations(
    os.path.join(BaseConfig.DATA_DIR, "keyword_translations.json")
)
# Процессор ключевых слов
keywords_processor = KeywordsProcessor(lang_processor=language_processor)
# Процессор аннотаций
abstract_processor = AbstractProcessor()
# Процессор текстов статей
articles_processor = TextProcessor()


def process_articles(database):
    for db_record in tqdm(
        database.list(
            {
                "parse_status": DocumentStatusType.COMPLETED,
                "processing_status": DocumentStatusType.WAITING,
            }
        )
    ):
        try:
            document = ArticleDocument(**db_record)
            if document.reference and document.language == "russian":
                # Обработка ключевых слов
                keywords = keywords_processor.filter_symbols(document.keywords)
                keywords = keywords_processor.translate(keywords)
                document.keywords = keywords
                # Обработка аннотаций
                abstract = abstract_processor.filter_letters(document.abstract)
                abstract = language_processor.translate_text(abstract)
                document.abstract = abstract
                # Обработка текстов
                text = articles_processor.fix_letters(document.text)
                text = articles_processor.cleanup(text)
                document.text = text
                document.processing_status = DocumentStatusType.COMPLETED

                database.update(
                    {"_id": db_record.get("_id")},
                    {"$set": document.to_dict()},
                )
        except Exception as e:
            print(str(e))
            continue


if __name__ == "__main__":
    db = get_mongo_db_document_service()
    process_articles(db)
    # Сохраняем словарь переводов
    language_processor.save_translations(
        os.path.join(BaseConfig.DATA_DIR, "keyword_translations.json")
    )

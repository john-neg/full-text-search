from common.db_service import get_mongo_db_document_service
from common.func import get_nlp_model, lemmatization
from config import BaseConfig
from ml_models.func import get_db_list, get_lemmas_count


db = get_mongo_db_document_service()
nlp_model = get_nlp_model()

# Открываем внешний словарь
with open(BaseConfig.EXT_VOCAB_FILE, encoding="utf-8") as file:
    math_vocab = [item.strip() for item in file.readlines()]

# Лемматизация слов
vocabulary = set()

for keyword in math_vocab:
    vocabulary.update(lemmatization(nlp_model(keyword)))

# Считаем количество повторений каждой леммы в текстах
lemmas_counter = get_lemmas_count(get_db_list(db), show_progress=True)

# Создаем словарь наиболее часто встречаемых слов в текстах
articles_vocabulary = [
    word
    for word, _ in lemmas_counter.most_common(BaseConfig.VOCABULARY_SIZE)
    if word not in vocabulary
]

# Объединяем словари
final_vocabulary = list(vocabulary)
final_vocabulary.extend(articles_vocabulary)

# Сохраняем в файл
with open(BaseConfig.EXT_VOCAB_FILE, mode="w", encoding="utf-8") as file:
    file.write("\n".join(sorted(final_vocabulary[: BaseConfig.VOCABULARY_SIZE])))

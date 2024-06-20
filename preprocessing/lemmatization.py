import csv
import os
import sys
from typing import Iterable

import spacy
from tqdm import tqdm

from base.functions import lemmatization
from config import BaseConfig

csv.field_size_limit(sys.maxsize)

nlp = spacy.load("ru_core_news_lg")


def lemmatize_to_file(
    text_data: Iterable[tuple[str, str]], 
    batch_size: int = 50, 
    n_process: int = 3, 
    filename: str = "lemmatized_data",
):
    counter = 0

    with open(os.path.join(BaseConfig.DATASET_DIR, f'{filename}.csv'), 'w', newline='', encoding="utf-8-sig") as csvfile:
        fieldnames = ['reference', 'lemmas']
        writer = csv.DictWriter(csvfile, delimiter=';', fieldnames=fieldnames)
        writer.writeheader()

    with open(os.path.join(BaseConfig.DATASET_DIR, f'{filename}_errors.csv'), 'w', newline='', encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, delimiter=';', fieldnames=fieldnames)
        writer.writeheader()

    for text, context in nlp.pipe(
        text_data,
        batch_size=batch_size,
        n_process=n_process,
        disable=['parser', 'ner'],
        as_tuples=True
    ):
        counter += 1

        lemmas = lemmatization(text)
        result = {
            'reference': context,
            'lemmas': ' '.join(lemmas),
        }
        if result['lemmas'] and result['reference']:
            with open(os.path.join(BaseConfig.DATASET_DIR, f'{filename}.csv'), 'a', newline='', encoding="utf-8-sig") as file1:
                writer1 = csv.DictWriter(file1, delimiter=';', fieldnames=fieldnames)
                writer1.writerow(result)
        else:
            with open(os.path.join(BaseConfig.DATASET_DIR, f'{filename}_errors.csv'), 'a', newline='', encoding="utf-8-sig") as file2:
                result['reference'] = f"{counter} {result['reference']}"
                writer2 = csv.DictWriter(file2, delimiter=';', fieldnames=fieldnames)
                writer2.writerow(result)


if __name__ == "__main__":
    with open(os.path.join(BaseConfig.DATASET_DIR, 'processed_articles.csv'), 'rt+', newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=['reference', 'keywords', 'abstract', 'text'])

        data = ((f"{' '.join(row['keywords'])} {row['abstract']}", row['reference']) for row in reader)
        lemmatize_to_file(tqdm(data))

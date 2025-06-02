import pandas as pd
import numpy as np
import datetime
import re
from pymorphy2 import MorphAnalyzer
from nltk.corpus import stopwords
import onnxruntime as ort
from transformers import AutoTokenizer

# Создание списка стоп-слов
stopwords_ru = stopwords.words('russian')
stopwords_ru.remove('ничего')
stopwords_ru.remove('один')
stopwords_ru.remove('сейчас')
stopwords_ru.remove('никогда')
stopwords_ru.remove('другой')
stopwords_ru.remove('иногда')


model_path = r'D:\Работа\ЭНЭКА\Модели\nomic-embed-text\onnx\model.onnx'
session = ort.InferenceSession(model_path, providers=['DmlExecutionProvider', 'CPUExecutionProvider'])
tokenizer = AutoTokenizer.from_pretrained(r'D:\Работа\ЭНЭКА\Модели\nomic-embed-text')


def clean_data(x: str) -> list | str:
    split = x.split(',')
    if len(split) > 1:
        return [v.strip().replace(' ', '').lower() for v in split]
    else:
        return x.strip().replace(' ', '').lower()
    

def create_soup(x: dict) -> str:
    description = x['description'].lower().replace('\n', ' ') if isinstance(x['description'], str) else ''
    
    country = x['country']
    if isinstance(country, list):
        country = ', '.join(country)
        
    directors = x['directors']
    if isinstance(directors, list):
        directors = ', '.join(directors)
        
    starring = x['starring']
    if isinstance(starring, list):
        starring = ', '.join(starring)
        
    genre = x['genre']
    if isinstance(genre, list):
        genre = ', '.join(genre)
        
    return re.sub('[^A-Za-zА-Яа-я0-9/ ]+', '', 
        'описание: ' + description + '; страна: ' + country + '; год: ' + str(
            x['year']
        ) + '; режиссер: ' + directors + '; актеры: ' + starring + '; возрастное ограничение: ' + str(
            x['age_limit']
        ) + '; жанр: ' + genre
    )
    

morph = MorphAnalyzer()
def lemmatize(document: str) -> str:
    words = []
    for word in document.replace('/', ' ').split():
        word = word.strip(';:,.!? ')
        if word and word not in stopwords_ru:
            word = morph.normal_forms(word)[0]
            words.append(word)
    if len(words) > 2:
        return ' '.join(words)
    return ''


def encode_sentences(sentences: str) -> np.array:
    inputs = tokenizer(sentences, return_tensors='np', padding=True, truncation=True)
    inputs = {k: v.astype(np.int64) for k, v in inputs.items()}
    
    outputs = session.run(None, inputs)
    token_embeddings = outputs[0]  
    input_mask_expanded = inputs['attention_mask'].astype(np.float32)[..., np.newaxis]
    
    sum_embeddings = np.sum(token_embeddings*input_mask_expanded, axis=1)
    sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
    mean_embeddings = sum_embeddings / sum_mask
    
    norms = np.linalg.norm(mean_embeddings, axis=1, keepdims=True)
    return mean_embeddings / norms


def embeddings_formation(data: dict) -> str:
    movies = data.copy()
    year = movies['year']
    movies['year'] = year if year else datetime.date.today().year
    
    features = ('country', 'directors', 'starring', 'genre')
    for feature in features:
        value = movies[feature]
        movies[feature] = clean_data(value) if value else ''

    soup = create_soup(movies)
    lemmatize_soup = lemmatize(soup)
    embeddings = encode_sentences(lemmatize_soup)[0]
    
    return str(embeddings)


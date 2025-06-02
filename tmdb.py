import requests
import unidecode
import re
import streamlit as st

api_key = 'bca0301fdaef731a39446ec876ff257f'

def slugify(title: str) -> str:
    title = unidecode.unidecode(title).lower()
    title = re.sub(r'[^a-z0-9\s-]', '', title)
    title = re.sub(r'[\s]+', '-', title)
    return title.strip('-')

@st.cache_data(ttl=86400)  # Кэшируем на 24 часа
def search_movie(title: str, language='ru-RU'):
    search_url = "https://api.themoviedb.org/3/search/movie"
    search_params = {
        "api_key": api_key,
        "query": title,
        "language": language
    }
    search_response = requests.get(search_url, params=search_params)
    return search_response.json()

@st.cache_data(ttl=86400)  # Кэшируем на 24 часа
def get_similar_movies(movie_id: int, language='ru-RU'):
    similar_url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
    similar_params = {
        "api_key": api_key,
        "language": language,
        "page": 1
    }
    similar_response = requests.get(similar_url, params=similar_params)
    return similar_response.json()

def tmdb_similar_movies(title: str, language='ru-RU') -> list:
    try:
        # Поиск id фильма по русскому названию с использованием кэшированной функции
        search_data = search_movie(title, language)

        if not search_data.get('results'):
            return []

        movie_id = search_data['results'][0]['id']

        # Запрос похожих фильмов с использованием кэшированной функции
        similar_data = get_similar_movies(movie_id, language)
        similar_movies = similar_data.get('results', [])

        return [{
                'name': movie['title'],
                'tmdb_url': f"https://www.themoviedb.org/movie/{movie['id']}-{slugify(movie['title'])}"
            }
            for movie in similar_movies
        ]
    except:
        return []

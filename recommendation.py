from supabase_connection import supabase_client
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_distances



def recommendation(movie_id: int, m=5) -> list:
    movies = pd.DataFrame(
        supabase_client.table('movies').select('*').execute().data
    )

    movies['embedding'] = movies['embedding'].map(
        lambda x: np.fromstring(x.strip('[]'), sep=' ')
    )
    movies['genre'] = movies['genre'].map(lambda x: set(x) if isinstance(x, list) else {x})

    # Получаем информацию о текущем фильме
    current_movie = movies[movies['id'] == movie_id].iloc[0]
    genre = current_movie['genre']
    age_limit = current_movie['age_limit']
    
    # Получаем список всех id фильмов, кроме текущего
    ids = list(movies['id'].values)
    ids.remove(movie_id)
    
    # Фильтруем фильмы по жанру и возрастному ограничению
    applicants_genre_age = []
    # applicants_genre = []
    # applicants_age = []
    for i in ids:
        i_genre = movies[movies['id'] == i]['genre'].iloc[0]
        i_age_limit = movies[movies['id'] == i]['age_limit'].iloc[0]

        if (i_genre & genre) and (i_age_limit >= age_limit):
            applicants_genre_age.append(i)
        # elif i_genre & genre:
        #     applicants_genre.append(i)
        # elif i_age_limit >= age_limit:
        #     applicants_age.append(i)
        else:
            continue
        
    
    distances = cosine_distances(np.stack(movies['embedding'].values))
    movie_index = movies[movies['id'] == movie_id].index[0]
    
    if applicants_genre_age:
        applicants_indeces = movies[movies['id'].isin(applicants_genre_age)].index
    # elif applicants_genre:
    #     applicants_indeces = movies[movies['id'].isin(applicants_genre)].index 
    # elif applicants_age:
    #     applicants_indeces = movies[movies['id'].isin(applicants_age)].index
    else:
        applicants_indeces = []

    if len(applicants_indeces):  
        movie_distances = distances[movie_index][applicants_indeces]
        sorted_indices = np.argsort(movie_distances)[:m]
        similar_movies = movies.iloc[np.array(applicants_indeces)[sorted_indices]]['id'].values
        
        similar_movies = supabase_client.table(
            'movies'
        ).select('id, name').in_(
            'id', similar_movies
        ).execute().data
    else:
        similar_movies = []

    return similar_movies

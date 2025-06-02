import streamlit as st
from supabase_connection import supabase_client

def init_api():
    def get_rating(movie_id, user_id):
        result = supabase_client.table('history').select('rating').eq('movie_id', movie_id).eq('user_id', user_id).execute()
        if result.data and result.data[0]['rating'] is not None:
            return result.data[0]['rating']
        return None


    def save_rating(movie_id, user_id, rating):
        # Проверяем существование записи
        existing = supabase_client.table('history').select('*').eq('movie_id', movie_id).eq('user_id', user_id).execute()
        
        if existing.data:
            # Обновляем существующую запись
            supabase_client.table('history').update({'rating': rating}).eq('movie_id', movie_id).eq('user_id', user_id).execute()
        else:
            # Создаем новую запись
            supabase_client.table('history').insert({
                'movie_id': movie_id,
                'user_id': user_id,
                'rating': rating,
                'watched': 1
            }).execute()
        
        return True

    # Регистрируем API-эндпоинты
    if 'api' not in st.session_state:
        st.session_state.api = {
            'get_rating': get_rating,
            'save_rating': save_rating
        } 
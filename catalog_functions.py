from supabase_connection import supabase_client, supabase_bucket_name
import streamlit as st
import streamlit.components.v1 as components
from recommendation import recommendation
import pandas as pd
from tmdb import tmdb_similar_movies

@st.cache_data(ttl=3600)
def get_movie_history(user_id, movie_id):
    return supabase_client.table('history').select('*').eq('user_id', user_id).eq('movie_id', movie_id).execute()

@st.cache_data(ttl=3600)
def get_movie_from_db(movie_name):
    return supabase_client.table('movies').select('id, name').eq('name', movie_name).execute()

@st.cache_data(ttl=3600)
def get_poster_url(poster_path):
    return supabase_client.storage.from_(supabase_bucket_name).get_public_url(poster_path)

def show_movie_details(movie):
    st.header(f"{movie['name']}")

    # Сбрасываем рейтинг при изменении фильма
    if 'last_movie_id' not in st.session_state:
        st.session_state.last_movie_id = movie['id']
    elif st.session_state.last_movie_id != movie['id']:
        if 'movie_rating' in st.session_state:
            del st.session_state.movie_rating
        st.session_state.last_movie_id = movie['id']

    history_data = {
        'user_id': st.session_state.user.id,
        'movie_id': movie['id']
    }
    
    # Проверяем существование записи с использованием кэшированной функции
    existing_record = get_movie_history(history_data['user_id'], history_data['movie_id'])
    
    if len(existing_record.data) > 0:
        # Если запись существует, увеличиваем watched на 1
        current_watched = existing_record.data[0]['watched']
        supabase_client.table('history').update({'watched': current_watched + 1}).eq('user_id', history_data['user_id']).eq('movie_id', history_data['movie_id']).execute()
    else:
        # Если записи нет, создаем новую с watched = 1
        history_data['watched'] = 1
        supabase_client.table('history').insert(history_data).execute()

    # Получаем URL постера с использованием кэшированной функции
    poster_url = get_poster_url(movie['poster'])
    
    # Формируем HTML для всей информации о фильме
    params = {
        'description': 'Описание',
        'country': 'Страна производства',
        'year': 'Год выпуска',
        'directors': 'Режиссёры',
        'starring': 'Актёры',
        'duration': 'Продолжительность',
        'age_limit': 'Возрастное ограничение',
        'genre': 'Жанры'
    }
    movie_info = '<div class="movie-info">'
    for key, value in params.items():
        param = movie.get(key, None)
        if param:
            movie_info += f'<h3>{value}</h3><p>{param}</p>'
    movie_info += '</div>'
    
    poster_html = f"""
    <style>
        .poster-container {{
            position: relative;
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            height: auto;
        }}
        .poster-image {{
            width: 100%;
            height: auto;
            transition: filter 0.3s ease;
        }}
        .poster-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 30px;
            opacity: 0;
            transition: opacity 0.3s ease;
            overflow-y: hidden;
            box-sizing: border-box;
            scrollbar-width: thin;
            scrollbar-color: #b91c1c rgba(0, 0, 0, 0.3);
        }}
        .poster-overlay::-webkit-scrollbar {{
            width: 8px;
        }}
        .poster-overlay::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.3);
        }}
        .poster-overlay::-webkit-scrollbar-thumb {{
            background-color: #b91c1c;
            border-radius: 4px;
        }}
        .poster-container:hover .poster-image {{
            filter: brightness(0.7);
        }}
        .poster-container:hover .poster-overlay {{
            opacity: 1;
        }}
        .movie-info h3 {{
            color: #b91c1c;
            margin: 0;
            font-size: 21px;
        }}
        .movie-info p {{
            margin: 5px 0 15px 0;
            line-height: 1.4;
            font-size: 17px;
        }}
    </style>
    <div class="poster-container">
        <img src="{poster_url}" class="poster-image">
        <div class="poster-overlay">
            {movie_info}
        </div>
    </div>
    <script>
        function checkOverflow() {{
            const overlay = document.querySelector('.poster-overlay');
            const content = document.querySelector('.movie-info');
            
            if (content.scrollHeight > overlay.clientHeight) {{
                overlay.style.overflowY = 'auto';
            }} else {{
                overlay.style.overflowY = 'hidden';
            }}
        }}
        
        window.addEventListener('load', checkOverflow);
        window.addEventListener('resize', checkOverflow);
        
        const overlay = document.querySelector('.poster-overlay');
        const observer = new MutationObserver((mutations) => {{
            mutations.forEach((mutation) => {{
                if (mutation.attributeName === 'style') {{
                    const opacity = window.getComputedStyle(overlay).opacity;
                    if (opacity === '1') {{
                        checkOverflow();
                    }}
                }}
            }});
        }});
        
        observer.observe(overlay, {{ attributes: true }});
    </script>
    """
    
    # Используем components.html для корректного рендеринга HTML
    components.html(poster_html, height=800)

    # Получаем текущий рейтинг
    current_rating = None
    if existing_record.data and existing_record.data[0]['rating'] is not None:
        current_rating = existing_record.data[0]['rating']

    # Добавляем CSS для кнопок рейтинга и звезд
    st.markdown(f'''
    <style>
    /* Стили для кнопок рейтинга */
    [data-testid="stButton"] button[key^="star_"] {{
        background: none !important;
        color: #ccc !important;
        border: none !important;
        padding: 0 !important;
        font-size: 2em !important;
        cursor: pointer;
        box-shadow: none !important;
        transition: color 0.2s !important;
    }}
    /* Стили для отображения рейтинга */
    .rating-display {{
        font-size: 2em;
        color: #b91c1c;
        text-align: center;
        margin: 20px 0;
    }}
    </style>
    ''', unsafe_allow_html=True)

    # Отображаем рейтинг
    st.header(f"Оцените фильм")
    
    if 'movie_rating' in st.session_state:
        # Если рейтинг уже установлен в текущей сессии, показываем звезды
        stars = "★" * st.session_state.movie_rating
        st.markdown(f'<div class="rating-display">{stars}</div>', unsafe_allow_html=True)
    else:
        # Если рейтинг еще не установлен в текущей сессии, показываем кнопки
        cols = st.columns(5)
        for i, col in enumerate(cols, 1):
            if col.button("★", key=f"star_{i}", use_container_width=True):
                # Обновляем рейтинг в базе данных
                if existing_record.data:
                    supabase_client.table('history').update({'rating': i}).eq('user_id', history_data['user_id']).eq('movie_id', history_data['movie_id']).execute()
                else:
                    history_data['rating'] = i
                    supabase_client.table('history').insert(history_data).execute()
                # Сохраняем рейтинг в session_state
                st.session_state.movie_rating = i
                st.rerun()
    
    # Получаем похожие фильмы
    similar_movies = recommendation(movie['id'])
    
    if similar_movies:
        st.header(f"Похожие фильмы")
        for similar_movie in similar_movies:
            if st.button(f"{similar_movie['name']}", key=f"similar_{similar_movie['id']}"):
                st.session_state.selected_movie_id = similar_movie['id']
                st.rerun()
    else:
        similar_movies = tmdb_similar_movies(movie['name'])
        if similar_movies:
            st.header("Похожие фильмы из TMDB")
            found_movies = []
            for similar_movie in similar_movies:
                # Ищем фильм в базе данных по названию с использованием кэшированной функции
                movie_in_db = get_movie_from_db(similar_movie['name'])
                if movie_in_db.data:
                    found_movies.append(movie_in_db.data[0])
                    if len(found_movies) > 5:
                        break
            
            if found_movies:
                for found_movie in found_movies:
                    if st.button(f"{found_movie['name']}", key=f"tmdb_similar_{found_movie['id']}"):
                        st.session_state.selected_movie_id = found_movie['id']
                        st.rerun()
            else:
                for similar_movie in similar_movies[:5]:
                    st.markdown(f"""
                        <style>
                        .st-link-button {{
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            font-family: "Source Sans Pro", sans-serif;
                            font-size: 1rem;
                            font-weight: 400;
                            line-height: 1.6;
                            color: rgb(250, 250, 250);
                            background-color: rgb(19, 23, 32);
                            border: 1px solid rgba(250, 250, 250, 0.2);
                            border-radius: 0.5rem;
                            padding: 0.25rem 0.75rem;
                            min-height: 2.5rem;
                            margin: 0px;
                            cursor: pointer;
                            text-align: center;
                            text-decoration: none;
                            transition: all 0.2s ease;
                            user-select: none;
                            text-transform: none;
                            width: auto;
                        }}
                        .st-link-button:hover {{
                            color: #b91c1c;
                            border-color: #b91c1c;
                        }}
                        </style>

                        <div style="margin: 0.5rem 0;">
                            <a href="{similar_movie['tmdb_url']}" target="_blank" style="text-decoration: none;">
                                <button class="st-link-button">{similar_movie['name']}</button>
                            </a>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.write(f"К сожалению, системе не удалось найти похожие фильмы.")

    st.divider()
    if st.button('← Назад к расписанию'):
        st.session_state.selected_movie_id = None
        st.rerun()
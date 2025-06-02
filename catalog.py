import streamlit as st
from supabase_connection import supabase_client   
from datetime import datetime

from catalog_functions import show_movie_details


# Кэширование на 3600 секунд
@st.cache_data(ttl=3600)
def load_movies():
    return supabase_client.table("movies").select("*").execute().data or []

@st.cache_data(ttl=3600)
def load_cinemas():
    return supabase_client.table("cinemas").select("*").execute().data or []

@st.cache_data(ttl=3600)
def load_movie_cinema():
    return supabase_client.table("movie_cinema").select("*").execute().data or []


# Проверка аутентификации
if "user" not in st.session_state or not st.session_state.user:
    st.warning("Пожалуйста, войдите в систему для просмотра каталога")
    st.stop()

if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None


# Загрузка данных с кэшированием
movies = load_movies()
cinemas = load_cinemas()
movie_cinema = load_movie_cinema()

# Создаем словари для быстрого поиска по id
movie_dict = {m['id']: m for m in movies}
cinema_dict = {c['id']: c for c in cinemas}

# Группируем сеансы по дате (только дата, без времени)
sessions_by_date = {}
for session in movie_cinema:
    date_str = session['datetime'].split(', ')[0]
    if date_str not in sessions_by_date:
        sessions_by_date[date_str] = []
    sessions_by_date[date_str].append(session)


if st.session_state.selected_movie_id:
    st.header("Подробно о фильме")
    movie = movie_dict.get(st.session_state.selected_movie_id)
    if movie:
        show_movie_details(movie)
else:
    dates = list(sessions_by_date.keys())
    dates.sort(key=lambda x: datetime.strptime(x, '%d.%m.%Y'))
    for date_str in dates:
        st.subheader(date_str)
        # Собираем строки для таблицы
        rows = []
        for session in sorted(
            sessions_by_date[date_str], key=lambda x: (
                    cinema_dict.get(x['cinema_id'], {'name': ''})['name'],
                    movie_dict.get(x['movie_id'], {'name': ''})['name'],
                    datetime.strptime(x['datetime'].split(', ')[1], '%H:%M')
                )
            ):
            movie = movie_dict.get(session['movie_id'], {'name': 'Неизвестно', 'id': None})
            cinema = cinema_dict.get(session['cinema_id'], {'name': 'Неизвестно'})
            rows.append({
                'Кинотеатр': cinema['name'],
                'Фильм': movie['name'],
                'Время': session['datetime'].split(', ')[1],
                'movie_id': movie['id']
            })

        # Объединяем одинаковые значения
        cinemas_column, movies_column = set(), {}
        for i in range(len(rows)):
            cinema = rows[i]['Кинотеатр']
            if cinema in cinemas_column:
                rows[i]['Кинотеатр'] = ''
            cinemas_column.add(cinema)

            if cinema not in movies_column:
                movies_column[cinema] = set()

            movie_name = rows[i]['Фильм']
            if cinema in movies_column and movie_name in movies_column[cinema]:
                rows[i]['Фильм'] = ''
            movies_column[cinema].add(movie_name)

        # Выводим таблицу через Streamlit-компоненты
        header_cols = st.columns([0.35, 0.5, 0.15])
        header_cols[0].markdown('<b>Кинотеатр</b>', unsafe_allow_html=True)
        header_cols[1].markdown('<b>Фильм</b>', unsafe_allow_html=True)
        header_cols[2].markdown('<b>Время</b>', unsafe_allow_html=True)
        for i, row in enumerate(rows):
            cols = st.columns([0.35, 0.5, 0.15])
            # Кинотеатр
            cols[0].write(row['Кинотеатр'])
            # Фильм (кнопка-ссылка)
            if row['Фильм']:
                if cols[1].button(row['Фильм'], key=f"movie_btn_{date_str}_{i}"):
                    st.session_state.selected_movie_id = row['movie_id']
                    st.rerun()
            else:
                cols[1].write("")
            # Время
            cols[2].write(row['Время'])

# JS обработчик для кнопок фильмов show_movie_details
st.markdown('''
<script>
window.addEventListener('message', (event) => {
    if (event.data && event.data.isStreamlitMessage && event.data.type === 'streamlit:setComponentValue') {
        window.parent.postMessage({isStreamlitMessage: true, type: 'streamlit:setComponentValue', key: event.data.key, value: event.data.value}, '*');
        window.location.reload();
    }
});
</script>
''', unsafe_allow_html=True)

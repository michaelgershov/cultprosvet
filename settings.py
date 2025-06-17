import streamlit as st
from supabase_connection import supabase_client
from recommendation import recommendation
from catalog_functions import show_movie_details
from catalog import movie_dict

def load_history(user_id):
    response = supabase_client.table('history').select('*').eq('user_id', user_id).execute()
    return response.data or []

def personal_recommendation(user_id, k=5) -> list:
    history = load_history(user_id)
    if len(history):
        movies_sorted = sorted(
            history,
            key=lambda x: x['watched']
        )
        related_movies = set()
        for m in movies_sorted[:k]:
            recommended = recommendation(m['movie_id'])
            for r in recommended:
                related_movies.add(tuple(r.values()))

        if related_movies:
            return tuple(related_movies)[:k]
        else:
            return []
    else:
        return []
    
if "selected_movie_id" not in st.session_state:
    st.session_state.selected_movie_id = None

if st.session_state.selected_movie_id:
    st.header("Подробно о фильме")
    movie = movie_dict.get(st.session_state.selected_movie_id)
    if movie:
        show_movie_details(movie)
else:
    st.header("Параметры пользователя")

    # Отображение информации о пользователе
    st.write(f"Email: {st.session_state.user.email}")

    st.header("Персональные рекомендации")
    # Получаем похожие фильмы
    personal_recommended = personal_recommendation(
        st.session_state.user.id
    )
    if personal_recommended:
        for m in personal_recommended:
            if st.button(f"{m[1]}", key=f"{m[0]}"):
                st.session_state.selected_movie_id = m[0]
                st.rerun()
    else:
        st.write("Для получения персональных рекомендаций посмотрите чуть больше фильмов из каталога")
        
    # Изменение пароля
    st.header("Изменить пароль")
    current_password = st.text_input("Текущий пароль", type="password")
    new_password = st.text_input("Новый пароль", type="password")
    confirm_password = st.text_input("Подтвердите новый пароль", type="password")

    if st.button("Изменить пароль"):
        if new_password != confirm_password:
            st.error("Новые пароли не совпадают")
        elif len(new_password) < 6:
            st.error("Длина пароля должна быть не менее 6 символов")
        else:
            try:
                # Обновляем пароль через Supabase
                supabase_client.auth.update_user({"password": new_password})
                st.success("Пароль успешно изменен")
            except Exception as e:
                st.error(f"Ошибка при изменении пароля: {str(e)}")

    # Удаление аккаунта
    st.header("Удаление аккаунта")
    st.warning("Данный функционал находится в разработке.")
    # if st.button("Удалить аккаунт", type="primary"):
    #     if st.checkbox("Я подтверждаю удаление аккаунта"):
    #         try:
    #             # Удаляем пользователя через Supabase
    #             supabase_client.auth.admin.delete_user(st.session_state.user.id)
    #             st.success("Аккаунт успешно удален")
    #             # Выходим из системы
    #             supabase_logout()
    #             st.rerun()
    #         except Exception as e:
    #             st.error(f"Ошибка при удалении аккаунта: {str(e)}")

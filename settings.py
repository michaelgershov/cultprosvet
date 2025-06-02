import streamlit as st
from supabase_connection import supabase_client, supabase_logout

st.header("Параметры пользователя")

# Отображение информации о пользователе
st.subheader("Информация о пользователе")
st.write(f"Email: {st.session_state.user.email}")
st.write(f"ID пользователя: {st.session_state.user.id}")

# Изменение пароля
st.subheader("Изменить пароль")
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
st.subheader("Удаление аккаунта")
st.warning("Внимание: это действие необратимо. Все ваши данные будут удалены.")
if st.button("Удалить аккаунт", type="primary"):
    if st.checkbox("Я подтверждаю удаление аккаунта"):
        try:
            # Удаляем пользователя через Supabase
            supabase_client.auth.admin.delete_user(st.session_state.user.id)
            st.success("Аккаунт успешно удален")
            # Выходим из системы
            supabase_logout()
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка при удалении аккаунта: {str(e)}")
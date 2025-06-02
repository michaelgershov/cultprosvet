import time
import streamlit as st
from supabase_connection import supabase_login, supabase_register, supabase_logout
from api import init_api

# Инициализация API
init_api()

if "user" not in st.session_state:
    st.session_state.user = None



def login():
    st.header("Войти")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Пароль", type="password", key="login_pwd")

    if "login_attempt" not in st.session_state:
        st.session_state.login_attempt = False

    if st.button("Войти"):
        try:
            response = supabase_login(email, password)
            if response.user:
                st.session_state.user = response.user
                st.session_state.login_attempt = True
                st.rerun()
            else:
                st.error("Произошла ошибка аутентификации, попробуйте снова")
        except Exception as e:
            st.error("Неверные адрес электронной почты или пароль")

    # После rerun: если вход был успешным
    if st.session_state.get("login_attempt") and st.session_state.get("user"):
        # Сбросить флаг, чтобы не выполнять вход снова
        st.session_state.login_attempt = False
            
        

def logout():
    response = supabase_logout()
    st.session_state.user = None
    st.rerun()


# добавить переход на страницу входа после успешной регистрации
def register():
    st.header("Регистрация")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Пароль", type="password", key="register_pwd")

    if st.button("Зарегистрироваться"):
        try:
            if len(password) < 6:
                st.error("Длина пароля должна быть не менее 6 символов")
            else:
                response = supabase_register(email, password)
                if response.user:
                    st.success("Письмо с подтверждением регистрации отправлено на указанный адрес электронной почты")
                    time.sleep(5)
                    st.rerun()
                else:
                    st.error("Произошла ошибка регистрации, попробуйте снова")
        except Exception as e:
            st.error(f"Ошибка: {e}")



user = st.session_state.user

logout_page = st.Page(logout, title="Выйти", icon=":material/logout:")
settings = st.Page("settings.py", title="Параметры", icon=":material/settings:")
catalog = st.Page(
    "catalog.py",
    title="Каталог",
    icon=":material/apps:",
    default=True,
)


account_pages = [logout_page, settings]
catalog_pages = [catalog]


st.title("Приложение-агрегатор")
st.logo("images/horizontal.png", icon_image="images/icon_blue.png")

page_dict = {}
if st.session_state.user:
    page_dict["Каталог"] = catalog_pages


if len(page_dict) > 0:
    pg = st.navigation({"Пользователь": account_pages} | page_dict)
else:
    pg = st.navigation([st.Page(login, title="Войти"), st.Page(register, title="Зарегистрироваться")])

pg.run()

import streamlit as st
from supabase_connection import supabase_client, supabase_logout

st.header("О проекте")

st.write("""
    Приложение "Культпросвет" на данный момент является минимально жизнеспособной версией более масштабного проекта,
    направленного на культурное просвещение населения.
    
    Основной источник данных для приложения – интернет-платформа afisha.relax.by:
""")

st.image("images/relax.png", caption="afisha.relax.by", use_column_width=True)


st.write("""
    Дополнительный источник данных для приложения – база данных themoviedb.org (TMDb):
""")

st.image("images/tmdb.svg", caption="themoviedb.org", use_column_width=True)


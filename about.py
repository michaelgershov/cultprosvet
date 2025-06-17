import streamlit as st
from supabase_connection import supabase_client, supabase_logout

st.header("О проекте")

st.write("""
    Приложение "Культпросвет" на данный момент является минимально жизнеспособной версией более масштабного проекта,
    направленного на культурное просвещение населения.
    
    Основной источник данных для приложения – интернет-платформа <a href="https://afisha.relax.by" target="_blank">afisha.relax.by</a>:
""", unsafe_allow_html=True)

st.image("images/relax.png", use_container_width=True)


st.write("""
    Дополнительный источник данных для приложения – база данных <a href="https://www.themoviedb.org" target="_blank">themoviedb.org</a> (TMDb):
""", unsafe_allow_html=True)

st.image("images/tmdb.svg", use_container_width=True)


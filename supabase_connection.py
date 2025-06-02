import streamlit as st
from supabase import create_client


supabase_url = st.secrets["supabase_url"]
supabase_key = st.secrets["supabase_key"]
supabase_admin_key = st.secrets["supabase_admin_key"]
supabase_bucket_name = "cultprosvet-images"

supabase_client = create_client(supabase_url, supabase_key)


def supabase_login(email: str, password: str):
    return supabase_client.auth.sign_in_with_password(
        {"email": email, "password": password}
    )


def supabase_register(email, password):
    return supabase_client.auth.sign_up(
        {"email": email, "password": password}
    )


def supabase_logout():
    return supabase_client.auth.sign_out()

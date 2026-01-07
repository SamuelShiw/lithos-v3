# Archivo: mining_ops/db/supabase_client.py
import streamlit as st
from supabase import create_client, Client
from config.settings import SUPABASE_URL, SUPABASE_KEY

@st.cache_resource
def get_supabase() -> Client:
    """
    Crea y cachea la conexión a Supabase usando las credenciales
    definidas en config/settings.py
    """
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"🔥 Error crítico conectando a Supabase: {e}")
        raise e
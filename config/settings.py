# Archivo: mining_ops/config/settings.py
import streamlit as st

try:
    # Intentamos cargar desde los secretos de Streamlit
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
except FileNotFoundError:
    # Fallback por si no encuentra el archivo (útil para debug)
    raise RuntimeError("❌ No se encontró el archivo .streamlit/secrets.toml")
except KeyError:
    raise RuntimeError("❌ El archivo secrets.toml no tiene la sección [supabase] correcta.")
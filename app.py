import streamlit as st

# Configuración Global
st.set_page_config(page_title="LITHOS V3", page_icon="💎", layout="wide")

# Inicializar Estado de Sesión
if 'user' not in st.session_state:
    st.session_state.user = None

# IMPORTAR VISTAS
from views.login import mostrar_login
from views.dashboard import mostrar_dashboard

# === EL CEREBRO (ROUTER) ===
def main():
    if st.session_state.user is None:
        # No hay usuario -> Mostrar Login
        mostrar_login()
    else:
        # Hay usuario -> Mostrar Dashboard
        mostrar_dashboard()

if __name__ == "__main__":
    main()
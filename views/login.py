import streamlit as st
import time
from db.repositories.usuarios_repo import validar_login

def mostrar_login():
    # ==========================================================================
    # CSS AVANZADO: CORRECCIÓN DE COLOR DE TEXTO
    # ==========================================================================
    st.markdown("""
    <style>
        /* 1. Ocultar Elementos de Navegación de Streamlit */
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stHeader"] { visibility: hidden !important; }
        footer { visibility: hidden !important; }

        /* 2. Tipografía Formal del Sistema */
        .system-title {
            font-family: 'Roboto', sans-serif;
            color: #154360; /* Azul Corporativo */
            font-size: 2.2rem;
            font-weight: 900;
            margin-bottom: 0;
            letter-spacing: -1px;
            line-height: 1.2;
        }
        
        .system-subtitle {
            color: #7F8C8D;
            font-size: 0.85rem;
            margin-bottom: 25px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
        }
        
        /* 3. Ajuste de Inputs (AQUÍ ESTÁ LA CORRECCIÓN) */
        .stTextInput input {
            background-color: #F8F9F9 !important; /* Fondo claro */
            color: #17202A !important;           /* 🔥 TEXTO OSCURO OBLIGATORIO */
            caret-color: #17202A !important;     /* Color del cursor (la barrita que parpadea) */
            border: 1px solid #E5E8E8 !important;
        }
        
        /* Aseguramos que al escribir se vea oscuro */
        .stTextInput input:focus {
            border-color: #154360 !important;
            box-shadow: 0 0 0 1px #154360 !important;
            color: #17202A !important;
        }
        
        /* Corrección para autocompletado de Chrome (fondo amarillo feo) */
        .stTextInput input:-webkit-autofill {
            -webkit-text-fill-color: #17202A !important;
            -webkit-box-shadow: 0 0 0px 1000px #F8F9F9 inset !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # LAYOUT CENTRADO
    # ==========================================================================
    # Usamos columnas para centrar la tarjeta de login
    c1, c2, c3 = st.columns([1, 1.2, 1])

    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True) # Espacio superior para centrar verticalmente
        
        # Contenedor con borde suave
        with st.container(border=True):
            # --- HEADER DE LA TARJETA ---
            st.markdown("""
                <div style="text-align: center;">
                    <img src="https://cdn-icons-png.flaticon.com/512/2592/2592312.png" width="70" style="margin-bottom: 15px; opacity: 0.9;">
                    <div class="system-title">LITHOS V3</div>
                    <div class="system-subtitle">Control de Operaciones Mineras</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---") # Divisor sutil

            # --- FORMULARIO ---
            with st.form("frm_login", clear_on_submit=True, border=False):
                # Inputs
                user_in = st.text_input("ID de Usuario", placeholder="Ingrese su usuario")
                pass_in = st.text_input("Contraseña", type="password", placeholder="••••••••")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Botón de Acción Principal
                btn_login = st.form_submit_button("🔒 INICIAR SESIÓN", type="primary", use_container_width=True)

                # Lógica de Validación
                if btn_login:
                    if not user_in or not pass_in:
                        st.warning("⚠️ Por favor ingrese sus credenciales completas.")
                    else:
                        usuario = validar_login(user_in, pass_in)
                        
                        if usuario:
                            # EXITO: Guardar en sesión y recargar
                            st.session_state.user = usuario
                            st.success(f"Bienvenido, {usuario.get('nombre_completo', 'Usuario')}")
                            time.sleep(0.5) # Breve pausa para UX
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas o acceso denegado.")

        # --- FOOTER DISCRETO ---
        st.markdown("""
            <div style="text-align: center; margin-top: 25px; color: #BDC3C7; font-size: 0.75rem;">
                © 2026 LITHOS Mining Solutions<br>
                Acceso exclusivo para personal autorizado
            </div>
        """, unsafe_allow_html=True)
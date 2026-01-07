import streamlit as st
import pandas as pd
from datetime import datetime

# Repositorios
from db.repositories.labores_repo import get_todas_labores, crear_labor, cambiar_estado_labor
from db.repositories.actividades_repo import get_todas_actividades, crear_actividad, toggle_actividad
from db.repositories.recursos_repo import get_todos_recursos, crear_recurso, actualizar_precio_recurso, toggle_recurso
from db.repositories.usuarios_repo import get_todos_usuarios, crear_usuario, actualizar_datos_usuario, toggle_usuario, reset_password

# ==============================================================================
# SEGURIDAD DE PÁGINA (Solo Admin entra aquí)
# ==============================================================================
if 'user' not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")

usuario_actual = st.session_state.user
if usuario_actual.get('rol_sistema') != 'ADMIN':
    st.error("⛔ Acceso Restringido: Solo Administradores.")
    st.stop()

# ==============================================================================
# CONFIGURACIÓN VISUAL
# ==============================================================================
st.set_page_config(page_title="Configuración", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; padding-top: 10px; }
    .stTabs [aria-selected="true"] { background-color: #F8F9F9; border-bottom: 2px solid #154360; color: #154360; font-weight: bold; }

    /* Inputs y Botones */
    .stSelectbox div[data-baseweb="select"] > div, .stTextInput input { background-color: #2C3E50 !important; color: white !important; }
    div.stButton > button { background-color: #154360; color: white; border-radius: 6px; height: 45px; }
    </style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2592/2592312.png", width=50)
    st.markdown("### LITHOS V3")
    st.page_link("app.py", label="Inicio", icon="🏠")
    st.page_link("pages/1_registro.py", label="Registrar Evento", icon="➕")
    st.page_link("pages/2_consultas.py", label="Consultas", icon="📊")
    st.page_link("pages/3_indicadores.py", label="Indicadores", icon="📈")
    st.page_link("pages/4_configuracion.py", label="Configuración", icon="⚙️")
    st.markdown("---")
    if st.button("Volver al Inicio"): st.switch_page("app.py")

st.title("⚙️ Configuración del Sistema")
st.markdown("Gobierno de datos maestros y ciclo de vida operativo.")

# TABS PRINCIPALES
tab_lab, tab_act, tab_rec, tab_usr = st.tabs(["📍 4.1 Labores", "⚒️ 4.2 Actividades", "📦 4.3 Recursos", "👥 4.4 Personal"])

# ==============================================================================
# TAB 4.1: GESTIÓN DE LABORES
# ==============================================================================
with tab_lab:
    col_main, col_gestion = st.columns([2, 1])

    with col_main:
        st.subheader("Inventario de Labores")
        labores_db = get_todas_labores()
        
        if labores_db:
            df_lab = pd.DataFrame(labores_db)
            if 'estado_ciclo' not in df_lab.columns: df_lab['estado_ciclo'] = 'ACTIVA'
            if 'zona_nivel' not in df_lab.columns: df_lab['zona_nivel'] = '---'
            
            st.dataframe(
                df_lab[['nombre', 'zona_nivel', 'estado_ciclo', 'motivo_estado']],
                column_config={
                    "nombre": "Nombre Labor",
                    "zona_nivel": "Zona / Nivel",
                    "estado_ciclo": st.column_config.TextColumn("Estado", width="small"),
                    "motivo_estado": "Motivo / Condición Actual"
                },
                use_container_width=True, height=400, hide_index=True
            )
            st.caption("*Seleccione una labor a la derecha para gestionar su ciclo.")
        else:
            st.info("No hay labores registradas.")

    with col_gestion:
        st.markdown("### 🛠️ Gestión")
        accion = st.radio("Acción:", ["Nueva Labor", "Cambiar Estado"], horizontal=True, label_visibility="collapsed")
        st.divider()
        
        if accion == "Nueva Labor":
            st.markdown("#### ✨ Crear Labor")
            with st.form("form_crear_labor"):
                new_nombre = st.text_input("Nombre de la Labor", placeholder="Ej: Tajo 32")
                new_zona = st.text_input("Zona o Nivel", placeholder="Ej: Nivel 340 - Zona Este")
                
                tipos_mineros = ["Galería", "Crucero", "Rampa", "Pique", "Bypass", "Chimenea", "Subnivel", "Tajo", "Cámara"]
                new_tipo = st.selectbox("Tipo Geométrico", tipos_mineros) 
                
                if st.form_submit_button("Crear Labor"):
                    if not new_nombre or not new_zona:
                        st.error("El nombre y la Zona/Nivel son obligatorios.")
                    else:
                        ok, msg = crear_labor(new_nombre, 1, new_zona) 
                        if ok: st.success(msg); st.rerun()
                        else: st.error(f"Error: {msg}")

        elif accion == "Cambiar Estado":
            st.markdown("#### 🚦 Ciclo de Vida")
            
            if labores_db:
                labor_dict = {l['nombre']: l for l in labores_db}
                sel_name = st.selectbox("Seleccione Labor", list(labor_dict.keys()))
                labor_sel = labor_dict[sel_name]
                
                curr = labor_sel.get('estado_ciclo', 'ACTIVA')
                c_map = {"ACTIVA": "green", "STANDBY": "orange", "PARADA": "red", "CERRADA": "grey"}
                st.markdown(f"Actual: **:{c_map.get(curr, 'grey')}[{curr}]**")
                
                st.divider()

                opciones_estado = ["ACTIVA", "STANDBY", "PARADA", "CERRADA"]
                idx_actual = opciones_estado.index(curr) if curr in opciones_estado else 0

                new_status = st.selectbox("Nuevo Estado Objetivo", opciones_estado, index=idx_actual)
                
                with st.form("form_estado_final"):
                    motivo = st.text_input("Motivo Principal")
                    
                    if st.form_submit_button("Confirmar Cambio"):
                        ok, msg = cambiar_estado_labor(labor_sel['id'], new_status, motivo)
                        if ok: st.success(f"✅ {msg}"); st.rerun()
                        else: st.error(msg)
            else:
                st.warning("No hay labores.")

# ==============================================================================
# TAB 4.2: GESTIÓN DE ACTIVIDADES
# ==============================================================================
with tab_act:
    col_lista_act, col_form_act = st.columns([2, 1])
    
    with col_lista_act:
        st.subheader("Catálogo de Actividades y Reglas")
        acts_db = get_todas_actividades()
        
        if acts_db:
            df_acts = pd.DataFrame(acts_db)
            
            def format_flags(row):
                flags = []
                if row.get('req_tonelaje'): flags.append("⚖️ Ton")
                if row.get('req_avance'): flags.append("📏 Mts")
                if row.get('req_taladros'): flags.append("🔫 Tal")
                return " + ".join(flags) if flags else "🔧 Solo Servicios"
                
            df_acts['Reglas de Negocio'] = df_acts.apply(format_flags, axis=1)
            
            st.dataframe(
                df_acts[['nombre', 'unidad_produccion', 'Reglas de Negocio', 'activo']],
                column_config={
                    "nombre": "Actividad",
                    "unidad_produccion": st.column_config.TextColumn("Unidad", width="small"),
                    "activo": st.column_config.CheckboxColumn("Activo", width="small"),
                    "Reglas de Negocio": st.column_config.TextColumn("Datos Requeridos", width="medium")
                },
                use_container_width=True, height=400, hide_index=True
            )
        else:
            st.info("No hay actividades configuradas.")

    with col_form_act:
        st.markdown("### ✨ Nueva Actividad")
        st.divider()
        
        with st.form("form_nueva_actividad"):
            a_nom = st.text_input("Nombre Actividad", placeholder="Ej: Relleno Hidráulico")
            a_und = st.selectbox("Unidad de Producción", ["m", "ton", "disparo", "m3", "pza", "gln", "hrs"])
            
            st.markdown("**Reglas de Registro (Flags):**")
            c_f1, c_f2 = st.columns(2)
            f_ton = c_f1.checkbox("Pide Tonelaje")
            f_mts = c_f2.checkbox("Pide Avance (m)")
            f_tal = c_f1.checkbox("Pide Taladros")
            
            if st.form_submit_button("Guardar Actividad"):
                if not a_nom:
                    st.error("El nombre es obligatorio.")
                else:
                    ok, msg = crear_actividad(a_nom, a_und, f_ton, f_mts, f_tal)
                    if ok: st.success(msg); st.rerun()
                    else: st.error(f"Error: {msg}")
        
        if acts_db:
            st.divider()
            st.markdown("#### 🔌 Control de Estado")
            dict_a = {a['nombre']: a for a in acts_db}
            sel_a = st.selectbox("Seleccionar Actividad", list(dict_a.keys()))
            obj_a = dict_a[sel_a]
            
            estado_btn = "Desactivar 🔴" if obj_a['activo'] else "Re-Activar 🟢"
            # KEY ÚNICO
            if st.button(estado_btn, use_container_width=True, key=f"btn_act_{obj_a['id']}"):
                ok, msg = toggle_actividad(obj_a['id'], obj_a['activo'])
                if ok: st.rerun()

# ==============================================================================
# TAB 4.3: GESTIÓN DE RECURSOS (Precios en Soles S/.)
# ==============================================================================
with tab_rec:
    c_lista_rec, c_form_rec = st.columns([2, 1])

    with c_lista_rec:
        st.subheader("Maestro de Materiales")
        recursos_db = get_todos_recursos()
        
        if recursos_db:
            df_rec = pd.DataFrame(recursos_db)
            if 'costo_unitario' in df_rec.columns:
                # CAMBIO A SOLES (S/.)
                df_rec['Costo Unit.'] = df_rec['costo_unitario'].apply(lambda x: f"S/. {float(x):.2f}")
            else:
                df_rec['Costo Unit.'] = "S/. 0.00"

            st.dataframe(
                df_rec[['nombre', 'unidad_medida', 'tipo', 'Costo Unit.', 'activo']],
                column_config={
                    "nombre": "Insumo",
                    "unidad_medida": st.column_config.TextColumn("Und", width="small"),
                    "tipo": st.column_config.TextColumn("Categoría", width="medium"),
                    "activo": st.column_config.CheckboxColumn("Disp", width="small")
                },
                use_container_width=True, height=500, hide_index=True
            )
        else:
            st.info("Almacén vacío.")

    with c_form_rec:
        st.markdown("### 📦 Gestión Almacén")
        accion_rec = st.radio("Operación:", ["Nuevo Producto", "Ajuste Precios", "Activar/Desactivar"], label_visibility="collapsed")
        st.divider()
        
        if accion_rec == "Nuevo Producto":
            with st.form("form_new_rec"):
                r_nom = st.text_input("Nombre del Insumo", placeholder="Ej: Emulsión 3000")
                c1, c2 = st.columns(2)
                r_und = c1.selectbox("Unidad Medida", ["pza", "kg", "m", "m2", "und", "gln", "lts", "cartucho", "caja"])
                r_tipo = c2.selectbox("Categoría", ["EXPLOSIVO", "SOSTENIMIENTO", "ACERO", "OTROS"])
                # CAMBIO A SOLES (S/.)
                r_costo = st.number_input("Costo Unitario (S/.)", min_value=0.0, step=0.1, format="%.2f")
                
                if st.form_submit_button("Ingresar al Maestro"):
                    if r_nom:
                        ok, msg = crear_recurso(r_nom, r_und, r_tipo, r_costo)
                        if ok: st.success(msg); st.rerun()
                        else: st.error(msg)
                    else: st.error("Nombre requerido")

        elif accion_rec == "Ajuste Precios":
            if recursos_db:
                r_dict = {f"{r['nombre']} ({r['tipo']})": r for r in recursos_db}
                sel_r = st.selectbox("Buscar Insumo", list(r_dict.keys()))
                obj_r = r_dict[sel_r]
                
                precio_actual = float(obj_r.get('costo_unitario', 0.0))
                # CAMBIO A SOLES (S/.)
                st.markdown(f"Precio Actual: **S/. {precio_actual:.2f}**")
                
                with st.form("form_price"):
                    # CAMBIO A SOLES (S/.)
                    new_price = st.number_input("Nuevo Precio (S/.)", value=precio_actual, min_value=0.0, step=0.01)
                    if st.form_submit_button("Actualizar Costo"):
                        ok, msg = actualizar_precio_recurso(obj_r['id'], new_price)
                        if ok: st.success(msg); st.rerun()
                        else: st.error(msg)
            else:
                st.warning("No hay recursos.")

        elif accion_rec == "Activar/Desactivar":
            if recursos_db:
                r_dict = {r['nombre']: r for r in recursos_db}
                sel_r = st.selectbox("Insumo", list(r_dict.keys()))
                obj_r = r_dict[sel_r]
                
                btn_txt = "Desactivar 🔴" if obj_r['activo'] else "Re-Activar 🟢"
                
                # KEY ÚNICO
                if st.button(btn_txt, use_container_width=True, key=f"btn_rec_{obj_r['id']}"):
                    toggle_recurso(obj_r['id'], obj_r['activo'])
                    st.rerun()

# ==============================================================================
# TAB 4.4: GESTIÓN DE PERSONAL (COMPLETO)
# ==============================================================================
with tab_usr:
    c_list_usr, c_form_usr = st.columns([2, 1])
    
    # --- A. LISTADO DE USUARIOS ---
    with c_list_usr:
        st.subheader("Directorio de Usuarios")
        usuarios_db = get_todos_usuarios()
        
        if usuarios_db:
            df_usr = pd.DataFrame(usuarios_db)
            st.dataframe(
                df_usr[['nombre_completo', 'username', 'rol_sistema', 'cargo', 'activo']],
                column_config={
                    "nombre_completo": "Nombre Completo",
                    "username": "Usuario (Login)",
                    "rol_sistema": st.column_config.SelectboxColumn("Permiso", options=["ADMIN", "OPERATIVO", "LECTOR"], disabled=True),
                    "cargo": "Cargo RRHH",
                    "activo": st.column_config.CheckboxColumn("Activo")
                },
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No hay usuarios registrados.")

    # --- B. FORMULARIO DE GESTIÓN (Nuevo / Editar) ---
    with c_form_usr:
        # Pestañas internas para organizar
        sub_t1, sub_t2 = st.tabs(["✨ Crear Nuevo", "✏️ Editar Existente"])
        
        # 1. CREAR USUARIO
        with sub_t1:
            st.markdown("#### Alta de Personal")
            with st.form("form_nuevo_usr"):
                u_nom = st.text_input("Nombre Completo")
                u_user = st.text_input("Usuario (Login)", placeholder="sin espacios")
                u_pass = st.text_input("Contraseña", type="password")
                
                c_rol, c_cargo = st.columns(2)
                u_rol = c_rol.selectbox("Permiso", ["OPERATIVO", "LECTOR", "ADMIN"], help="ADMIN: Total, OPERATIVO: Registro, LECTOR: Solo ver")
                u_cargo = c_cargo.text_input("Cargo", placeholder="Ej: Jefe Guardia")
                
                if st.form_submit_button("Registrar Usuario"):
                    if u_nom and u_user and u_pass:
                        ok, msg = crear_usuario(u_nom, u_user, u_pass, u_rol, u_cargo)
                        if ok: st.success(msg); st.rerun()
                        else: st.error(msg)
                    else:
                        st.error("Faltan datos obligatorios")

        # 2. EDITAR USUARIO
        with sub_t2:
            st.markdown("#### Modificación de Datos")
            
            if usuarios_db:
                # Selector de usuario a editar
                dic_u = {f"{u['username']} | {u['nombre_completo']}": u for u in usuarios_db}
                sel_u_key = st.selectbox("Buscar Usuario", list(dic_u.keys()))
                usuario_sel = dic_u[sel_u_key]
                
                st.divider()
                
                # --- EDICIÓN DE DATOS GENERALES ---
                with st.form("form_edit_usr"):
                    st.caption(f"Editando a: **{usuario_sel['nombre_completo']}**")
                    
                    e_nom = st.text_input("Nombre Completo", value=usuario_sel.get('nombre_completo', ''))
                    e_user = st.text_input("Usuario (Login)", value=usuario_sel.get('username', ''))
                    
                    c_e1, c_e2 = st.columns(2)
                    current_rol = usuario_sel.get('rol_sistema')
                    opts_rol = ["OPERATIVO", "LECTOR", "ADMIN"]
                    idx_rol = opts_rol.index(current_rol) if current_rol in opts_rol else 1
                    
                    e_rol = c_e1.selectbox("Permiso Sistema", opts_rol, index=idx_rol)
                    e_cargo = c_e2.text_input("Cargo", value=usuario_sel.get('cargo', ''))
                    
                    if st.form_submit_button("💾 Guardar Cambios"):
                        if e_nom and e_user:
                            ok, msg = actualizar_datos_usuario(usuario_sel['id'], e_nom, e_user, e_rol, e_cargo)
                            if ok: st.success(msg); st.rerun()
                            else: st.error(msg)
                        else:
                            st.error("Nombre y Usuario requeridos")

                # --- ACCIONES CRÍTICAS (Fuera del form principal) ---
                st.markdown("##### Acciones de Seguridad")
                col_pass, col_act = st.columns(2)
                
                # Cambio de Contraseña
                with col_pass:
                    with st.popover("🔑 Cambiar Clave"):
                        st.markdown(f"Nueva clave para **{usuario_sel['username']}**")
                        new_pass = st.text_input("Nueva Contraseña", type="password", key=f"np_{usuario_sel['id']}")
                        if st.button("Actualizar Clave", key=f"btn_pass_{usuario_sel['id']}"):
                            if new_pass:
                                reset_password(usuario_sel['id'], new_pass)
                                st.success("Clave cambiada")
                            else:
                                st.warning("Escriba algo")

                # Activar / Desactivar
                with col_act:
                    estado_lbl = "Desactivar 🔴" if usuario_sel['activo'] else "Reactivar 🟢"
                    if st.button(estado_lbl, use_container_width=True, key=f"btn_st_{usuario_sel['id']}"):
                        toggle_usuario(usuario_sel['id'], usuario_sel['activo'])
                        st.rerun()
            else:
                st.info("No hay usuarios para editar.")
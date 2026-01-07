import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from db.supabase_client import get_supabase
from db.repositories.labores_repo import get_todas_labores
from db.repositories.actividades_repo import get_todas_actividades

# ==============================================================================
# 🔒 SEGURIDAD DE SESIÓN
# ==============================================================================
if 'user' not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")
    st.stop()

usuario = st.session_state.user
rol = usuario.get('rol_sistema', 'LECTOR')
nombre_usr = usuario.get('nombre_completo', 'Usuario')

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(page_title="Consultas", page_icon="📊", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    
    [data-testid="stSidebarNav"] { display: none !important; }

    .metric-card {
        background-color: #F8F9F9; border: 1px solid #D5D8DC;
        border-radius: 8px; padding: 15px; text-align: center;
    }
    .metric-val { font-size: 1.5rem; font-weight: bold; color: #154360; }
    
    .detail-box {
        background-color: #EBF5FB; border-left: 5px solid #2980B9;
        padding: 20px; border-radius: 4px; margin: 20px 0;
    }
    
    [data-theme="dark"] .metric-card { background-color: #262730; border-color: #404040; }
    [data-theme="dark"] .metric-val { color: #AED6F1; }
    [data-theme="dark"] .detail-box { background-color: #1A202C; border-left-color: #5DADE2; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2592/2592312.png", width=50)
    st.markdown("### LITHOS V3")
    st.caption(f"👤 {nombre_usr}")
    st.markdown("---")
    
    st.page_link("app.py", label="Inicio", icon="🏠")
    if rol in ['ADMIN', 'OPERATIVO']:
        st.page_link("pages/1_registro.py", label="Registrar Evento", icon="➕")
    st.page_link("pages/2_consultas.py", label="Consultas", icon="📊")
    st.page_link("pages/3_indicadores.py", label="Indicadores", icon="📈")
    if rol == 'ADMIN':
        st.markdown("---")
        st.page_link("pages/4_configuracion.py", label="Configuración", icon="⚙️")
        
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.user = None
        st.switch_page("app.py")

# ==============================================================================
# LÓGICA PRINCIPAL
# ==============================================================================
st.title("📊 Explorador Operativo")
st.markdown("Consulta de partes diarios, historial y análisis de detalle.")

# 1. FILTROS
with st.expander("🔎 Filtros de Búsqueda", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        f_inicio = st.date_input("Desde", date.today() - timedelta(days=7))
    with col2:
        f_fin = st.date_input("Hasta", date.today())
    
    # Carga de catálogos
    labores_db = get_todas_labores()
    actividades_db = get_todas_actividades()
    
    list_labores = [l['nombre'] for l in labores_db] if labores_db else []
    list_acts = [a['nombre'] for a in actividades_db] if actividades_db else []
    
    with col3:
        filtro_labor = st.multiselect("Labor / Frente", list_labores)
    with col4:
        filtro_act = st.multiselect("Actividad", list_acts)

    st.write("")
    if st.button("🔍 Buscar Registros", use_container_width=True, type="primary"):
        st.session_state.exec_search = True

# 2. EJECUCIÓN
client = get_supabase()

try:
    # Consulta a tablas reales
    query = client.table("eventos_operativos").select(
        """
        *,
        labores(nombre, zona_nivel),
        actividades_catalogo(nombre, unidad_produccion)
        """
    ).gte("fecha", f_inicio).lte("fecha", f_fin).order("fecha", desc=True)
    
    response = query.execute()
    data = response.data
    
    if data:
        # Aplanar datos
        clean_data = []
        for d in data:
            lab_obj = d.get('labores') or {}
            act_obj = d.get('actividades_catalogo') or d.get('actividades') or {}

            nom_labor = lab_obj.get('nombre', '---')
            zona_labor = lab_obj.get('zona_nivel', '')
            nom_act = act_obj.get('nombre', '---')
            
            if filtro_labor and nom_labor not in filtro_labor: continue
            if filtro_act and nom_act not in filtro_act: continue
            
            clean_data.append({
                "ID": d.get('id'),
                "Fecha": d.get('fecha'),
                "Guardia": d.get('guardia'),
                "Labor": nom_labor,
                "Zona": zona_labor,
                "Actividad": nom_act,
                "Estado": d.get('estado_operativo', 'Normal'),
                "Motivo": d.get('motivo_parada') or '-',
                "Responsable": d.get('responsable_registro', '---'),
                "Observaciones": d.get('observaciones', '')
            })
            
        df = pd.DataFrame(clean_data)
        
        if not df.empty:
            st.divider()

            # ==================================================================
            # 🕹️ SELECTOR DE DETALLE (LA OPCIÓN QUE FALTABA)
            # ==================================================================
            # Obtenemos las labores únicas encontradas en la búsqueda
            labores_encontradas = sorted(df['Labor'].unique().tolist())
            
            # Selector manual para activar el detalle
            col_sel_det, col_vacia = st.columns([1, 2])
            with col_sel_det:
                opcion_labor = st.selectbox(
                    "🔬 Inspeccionar Labor Específica:", 
                    ["(Vista General)"] + labores_encontradas
                )

            # ==================================================================
            # 🔍 VISTA DETALLADA (Si se selecciona una labor)
            # ==================================================================
            if opcion_labor != "(Vista General)":
                st.markdown(f"<div class='detail-box'><h3>📍 Detalle: {opcion_labor}</h3></div>", unsafe_allow_html=True)
                
                # Filtrar DF solo para esta labor
                df_detail = df[df['Labor'] == opcion_labor]
                
                # KPIs Específicos
                c_k1, c_k2, c_k3, c_k4 = st.columns(4)
                c_k1.metric("Eventos Registrados", len(df_detail))
                c_k2.metric("Última Actividad", df_detail.iloc[0]['Actividad'] if not df_detail.empty else "-")
                
                top_estado = df_detail['Estado'].mode()[0] if not df_detail.empty else "N/A"
                c_k3.metric("Condición Frecuente", top_estado)
                
                top_guardia = df_detail['Guardia'].mode()[0] if not df_detail.empty else "-"
                c_k4.metric("Guardia Dominante", top_guardia)
                
                # Gráfico de Línea de Tiempo
                st.subheader("📅 Cronología de Eventos")
                if not df_detail.empty:
                    fig_timeline = px.scatter(
                        df_detail, 
                        x="Fecha", 
                        y="Actividad", 
                        color="Estado", 
                        symbol="Guardia", 
                        hover_data=["Responsable", "Observaciones"],
                        title=f"Línea de tiempo - {opcion_labor}",
                        height=350
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
                
                st.markdown("---")

            # ==================================================================
            # 📋 VISTA GENERAL (Siempre visible abajo)
            # ==================================================================
            st.subheader("📋 Listado de Registros")
            
            tab_list, tab_viz = st.tabs(["Base de Datos", "Gráficos Globales"])
            
            with tab_list:
                st.dataframe(
                    df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "ID": st.column_config.NumberColumn("Ref", width="small"),
                        "Estado": st.column_config.TextColumn("Condición", width="medium"),
                    }
                )
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Reporte CSV", csv, f"Reporte_{f_inicio}.csv", "text/csv")

            with tab_viz:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Eventos por Labor**")
                    st.bar_chart(df['Labor'].value_counts())
                with c2:
                    st.markdown("**Eventos por Actividad**")
                    st.bar_chart(df['Actividad'].value_counts(), color="#2E86C1")

        else:
            st.info("No se encontraron registros.")
            
    else:
        st.info("No hay datos en este rango.")

except Exception as e:
    st.error(f"Error de conexión: {e}")
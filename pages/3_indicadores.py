import streamlit as st
import pandas as pd
import altair as alt # Para gráficos más bonitos si se requiere, o usamos los nativos
from datetime import date, timedelta
from io import BytesIO
from datetime import datetime # <--- Agrega esto si no lo tienes


# --- IMPORTACIONES DE LIBRERÍAS EXTERNAS (MANEJO DE ERRORES) ---
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

# --- CAPA DE DATOS ---
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

st.set_page_config(page_title="Tablero de Control", page_icon="🧠", layout="wide")

# ==============================================================================
# 🧠 MOTOR DE ANALÍTICA (Lógica Local para no depender de archivos externos)
# ==============================================================================
class AnalyticsEngine:
    @staticmethod
    def fetch_data(fecha_ini, fecha_fin, labor_id=None, guardia=None, actividades_list=None):
        client = get_supabase()
        
        # 1. Consulta Base: Eventos Operativos
        query = client.table("eventos_operativos").select("*").gte("fecha", fecha_ini).lte("fecha", fecha_fin)
        
        if labor_id:
            query = query.eq("labor_id", labor_id)
        if guardia and guardia != "Todas":
            query = query.eq("guardia", guardia)
            
        res_ev = query.execute()
        df_ev = pd.DataFrame(res_ev.data)
        
        if df_ev.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Filtrado por actividad en memoria (porque es texto en la lista)
        # Nota: Idealmente se filtra por ID, pero aquí usaremos el ID que obtuvimos previamente
        # Si actividades_list tiene nombres, necesitamos IDs. Por simplicidad, asumimos filtrado posterior o ignoramos si es complejo.
        
        ids_eventos = df_ev['id'].tolist()
        
        # 2. Producción Física (Resultados)
        res_prod = client.table("resultados_fisicos").select("*").in_("evento_id", ids_eventos).execute()
        df_prod = pd.DataFrame(res_prod.data)
        
        # 3. Consumo de Recursos (Costos)
        res_cons = client.table("consumo_recursos").select("*, recursos_catalogo(nombre, tipo)").in_("evento_id", ids_eventos).execute()
        
        # Aplanar datos de consumo
        cons_data = []
        for c in res_cons.data:
            rec = c.get('recursos_catalogo') or {}
            cons_data.append({
                "evento_id": c['evento_id'],
                "recurso": rec.get('nombre', 'Desc'),
                "tipo_recurso": rec.get('tipo', 'Otros'),
                "cantidad": c['cantidad'],
                "precio": c['precio_snapshot'],
                "costo_total": float(c['cantidad']) * float(c['precio_snapshot'])
            })
        df_cons = pd.DataFrame(cons_data)
        
        return df_ev, df_prod, df_cons

    @staticmethod
    def calcular_kpis(df_ev, df_prod, df_cons):
        kpis = {
            "prod_ton": 0, "prod_mts": 0, "prod_tal": 0,
            "costo_total": 0, "costo_ton": 0, "costo_m": 0,
            "efi_ton_turno": 0, "efi_mts_turno": 0
        }
        
        if not df_prod.empty:
            # Sumar según tipo de dato
            kpis["prod_ton"] = df_prod[df_prod['tipo_dato'] == 'TONELAJE']['cantidad_lograda'].sum()
            kpis["prod_mts"] = df_prod[df_prod['tipo_dato'] == 'AVANCE_M']['cantidad_lograda'].sum()
            kpis["prod_tal"] = df_prod[df_prod['tipo_dato'] == 'TALADROS']['cantidad_lograda'].sum()
            
        if not df_cons.empty:
            kpis["costo_total"] = df_cons['costo_total'].sum()
            
        # Ratios
        if kpis["prod_ton"] > 0:
            kpis["costo_ton"] = kpis["costo_total"] / kpis["prod_ton"]
        
        if kpis["prod_mts"] > 0:
            kpis["costo_m"] = kpis["costo_total"] / kpis["prod_mts"]
            
        # Eficiencia (Promedios por evento)
        total_eventos = len(df_ev)
        if total_eventos > 0:
            kpis["efi_ton_turno"] = kpis["prod_ton"] / total_eventos
            kpis["efi_mts_turno"] = kpis["prod_mts"] / total_eventos
            
        return kpis

    @staticmethod
    def preparar_series_tiempo(df_ev, df_prod):
        if df_ev.empty or df_prod.empty: return pd.DataFrame()
        
        # Unir eventos con producción
        df_merged = pd.merge(df_ev, df_prod, left_on='id', right_on='evento_id')
        
        # Convertir fecha
        df_merged['fecha'] = pd.to_datetime(df_merged['fecha'])
        
        # Pivotar: Fecha vs Tipo Dato
        df_pivot = df_merged.pivot_table(index='fecha', columns='tipo_dato', values='cantidad_lograda', aggfunc='sum').fillna(0)
        return df_pivot

# ==============================================================================
# CSS & ESTILOS
# ==============================================================================
st.markdown("""
    <style>
    /* Ocultar menú automático */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* Estilo de Tarjetas KPI */
    div[data-testid="stMetric"] {
        background-color: #FDFEFE;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        text-align: center;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem;
        color: #6B7280;
        text-transform: uppercase;
        font-weight: 700;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        color: #154360;
        font-weight: 800;
    }
    
    /* Títulos de Sección */
    .kpi-row-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2C3E50;
        margin-top: 25px;
        margin-bottom: 15px;
        border-bottom: 2px solid #EAECEE;
        padding-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2592/2592312.png", width=50)
    st.caption("Sistema LITHOS V3")
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
    
    st.markdown("**📊 Vistas del Tablero**")
    vista = st.radio("Seleccione análisis:", 
        ["3.1 Tablero Principal", "3.2 Análisis Temporal", "3.3 Costos Operativos", "3.4 Reportes"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.user = None
        st.switch_page("app.py")

# ==============================================================================
# ENCABEZADO Y FILTROS
# ==============================================================================
st.title("🧠 Inteligencia Operativa")

with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns([2, 1, 2, 2, 1])
    
    f_ini = c1.date_input("Desde", date.today() - timedelta(days=30))
    f_fin = date.today() # Siempre hasta hoy por defecto
    
    f_guardia = c2.selectbox("Guardia", ["Todas", "Día", "Noche"])
    
    # Cargar catálogos
    labs_db = get_todas_labores()
    dict_labs = {l['nombre']: l['id'] for l in labs_db} if labs_db else {}
    
    f_labor_nom = c3.selectbox("Labor", ["Todas"] + list(dict_labs.keys()))
    f_labor_id = dict_labs.get(f_labor_nom) if f_labor_nom != "Todas" else None
    
    c4.info(f"📅 Periodo: {f_ini} al {f_fin}")

    c5.write("") 
    if c5.button("🔄 Actualizar", type="primary", use_container_width=True):
        st.rerun()

# ==============================================================================
# PROCESAMIENTO DE DATOS
# ==============================================================================
df_ev, df_prod, df_cons = AnalyticsEngine.fetch_data(f_ini, f_fin, f_labor_id, f_guardia)
kpis = AnalyticsEngine.calcular_kpis(df_ev, df_prod, df_cons)

if df_ev.empty:
    st.warning("⚠️ No hay datos registrados en este periodo con los filtros seleccionados.")
    st.stop()

# ==============================================================================
# VISTA 3.1 — TABLERO PRINCIPAL
# ==============================================================================
if vista == "3.1 Tablero Principal":
    
    st.markdown('<div class="kpi-row-title">📦 Producción Física</div>', unsafe_allow_html=True)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tonelaje Total", f"{kpis['prod_ton']:,.0f} ton")
    k2.metric("Avance Total", f"{kpis['prod_mts']:,.1f} m")
    k3.metric("Taladros Perf.", f"{kpis['prod_tal']:,.0f}")
    k4.metric("Total Eventos", f"{len(df_ev)}")
    
    st.markdown('<div class="kpi-row-title">🚀 Eficiencia & Costos Unitarios</div>', unsafe_allow_html=True)
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Ton / Turno", f"{kpis['efi_ton_turno']:.1f}")
    e2.metric("Mts / Turno", f"{kpis['efi_mts_turno']:.2f}")
    e3.metric("Costo / Ton", f"S/. {kpis['costo_ton']:.2f}")
    e4.metric("Costo / Metro", f"S/. {kpis['costo_m']:.2f}")
    
    st.markdown("---")
    st.markdown("#### 📉 Tendencia de Producción")
    
    df_chart = AnalyticsEngine.preparar_series_tiempo(df_ev, df_prod)
    
    if not df_chart.empty:
        g1, g2 = st.columns(2)
        with g1:
            st.caption("Evolución de Tonelaje")
            if 'TONELAJE' in df_chart.columns:
                st.area_chart(df_chart[['TONELAJE']], color="#154360", height=250)
            else: st.info("Sin datos de Tonelaje")
        with g2:
            st.caption("Evolución de Avance (Metros)")
            if 'AVANCE_M' in df_chart.columns:
                st.bar_chart(df_chart[['AVANCE_M']], color="#27AE60", height=250)
            else: st.info("Sin datos de Avance")
    else:
        st.caption("No hay datos suficientes para graficar.")

# ==============================================================================
# VISTA 3.2 — ANÁLISIS TEMPORAL
# ==============================================================================
elif vista == "3.2 Análisis Temporal":
    st.subheader("📅 Evolución Detallada")
    
    df_time = AnalyticsEngine.preparar_series_tiempo(df_ev, df_prod)
    
    if not df_time.empty:
        st.markdown("##### 📦 Histórico de Producción")
        st.line_chart(df_time, height=400)
        
        with st.expander("Ver Tabla de Datos"):
            st.dataframe(df_time, use_container_width=True)
    else:
        st.warning("No hay datos para generar series temporales.")

# ==============================================================================
# VISTA 3.3 — COSTOS OPERATIVOS
# ==============================================================================
elif vista == "3.3 Costos Operativos":
    st.subheader("💰 Control de Costos")
    
    if df_cons.empty:
        st.info("No hay registro de consumo de materiales en este periodo.")
    else:
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.metric("Gasto Total", f"S/. {kpis['costo_total']:,.2f}")
            st.metric("Ratio $/Ton", f"S/. {kpis['costo_ton']:.2f}")
            
        with c2:
            st.markdown("**Distribución por Tipo de Recurso**")
            # Agrupar por tipo (Explosivo, Acero, etc)
            df_tipo = df_cons.groupby('tipo_recurso')['costo_total'].sum()
            st.bar_chart(df_tipo, color="#7D3C98", horizontal=True)

        st.divider()
        st.markdown("**Detalle de Consumos Top 10 (S/.)**")
        df_top = df_cons.groupby('recurso')['costo_total'].sum().sort_values(ascending=False).head(10)
        st.bar_chart(df_top, color="#154360")

# ==============================================================================
# VISTA 3.4 — REPORTES
# ==============================================================================
elif vista == "3.4 Reportes":
    st.subheader("📤 Exportación Ejecutiva")
    
    if FPDF is None:
        st.warning("⚠️ La librería 'fpdf' no está instalada. Solo Excel y TXT disponibles. (pip install fpdf)")

    with st.container(border=True):
        st.info("Genera documentos oficiales basados en los filtros actuales.")
        
        comentarios = st.text_area("Notas del Ingeniero:", placeholder="Ej: Producción afectada por mantenimiento en scoop...")

        # Datos para Excel
        data_resumen = {
            "Indicador": ["Producción (Ton)", "Avance (m)", "Taladros", "Costo Total (S/.)", "Costo/Ton"],
            "Valor": [kpis['prod_ton'], kpis['prod_mts'], kpis['prod_tal'], kpis['costo_total'], kpis['costo_ton']]
        }
        df_export = pd.DataFrame(data_resumen)

        # --- GENERADORES ---
        def generar_excel():
            output = BytesIO()
            # Usamos xlsxwriter como motor para dar formato
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                
                # --- A. DEFINICIÓN DE FORMATOS ---
                workbook = writer.book
                
                # Estilos visuales
                fmt_titulo = workbook.add_format({'bold': True, 'font_size': 14, 'font_color': '#154360', 'align': 'left'})
                fmt_meta   = workbook.add_format({'font_size': 9, 'font_color': '#566573', 'italic': True})
                fmt_header = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#154360', 'font_color': '#FFFFFF', 'border': 1, 'align': 'center'})
                fmt_cell   = workbook.add_format({'border': 1, 'align': 'left'})
                fmt_num    = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'align': 'right'})

                # --- B. HOJA 1: RESUMEN EJECUTIVO ---
                sheet_name = 'Resumen Ejecutivo'
                # Escribimos el DataFrame saltando las primeras 6 filas para poner el encabezado
                df_export.to_excel(writer, sheet_name=sheet_name, startrow=6, index=False)
                
                worksheet = writer.sheets[sheet_name]
                
                # 1. Encabezado del Reporte (Quién y Cuándo)
                worksheet.write('A1', "REPORTE OPERATIVO: LITHOS V3", fmt_titulo)
                worksheet.write('A2', f"Generado por: {nombre_usr} ({rol})", fmt_meta)
                worksheet.write('A3', f"Fecha de Emisión: {datetime.now().strftime('%d/%m/%Y %H:%M')}", fmt_meta)
                worksheet.write('A4', f"Filtros: {f_ini} al {f_fin} | Labor: {f_labor_nom}", fmt_meta)

                # 2. Formato a la Tabla (Headers y Celdas)
                # Aplicar estilo al Encabezado de la tabla (Fila 6)
                for col_num, value in enumerate(df_export.columns.values):
                    worksheet.write(6, col_num, value, fmt_header)
                
                # Aplicar bordes y formato numérico a los datos
                for row_num, row_data in enumerate(df_export.values):
                    for col_num, cell_data in enumerate(row_data):
                        # Si es número, formato moneda/decimal
                        if isinstance(cell_data, (float, int)):
                            worksheet.write(row_num + 7, col_num, cell_data, fmt_num)
                        else:
                            worksheet.write(row_num + 7, col_num, cell_data, fmt_cell)

                # 3. AUTO-AJUSTE DE COLUMNAS (Para que se vea bien)
                worksheet.set_column('A:A', 30) # Columna Indicador ancha
                worksheet.set_column('B:B', 20) # Columna Valor

                # --- C. HOJA 2: DETALLE DE EVENTOS (SI HAY DATOS) ---
                if not df_ev.empty:
                    sheet_ev = 'Detalle Eventos'
                    df_clean = df_ev.drop(columns=['created_at', 'foto_url'], errors='ignore')
                    df_clean.to_excel(writer, sheet_name=sheet_ev, startrow=1, index=False)
                    ws_ev = writer.sheets[sheet_ev]
                    
                    # Formato Header
                    for col_num, value in enumerate(df_clean.columns.values):
                        ws_ev.write(1, col_num, value, fmt_header)
                        ws_ev.set_column(col_num, col_num, 15) # Ancho estándar
                    
                    ws_ev.write('A1', "LOG DE EVENTOS OPERATIVOS - DETALLE", fmt_titulo)

            return output.getvalue()

        def generar_pdf():
            if FPDF is None: return b""
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "REPORTE LITHOS V3", 0, 1, 'C')
            pdf.set_font("Arial", size=10)
            pdf.cell(0, 10, f"Periodo: {f_ini} al {f_fin} | Labor: {f_labor_nom}", 0, 1, 'C')
            pdf.line(10, 30, 200, 30)
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "1. RESUMEN DE INDICADORES", 0, 1)
            pdf.set_font("Arial", size=11)
            
            for index, row in df_export.iterrows():
                pdf.cell(100, 8, str(row['Indicador']), 1)
                pdf.cell(40, 8, f"{row['Valor']:,.2f}", 1, 1, 'R')
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "2. OBSERVACIONES", 0, 1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 6, comentarios if comentarios else "Sin observaciones adicionales.")
            
            return pdf.output(dest='S').encode('latin-1')

        # --- BOTONES ---
        c1, c2, c3 = st.columns(3)
        nombre_file = f"Reporte_{f_ini}_{f_fin}"
        
        with c1:
            if FPDF:
                pdf_data = generar_pdf()
                st.download_button("📄 PDF", pdf_data, f"{nombre_file}.pdf", "application/pdf", use_container_width=True)
        
        with c2:
            try:
                xls_data = generar_excel()
                st.download_button("📊 Excel", xls_data, f"{nombre_file}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except Exception as e:
                st.error("Error Excel")

        with c3:
            txt_data = f"REPORTE LITHOS\nFecha: {date.today()}\n\n{df_export.to_string(index=False)}\n\nNOTAS:\n{comentarios}"
            st.download_button("📝 TXT", txt_data, f"{nombre_file}.txt", "text/plain", use_container_width=True)
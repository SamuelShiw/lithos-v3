import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date

# Repositorios y Servicios
from db.repositories.labores_repo import get_labores_activas
from db.repositories.actividades_repo import get_actividades_activas
from db.repositories.recursos_repo import get_recursos_activos
from services.registro_eventos import registrar_nuevo_evento

# ==============================================================================
# [NUEVO] 🧠 CEREBRO DE INGENIERÍA (SIMULACIÓN DE ESTÁNDARES)
# ==============================================================================
# Esto simula la tabla de estándares que el Ingeniero pidió.
# Relaciona el Nombre de la Labor con su Geometría y Geología.
ESTANDARES_MINA = {
    # Nombre Labor (Parcial): {Seccion (m2), Densidad, Roca, Malla Teórica, Factor Carga kg/tal}
    "CX": {"seccion": 12.0, "densidad": 2.8, "roca": "III-B (Regular)", "taladros_std": 45, "fc": 0.8},
    "RP": {"seccion": 16.0, "densidad": 2.7, "roca": "II-A (Buena)",    "taladros_std": 52, "fc": 0.9},
    "TJ": {"seccion": 4.0,  "densidad": 3.2, "roca": "IV (Mala)",       "taladros_std": 28, "fc": 0.6},
    "GL": {"seccion": 9.0,  "densidad": 2.8, "roca": "III-A",           "taladros_std": 38, "fc": 0.75},
}

def get_parametros_labor(nombre_labor):
    """Busca los parámetros técnicos según el nombre de la labor."""
    for key, params in ESTANDARES_MINA.items():
        if key in nombre_labor:
            return params
    # Valor por defecto (Promedio) si no encuentra coincidencia
    return {"seccion": 10.0, "densidad": 2.8, "roca": "Estándar", "taladros_std": 40, "fc": 0.8}

# ==============================================================================
# 🔒 1. SEGURIDAD DE SESIÓN
# ==============================================================================
if 'user' not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")
    st.stop()

usuario_actual = st.session_state.user
rol_actual = usuario_actual.get('rol_sistema', 'LECTOR')
nombre_usuario = usuario_actual.get('nombre_completo', 'Usuario')

if rol_actual not in ["ADMIN", "OPERATIVO"]:
    st.error(f"⛔ ACCESO DENEGADO")
    st.markdown(f"Su perfil **{rol_actual}** no tiene permisos para registrar partes diarios.")
    if st.button("Volver al Dashboard"):
        st.switch_page("app.py")
    st.stop()

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Registro Operativo", 
    page_icon="📝", 
    layout="centered",
    initial_sidebar_state="expanded"
)

# CSS MINIMALISTA (SIN RUIDO VISUAL)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }
    
    /* Ocultar navegación automática */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Contenedor Limpio */
    .clean-block {
        padding: 20px 5px; 
        margin-bottom: 10px;
    }
    
    /* Títulos */
    .clean-title {
        font-size: 1.1rem; 
        font-weight: 600; 
        color: #154360; 
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Firmas */
    .signature-box input {
        font-family: 'Inter', sans-serif; 
        font-weight: 600; 
        text-align: center;
        background-color: #F8F9F9 !important; 
        color: #566573 !important; 
        border: 1px solid #EAECEE !important;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    
    /* Botón Principal */
    div.stButton > button {
        width: 100%; 
        height: 55px; 
        font-size: 1rem; 
        font-weight: 600; 
        border-radius: 8px;
        border: none; 
        background-color: #154360; 
        color: white !important; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s;
    }
    div.stButton > button:hover { 
        background-color: #1A5276; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    
    /* Ajuste de inputs */
    .stSelectbox, .stTextInput, .stNumberInput, .stDateInput {
        margin-bottom: 10px;
    }
    
    /* [NUEVO] Estilo para tarjeta de ingeniería */
    .engineering-card {
        background-color: #EBF5FB;
        border-left: 5px solid #2980B9;
        padding: 15px;
        border-radius: 4px;
        font-size: 0.9rem;
        color: #154360;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# SIDEBAR DINÁMICO
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2592/2592312.png", width=50)
    st.markdown("### LITHOS V3")
    
    st.caption(f"👤 {nombre_usuario}")
    st.caption(f"🔑 {rol_actual}")
    st.markdown("---")
    
    st.page_link("app.py", label="Inicio", icon="🏠")
    st.page_link("pages/1_registro.py", label="Registrar Evento", icon="➕")
    st.page_link("pages/2_consultas.py", label="Consultas", icon="📊")
    st.page_link("pages/3_indicadores.py", label="Indicadores", icon="📈")
    
    if rol_actual == 'ADMIN':
        st.markdown("---")
        st.page_link("pages/4_configuracion.py", label="Configuración", icon="⚙️")
    
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.user = None
        st.switch_page("app.py")

# ==============================================================================
# LÓGICA PRINCIPAL DEL REPORTE
# ==============================================================================
st.title("📝 Parte Diario")
st.markdown("Complete los datos operativos del turno.")
st.write("") 

# --- CARGA DE DATOS ---
try:
    labores = get_labores_activas()
    recursos = get_recursos_activos()
    
    rec_explo = [r for r in recursos if r['tipo'] == 'EXPLOSIVO']
    rec_sost = [r for r in recursos if r['tipo'] == 'SOSTENIMIENTO']
    rec_acero = [r for r in recursos if r['tipo'] == 'ACERO']
    rec_otros = [r for r in recursos if r not in rec_explo + rec_sost + rec_acero]
    
except Exception as e:
    st.error(f"⚠️ Error cargando datos maestros: {e}")
    st.stop()

hora = datetime.now().hour
idx_turno = 1 if (hora >= 18 or hora < 6) else 0

# BLOQUE 1: CONTEXTO
st.markdown('<div class="clean-block">', unsafe_allow_html=True)
st.markdown('<div class="clean-title">📍 Contexto & Ubicación</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
fecha = c1.date_input("Fecha", date.today())
turno = c2.selectbox("Guardia", ["Día", "Noche"], index=idx_turno)

if not labores:
    st.warning("⚠️ No hay labores activas.")
    st.stop()

map_labores = {f"{l['nombre']} ({l.get('zona_nivel', '---')})": l for l in labores}
sel_labor = st.selectbox("Labor / Frente", list(map_labores.keys()))
labor_actual = map_labores[sel_labor]

# [NUEVO] OBTENER PARÁMETROS DE INGENIERÍA PARA LA LABOR SELECCIONADA
params_ing = get_parametros_labor(labor_actual['nombre'])

# Actividades (Sin filtro estricto)
actividades_geo = get_actividades_activas(filtro_geo_id=None) 
map_acts = {a['nombre']: a for a in actividades_geo} 

if not map_acts:
    st.warning("⚠️ Sin actividades configuradas.")
    sel_acts = []
else:
    sel_acts = st.multiselect("Actividades Realizadas", list(map_acts.keys()), placeholder="Seleccione actividades...")

st.write("") 
c_cond, c_motivo = st.columns(2) 
detalle_parada = "" 

with c_cond:
    estado_op = st.selectbox("Estado Operativo", ["Normal", "Restringido", "Parada Total"])

with c_motivo:
    if estado_op != "Normal":
        # Guardamos lo que el usuario escribe en la variable detalle_parada
        detalle_parada = st.text_input("Motivo de Parada", placeholder="Describa la causa...")

st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# BLOQUE 2: REPORTE FÍSICO
st.markdown('<div class="clean-block">', unsafe_allow_html=True)
st.markdown('<div class="clean-title">📊 Producción Física</div>', unsafe_allow_html=True)

col_fis1, col_fis2, col_fis3 = st.columns(3)
with col_fis1: r_ton = st.number_input("Tonelaje (ton)", min_value=0, step=1, format="%d")
with col_fis2: r_mts = st.number_input("Avance (m)", min_value=0.0, step=0.1, format="%.1f")
with col_fis3:
    r_tal_prod = st.number_input("Tal. Producción", min_value=0, step=1)
    r_tal_serv = st.number_input("Tal. Servicios", min_value=0, step=1)

# [NUEVO] TARJETA DE CÁLCULO AUTOMÁTICO (INGENIERÍA)
# Esto responde al requerimiento: "cuando saca sección debe salir automatico el tonelaje"
if r_mts > 0:
    vol_teorico = r_mts * params_ing['seccion']
    ton_teorica = vol_teorico * params_ing['densidad']
    explo_teorico = params_ing['taladros_std'] * params_ing['fc']
    
    st.markdown(f"""
    <div class="engineering-card">
        <strong>🤖 CÁLCULO AUTOMÁTICO (MODELADO)</strong><br>
        Según estándar <em>{params_ing['roca']}</em> (Sección {params_ing['seccion']} m²):<br>
        <ul>
            <li><strong>Volumen Quebrado:</strong> {vol_teorico:.2f} m³</li>
            <li><strong>Tonelaje Esperado:</strong> {ton_teorica:.1f} TM (vs Real: {r_ton})</li>
            <li><strong>Explosivo Teórico:</strong> {explo_teorico:.1f} kg (Malla: {params_ing['taladros_std']} tal)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# BLOQUE 3: CONSUMOS
st.markdown('<div class="clean-block">', unsafe_allow_html=True)
st.markdown('<div class="clean-title">📦 Consumo de Materiales</div>', unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["🧨 Explosivos", "🌲 Sostenimiento", "🔩 Aceros", "📦 Varios"])
consumos_finales = []

def render_inputs(lista, suffix):
    sel = []
    if not lista: return []
    cols = st.columns(2)
    for idx, r in enumerate(lista):
        with cols[idx % 2]:
            label = f"{r['nombre']} ({r.get('unidad_medida', 'u')})"
            val = st.number_input(label, min_value=0, step=1, format="%d", key=f"c_{r['id']}_{suffix}")
            if val > 0:
                costo = r.get('costo_unitario', 0.0)
                sel.append({"id": r['id'], "cantidad": int(val), "precio": float(costo)})
    return sel

with t1: consumos_finales.extend(render_inputs(rec_explo, "exp"))
with t2: consumos_finales.extend(render_inputs(rec_sost, "sos"))

# [NUEVO] LÓGICA DE ACEROS (PIES PERFORADOS)
# Esto responde al requerimiento: "cuantos pies has perforado debe estar relacionado con los aceros"
with t3: 
    st.caption("🔧 Análisis de Vida Útil de Aceros")
    c_ac1, c_ac2 = st.columns(2)
    longitud_pies = c_ac1.selectbox("Longitud de Barreno (Pies)", [4, 5, 6, 8, 10], index=2)
    
    if r_tal_prod > 0:
        total_pies = r_tal_prod * longitud_pies
        c_ac2.metric("Total Pies Perforados", f"{total_pies} pies")
        st.info("Ingrese abajo la cantidad de aceros que se rompieron o descartaron hoy para calcular el rendimiento.")
    
    # Renderizamos los inputs normales de aceros
    consumos_aceros_registrados = render_inputs(rec_acero, "ace")
    consumos_finales.extend(consumos_aceros_registrados)

with t4: consumos_finales.extend(render_inputs(rec_otros, "otr"))
st.markdown('</div>', unsafe_allow_html=True)
st.divider()

# BLOQUE 4: CIERRE
st.markdown('<div class="clean-block">', unsafe_allow_html=True)
st.markdown('<div class="clean-title">🛡️ Cierre & Seguridad</div>', unsafe_allow_html=True)

with st.expander("Verificar Condiciones de Seguridad (Checklist)", expanded=True):
    chk1, chk2 = st.columns(2)
    s_vent = chk1.checkbox("Ventilación Adecuada", value=True)
    s_epp = chk2.checkbox("Orden y Limpieza", value=True)
    s_des = chk1.checkbox("Desatado de Rocas", value=True)
    s_alm = chk2.checkbox("Almacenamiento Seguro", value=True)
    str_seguridad = f"Vent:{s_vent}, EPP:{s_epp}, Desat:{s_des}, Alm:{s_alm}"

st.write("")
obs_txt = st.text_area("Observaciones Generales", height=80, placeholder="Incidencias, novedades o pendientes...")

st.write("")
c_decl, c_sign = st.columns([2, 1])
firma_nombre = nombre_usuario
firma_hash = str(uuid.uuid4()).split('-')[0].upper()

with c_decl:
    st.caption("Responsable del Registro")
    st.markdown(f'<div class="signature-box"><input type="text" value="{firma_nombre}" disabled style="width:100%; padding:10px;"></div>', unsafe_allow_html=True)

with c_sign:
    st.caption("Hash de Firma")
    st.markdown(f'<div class="signature-box"><input type="text" value="KEY-{firma_hash}" disabled style="width:100%; padding:10px;"></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.write("")

# BOTÓN DE GUARDADO
if st.button("💾 REGISTRAR PARTE DIARIO", use_container_width=True):
    # Validaciones
    if not sel_acts: st.error("⚠️ Debe seleccionar al menos una actividad."); st.stop()
    if estado_op != "Normal" and not detalle_parada.strip(): st.error("⚠️ Indique motivo de la parada."); st.stop()
    
    # Lógica Principal
    objs_seleccionados = [map_acts[name] for name in sel_acts]
    objs_seleccionados.sort(key=lambda x: 0 if "Perforación" in x['nombre'] else (1 if "Limpieza" in x['nombre'] else 2))
    actividad_principal = objs_seleccionados[0]
    
    # Construcción de Observación Final
    prefijo_estado = f"[{estado_op.upper()}: {detalle_parada}] " if estado_op != "Normal" else ""
    obs_final = f"{prefijo_estado}ACT: {', '.join(sel_acts)}. {obs_txt}. SEG: {str_seguridad}"
    
    # Lista de Resultados
    res_list = []
    if r_ton > 0: res_list.append({"tipo": "TONELAJE", "cantidad": float(r_ton)})
    if r_mts > 0: res_list.append({"tipo": "AVANCE_M", "cantidad": r_mts})
    if r_tal_prod > 0: res_list.append({"tipo": "TALADROS", "cantidad": float(r_tal_prod)})
    if r_tal_serv > 0: res_list.append({"tipo": "TALADROS_SERV", "cantidad": float(r_tal_serv)})
    
    # GUARDADO EN BD
    exito, msg = registrar_nuevo_evento(
        fecha=fecha, guardia=turno, 
        labor_id=labor_actual['id'], 
        actividad_id=actividad_principal['id'], 
        responsable=firma_nombre,
        obs=obs_final,
        estado_op=estado_op, 
        tiempo_imp=0, 
        motivo=detalle_parada,  
        lista_consumos_ui=consumos_finales,
        lista_resultados_ui=res_list
    )
    
    if exito: 
        st.success("✅ Guardado Exitosamente")
        st.balloons()
    else: 
        st.error(f"❌ Error al guardar: {msg}")
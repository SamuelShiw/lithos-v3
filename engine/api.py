# engine/api.py
from fastapi import FastAPI
from pydantic import BaseModel
# --- AQUÍ ESTÁ EL CAMBIO IMPORTANTE (USAR PUNTOS RELATIVOS) ---
from .formulas import calcular_holmberg_simplificado
from .modelo_ia import CerebroMinero

app = FastAPI(title="Motor LITHOS AI")
cerebro = CerebroMinero()

class DatosFrente(BaseModel):
    ancho: float
    alto: float
    tipo_roca: str

@app.post("/calcular_malla")
def calcular(datos: DatosFrente):
    # 1. Preguntar a la Física (Holmberg)
    tal_holmberg, explicacion_fisica = calcular_holmberg_simplificado(
        datos.ancho, datos.alto, datos.tipo_roca
    )
    
    # 2. Preguntar a la IA (Experiencia)
    tal_ia = cerebro.predecir_taladros(
        datos.ancho, datos.alto, datos.tipo_roca
    )
    
    # 3. Consenso
    tal_final = tal_ia
    
    nota_ia = ""
    diferencia = tal_ia - tal_holmberg
    if diferencia > 0:
        nota_ia = f"La IA aumentó {diferencia} taladros basado en históricos."
    elif diferencia < 0:
        nota_ia = f"La IA optimizó reduciendo {abs(diferencia)} taladros."
    
    return {
        "taladros_sugeridos": tal_final,
        "holmberg_base": tal_holmberg,
        "ia_prediccion": tal_ia,
        "explicacion": f"{explicacion_fisica} \n\n🤖 Ajuste IA: {nota_ia}"
    }
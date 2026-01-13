from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

# --- VOLVEMOS A IMPORTACIÓN ABSOLUTA (AHORA SÍ FUNCIONARÁ PORQUE TIENES __INIT__.PY) ---
from engine.formulas import calcular_holmberg_simplificado
from engine.modelo_ia import CerebroMinero

app = FastAPI(title="Motor LITHOS AI")

try:
    cerebro = CerebroMinero()
except Exception as e:
    print(f"Error inicializando modelo IA: {e}")
    cerebro = None

class DatosFrente(BaseModel):
    ancho: float
    alto: float
    tipo_roca: str

@app.post("/calcular_malla")
def calcular(datos: DatosFrente) -> Dict[str, Any]:
    try:
        # Validación de entrada
        if datos.ancho <= 0 or datos.alto <= 0:
            raise HTTPException(status_code=400, detail="Ancho y alto deben ser mayores a 0")
        
        # 1. Preguntar a la Física (Holmberg)
        tal_holmberg, explicacion_fisica = calcular_holmberg_simplificado(
            datos.ancho, datos.alto, datos.tipo_roca
        )
        
        # 2. Preguntar a la IA (Experiencia)
        tal_ia = None
        if cerebro is not None:
            tal_ia = cerebro.predecir_taladros(
                datos.ancho, datos.alto, datos.tipo_roca
            )
        
        # 3. Consenso - Usar promedio si ambas estimaciones están disponibles
        if tal_ia is not None:
            tal_final = round((tal_holmberg + tal_ia) / 2)  # Promedio
            diferencia = tal_ia - tal_holmberg
            if diferencia > 0:
                nota_ia = f"La IA sugiere {diferencia} taladros más basado en históricos."
            elif diferencia < 0:
                nota_ia = f"La IA optimizó reduciendo {abs(diferencia)} taladros."
            else:
                nota_ia = "La IA y física coinciden en la estimación."
        else:
            tal_final = tal_holmberg
            nota_ia = "IA no disponible - usando solo cálculo físico."
        
        return {
            "taladros_sugeridos": tal_final,
            "holmberg_base": tal_holmberg,
            "ia_prediccion": tal_ia,
            "diferencia": tal_ia - tal_holmberg if tal_ia else None,
            "explicacion": f"{explicacion_fisica}\n\n🤖 Ajuste IA: {nota_ia}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en cálculo: {str(e)}")
# engine/formulas.py
import math

def calcular_holmberg_simplificado(ancho, alto, tipo_roca):
    """
    Aplica principios de Holmberg para estimar burden y espaciamiento.
    """
    area = ancho * alto
    perimetro = (2 * ancho) + (2 * alto)
    
    # Constantes de Roca (Factor 'c' de Holmberg simplificado)
    # Roca Dura = Requiere más perforación (factor alto)
    # Roca Suave = Requiere menos (factor bajo)
    if "Dura" in tipo_roca or "II-A" in tipo_roca:
        factor_roca = 1.1  # Roca dura (Coeficiente alto)
        burden_teorico = 0.6 # Metros
    elif "Media" in tipo_roca or "III" in tipo_roca:
        factor_roca = 1.0
        burden_teorico = 0.7
    else: # Suave
        factor_roca = 0.8
        burden_teorico = 0.85

    # Cálculo de Taladros (Estimación basada en Área y Burden)
    # Fórmula empírica: N = (Perímetro / Espaciamiento) + (Area / (B*S))
    espaciamiento = burden_teorico * 1.1 # S suele ser un poco mayor que B
    
    num_taladros = int((perimetro / espaciamiento) + (area * factor_roca / (burden_teorico * espaciamiento)))
    
    # Ajuste de seguridad (Factor Samuel: Asegurar el tiro)
    num_taladros += 2 # Taladros de alivio/seguridad
    
    explicacion = (
        f"Cálculo Físico (Holmberg): Se usó un Burden de {burden_teorico}m debido a roca '{tipo_roca}'. "
        f"Para una sección de {area}m², la geometría dicta {num_taladros} taladros."
    )
    
    return num_taladros, explicacion
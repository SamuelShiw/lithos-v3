# Módulo: rules.py
# domain/rules_pv.py
from dataclasses import dataclass

@dataclass
class ResultadoModelado:
    volumen_teorico: float
    tonelaje_teorico: float
    taladros_teoricos: int
    cartuchos_teoricos: int
    explosivo_kg_teorico: float

class ReglasPerforacion:
    """
    Reglas de negocio puras (Hard rules de la mina)
    """
    
    # Peso promedio de un cartucho de emulsión (ej: 1-1/8 x 8)
    # Ajustar este valor al real de la mina (ej: 0.18 kg o 0.25 kg)
    PESO_CARTUCHO_KG = 0.25 

    @staticmethod
    def estimar_cartuchos_por_taladro(pies_barreno: int, dureza_roca: str) -> int:
        """
        Regla empírica del ingeniero:
        4 pies -> ~4 cartuchos
        5 pies -> ~5 cartuchos
        6 pies -> ~6 cartuchos
        """
        base = pies_barreno
        
        # Factor de corrección por roca (Opcional, escalable)
        factor = 1.0
        if dureza_roca == 'Dura': factor = 1.2
        if dureza_roca == 'Suave': factor = 0.8
        
        return int(base * factor)

    @staticmethod
    def calcular_taladros_malla(area_m2: float, tipo_roca: str) -> int:
        """
        Calcula taladros necesarios según área y roca (Burden/Espaciamiento simplificado)
        Fórmula empírica: Area / Factor + Taladros de alivio
        """
        # Ejemplo simple escalable:
        # Roca Media: ~4 taladros por m2
        factor = 4.0 
        if tipo_roca == 'Baja': factor = 3.5
        
        return int(area_m2 * factor)
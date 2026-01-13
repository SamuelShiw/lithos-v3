# services/modeling_service.py
from domain.rules_pv import ReglasPerforacion, ResultadoModelado

class OperationalModelService:
    
    def __init__(self, supabase_client):
        self.db = supabase_client

    def simular_disparo(self, labor_id, avance_registrado, longitud_barreno_pies):
        """
        Recibe los inputs del capataz y devuelve lo que DEBIÓ pasar.
        """
        # 1. Obtener Estándar de la Labor (Desde DB o Cache)
        # Query simulada a la tabla estandares_labores
        std = self._get_standar_labor(labor_id) 
        
        # 2. Cálculos Geométricos
        volumen = std['area_m2'] * avance_registrado
        tonelaje = volumen * std['densidad_roca']
        
        # 3. Cálculos P&V (Usando reglas de dominio)
        # Si la tabla tiene malla fija, se usa esa. Si no, se calcula.
        taladros = std['malla_base_taladros'] 
        if not taladros:
            taladros = ReglasPerforacion.calcular_taladros_malla(std['area_m2'], std['tipo_roca'])
            
        cartuchos_por_taladro = ReglasPerforacion.estimar_cartuchos_por_taladro(
            longitud_barreno_pies, std['tipo_roca']
        )
        
        total_cartuchos = taladros * cartuchos_por_taladro
        total_kg_explosivo = total_cartuchos * ReglasPerforacion.PESO_CARTUCHO_KG
        
        return ResultadoModelado(
            volumen_teorico=round(volumen, 2),
            tonelaje_teorico=round(tonelaje, 2),
            taladros_teoricos=taladros,
            cartuchos_teoricos=total_cartuchos,
            explosivo_kg_teorico=round(total_kg_explosivo, 2)
        )

    def _get_standar_labor(self, labor_id):
        # Aquí harías la consulta real a Supabase
        # Por ahora simulamos respuesta de DB para tu demo
        return {
            "area_m2": 7.84, # 2.8 x 2.8
            "densidad_roca": 2.7,
            "tipo_roca": "Media",
            "malla_base_taladros": 38 # Estándar típico 3x3
        }
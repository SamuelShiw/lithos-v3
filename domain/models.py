# mining_ops/domain/models.py
from dataclasses import dataclass
from datetime import date
from typing import Optional, List

# --- NUEVO: Catálogo de Geometría ---
@dataclass
class TipoGeometrico:
    id: int
    nombre: str # CHIMENEA, RAMPA, GALERIA, ETC.

@dataclass
class Labor:
    id: int
    codigo: str
    nombre: str
    zona_nivel: str
    tipo_geometrico_id: int # FK Nueva
    nombre_geometrico: Optional[str] = None # Para mostrar en UI (ej. "Chimenea")

@dataclass
class Actividad:
    id: int
    nombre: str
    unidad_produccion: Optional[str]
    # --- NUEVOS CAMPOS DE COMPORTAMIENTO ---
    tipo_geometrico_id: Optional[int] # Si es None, aplica a todas (opcional)
    req_tonelaje: bool = False
    req_avance: bool = False
    req_taladros: bool = False

# ... (El resto de modelos Recurso, EventoOperativo, etc. se mantienen igual) ...
@dataclass
class Recurso:
    id: int
    nombre: str
    tipo: str
    unidad: str
    costo_actual: float

@dataclass
class ItemConsumo:
    recurso_id: int
    cantidad: float
    precio_snapshot: float

@dataclass
class ResultadoFisico:
    cantidad: float
    tipo: str

@dataclass
class EventoOperativo:
    fecha: date
    guardia: str
    labor_id: int
    actividad_id: int
    responsable_id: str
    observaciones: str
    consumos: List[ItemConsumo]
    resultados: List[ResultadoFisico]
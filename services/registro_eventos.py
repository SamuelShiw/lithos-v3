# mining_ops/services/registro_eventos.py
from domain.models import EventoOperativo, ItemConsumo, ResultadoFisico
from db.repositories.eventos_repo import guardar_evento_atomico

# mining_ops/services/registro_eventos.py
from db.repositories.eventos_repo import guardar_evento_atomico

def registrar_nuevo_evento(fecha, guardia, labor_id, actividad_id, responsable, obs, 
                           estado_op, tiempo_imp, motivo, # <--- NUEVOS ARGUMENTOS
                           lista_consumos_ui, lista_resultados_ui):
    
    # Preparamos el diccionario maestro
    data_evento = {
        "fecha": fecha.isoformat(),
        "guardia": guardia,
        "labor_id": labor_id,
        "actividad_id": actividad_id,
        "responsable_registro": responsable,
        "observaciones": obs,
        # Nuevos campos
        "estado_operativo": estado_op,
        "tiempo_improductivo": tiempo_imp,
        "motivo_parada": motivo
    }
    
    return guardar_evento_atomico(data_evento, lista_consumos_ui, lista_resultados_ui)
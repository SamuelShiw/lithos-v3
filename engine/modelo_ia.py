# engine/modelo_ia.py
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import numpy as np

class CerebroMinero:
    def __init__(self):
        self.modelo = self._entrenar_modelo_inicial()

    def _entrenar_modelo_inicial(self):
        # 1. CREAR DATOS SINTÉTICOS (SIMULANDO TU EXPERIENCIA)
        # Features: [Ancho, Alto, Dureza(1=Suave, 2=Media, 3=Dura)]
        # Target: [Taladros Reales usados en campo]
        data = {
            'ancho':  [2.5, 3.0, 3.5, 2.8, 4.0, 2.5, 3.0],
            'alto':   [2.5, 3.0, 3.5, 2.8, 4.0, 2.5, 3.0],
            'dureza': [3,   2,   1,   3,   2,   1,   3], # 3 es Dura
            'taladros': [38,  42,  40,  45,  52,  32,  48] # Tus datos históricos
        }
        df = pd.DataFrame(data)
        
        X = df[['ancho', 'alto', 'dureza']]
        y = df['taladros']
        
        # 2. ENTRENAR RANDOM FOREST
        rf = RandomForestRegressor(n_estimators=50, random_state=42)
        rf.fit(X, y)
        return rf

    def predecir_taladros(self, ancho, alto, tipo_roca):
        # Convertir texto roca a número
        dureza_val = 2 # Media por defecto
        if "Dura" in tipo_roca: dureza_val = 3
        elif "Suave" in tipo_roca: dureza_val = 1
        
        # Predecir
        prediccion = self.modelo.predict([[ancho, alto, dureza_val]])
        return int(prediccion[0])
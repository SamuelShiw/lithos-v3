# mining_ops/services/auth.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class Usuario:
    username: str
    rol: str  # 'CACHIMBO' o 'INGENIERO'

class AuthService:
    """
    Módulo 0: Control de acceso.
    No contiene lógica minera. Solo dice QUIÉN es el usuario.
    """
    
    @staticmethod
    def login(username: str) -> Optional[Usuario]:
        # TODO: Conectar a tabla 'usuarios' en Supabase en el futuro.
        # Por ahora, simulamos la lógica dura.
        
        users_db = {
            "cachimbo": Usuario("cachimbo", "CACHIMBO"),
            "admin": Usuario("admin", "INGENIERO"),
            "super": Usuario("super", "INGENIERO")
        }
        return users_db.get(username.lower())

    @staticmethod
    def puede_configurar(usuario: Usuario) -> bool:
        return usuario.rol == "INGENIERO"

    @staticmethod
    def puede_registrar(usuario: Usuario) -> bool:
        return usuario.rol in ["CACHIMBO", "INGENIERO"]
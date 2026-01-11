try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except Exception:
    bcrypt = None
    BCRYPT_AVAILABLE = False

from db.supabase_client import get_supabase
import streamlit as st


# import bcrypt  # Comentado para la demo, usaremos texto plano por ahora

# Nota: la versión legacy de `validar_login` fue removida porque estaba duplicada.
# La función unificada `validar_login` más abajo soporta tanto `password_hash` como
# el campo `password` en texto plano para compatibilidad temporal.


# --- UTILIDADES DE HASH ---
def hash_password(password):
    if not BCRYPT_AVAILABLE:
        raise RuntimeError("bcrypt no disponible. Instala 'bcrypt' en tu entorno (pip install bcrypt)")
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    if not BCRYPT_AVAILABLE:
        raise RuntimeError("bcrypt no disponible. Instala 'bcrypt' en tu entorno (pip install bcrypt)")
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- LOGIN Y CONSULTAS ---
def validar_login(username, password):
    """
    Valida el login soportando:
    - usuarios con 'password_hash' (hashed)
    - usuarios legacy con 'password' en texto plano (compatibilidad)

    Agrega logs controlados para ayudar en debugging sin exponer contraseñas.
    """
    client = get_supabase()
    # 1. Buscar usuario activo
    response = client.table("usuarios").select("*")\
        .eq("username", username)\
        .eq("activo", True)\
        .execute()
    
    if response.data:
        usuario = response.data[0]
        # 2. Verificar contraseña (hash o texto plano)
        stored_hash = usuario.get('password_hash')
        stored_pw = usuario.get('password')
        # Verificar hash si existe
        if stored_hash and check_password(password, stored_hash):
            return usuario
        # Compatibilidad: verificar texto plano si existe
        if stored_pw and stored_pw == password:
            return usuario

    # Ninguna verificación coincide
    print(f"[debug login] Falló autenticación para '{username}'.")
    return None

def get_todos_usuarios():
    client = get_supabase()
    return client.table("usuarios").select("*").order("nombre_completo").execute().data

# --- CREACIÓN ---
def crear_usuario(nombre, username, password, rol_sistema, cargo):
    client = get_supabase()
    p_hash = hash_password(password)
    data = {
        "nombre_completo": nombre,
        "username": username,
        "password_hash": p_hash,
        "rol_sistema": rol_sistema,
        "cargo": cargo,
        "activo": True
    }
    try:
        client.table("usuarios").insert(data).execute()
        return True, "Usuario creado exitosamente."
    except Exception as e:
        return False, f"Error: {str(e)}"

# --- EDICIÓN Y GESTIÓN (NUEVO) ---
def actualizar_datos_usuario(id_usuario, nombre, username, rol_sistema, cargo):
    """
    Actualiza los datos informativos y permisos (sin tocar la contraseña).
    """
    client = get_supabase()
    data = {
        "nombre_completo": nombre,
        "username": username,
        "rol_sistema": rol_sistema,
        "cargo": cargo
    }
    try:
        client.table("usuarios").update(data).eq("id", id_usuario).execute()
        return True, "Datos actualizados correctamente."
    except Exception as e:
        return False, f"Error al actualizar: {str(e)}"

def toggle_usuario(id_usuario, estado_actual):
    client = get_supabase()
    try:
        client.table("usuarios").update({"activo": not estado_actual}).eq("id", id_usuario).execute()
        return True, "Estado actualizado."
    except Exception as e:
        return False, str(e)
        
def reset_password(id_usuario, new_password):
    client = get_supabase()
    p_hash = hash_password(new_password)
    try:
        client.table("usuarios").update({"password_hash": p_hash}).eq("id", id_usuario).execute()
        return True, "Contraseña restablecida."
    except Exception as e:
        return False, str(e)
    

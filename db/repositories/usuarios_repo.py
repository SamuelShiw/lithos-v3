import bcrypt
from db.supabase_client import get_supabase
import streamlit as st


# import bcrypt  # Comentado para la demo, usaremos texto plano por ahora

def validar_login(username, password_input):
    """
    Valida usuario contra Supabase.
    Acepta contraseña '1234' (texto plano) para tu Demo.
    """
    supabase = get_supabase()
    
    try:
        # 1. Buscar al usuario por su username
        response = supabase.table("usuarios")\
            .select("*")\
            .eq("username", username)\
            .execute()
        
        # Si no existe el usuario
        if not response.data:
            return None
        
        user = response.data[0]
        
        # 2. Verificar si está activo
        if not user.get('activo', True):
            st.error("Usuario inactivo. Contacte al administrador.")
            return None

        # 3. VERIFICACIÓN DE CONTRASEÑA (CRÍTICO PARA TU DEMO)
        # Aquí verificamos si la contraseña de la BD coincide con la escrita
        
        # A) Intento con Texto Plano (Esto es lo que hará funcionar tu '1234')
        if user.get('password') == password_input:
            return user
            
        # B) (Futuro) Aquí iría la validación de Hash si usaras encriptación
        # if user.get('password_hash') and check_password_hash(user['password_hash'], password_input):
        #     return user

        # Si ninguna coincide
        return None

    except Exception as e:
        print(f"Error en login: {e}")
        return None

# --- UTILIDADES DE HASH ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# --- LOGIN Y CONSULTAS ---
def validar_login(username, password):
    client = get_supabase()
    # 1. Buscar usuario activo
    response = client.table("usuarios").select("*")\
        .eq("username", username)\
        .eq("activo", True)\
        .execute()
    
    if response.data:
        usuario = response.data[0]
        # 2. Verificar Hash
        stored_hash = usuario.get('password_hash')
        if stored_hash and check_password(password, stored_hash):
            return usuario
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
    

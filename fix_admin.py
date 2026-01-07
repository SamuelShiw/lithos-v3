from db.repositories.usuarios_repo import crear_usuario

print("--- INICIANDO CREACIÓN DE ADMIN ---")

# Intenta crear el usuario usando las columnas correctas
ok, msg = crear_usuario(
    nombre="Administrador Global",
    username="admin",        # <--- OJO: Enviamos a 'username', NO 'nombreusuario'
    password="admin123",     # Tu contraseña será esta
    rol_sistema="ADMIN",
    cargo="Soporte TI"
)

if ok:
    print(f"✅ ÉXITO: {msg}")
    print("Ahora puedes iniciar sesión con:")
    print("Usuario: admin")
    print("Clave:   admin123")
else:
    print(f"❌ ERROR: {msg}")
    print("\nSi el error dice que 'username' no existe, revisa tu archivo 'db/repositories/usuarios_repo.py'")
    print("y asegúrate que en el diccionario 'data' diga 'username': username")
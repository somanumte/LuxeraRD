# ============================================
# PUNTO DE ENTRADA DE LA APLICACIÓN LUXERA
# ============================================
# Este es el archivo que ejecutas para iniciar la aplicación
# Comando: python run.py

import os
from app import create_app, db
from app.models.user import User

# ===== CREAR LA APLICACIÓN =====

# Obtener el entorno de ejecución desde variable de entorno
# Por defecto: 'default' (que apunta a DevelopmentConfig)
config_name = os.environ.get('FLASK_ENV', 'default')

# Crear la aplicación usando el patrón Factory
app = create_app(config_name)


# Esto ejecuta toda la configuración en app/__init__.py


# ===== CONTEXTO DE SHELL =====

@app.shell_context_processor
def make_shell_context():
    """
    Define variables disponibles en el shell interactivo de Flask

    ¿Qué es el shell de Flask?
    Ejecuta: flask shell
    Es una consola Python con acceso a tu app y modelos

    ¿Para qué sirve?
    - Testing rápido
    - Consultas a la DB
    - Crear usuarios manualmente

    Ejemplo de uso:
    $ flask shell
    >>> user = User.query.first()
    >>> print(user.username)
    >>> db.session.add(...)

    Returns:
        dict: Variables disponibles en el shell
    """
    return {
        'db': db,  # Base de datos
        'User': User  # Modelo de usuario
    }
    # Ahora en flask shell puedes usar 'db' y 'User' directamente


# ===== COMANDOS CLI PERSONALIZADOS =====

@app.cli.command()
def init_db():
    """
    Comando para inicializar la base de datos

    Uso desde terminal:
    $ flask init-db

    ¿Qué hace?
    1. Elimina todas las tablas existentes
    2. Crea nuevas tablas desde cero
    3. Útil para empezar limpio

    ⚠️ CUIDADO: Esto BORRA todos los datos
    """
    print("🗑️  Eliminando tablas existentes...")
    db.drop_all()

    print("🔨 Creando nuevas tablas...")
    db.create_all()

    print("✅ Base de datos inicializada correctamente")


@app.cli.command()
def create_admin():
    """
    Comando para crear un usuario administrador

    Uso desde terminal:
    $ flask create-admin

    ¿Qué hace?
    Crea un usuario admin con credenciales predefinidas

    Credenciales por defecto:
    - Username: admin
    - Email: admin@luxera.com
    - Password: admin123

    ⚠️ IMPORTANTE: Cambia la contraseña después del primer login
    """
    # Verificar si ya existe un admin
    existing_admin = User.query.filter_by(username='admin').first()

    if existing_admin:
        print("⚠️  El usuario 'admin' ya existe")
        return

    try:
        # Crear usuario administrador
        admin = User.create_user(
            username='admin',
            email='admin@luxera.com',
            password='admin123',  # ⚠️ CAMBIAR ESTO EN PRODUCCIÓN
            full_name='Administrador',
            is_admin=True
        )

        print("✅ Usuario administrador creado exitosamente")
        print("")
        print("📋 Credenciales:")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print("   Password: admin123")
        print("")
        print("⚠️  IMPORTANTE: Cambia la contraseña después del primer login")

    except Exception as e:
        print(f"❌ Error al crear admin: {str(e)}")


@app.cli.command()
def create_test_users():
    """
    Comando para crear usuarios de prueba

    Uso desde terminal:
    $ flask create-test-users

    ¿Qué hace?
    Crea 5 usuarios de prueba para desarrollo/testing

    ⚠️ Solo usar en desarrollo, NO en producción
    """
    test_users = [
        {
            'username': 'felix',
            'email': 'felix@test.com',
            'password': 'test123',
            'full_name': 'Felix Rodriguez'
        },
        {
            'username': 'maria',
            'email': 'maria@test.com',
            'password': 'test123',
            'full_name': 'Maria Garcia'
        },
        {
            'username': 'juan',
            'email': 'juan@test.com',
            'password': 'test123',
            'full_name': 'Juan Perez'
        },
        {
            'username': 'ana',
            'email': 'ana@test.com',
            'password': 'test123',
            'full_name': 'Ana Martinez'
        },
        {
            'username': 'carlos',
            'email': 'carlos@test.com',
            'password': 'test123',
            'full_name': 'Carlos Lopez'
        }
    ]

    created_count = 0

    for user_data in test_users:
        try:
            User.create_user(**user_data)
            print(f"✅ Usuario '{user_data['username']}' creado")
            created_count += 1
        except ValueError as e:
            print(f"⚠️  '{user_data['username']}': {str(e)}")
        except Exception as e:
            print(f"❌ Error con '{user_data['username']}': {str(e)}")

    print(f"\n📊 Resumen: {created_count} usuarios de prueba creados")


@app.cli.command()
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()

    if not users:
        print("📭 No hay usuarios registrados")
        return

    print(f"\n📋 Total de usuarios: {len(users)}")
    print("\n" + "=" * 80)
    print(f"{'ID':<5} {'Username':<15} {'Email':<25} {'Admin':<8} {'Activo':<8}")
    print("=" * 80)

    for user in users:
        print(
            f"{user.id:<5} "
            f"{user.username:<15} "
            f"{user.email:<25} "
            f"{'Sí' if user.is_admin else 'No':<8} "
            f"{'Sí' if user.is_active else 'No':<8}"
        )

    print("=" * 80 + "\n")


@app.cli.command()
def reset_password():
    """
    Comando para resetear la contraseña de un usuario

    Uso desde terminal:
    $ flask reset-password

    ¿Qué hace?
    Te pide el username y nueva contraseña para resetearla
    Útil cuando un usuario olvida su contraseña
    """
    username = input("Ingresa el username del usuario: ").strip()

    user = User.query.filter_by(username=username).first()

    if not user:
        print(f"❌ No existe el usuario '{username}'")
        return

    new_password = input("Ingresa la nueva contraseña: ").strip()

    if len(new_password) < 6:
        print("❌ La contraseña debe tener al menos 6 caracteres")
        return

    user.set_password(new_password)
    user.reset_failed_login()  # Resetear intentos fallidos
    db.session.commit()

    print(f"✅ Contraseña actualizada para '{username}'")


# ===== EJECUTAR LA APLICACIÓN =====

if __name__ == '__main__':
    """
    Punto de entrada cuando ejecutas: python run.py

    ¿Qué hace?
    Inicia el servidor de desarrollo de Flask

    Parámetros:
    - host='0.0.0.0': Acepta conexiones desde cualquier IP (toda la red)
    - port=5000: Puerto donde corre el servidor
    - debug=True: Activa modo debug (recarga automática, errores detallados)

    ⚠️ IMPORTANTE:
    En producción usa un servidor WSGI como Gunicorn o uWSGI
    El servidor de desarrollo de Flask NO es para producción
    """

    print("\n" + "=" * 60)
    print("🚀 INICIANDO SERVIDOR LUXERA")
    print("=" * 60)
    print(f"📍 URL Local: http://127.0.0.1:5000")
    print(f"🌐 URL Red: http://10.0.0.81:5000")
    print("=" * 60)
    print("💡 Presiona CTRL+C para detener el servidor")
    print("=" * 60 + "\n")

    # Iniciar servidor
    app.run(
        host='0.0.0.0',  # Acepta conexiones desde toda la red
        port=5000,  # Puerto 5000
        debug=True  # Modo debug activado
    )
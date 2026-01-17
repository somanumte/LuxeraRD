import os
from datetime import timedelta
import keyring

basedir = os.path.abspath(os.path.dirname(__file__))

# Configuración de PostgreSQL
DB_USER = "LuxeraUSR"
DB_NAME = "LuxeraDB"
DB_HOST = "localhost"
DB_PORT = "5432"
VAULT_SERVICE_NAME = "LuxeraRD"


def obtener_db_password():
    """
    Obtiene la contraseña de la base de datos.
    Prioridad:
    1. Windows Vault (keyring)
    2. Variable de entorno DB_PASSWORD
    3. Contraseña por defecto
    """
    password_vault = keyring.get_password(VAULT_SERVICE_NAME, DB_USER)
    if password_vault:
        print(f"🔑 Contraseña recuperada desde Windows Vault ({VAULT_SERVICE_NAME})")
        return password_vault

    password_env = os.environ.get('DB_PASSWORD')
    if password_env:
        print("🔑 Contraseña recuperada desde variable de entorno (.env)")
        return password_env

    print("⚠️  Usando contraseña por defecto (cambiar en producción)")
    return "******"


class Config:
    # SEGURIDAD - Clave generada aleatoriamente
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'f4e3d2c1b0a9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3'

    # BASE DE DATOS - PostgreSQL (CORREGIDO: agregado +psycopg)
    DB_PASSWORD = obtener_db_password()
    SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True

    # SESIONES Y COOKIES
    SESSION_COOKIE_NAME = 'luxera_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)

    # FLASK-LOGIN
    LOGIN_VIEW = 'auth.login'
    LOGIN_MESSAGE = 'Por favor inicia sesión para acceder a esta página.'
    LOGIN_MESSAGE_CATEGORY = 'info'

    # WTFORMS
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # CONFIGURACIONES PERSONALIZADAS
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_TIME = 15
    ALLOW_REGISTRATION = False  # Solo creación manual de usuarios
    REQUIRE_EMAIL_VERIFICATION = False

    # ===== CONFIGURACIÓN DE ELIMINACIÓN DE FONDO =====
    # Configuración para el procesamiento automático de imágenes
    REMOVE_BG_ENABLED = False  # Habilitar/deshabilitar funcionalidad globalmente
    REMOVE_BG_DEFAULT_COVER = False  # Aplicar a imágenes de portada nuevas por defecto
    REMOVE_BG_DEFAULT_ALL = False  # NO aplicar a todas las imágenes por defecto

    # Límites de procesamiento
    REMOVE_BG_MAX_IMAGE_SIZE_MB = 10  # Rechazar imágenes > 10MB
    REMOVE_BG_PROCESSING_TIMEOUT = 30  # Segundos máximos por imagen

    # Formatos soportados
    REMOVE_BG_SUPPORTED_FORMATS = {'jpg', 'jpeg', 'png', 'webp', 'bmp'}

    # Sistema de backup
    REMOVE_BG_KEEP_BACKUPS = 1  # Número de backups recientes a mantener
    REMOVE_BG_BACKUP_ORIGINAL = True  # Crear backup antes de procesar


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ECHO = False
    # En producción, podemos querer desactivar si hay problemas de rendimiento
    # REMOVE_BG_ENABLED = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    # En testing, desactivar para no depender de rembg
    REMOVE_BG_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
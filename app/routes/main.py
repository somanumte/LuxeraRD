# ============================================
# RUTAS PRINCIPALES
# ============================================
# Maneja las rutas principales de la aplicación

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models.user import User  # ← LÍNEA AGREGADA
# ============================================
# CREAR BLUEPRINT PRINCIPAL
# ============================================

main_bp = Blueprint(
    'main',  # Nombre del blueprint
    __name__  # Módulo actual
    # url_prefix: No tiene prefijo (las rutas son /, /dashboard, etc.)
)


# ============================================
# RUTA: PÁGINA PRINCIPAL
# ============================================

@main_bp.route('/')
def index():
    """
    Página principal / landing page

    URL: /

    Accesible para todos (logueados y no logueados)

    Returns:
        Template index.html
    """

    # Si el usuario ya está logueado, podría redirigir al dashboard
    # Pero lo dejamos así para que pueda ver la landing page

    return render_template('index.html')

# ============================================
# RUTA: PÁGINA "ACERCA DE"
# ============================================

@main_bp.route('/about')
def about():
    """
    Página "Acerca de"

    URL: /about

    Información sobre el proyecto Luxera

    Returns:
        Template about.html
    """

    return render_template('about.html')


# ============================================
# RUTA: CONTACTO
# ============================================

@main_bp.route('/contact')
def contact():
    """
    Página de contacto

    URL: /contact

    Formulario de contacto (futuro)

    Returns:
        Template contact.html
    """

    return render_template('contact.html')


# ============================================
# RUTAS DE ADMIN (SOLO ADMINISTRADORES)
# ============================================

@main_bp.route('/admin')
@login_required
def admin_panel():
    """
    Panel de administración

    URL: /admin

    Solo accesible para usuarios con is_admin=True

    Returns:
        Template admin/panel.html o error 403
    """

    # Verificar si el usuario es admin
    if not current_user.is_admin:
        # Si no es admin, mostrar error 403 (Prohibido)
        from flask import abort
        abort(403)
        # Esto dispara el error_handler de 403 que definimos en __init__.py

    # Si es admin, mostrar el panel
    from app.models.user import User

    # Obtener estadísticas
    total_users = User.query.count()
    # count() cuenta cuántos usuarios hay

    active_users = User.query.filter_by(is_active=True).count()
    # Cuenta solo usuarios activos

    admin_users = User.query.filter_by(is_admin=True).count()
    # Cuenta solo admins

    # Obtener últimos 10 usuarios registrados
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    # order_by(User.created_at.desc()) → Ordenar por fecha descendente (más recientes primero)
    # limit(10) → Solo los primeros 10
    # .all() → Retorna una lista

    return render_template(
        'admin/panel.html',
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        recent_users=recent_users
    )


@main_bp.route('/admin/users')
@login_required
def admin_users():
    """
    Lista de todos los usuarios (solo admin)

    URL: /admin/users

    Returns:
        Template admin/users.html con lista de usuarios
    """

    # Verificar que sea admin
    if not current_user.is_admin:
        from flask import abort
        abort(403)

    # Obtener todos los usuarios
    users = User.query.order_by(User.created_at.desc()).all()
    # Ordenados por fecha de creación (más recientes primero)

    return render_template(
        'admin/users.html',
        users=users
    )


# ===== MANEJADORES DE ERRORES =====

def register_error_handlers(app):
    """
    Registra los manejadores de errores personalizados
    Se llama desde app/__init__.py
    """

    @app.errorhandler(403)
    def forbidden(error):
        """Error 403: Acceso prohibido"""
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        """Error 404: Página no encontrada"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        """Error 500: Error interno del servidor"""
        from app import db
        db.session.rollback()  # Revertir cualquier transacción pendiente
        return render_template('errors/500.html'), 500
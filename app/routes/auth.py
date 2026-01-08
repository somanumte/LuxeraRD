# ============================================
# RUTAS DE AUTENTICACIÓN
# ============================================
# Maneja login, registro y logout de usuarios

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models.user import User
from app.forms.auth import LoginForm, RegisterForm
from datetime import datetime

# ============================================
# CREAR BLUEPRINT DE AUTENTICACIÓN
# ============================================

auth_bp = Blueprint(
    'auth',  # Nombre del blueprint
    __name__,  # Módulo actual
    url_prefix='/auth'  # Todas las rutas tendrán el prefijo /auth/
)


# Ejemplo:
# @auth_bp.route('/login') → URL real: /auth/login
# @auth_bp.route('/register') → URL real: /auth/register


# ============================================
# RUTA: LOGIN
# ============================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Ruta de inicio de sesión

    GET:  Muestra el formulario de login
    POST: Procesa el intento de login

    URL: /auth/login

    Returns:
        GET:  Template login.html con el formulario
        POST: Redirección al dashboard o vuelta al login con errores
    """

    # ===== SI YA ESTÁ LOGUEADO, REDIRIGIR =====
    if current_user.is_authenticated:
        # current_user.is_authenticated = True si hay sesión activa
        # No tiene sentido que un usuario logueado vea la página de login
        flash('Ya has iniciado sesión', 'info')
        return redirect(url_for('inventory.laptops_list'))
        # url_for('main.dashboard') genera la URL: /dashboard

    # ===== CREAR INSTANCIA DEL FORMULARIO =====
    form = LoginForm()
    # Esto crea el formulario con todos sus campos y validaciones

    # ===== PROCESAR SUBMIT DEL FORMULARIO =====
    if form.validate_on_submit():
        """
        validate_on_submit() retorna True si:
        1. Es un POST request
        2. El token CSRF es válido
        3. Todas las validaciones pasaron
        """

        # --- PASO 1: OBTENER DATOS DEL FORMULARIO ---
        email = form.email.data
        password = form.password.data
        remember = form.remember_me.data
        # .data obtiene el valor que el usuario escribió

        # --- PASO 2: BUSCAR USUARIO EN LA BASE DE DATOS ---
        user = User.query.filter_by(email=email).first()
        # filter_by(email=email) → WHERE email = 'felix@luxera.com'
        # .first() → Retorna el primer resultado o None

        # --- PASO 3: VERIFICAR CONTRASEÑA ---
        if user and user.check_password(password):
            # user existe AND contraseña es correcta

            # --- PASO 4: VERIFICAR SI ESTÁ ACTIVO ---
            if not user.is_active:
                flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'error')
                return redirect(url_for('auth.login'))

            # --- PASO 5: VERIFICAR SI ESTÁ BLOQUEADO ---
            if user.is_locked():
                flash(
                    'Tu cuenta está bloqueada temporalmente por múltiples intentos fallidos. '
                    'Intenta de nuevo más tarde.',
                    'error'
                )
                return redirect(url_for('auth.login'))

            # --- PASO 6: LOGIN EXITOSO ---

            # Hacer login con Flask-Login
            login_user(user, remember=remember)
            # Esto hace:
            # 1. Crea una sesión (cookie) con el user.id
            # 2. El usuario queda "logueado"
            # 3. current_user ahora es este usuario
            # 4. Si remember=True, la sesión dura más tiempo

            # Reiniciar contador de intentos fallidos
            user.reset_failed_login()

            # Actualizar fecha de último login
            user.update_last_login()

            # Mensaje de éxito
            flash(f'¡Bienvenido de vuelta, {user.username}!', 'success')

            # --- PASO 7: REDIRIGIR AL DESTINO ---

            # Obtener la página que el usuario quería visitar antes de hacer login
            next_page = request.args.get('next')
            # Ejemplo: si intentó ir a /dashboard sin estar logueado
            # Flask lo redirigió a /auth/login?next=/dashboard
            # next_page = '/dashboard'

            # Validar que 'next' sea una URL segura (misma aplicación)
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            else:
                # Si no hay 'next' o no es seguro, ir al dashboard
                return redirect(url_for('inventory.laptops_list'))


        # --- PASO 8: LOGIN FALLIDO ---
        else:
            # Contraseña incorrecta o usuario no existe

            if user:
                # El usuario existe pero la contraseña es incorrecta
                user.increment_failed_login()
                # Incrementa el contador de intentos fallidos
                # Si llega a 5, bloquea temporalmente

                flash(
                    f'Contraseña incorrecta. '
                    f'Intentos restantes: {5 - user.failed_login_attempts}',
                    'error'
                )
            else:
                # El usuario no existe
                flash('Email o contraseña incorrectos', 'error')
                # No decimos "email no existe" por seguridad
                # Los hackers no deben saber qué emails están registrados

            # Redirigir de vuelta al login
            return redirect(url_for('auth.login'))

    # ===== RENDERIZAR TEMPLATE =====
    # Si es GET o si las validaciones fallaron
    return render_template('auth/login.html', form=form)
    # Pasa el formulario al template para mostrarlo


# ============================================
# RUTA: REGISTRO
# ============================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Ruta de registro de nuevos usuarios

    GET:  Muestra el formulario de registro
    POST: Procesa el registro

    URL: /auth/register

    Nota:
    Esta ruta solo funciona si ALLOW_REGISTRATION=True en config.py

    Returns:
        GET:  Template register.html con el formulario
        POST: Redirección al login o vuelta al registro con errores
    """

    # ===== VERIFICAR SI EL REGISTRO ESTÁ HABILITADO =====
    from flask import current_app

    if not current_app.config.get('ALLOW_REGISTRATION', False):
        # Si ALLOW_REGISTRATION = False, el registro está cerrado
        flash('El registro de nuevos usuarios no está disponible actualmente.', 'info')
        return redirect(url_for('auth.login'))

    # ===== SI YA ESTÁ LOGUEADO, REDIRIGIR =====
    if current_user.is_authenticated:
        flash('Ya tienes una cuenta activa', 'info')
        return redirect(url_for('inventory.laptops_list'))

    # ===== CREAR INSTANCIA DEL FORMULARIO =====
    form = RegisterForm()

    # ===== PROCESAR SUBMIT DEL FORMULARIO =====
    if form.validate_on_submit():
        """
        validate_on_submit() ejecuta TODAS las validaciones:
        - Campos requeridos
        - Formato de email
        - Longitud de contraseña
        - Contraseñas coinciden
        - Username/email no existen (validaciones personalizadas)
        """

        try:
            # --- PASO 1: CREAR USUARIO ---
            user = User.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                full_name=form.full_name.data if form.full_name.data else None,
                is_admin=False  # Los usuarios normales no son admin
            )
            # create_user() hace:
            # 1. Verifica que username/email no existan
            # 2. Crea el usuario
            # 3. Encripta la contraseña
            # 4. Guarda en la base de datos

            # --- PASO 2: MENSAJE DE ÉXITO ---
            flash(
                f'¡Cuenta creada exitosamente! Bienvenido, {user.username}. '
                'Ahora puedes iniciar sesión.',
                'success'
            )

            # --- PASO 3: REDIRIGIR AL LOGIN ---
            return redirect(url_for('auth.login'))
            # El usuario debe hacer login manualmente
            # Esto es más seguro que hacer auto-login


        except ValueError as e:
            # Si create_user() falla (username/email duplicado)
            flash(str(e), 'error')
            return redirect(url_for('auth.register'))

        except Exception as e:
            # Si ocurre cualquier otro error
            db.session.rollback()  # Deshacer cambios en la DB
            flash('Ocurrió un error al crear la cuenta. Intenta de nuevo.', 'error')

            # Log del error (útil para debugging)
            from flask import current_app
            current_app.logger.error(f'Error en registro: {str(e)}')

            return redirect(url_for('auth.register'))

@auth_bp.route('/logout')
@login_required
def logout():
    """
    Ruta para cerrar sesión
    """
    username = current_user.username
    logout_user()
    flash(f'¡Hasta pronto, {username}!', 'success')
    return redirect(url_for('public.landing'))
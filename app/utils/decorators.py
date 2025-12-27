# ============================================
# DECORADORES PERSONALIZADOS
# ============================================
# Decoradores reutilizables para rutas y funciones

from functools import wraps
from flask import abort, jsonify, request
from flask_login import current_user


def admin_required(f):
    """
    Decorador que requiere que el usuario sea administrador

    Uso:
        @app.route('/admin/panel')
        @login_required
        @admin_required
        def admin_panel():
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(403, description="Debes iniciar sesión para acceder a esta página")

        if not current_user.is_admin:
            abort(403, description="Solo administradores pueden acceder a esta página")

        return f(*args, **kwargs)

    return decorated_function


def permission_required(permission):
    """
    Decorador que verifica permisos específicos
    (Para uso futuro cuando se implementen permisos granulares)

    Uso:
        @app.route('/inventory/delete')
        @login_required
        @permission_required('inventory.delete')
        def delete_item():
            ...

    Args:
        permission: Nombre del permiso requerido
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403, description="Debes iniciar sesión")

            # Por ahora, solo verificamos si es admin
            # En el futuro aquí se verificaría current_user.has_permission(permission)
            if not current_user.is_admin:
                abort(403, description=f"No tienes permiso: {permission}")

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def json_response(f):
    """
    Decorador que convierte automáticamente la respuesta a JSON

    Uso:
        @app.route('/api/data')
        @json_response
        def get_data():
            return {'status': 'success', 'data': [1, 2, 3]}
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        result = f(*args, **kwargs)

        # Si ya es una respuesta Flask, retornarla directamente
        if hasattr(result, 'get_json'):
            return result

        # Si es un dict o list, convertir a JSON
        if isinstance(result, (dict, list)):
            return jsonify(result)

        # Si es una tupla (data, status_code)
        if isinstance(result, tuple):
            data, status_code = result
            return jsonify(data), status_code

        return result

    return decorated_function


def validate_json(required_fields=None):
    """
    Decorador que valida que el request tenga JSON válido
    y opcionalmente verifica campos requeridos

    Uso:
        @app.route('/api/create', methods=['POST'])
        @validate_json(['name', 'price'])
        def create_item():
            data = request.get_json()
            ...

    Args:
        required_fields: Lista de campos requeridos
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar que sea JSON
            if not request.is_json:
                return jsonify({
                    'error': 'Content-Type debe ser application/json'
                }), 400

            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({
                    'error': 'JSON inválido',
                    'message': str(e)
                }), 400

            # Verificar campos requeridos
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None or data[field] == '':
                        missing_fields.append(field)

                if missing_fields:
                    return jsonify({
                        'error': 'Campos requeridos faltantes',
                        'missing_fields': missing_fields
                    }), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def handle_exceptions(f):
    """
    Decorador que captura excepciones y retorna respuestas JSON apropiadas
    Útil para endpoints API

    Uso:
        @app.route('/api/process')
        @handle_exceptions
        def process_data():
            # Si hay un error, automáticamente se retorna JSON
            result = risky_operation()
            return {'data': result}
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({
                'error': 'Valor inválido',
                'message': str(e)
            }), 400
        except KeyError as e:
            return jsonify({
                'error': 'Campo faltante',
                'message': f'Campo requerido: {str(e)}'
            }), 400
        except PermissionError as e:
            return jsonify({
                'error': 'Permiso denegado',
                'message': str(e)
            }), 403
        except Exception as e:
            # Log the error (en producción deberías usar logging)
            print(f"Error no manejado: {str(e)}")
            return jsonify({
                'error': 'Error interno del servidor',
                'message': 'Ocurrió un error inesperado'
            }), 500

    return decorated_function


def rate_limit(max_requests=60, window=60):
    """
    Decorador simple de rate limiting
    (En producción usar Flask-Limiter o similar)

    Uso:
        @app.route('/api/search')
        @rate_limit(max_requests=30, window=60)
        def search():
            ...

    Args:
        max_requests: Número máximo de requests
        window: Ventana de tiempo en segundos
    """

    def decorator(f):
        # Almacenamiento simple en memoria (en producción usar Redis)
        request_counts = {}

        @wraps(f)
        def decorated_function(*args, **kwargs):
            from time import time

            # Identificar usuario (por IP o user_id)
            if current_user.is_authenticated:
                identifier = f"user_{current_user.id}"
            else:
                identifier = f"ip_{request.remote_addr}"

            current_time = int(time())
            window_start = current_time - window

            # Limpiar requests antiguos
            if identifier in request_counts:
                request_counts[identifier] = [
                    timestamp for timestamp in request_counts[identifier]
                    if timestamp > window_start
                ]
            else:
                request_counts[identifier] = []

            # Verificar límite
            if len(request_counts[identifier]) >= max_requests:
                return jsonify({
                    'error': 'Límite de requests excedido',
                    'message': f'Máximo {max_requests} requests por {window} segundos'
                }), 429

            # Registrar request
            request_counts[identifier].append(current_time)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def cache_response(timeout=300):
    """
    Decorador simple de caché
    (En producción usar Flask-Caching)

    Uso:
        @app.route('/api/stats')
        @cache_response(timeout=60)
        def get_stats():
            # Esta función se ejecuta solo cada 60 segundos
            ...

    Args:
        timeout: Tiempo en segundos para cachear
    """

    def decorator(f):
        cache = {}

        @wraps(f)
        def decorated_function(*args, **kwargs):
            from time import time

            # Crear clave de caché basada en la función y argumentos
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            current_time = time()

            # Verificar si existe en caché y no ha expirado
            if cache_key in cache:
                cached_time, cached_result = cache[cache_key]
                if current_time - cached_time < timeout:
                    return cached_result

            # Ejecutar función y cachear resultado
            result = f(*args, **kwargs)
            cache[cache_key] = (current_time, result)

            return result

        return decorated_function

    return decorator


def log_activity(action):
    """
    Decorador que registra actividades de usuarios
    (Para auditoría)

    Uso:
        @app.route('/inventory/delete/<id>')
        @login_required
        @log_activity('delete_laptop')
        def delete_laptop(id):
            ...

    Args:
        action: Descripción de la acción
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Ejecutar función
            result = f(*args, **kwargs)

            # Registrar actividad (en producción guardar en DB)
            if current_user.is_authenticated:
                log_entry = {
                    'user_id': current_user.id,
                    'username': current_user.username,
                    'action': action,
                    'timestamp': str(__import__('datetime').datetime.utcnow()),
                    'ip': request.remote_addr,
                    'args': str(args),
                    'kwargs': str(kwargs)
                }
                # Aquí guardarías en tabla de auditoría
                print(f"AUDIT LOG: {log_entry}")

            return result

        return decorated_function

    return decorator


def api_key_required(f):
    """
    Decorador que requiere API key para acceder
    (Para APIs públicas/externas)

    Uso:
        @app.route('/api/external/data')
        @api_key_required
        def external_api():
            ...

    La API key debe enviarse en el header:
    Authorization: Bearer YOUR_API_KEY
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization')

        if not api_key:
            return jsonify({
                'error': 'API key requerida',
                'message': 'Incluye "Authorization: Bearer YOUR_API_KEY" en headers'
            }), 401

        # Remover "Bearer " si existe
        if api_key.startswith('Bearer '):
            api_key = api_key[7:]

        # Validar API key (en producción verificar contra DB)
        # Por ahora, aceptar cualquier key para desarrollo
        valid_keys = ['dev-key-123']  # En producción: consultar DB

        if api_key not in valid_keys:
            return jsonify({
                'error': 'API key inválida'
            }), 401

        return f(*args, **kwargs)

    return decorated_function
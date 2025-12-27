# ============================================
# API DE CATÁLOGOS - Endpoints para Select2
# ============================================
# Endpoints JSON para dropdowns dinámicos

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, StorageType, RAMType, Store, Location
)
from app.utils.decorators import admin_required, json_response, handle_exceptions
from sqlalchemy import or_

# Crear Blueprint
catalog_api_bp = Blueprint('catalog_api', __name__, url_prefix='/api/catalog')


# ===== FUNCIÓN HELPER GENÉRICA =====

def get_catalog_items(model, search_term='', page=1, page_size=20):
    """
    Función genérica para obtener items de catálogo con búsqueda y paginación

    Args:
        model: Modelo de SQLAlchemy (Brand, Processor, etc.)
        search_term: Término de búsqueda
        page: Página actual
        page_size: Items por página

    Returns:
        dict: Respuesta en formato Select2
    """
    # Query base
    query = model.query.filter_by(is_active=True)

    # Búsqueda
    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(model.name.ilike(search_pattern))

    # Ordenar por nombre
    query = query.order_by(model.name)

    # Calcular total
    total = query.count()

    # Paginación
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Formatear para Select2
    results = [
        {'id': item.id, 'text': item.name}
        for item in items
    ]

    # Determinar si hay más páginas
    has_more = (offset + page_size) < total

    return {
        'results': results,
        'pagination': {
            'more': has_more
        }
    }


def create_catalog_item(model, name):
    """
    Crea un nuevo item en el catálogo

    Args:
        model: Modelo de SQLAlchemy
        name: Nombre del nuevo item

    Returns:
        tuple: (item, created) donde created es True si fue creado
    """
    # Verificar si ya existe
    existing = model.query.filter(
        db.func.lower(model.name) == name.lower()
    ).first()

    if existing:
        return existing, False

    # Crear nuevo
    new_item = model(name=name.strip())
    db.session.add(new_item)
    db.session.commit()

    return new_item, True


# ===== ENDPOINTS PARA CADA CATÁLOGO =====

# ===== BRANDS =====

@catalog_api_bp.route('/brands', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_brands():
    """GET: Obtener lista de marcas"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Brand, search, page)


@catalog_api_bp.route('/brands', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_brand():
    """POST: Crear nueva marca"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    if len(name) > 100:
        return {'error': 'El nombre es demasiado largo (máximo 100 caracteres)'}, 400

    brand, created = create_catalog_item(Brand, name)

    if created:
        return {
            'id': brand.id,
            'text': brand.name,
            'created': True,
            'message': f'Marca "{brand.name}" creada exitosamente'
        }, 201
    else:
        return {
            'id': brand.id,
            'text': brand.name,
            'created': False,
            'message': f'La marca "{brand.name}" ya existe'
        }, 200


# ===== LAPTOP MODELS =====

@catalog_api_bp.route('/models', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_models():
    """GET: Obtener lista de modelos"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(LaptopModel, search, page)


@catalog_api_bp.route('/models', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_model():
    """POST: Crear nuevo modelo"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    if len(name) > 200:
        return {'error': 'El nombre es demasiado largo (máximo 200 caracteres)'}, 400

    model, created = create_catalog_item(LaptopModel, name)

    return {
        'id': model.id,
        'text': model.name,
        'created': created,
        'message': f'Modelo "{model.name}" {"creado" if created else "ya existe"}'
    }, 201 if created else 200


# ===== PROCESSORS =====

@catalog_api_bp.route('/processors', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_processors():
    """GET: Obtener lista de procesadores"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Processor, search, page)


@catalog_api_bp.route('/processors', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_processor():
    """POST: Crear nuevo procesador"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    processor, created = create_catalog_item(Processor, name)

    return {
        'id': processor.id,
        'text': processor.name,
        'created': created,
        'message': f'Procesador "{processor.name}" {"creado" if created else "ya existe"}'
    }, 201 if created else 200


# ===== OPERATING SYSTEMS =====

@catalog_api_bp.route('/operating-systems', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_operating_systems():
    """GET: Obtener lista de sistemas operativos"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(OperatingSystem, search, page)


@catalog_api_bp.route('/operating-systems', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_operating_system():
    """POST: Crear nuevo sistema operativo"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    os, created = create_catalog_item(OperatingSystem, name)

    return {
        'id': os.id,
        'text': os.name,
        'created': created,
        'message': f'Sistema operativo "{os.name}" {"creado" if created else "ya existe"}'
    }, 201 if created else 200


# ===== SCREENS =====

@catalog_api_bp.route('/screens', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_screens():
    """GET: Obtener lista de pantallas"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Screen, search, page)


@catalog_api_bp.route('/screens', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_screen():
    """POST: Crear nueva pantalla"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    screen, created = create_catalog_item(Screen, name)

    return {
        'id': screen.id,
        'text': screen.name,
        'created': created,
        'message': f'Pantalla "{screen.name}" {"creada" if created else "ya existe"}'
    }, 201 if created else 200


# ===== GRAPHICS CARDS =====

@catalog_api_bp.route('/graphics-cards', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_graphics_cards():
    """GET: Obtener lista de tarjetas gráficas"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(GraphicsCard, search, page)


@catalog_api_bp.route('/graphics-cards', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_graphics_card():
    """POST: Crear nueva tarjeta gráfica"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    gpu, created = create_catalog_item(GraphicsCard, name)

    return {
        'id': gpu.id,
        'text': gpu.name,
        'created': created,
        'message': f'Tarjeta gráfica "{gpu.name}" {"creada" if created else "ya existe"}'
    }, 201 if created else 200


# ===== STORAGE TYPES =====

@catalog_api_bp.route('/storage-types', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_storage_types():
    """GET: Obtener lista de tipos de almacenamiento"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(StorageType, search, page)


@catalog_api_bp.route('/storage-types', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_storage_type():
    """POST: Crear nuevo tipo de almacenamiento"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    storage, created = create_catalog_item(StorageType, name)

    return {
        'id': storage.id,
        'text': storage.name,
        'created': created,
        'message': f'Almacenamiento "{storage.name}" {"creado" if created else "ya existe"}'
    }, 201 if created else 200


# ===== RAM TYPES =====

@catalog_api_bp.route('/ram-types', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_ram_types():
    """GET: Obtener lista de tipos de RAM"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(RAMType, search, page)


@catalog_api_bp.route('/ram-types', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_ram_type():
    """POST: Crear nuevo tipo de RAM"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    ram, created = create_catalog_item(RAMType, name)

    return {
        'id': ram.id,
        'text': ram.name,
        'created': created,
        'message': f'RAM "{ram.name}" {"creada" if created else "ya existe"}'
    }, 201 if created else 200


# ===== STORES =====

@catalog_api_bp.route('/stores', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_stores():
    """GET: Obtener lista de tiendas"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Store, search, page)


@catalog_api_bp.route('/stores', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_store():
    """POST: Crear nueva tienda"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    store, created = create_catalog_item(Store, name)

    return {
        'id': store.id,
        'text': store.name,
        'created': created,
        'message': f'Tienda "{store.name}" {"creada" if created else "ya existe"}'
    }, 201 if created else 200


# ===== LOCATIONS =====

@catalog_api_bp.route('/locations', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_locations():
    """GET: Obtener lista de ubicaciones"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Location, search, page)


@catalog_api_bp.route('/locations', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_location():
    """POST: Crear nueva ubicación"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    location, created = create_catalog_item(Location, name)

    return {
        'id': location.id,
        'text': location.name,
        'created': created,
        'message': f'Ubicación "{location.name}" {"creada" if created else "ya existe"}'
    }, 201 if created else 200


# ===== ENDPOINT DE BÚSQUEDA GLOBAL =====

@catalog_api_bp.route('/search', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def global_search():
    """
    Búsqueda global en todos los catálogos
    Útil para autocompletado general
    """
    search = request.args.get('q', '').strip()
    catalog = request.args.get('catalog', 'all')

    if not search:
        return {'results': []}, 200

    results = {}

    catalogs = {
        'brands': Brand,
        'models': LaptopModel,
        'processors': Processor,
        'os': OperatingSystem,
        'screens': Screen,
        'gpus': GraphicsCard,
        'storage': StorageType,
        'ram': RAMType,
        'stores': Store,
        'locations': Location
    }

    if catalog == 'all':
        for cat_name, model in catalogs.items():
            items = model.query.filter(
                model.name.ilike(f'%{search}%'),
                model.is_active == True
            ).limit(5).all()

            results[cat_name] = [
                {'id': item.id, 'text': item.name}
                for item in items
            ]
    else:
        if catalog in catalogs:
            model = catalogs[catalog]
            items = model.query.filter(
                model.name.ilike(f'%{search}%'),
                model.is_active == True
            ).limit(20).all()

            results[catalog] = [
                {'id': item.id, 'text': item.name}
                for item in items
            ]

    return {'results': results}, 200
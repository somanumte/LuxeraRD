# ============================================
# API DE CATÁLOGOS - Endpoints para Select2
# ============================================
# Actualizado al nuevo modelo de datos

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
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


def create_catalog_item(model, name, **extra_fields):
    """
    Crea un nuevo item en el catálogo

    Args:
        model: Modelo de SQLAlchemy
        name: Nombre del nuevo item
        **extra_fields: Campos adicionales para el modelo

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
    new_item = model(name=name.strip(), **extra_fields)
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
    brand_id = request.args.get('brand_id', type=int)

    query = LaptopModel.query.filter_by(is_active=True)

    if brand_id:
        query = query.filter_by(brand_id=brand_id)

    if search:
        query = query.filter(LaptopModel.name.ilike(f'%{search}%'))

    query = query.order_by(LaptopModel.name)

    total = query.count()
    page_size = 20
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    results = [{'id': item.id, 'text': item.name} for item in items]

    return {
        'results': results,
        'pagination': {'more': (offset + page_size) < total}
    }


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
    brand_id = data.get('brand_id')

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    if len(name) > 200:
        return {'error': 'El nombre es demasiado largo (máximo 200 caracteres)'}, 400

    extra_fields = {'brand_id': brand_id} if brand_id else {}
    model, created = create_catalog_item(LaptopModel, name, **extra_fields)

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


# ===== STORAGE =====

@catalog_api_bp.route('/storage', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_storage():
    """GET: Obtener lista de tipos de almacenamiento"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Storage, search, page)


@catalog_api_bp.route('/storage', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_storage():
    """POST: Crear nuevo tipo de almacenamiento"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    storage, created = create_catalog_item(Storage, name)

    return {
        'id': storage.id,
        'text': storage.name,
        'created': created,
        'message': f'Almacenamiento "{storage.name}" {"creado" if created else "ya existe"}'
    }, 201 if created else 200


# ===== RAM =====

@catalog_api_bp.route('/ram', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_ram():
    """GET: Obtener lista de tipos de RAM"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Ram, search, page)


@catalog_api_bp.route('/ram', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_ram():
    """POST: Crear nuevo tipo de RAM"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    ram, created = create_catalog_item(Ram, name)

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
    store_id = request.args.get('store_id', type=int)

    query = Location.query.filter_by(is_active=True)

    if store_id:
        query = query.filter_by(store_id=store_id)

    if search:
        query = query.filter(Location.name.ilike(f'%{search}%'))

    query = query.order_by(Location.name)

    total = query.count()
    page_size = 20
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    results = [{'id': item.id, 'text': item.name} for item in items]

    return {
        'results': results,
        'pagination': {'more': (offset + page_size) < total}
    }


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
    store_id = data.get('store_id')

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    extra_fields = {'store_id': store_id} if store_id else {}
    location, created = create_catalog_item(Location, name, **extra_fields)

    return {
        'id': location.id,
        'text': location.name,
        'created': created,
        'message': f'Ubicación "{location.name}" {"creada" if created else "ya existe"}'
    }, 201 if created else 200


# ===== SUPPLIERS =====

@catalog_api_bp.route('/suppliers', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_suppliers():
    """GET: Obtener lista de proveedores"""
    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    return get_catalog_items(Supplier, search, page)


@catalog_api_bp.route('/suppliers', methods=['POST'])
@login_required
@admin_required
@json_response
@handle_exceptions
def create_supplier():
    """POST: Crear nuevo proveedor"""
    data = request.get_json()

    if not data or 'name' not in data:
        return {'error': 'El nombre es requerido'}, 400

    name = data['name'].strip()

    if not name:
        return {'error': 'El nombre no puede estar vacío'}, 400

    # Campos adicionales opcionales
    extra_fields = {}
    if data.get('contact_name'):
        extra_fields['contact_name'] = data['contact_name'].strip()
    if data.get('email'):
        extra_fields['email'] = data['email'].strip()
    if data.get('phone'):
        extra_fields['phone'] = data['phone'].strip()

    supplier, created = create_catalog_item(Supplier, name, **extra_fields)

    return {
        'id': supplier.id,
        'text': supplier.name,
        'created': created,
        'message': f'Proveedor "{supplier.name}" {"creado" if created else "ya existe"}'
    }, 201 if created else 200


@catalog_api_bp.route('/suppliers/<int:id>', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def get_supplier_detail(id):
    """GET: Obtener detalle de un proveedor"""
    supplier = Supplier.query.get_or_404(id)

    return {
        'id': supplier.id,
        'name': supplier.name,
        'contact_name': supplier.contact_name,
        'email': supplier.email,
        'phone': supplier.phone,
        'address': supplier.address,
        'website': supplier.website,
        'notes': supplier.notes,
        'is_active': supplier.is_active
    }


@catalog_api_bp.route('/suppliers/<int:id>', methods=['PUT'])
@login_required
@admin_required
@json_response
@handle_exceptions
def update_supplier(id):
    """PUT: Actualizar proveedor"""
    supplier = Supplier.query.get_or_404(id)
    data = request.get_json()

    if 'name' in data:
        supplier.name = data['name'].strip()
    if 'contact_name' in data:
        supplier.contact_name = data['contact_name'].strip() if data['contact_name'] else None
    if 'email' in data:
        supplier.email = data['email'].strip() if data['email'] else None
    if 'phone' in data:
        supplier.phone = data['phone'].strip() if data['phone'] else None
    if 'address' in data:
        supplier.address = data['address'].strip() if data['address'] else None
    if 'website' in data:
        supplier.website = data['website'].strip() if data['website'] else None
    if 'notes' in data:
        supplier.notes = data['notes'].strip() if data['notes'] else None
    if 'is_active' in data:
        supplier.is_active = data['is_active']

    db.session.commit()

    return {
        'id': supplier.id,
        'text': supplier.name,
        'message': f'Proveedor "{supplier.name}" actualizado exitosamente'
    }


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
        'storage': Storage,
        'ram': Ram,
        'stores': Store,
        'locations': Location,
        'suppliers': Supplier
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


# ===== ESTADÍSTICAS DE CATÁLOGOS =====

@catalog_api_bp.route('/stats', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def catalog_stats():
    """
    Obtiene estadísticas de todos los catálogos
    """
    stats = {
        'brands': Brand.query.filter_by(is_active=True).count(),
        'models': LaptopModel.query.filter_by(is_active=True).count(),
        'processors': Processor.query.filter_by(is_active=True).count(),
        'operating_systems': OperatingSystem.query.filter_by(is_active=True).count(),
        'screens': Screen.query.filter_by(is_active=True).count(),
        'graphics_cards': GraphicsCard.query.filter_by(is_active=True).count(),
        'storage': Storage.query.filter_by(is_active=True).count(),
        'ram': Ram.query.filter_by(is_active=True).count(),
        'stores': Store.query.filter_by(is_active=True).count(),
        'locations': Location.query.filter_by(is_active=True).count(),
        'suppliers': Supplier.query.filter_by(is_active=True).count()
    }

    return stats
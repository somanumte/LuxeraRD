# ============================================
# RUTAS PÚBLICAS - LANDING PAGE Y CATÁLOGO (CORREGIDO)
# ============================================
# Blueprint para la landing page y catálogo público
# sin requerir autenticación

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import or_, and_, case
from sqlalchemy.orm import joinedload
from app import db
from app.models.laptop import Laptop, Brand, LaptopModel, Processor, Ram, Storage

# ============================================
# CREAR BLUEPRINT PÚBLICO
# ============================================

public_bp = Blueprint(
    'public',
    __name__,
    url_prefix='',  # Sin prefijo para que / sea la landing
)


# ============================================
# RUTA: LANDING PAGE PRINCIPAL
# ============================================

@public_bp.route('/')
def landing():
    """
    Landing page principal del sitio

    URL: /

    Muestra:
    - Hero section con producto destacado
    - Productos destacados (is_featured=True)
    - Características y beneficios
    - CTA para ir al catálogo

    Returns:
        Template landing/home.html
    """

    # Obtener productos destacados (máximo 6) CON imágenes precargadas
    featured_laptops = Laptop.query.options(
        joinedload(Laptop.images)  # Esto carga las imágenes en la misma consulta
    ).filter(
        Laptop.is_published == True,  # ⭐ CORREGIDO
        Laptop.is_featured == True,
        Laptop.quantity > 0  # ⭐ CORREGIDO
    ).order_by(
        Laptop.created_at.desc()
    ).limit(6).all()

    # Si no hay productos destacados, mostrar los más recientes
    if not featured_laptops:
        featured_laptops = Laptop.query.options(
            joinedload(Laptop.images)
        ).filter(
            Laptop.is_published == True,  # ⭐ CORREGIDO
            Laptop.quantity > 0  # ⭐ CORREGIDO
        ).order_by(
            Laptop.created_at.desc()
        ).limit(6).all()

    # Estadísticas para mostrar en la landing
    total_products = Laptop.query.filter_by(is_published=True).count()

    return render_template(
        'landing/home.html',
        featured_laptops=featured_laptops,
        total_products=total_products
    )


# ============================================
# RUTA: CATÁLOGO PÚBLICO
# ============================================

@public_bp.route('/catalog')
def catalog():
    """
    Catálogo público de productos

    URL: /catalog

    Parámetros opcionales (query params):
    - q: Búsqueda por texto
    - brand: Filtro por marca (ID)
    - min_price: Precio mínimo
    - max_price: Precio máximo
    - category: Categoría (gaming, profesional, estudiantes)
    - sort: Ordenamiento (price_asc, price_desc, newest, popular)
    - page: Página actual (default: 1)

    Returns:
        Template landing/catalog.html
    """

    # Obtener parámetros de búsqueda y filtros
    search_query = request.args.get('q', '').strip()
    brand_id = request.args.get('brand', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    category = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'newest')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # Query base: solo productos activos con stock (CON imágenes precargadas)
    query = Laptop.query.options(
        joinedload(Laptop.images)
    ).filter(
        Laptop.is_published == True,  # ⭐ CORREGIDO
        Laptop.quantity > 0  # ⭐ CORREGIDO
    )

    # ===== APLICAR FILTROS =====

    # Búsqueda por texto
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.join(Brand).filter(
            or_(
                Laptop.display_name.ilike(search_pattern),
                Laptop.short_description.ilike(search_pattern),
                Brand.name.ilike(search_pattern)
            )
        )

    # Filtro por marca
    if brand_id:
        query = query.filter(Laptop.brand_id == brand_id)

    # Filtro por precio (usa discount_price si existe, sino sale_price)
    if min_price:
        query = query.filter(
            or_(
                and_(Laptop.discount_price != None, Laptop.discount_price >= min_price),
                and_(Laptop.discount_price == None, Laptop.sale_price >= min_price)
            )
        )

    if max_price:
        query = query.filter(
            or_(
                and_(Laptop.discount_price != None, Laptop.discount_price <= max_price),
                and_(Laptop.discount_price == None, Laptop.sale_price <= max_price)
            )
        )

    # Filtro por categoría
    if category and category in ['laptop', 'gaming', 'workstation']:
        query = query.filter(Laptop.category == category)

    # ===== APLICAR ORDENAMIENTO =====

    if sort_by == 'price_asc':
        # Ordenar por precio ascendente (considerar discount_price si existe)
        query = query.order_by(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            ).asc()
        )
    elif sort_by == 'price_desc':
        # Ordenar por precio descendente
        query = query.order_by(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            ).desc()
        )
    elif sort_by == 'popular':
        # Ordenar por destacados primero, luego por fecha
        query = query.order_by(Laptop.is_featured.desc(), Laptop.created_at.desc())
    else:  # newest (default)
        query = query.order_by(Laptop.created_at.desc())

    # ===== EJECUTAR QUERY CON PAGINACIÓN =====

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    laptops = pagination.items

    # ===== DATOS PARA FILTROS =====

    # Todas las marcas activas (CatalogMixin tiene is_active)
    from app.models.laptop import Brand as BrandModel
    brands = BrandModel.query.filter_by(is_active=True).order_by(BrandModel.name).all()

    # Rango de precios (para slider)
    price_range = db.session.query(
        db.func.min(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        ),
        db.func.max(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        )
    ).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).first()

    min_price_available = float(price_range[0]) if price_range[0] else 0
    max_price_available = float(price_range[1]) if price_range[1] else 10000

    # ===== RENDERIZAR TEMPLATE =====

    return render_template(
        'landing/catalog.html',
        laptops=laptops,
        pagination=pagination,
        brands=brands,
        search_query=search_query,
        selected_brand=brand_id,
        min_price=min_price or min_price_available,
        max_price=max_price or max_price_available,
        min_price_available=min_price_available,
        max_price_available=max_price_available,
        category=category,
        sort_by=sort_by,
        total_products=pagination.total
    )


# ============================================
# RUTA: DETALLE DE PRODUCTO (PÚBLICO)
# ============================================

@public_bp.route('/product/<int:id>')
def product_detail(id):
    """
    Detalle público de un producto

    URL: /product/<id>

    Permite ver detalles de un producto sin autenticación.
    Si el usuario quiere comprar, se le redirige al login.

    Args:
        id: ID del laptop

    Returns:
        Template landing/product_detail.html o redirige a inventory.laptop_detail
    """

    laptop = Laptop.query.get_or_404(id)

    # Verificar que esté publicado
    if not laptop.is_published:
        from flask import abort
        abort(404)

    # Por ahora, redirigir al detalle de inventario
    # (puedes crear un template específico después)
    from flask import redirect, url_for
    return redirect(url_for('inventory.laptop_detail', id=id))


# ============================================
# API: BÚSQUEDA RÁPIDA (AUTOCOMPLETE)
# ============================================

@public_bp.route('/api/search')
def api_search():
    """
    API de búsqueda rápida para autocomplete

    URL: /api/search?q=<query>

    Returns:
        JSON con resultados de búsqueda
    """

    query = request.args.get('q', '').strip()

    if not query or len(query) < 2:
        return jsonify([])

    # Buscar en nombre y marca
    results = Laptop.query.join(Brand).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        or_(
            Laptop.display_name.ilike(f'%{query}%'),
            Brand.name.ilike(f'%{query}%')
        )
    ).limit(5).all()

    # Formatear resultados
    suggestions = [
        {
            'id': laptop.id,
            'name': laptop.display_name,
            'brand': laptop.brand.name if laptop.brand else '',
            'price': float(laptop.discount_price or laptop.sale_price),
            'image': laptop.get_cover_image_url() if hasattr(laptop, 'get_cover_image_url') else None,
            'url': f'/product/{laptop.id}'
        }
        for laptop in results
    ]

    return jsonify(suggestions)


# ============================================
# ERROR HANDLERS PARA RUTAS PÚBLICAS
# ============================================

@public_bp.errorhandler(404)
def not_found_error(error):
    """Página 404 personalizada para rutas públicas"""
    # Usar template de error genérico si no existe uno específico
    try:
        return render_template('errors/404_public.html'), 404
    except:
        return render_template('errors/404.html'), 404


@public_bp.errorhandler(500)
def internal_error(error):
    """Página 500 personalizada para rutas públicas"""
    db.session.rollback()
    # Usar template de error genérico si no existe uno específico
    try:
        return render_template('errors/500_public.html'), 500
    except:
        return render_template('errors/500.html'), 500
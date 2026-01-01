# ============================================
# RUTAS DE INVENTARIO - LAPTOPS
# ============================================
# Actualizado al nuevo modelo de datos

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.laptop import (
    Laptop, LaptopImage, Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)
from app.forms.laptop_forms import LaptopForm, FilterForm
from app.services.sku_service import SKUService
from app.services.catalog_service import CatalogService
from app.utils.decorators import admin_required
from datetime import datetime, date
from sqlalchemy import or_
import re
import os
from werkzeug.utils import secure_filename

# Configurar logging
logger = logging.getLogger(__name__)

# Crear Blueprint
inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# Configuración de imágenes
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'gif'}


# ===== UTILIDADES =====

def generate_slug(text):
    """
    Genera un slug URL-friendly a partir de texto

    Args:
        text: Texto a convertir en slug

    Returns:
        str: Slug generado
    """
    # Convertir a minusculas y reemplazar espacios
    slug = text.lower().strip()
    # Eliminar caracteres especiales, mantener solo alfanumericos y espacios
    slug = re.sub(r'[^\w\s-]', '', slug)
    # Reemplazar espacios y guiones multiples con un solo guion
    slug = re.sub(r'[-\s]+', '-', slug)
    # Eliminar guiones al inicio y final
    slug = slug.strip('-')
    return slug


def ensure_unique_slug(base_slug, laptop_id=None):
    """
    Asegura que el slug sea unico

    Args:
        base_slug: Slug base
        laptop_id: ID de la laptop actual (para edicion)

    Returns:
        str: Slug unico
    """
    slug = base_slug
    counter = 1

    while True:
        query = Laptop.query.filter_by(slug=slug)
        if laptop_id:
            query = query.filter(Laptop.id != laptop_id)

        if not query.first():
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1


def process_connectivity_ports(form_data):
    """
    Procesa los puertos de conectividad del formulario

    Args:
        form_data: Lista de puertos seleccionados

    Returns:
        dict: Diccionario con los puertos y sus cantidades
    """
    if not form_data:
        return {}

    # Convertir lista a diccionario con conteo
    ports = {}
    for port in form_data:
        ports[port] = ports.get(port, 0) + 1

    return ports


def allowed_image_file(filename):
    """
    Verifica si el archivo tiene una extensión de imagen permitida

    Args:
        filename: Nombre del archivo

    Returns:
        bool: True si es permitido, False si no
    """
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def process_laptop_images(laptop, form, is_edit=False):
    """
    Procesa las imágenes subidas en el formulario

    Args:
        laptop: Objeto Laptop
        form: Formulario LaptopForm
        is_edit: Si es edición (True) o creación (False)

    Returns:
        tuple: (success_count, error_messages)
    """
    # Lista de campos de imagen
    image_fields = [
        ('image_1', 'image_1_alt'),
        ('image_2', 'image_2_alt'),
        ('image_3', 'image_3_alt'),
        ('image_4', 'image_4_alt'),
        ('image_5', 'image_5_alt'),
        ('image_6', 'image_6_alt'),
        ('image_7', 'image_7_alt'),
        ('image_8', 'image_8_alt'),
    ]

    # Si es edición, obtener orden máximo actual
    if is_edit:
        max_order = db.session.query(db.func.max(LaptopImage.ordering)).filter_by(
            laptop_id=laptop.id
        ).scalar() or 0
    else:
        max_order = 0

    success_count = 0
    error_messages = []

    # Procesar cada campo de imagen
    for idx, (img_field, alt_field) in enumerate(image_fields, start=1):
        try:
            image_file = getattr(form, img_field).data
            alt_text = getattr(form, alt_field).data

            if not image_file or not image_file.filename:
                continue

            # Validar extensión del archivo
            if not allowed_image_file(image_file.filename):
                error_msg = f'Imagen {idx}: Formato no permitido. Use JPG, PNG, WebP o GIF.'
                error_messages.append(error_msg)
                logger.warning(f'Laptop {laptop.sku}: {error_msg}')
                continue

            # Validar tamaño del archivo
            image_file.seek(0, os.SEEK_END)
            file_size = image_file.tell()
            image_file.seek(0)  # Volver al inicio para guardar

            if file_size > MAX_IMAGE_SIZE:
                error_msg = f'Imagen {idx}: Archivo muy grande ({file_size / 1024 / 1024:.1f}MB). Máximo 5MB.'
                error_messages.append(error_msg)
                logger.warning(f'Laptop {laptop.sku}: {error_msg}')
                continue

            # Generar nombre seguro para el archivo
            filename = secure_filename(image_file.filename)
            # Agregar timestamp para evitar colisiones
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{laptop.sku}_{idx}_{timestamp}_{filename}"

            # Crear directorio si no existe
            upload_folder = os.path.join('app', 'static', 'uploads', 'laptops', str(laptop.id))
            os.makedirs(upload_folder, exist_ok=True)

            # Guardar archivo
            filepath = os.path.join(upload_folder, filename)
            image_file.save(filepath)

            # Ruta relativa para la base de datos
            relative_path = f"uploads/laptops/{laptop.id}/{filename}"

            # Determinar si es portada (la primera imagen con archivo)
            is_cover = False
            if idx == 1:
                # Si es la primera imagen, verificar si ya hay una portada
                existing_cover = LaptopImage.query.filter_by(
                    laptop_id=laptop.id,
                    is_cover=True
                ).first()
                if not existing_cover:
                    is_cover = True

            # Crear registro de imagen
            # Nota: position se incluye por compatibilidad con la BD existente
            image = LaptopImage(
                laptop_id=laptop.id,
                image_path=relative_path,
                alt_text=alt_text or f"{laptop.display_name} - imagen {idx}",
                is_cover=is_cover,
                ordering=max_order + idx,
                position=max_order + idx  # Columna requerida por la BD
            )

            db.session.add(image)
            success_count += 1
            logger.info(f'Laptop {laptop.sku}: Imagen {idx} guardada correctamente ({filename})')

        except Exception as e:
            error_msg = f'Imagen {idx}: Error al procesar - {str(e)}'
            error_messages.append(error_msg)
            logger.error(f'Laptop {laptop.sku}: {error_msg}', exc_info=True)

    return success_count, error_messages


# ===== RUTA PRINCIPAL: LISTADO DE LAPTOPS =====

@inventory_bp.route('/')
@login_required
def laptops_list():
    """
    Muestra el listado principal de laptops con filtros y busqueda
    """
    # Obtener parametros de filtros
    store_filter = request.args.get('store', type=int, default=0)
    brand_filter = request.args.get('brand', type=int, default=0)
    category_filter = request.args.get('category', '')
    processor_filter = request.args.get('processor', type=int, default=0)
    gpu_filter = request.args.get('gpu', type=int, default=0)
    screen_filter = request.args.get('screen', type=int, default=0)
    condition_filter = request.args.get('condition', '')
    supplier_filter = request.args.get('supplier', type=int, default=0)
    is_published_filter = request.args.get('is_published', '')
    is_featured_filter = request.args.get('is_featured', '')
    has_npu_filter = request.args.get('has_npu', '')
    min_price = request.args.get('min_price', type=float, default=0)
    max_price = request.args.get('max_price', type=float, default=0)
    search_query = request.args.get('q', '').strip()

    # Paginacion
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Query base
    query = Laptop.query

    # Busqueda por texto
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                Laptop.sku.ilike(search_pattern),
                Laptop.display_name.ilike(search_pattern),
                Laptop.slug.ilike(search_pattern),
                Laptop.short_description.ilike(search_pattern)
            )
        )

    # Aplicar filtros
    if store_filter and store_filter > 0:
        query = query.filter(Laptop.store_id == store_filter)

    if brand_filter and brand_filter > 0:
        query = query.filter(Laptop.brand_id == brand_filter)

    if category_filter:
        query = query.filter(Laptop.category == category_filter)

    if processor_filter and processor_filter > 0:
        query = query.filter(Laptop.processor_id == processor_filter)

    if gpu_filter and gpu_filter > 0:
        query = query.filter(Laptop.graphics_card_id == gpu_filter)

    if screen_filter and screen_filter > 0:
        query = query.filter(Laptop.screen_id == screen_filter)

    if condition_filter:
        query = query.filter(Laptop.condition == condition_filter)

    if supplier_filter and supplier_filter > 0:
        query = query.filter(Laptop.supplier_id == supplier_filter)

    if is_published_filter:
        query = query.filter(Laptop.is_published == (is_published_filter == '1'))

    if is_featured_filter:
        query = query.filter(Laptop.is_featured == (is_featured_filter == '1'))

    if has_npu_filter:
        query = query.filter(Laptop.npu == (has_npu_filter == '1'))

    if min_price > 0:
        query = query.filter(Laptop.sale_price >= min_price)

    if max_price > 0:
        query = query.filter(Laptop.sale_price <= max_price)

    # Ordenar por fecha de ingreso (mas recientes primero)
    query = query.order_by(Laptop.entry_date.desc())

    # Paginar
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    laptops = pagination.items

    # Calcular estadisticas GLOBALES (todas las laptops, no solo filtradas)
    all_laptops = Laptop.query.all()

    # VALOR TOTAL = suma del precio de venta * cantidad de TODAS las laptops
    total_inventory_value = sum(
        float(laptop.sale_price * laptop.quantity)
        for laptop in all_laptops
        if laptop.sale_price and laptop.quantity
    )

    # Contar laptops con stock bajo
    low_stock_count = len([l for l in all_laptops if l.is_low_stock])

    # Contar publicadas y destacadas
    published_count = len([l for l in all_laptops if l.is_published])
    featured_count = len([l for l in all_laptops if l.is_featured])

    stats = {
        'total': len(all_laptops),
        'total_value': total_inventory_value,
        'low_stock': low_stock_count,
        'published': published_count,
        'featured': featured_count
    }

    # Formularios
    filter_form = FilterForm()

    # Obtener rango de precios de la base de datos
    price_range = db.session.query(
        db.func.min(Laptop.sale_price),
        db.func.max(Laptop.sale_price)
    ).first()

    min_db_price = float(price_range[0]) if price_range[0] else 0
    max_db_price = float(price_range[1]) if price_range[1] else 10000

    return render_template(
        'inventory/laptops_list.html',
        laptops=laptops,
        pagination=pagination,
        stats=stats,
        filter_form=filter_form,
        min_db_price=min_db_price,
        max_db_price=max_db_price,
        search_query=search_query
    )


# ===== AGREGAR NUEVA LAPTOP =====

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def laptop_add():
    """
    Muestra el formulario y procesa la creacion de una nueva laptop
    """
    form = LaptopForm()

    if form.validate_on_submit():
        try:
            # Procesar catalogos dinamicos (crear si son strings)
            catalog_data = CatalogService.process_laptop_form_data({
                'brand_id': form.brand_id.data,
                'model_id': form.model_id.data,
                'processor_id': form.processor_id.data,
                'os_id': form.os_id.data,
                'screen_id': form.screen_id.data,
                'graphics_card_id': form.graphics_card_id.data,
                'storage_id': form.storage_id.data,
                'ram_id': form.ram_id.data,
                'store_id': form.store_id.data,
                'location_id': form.location_id.data,
                'supplier_id': form.supplier_id.data
            })

            # Generar SKU automaticamente
            sku = SKUService.generate_laptop_sku()

            # Generar slug
            base_slug = generate_slug(form.display_name.data)
            slug = form.slug.data if form.slug.data else ensure_unique_slug(base_slug)

            # Procesar puertos de conectividad
            connectivity_ports = process_connectivity_ports(form.connectivity_ports.data)

            # Crear nueva laptop
            laptop = Laptop(
                # Identificadores
                sku=sku,
                slug=slug,

                # Marketing y SEO
                display_name=form.display_name.data,
                short_description=form.short_description.data,
                long_description_html=form.long_description_html.data,
                is_published=form.is_published.data,
                is_featured=form.is_featured.data,
                seo_title=form.seo_title.data,
                seo_description=form.seo_description.data,

                # Relaciones
                brand_id=catalog_data['brand_id'],
                model_id=catalog_data['model_id'],
                processor_id=catalog_data['processor_id'],
                os_id=catalog_data['os_id'],
                screen_id=catalog_data['screen_id'],
                graphics_card_id=catalog_data['graphics_card_id'],
                storage_id=catalog_data['storage_id'],
                ram_id=catalog_data['ram_id'],
                store_id=catalog_data['store_id'],
                location_id=catalog_data.get('location_id'),
                supplier_id=catalog_data.get('supplier_id'),

                # Detalles tecnicos
                npu=form.npu.data,
                storage_upgradeable=form.storage_upgradeable.data,
                ram_upgradeable=form.ram_upgradeable.data,
                keyboard_layout=form.keyboard_layout.data,
                connectivity_ports=connectivity_ports,

                # Estado y categoria
                category=form.category.data,
                condition=form.condition.data,

                # Financieros
                purchase_cost=form.purchase_cost.data,
                sale_price=form.sale_price.data,
                discount_price=form.discount_price.data if form.discount_price.data else None,
                tax_percent=form.tax_percent.data if form.tax_percent.data else 0,

                # Inventario
                quantity=form.quantity.data,
                reserved_quantity=form.reserved_quantity.data if form.reserved_quantity.data else 0,
                min_alert=form.min_alert.data,

                # Timestamps
                entry_date=date.today(),  # Fecha automatica de ingreso
                sale_date=None,  # Se establece cuando se vende
                internal_notes=form.internal_notes.data,

                # Auditoria
                created_by_id=current_user.id
            )

            # Guardar en base de datos
            db.session.add(laptop)
            db.session.commit()

            # Procesar imágenes si se subieron
            img_success, img_errors = process_laptop_images(laptop, form, is_edit=False)
            db.session.commit()

            # Mensaje de éxito
            if img_success > 0:
                flash(f'✅ Laptop {sku} agregada con {img_success} imagen(es)', 'success')
            else:
                flash(f'✅ Laptop {sku} agregada exitosamente', 'success')

            # Mostrar errores de imágenes si los hay
            for error in img_errors:
                flash(f'⚠️ {error}', 'warning')

            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al agregar laptop: {str(e)}', exc_info=True)
            flash(f'❌ Error al agregar laptop: {str(e)}', 'error')

    # Si hay errores en el formulario
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')

    return render_template('inventory/laptop_form.html', form=form, mode='add')


# ===== VER DETALLE DE LAPTOP =====

@inventory_bp.route('/<int:id>')
@login_required
def laptop_detail(id):
    """
    Muestra el detalle completo de una laptop
    """
    laptop = Laptop.query.get_or_404(id)

    # Obtener laptops similares (misma categoria y marca)
    similar_laptops = Laptop.query.filter(
        Laptop.category == laptop.category,
        Laptop.brand_id == laptop.brand_id,
        Laptop.id != laptop.id,
        Laptop.is_published == True
    ).limit(5).all()

    # Obtener imagenes de la laptop
    images = laptop.images.order_by(LaptopImage.ordering).all()

    # Imagen de portada
    cover_image = laptop.images.filter_by(is_cover=True).first()

    return render_template(
        'inventory/laptop_detail.html',
        laptop=laptop,
        similar_laptops=similar_laptops,
        images=images,
        cover_image=cover_image
    )


# ===== VER LAPTOP POR SLUG (para URLs publicas) =====

@inventory_bp.route('/p/<slug>')
def laptop_by_slug(slug):
    """
    Muestra el detalle de una laptop por su slug (URL publica)
    """
    laptop = Laptop.query.filter_by(slug=slug, is_published=True).first_or_404()

    # Obtener laptops similares
    similar_laptops = Laptop.query.filter(
        Laptop.category == laptop.category,
        Laptop.brand_id == laptop.brand_id,
        Laptop.id != laptop.id,
        Laptop.is_published == True
    ).limit(5).all()

    # Obtener imagenes
    images = laptop.images.order_by(LaptopImage.ordering).all()
    cover_image = laptop.images.filter_by(is_cover=True).first()

    return render_template(
        'inventory/laptop_public.html',
        laptop=laptop,
        similar_laptops=similar_laptops,
        images=images,
        cover_image=cover_image
    )


# ===== ELIMINAR LAPTOP =====

@inventory_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def laptop_delete(id):
    """
    Elimina una laptop del inventario
    """
    laptop = Laptop.query.get_or_404(id)

    try:
        # Obtener y eliminar imágenes asociadas
        images = laptop.images.all()

        # Eliminar archivos de imágenes del sistema de archivos
        for image in images:
            try:
                filepath = os.path.join('app', 'static', image.image_path)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f'Laptop {laptop.sku}: Imagen eliminada {image.image_path}')
            except Exception as e:
                logger.error(f'Error al eliminar imagen {image.image_path}: {str(e)}')

        # Eliminar directorio de imágenes si existe
        image_folder = os.path.join('app', 'static', 'uploads', 'laptops', str(laptop.id))
        if os.path.exists(image_folder):
            try:
                os.rmdir(image_folder)
                logger.info(f'Laptop {laptop.sku}: Directorio de imágenes eliminado')
            except Exception as e:
                logger.error(f'Error al eliminar directorio de imágenes: {str(e)}')

        # Eliminar la laptop de la base de datos
        db.session.delete(laptop)
        db.session.commit()

        flash(f'✅ Laptop {laptop.sku} eliminada exitosamente', 'success')
        return redirect(url_for('inventory.laptops_list'))

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al eliminar laptop {laptop.sku}: {str(e)}', exc_info=True)
        flash(f'❌ Error al eliminar laptop: {str(e)}', 'error')
        return redirect(url_for('inventory.laptop_detail', id=id))


# ===== Duplicar LAPTOP =====

@inventory_bp.route('/inventory/<int:id>/duplicate', methods=['POST'])
@login_required
def laptop_duplicate(id):
    original = Laptop.query.get_or_404(id)

    duplicate = Laptop(
        sku=f"{original.sku}-COPY",
        display_name=f"{original.display_name} (Copia)",
        short_description=original.short_description,
        long_description_html=original.long_description_html,
        category=original.category,
        brand_id=original.brand_id,
        model_id=original.model_id,
        processor_id=original.processor_id,
        ram_id=original.ram_id,
        storage_id=original.storage_id,
        sale_price=original.sale_price,
        is_published=False,
        created_by_id=current_user.id
    )

    db.session.add(duplicate)
    db.session.commit()

    flash('Laptop duplicada correctamente', 'success')
    return redirect(url_for('inventory.laptop_edit', id=duplicate.id))


# ===== EDITAR LAPTOP =====

@inventory_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def laptop_edit(id):
    """
    Edita una laptop existente
    """
    laptop = Laptop.query.get_or_404(id)
    form = LaptopForm(obj=laptop)

    # Pre-poblar connectivity_ports si existe
    if request.method == 'GET' and laptop.connectivity_ports:
        form.connectivity_ports.data = list(laptop.connectivity_ports.keys())

    if form.validate_on_submit():
        try:
            # Procesar catalogos dinamicos
            catalog_data = CatalogService.process_laptop_form_data({
                'brand_id': form.brand_id.data,
                'model_id': form.model_id.data,
                'processor_id': form.processor_id.data,
                'os_id': form.os_id.data,
                'screen_id': form.screen_id.data,
                'graphics_card_id': form.graphics_card_id.data,
                'storage_id': form.storage_id.data,
                'ram_id': form.ram_id.data,
                'store_id': form.store_id.data,
                'location_id': form.location_id.data,
                'supplier_id': form.supplier_id.data
            })

            # Actualizar slug si cambio el nombre
            if form.slug.data:
                laptop.slug = ensure_unique_slug(form.slug.data, laptop.id)
            elif form.display_name.data != laptop.display_name:
                base_slug = generate_slug(form.display_name.data)
                laptop.slug = ensure_unique_slug(base_slug, laptop.id)

            # Procesar puertos de conectividad
            connectivity_ports = process_connectivity_ports(form.connectivity_ports.data)

            # Actualizar campos
            # Marketing y SEO
            laptop.display_name = form.display_name.data
            laptop.short_description = form.short_description.data
            laptop.long_description_html = form.long_description_html.data
            laptop.is_published = form.is_published.data
            laptop.is_featured = form.is_featured.data
            laptop.seo_title = form.seo_title.data
            laptop.seo_description = form.seo_description.data

            # Relaciones
            laptop.brand_id = catalog_data['brand_id']
            laptop.model_id = catalog_data['model_id']
            laptop.processor_id = catalog_data['processor_id']
            laptop.os_id = catalog_data['os_id']
            laptop.screen_id = catalog_data['screen_id']
            laptop.graphics_card_id = catalog_data['graphics_card_id']
            laptop.storage_id = catalog_data['storage_id']
            laptop.ram_id = catalog_data['ram_id']
            laptop.store_id = catalog_data['store_id']
            laptop.location_id = catalog_data.get('location_id')
            laptop.supplier_id = catalog_data.get('supplier_id')

            # Detalles tecnicos
            laptop.npu = form.npu.data
            laptop.storage_upgradeable = form.storage_upgradeable.data
            laptop.ram_upgradeable = form.ram_upgradeable.data
            laptop.keyboard_layout = form.keyboard_layout.data
            laptop.connectivity_ports = connectivity_ports

            # Estado y categoria
            laptop.category = form.category.data
            laptop.condition = form.condition.data

            # Financieros
            laptop.purchase_cost = form.purchase_cost.data
            laptop.sale_price = form.sale_price.data
            laptop.discount_price = form.discount_price.data if form.discount_price.data else None
            laptop.tax_percent = form.tax_percent.data if form.tax_percent.data else 0

            # Inventario
            laptop.quantity = form.quantity.data
            laptop.reserved_quantity = form.reserved_quantity.data if form.reserved_quantity.data else 0
            laptop.min_alert = form.min_alert.data

            # Notas
            laptop.internal_notes = form.internal_notes.data
            # entry_date no se modifica (se establecio al crear)
            # sale_date se establece desde otro proceso cuando se vende

            laptop.updated_at = datetime.utcnow()

            db.session.commit()

            # Procesar imágenes si se subieron
            img_success, img_errors = process_laptop_images(laptop, form, is_edit=True)
            db.session.commit()

            # Mensaje de éxito
            if img_success > 0:
                flash(f'✅ Laptop {laptop.sku} actualizada con {img_success} nueva(s) imagen(es)', 'success')
            else:
                flash(f'✅ Laptop {laptop.sku} actualizada exitosamente', 'success')

            # Mostrar errores de imágenes si los hay
            for error in img_errors:
                flash(f'⚠️ {error}', 'warning')

            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al actualizar laptop {laptop.sku}: {str(e)}', exc_info=True)
            flash(f'❌ Error al actualizar laptop: {str(e)}', 'error')

    # Si hay errores en el formulario
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')

    return render_template('inventory/laptop_form.html', form=form, mode='edit', laptop=laptop)
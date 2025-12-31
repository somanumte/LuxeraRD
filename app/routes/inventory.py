# ============================================
# RUTAS DE INVENTARIO - LAPTOPS
# ============================================
# Actualizado al nuevo modelo de datos

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.laptop import (
    Laptop, LaptopImage, Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)
from app.forms.laptop_forms import LaptopForm, LaptopImageForm, QuickSearchForm, FilterForm
from app.services.sku_service import SKUService
from app.services.catalog_service import CatalogService
from app.utils.decorators import admin_required
from datetime import datetime, date
from sqlalchemy import or_
import re
import os
from werkzeug.utils import secure_filename

# Crear Blueprint
inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


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

            flash(f'âœ… Laptop {sku} agregada exitosamente', 'success')
            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
            flash(f'âŒ Error al agregar laptop: {str(e)}', 'error')

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

            flash(f'âœ… Laptop {laptop.sku} actualizada exitosamente', 'success')
            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
            flash(f'âŒ Error al actualizar laptop: {str(e)}', 'error')

    # Si hay errores en el formulario
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')

    return render_template('inventory/laptop_form.html', form=form, mode='edit', laptop=laptop)


# ===== ELIMINAR LAPTOP =====

@inventory_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def laptop_delete(id):
    """
    Elimina una laptop (borrado fisico)
    """
    laptop = Laptop.query.get_or_404(id)
    sku = laptop.sku

    try:
        # Las imagenes se eliminaran automaticamente por cascade
        db.session.delete(laptop)
        db.session.commit()
        flash(f'ðŸ—‘ï¸ Laptop {sku} eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'âŒ Error al eliminar laptop: {str(e)}', 'error')

    return redirect(url_for('inventory.laptops_list'))


# ===== DUPLICAR LAPTOP =====

@inventory_bp.route('/<int:id>/duplicate', methods=['POST'])
@login_required
@admin_required
def laptop_duplicate(id):
    """
    Crea una copia de una laptop existente
    """
    original = Laptop.query.get_or_404(id)

    try:
        # Generar nuevo SKU
        new_sku = SKUService.generate_laptop_sku()

        # Generar nuevo slug
        base_slug = generate_slug(f"{original.display_name} copia")
        new_slug = ensure_unique_slug(base_slug)

        # Crear copia
        duplicate = Laptop(
            sku=new_sku,
            slug=new_slug,
            display_name=f"{original.display_name} (Copia)",
            short_description=original.short_description,
            long_description_html=original.long_description_html,
            is_published=False,  # No publicar automaticamente
            is_featured=False,
            seo_title=original.seo_title,
            seo_description=original.seo_description,
            brand_id=original.brand_id,
            model_id=original.model_id,
            processor_id=original.processor_id,
            os_id=original.os_id,
            screen_id=original.screen_id,
            graphics_card_id=original.graphics_card_id,
            storage_id=original.storage_id,
            ram_id=original.ram_id,
            store_id=original.store_id,
            location_id=original.location_id,
            supplier_id=original.supplier_id,
            npu=original.npu,
            storage_upgradeable=original.storage_upgradeable,
            ram_upgradeable=original.ram_upgradeable,
            keyboard_layout=original.keyboard_layout,
            connectivity_ports=original.connectivity_ports.copy() if original.connectivity_ports else {},
            category=original.category,
            condition=original.condition,
            purchase_cost=original.purchase_cost,
            sale_price=original.sale_price,
            discount_price=original.discount_price,
            tax_percent=original.tax_percent,
            quantity=1,  # Nueva laptop, cantidad 1
            reserved_quantity=0,
            min_alert=original.min_alert,
            entry_date=date.today(),  # Fecha actual
            internal_notes=f"Duplicado de {original.sku}",
            created_by_id=current_user.id
        )

        db.session.add(duplicate)
        db.session.commit()

        flash(f'âœ… Laptop duplicada con SKU: {new_sku}', 'success')
        return redirect(url_for('inventory.laptop_detail', id=duplicate.id))

    except Exception as e:
        db.session.rollback()
        flash(f'âŒ Error al duplicar laptop: {str(e)}', 'error')
        return redirect(url_for('inventory.laptop_detail', id=id))


# ===== GESTIÃ“N DE IMÃGENES =====

@inventory_bp.route('/<int:id>/images', methods=['GET', 'POST'])
@login_required
@admin_required
def laptop_images(id):
    """
    Gestiona las imagenes de una laptop
    """
    laptop = Laptop.query.get_or_404(id)
    form = LaptopImageForm()

    if form.validate_on_submit():
        try:
            file = form.image.data
            if file:
                # Generar nombre seguro para el archivo
                filename = secure_filename(file.filename)
                # Agregar timestamp para evitar colisiones
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{laptop.sku}_{timestamp}_{filename}"

                # Crear directorio si no existe
                upload_folder = os.path.join('app', 'static', 'uploads', 'laptops', str(laptop.id))
                os.makedirs(upload_folder, exist_ok=True)

                # Guardar archivo
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)

                # Ruta relativa para la base de datos
                relative_path = f"uploads/laptops/{laptop.id}/{filename}"

                # Si es portada, quitar portada de otras imagenes
                if form.is_cover.data:
                    LaptopImage.query.filter_by(laptop_id=laptop.id, is_cover=True).update({'is_cover': False})

                # Obtener siguiente orden
                max_order = db.session.query(db.func.max(LaptopImage.ordering)).filter_by(
                    laptop_id=laptop.id
                ).scalar() or 0

                # Crear registro de imagen
                image = LaptopImage(
                    laptop_id=laptop.id,
                    image_path=relative_path,
                    alt_text=form.alt_text.data,
                    is_cover=form.is_cover.data,
                    ordering=max_order + 1
                )

                db.session.add(image)
                db.session.commit()

                flash('âœ… Imagen agregada exitosamente', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'âŒ Error al subir imagen: {str(e)}', 'error')

    images = laptop.images.order_by(LaptopImage.ordering).all()

    return render_template(
        'inventory/laptop_images.html',
        laptop=laptop,
        form=form,
        images=images
    )


@inventory_bp.route('/images/<int:image_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_image(image_id):
    """
    Elimina una imagen de laptop
    """
    image = LaptopImage.query.get_or_404(image_id)
    laptop_id = image.laptop_id

    try:
        # Eliminar archivo fisico
        filepath = os.path.join('app', 'static', image.image_path)
        if os.path.exists(filepath):
            os.remove(filepath)

        # Eliminar registro
        db.session.delete(image)
        db.session.commit()

        flash('âœ… Imagen eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'âŒ Error al eliminar imagen: {str(e)}', 'error')

    return redirect(url_for('inventory.laptop_images', id=laptop_id))


@inventory_bp.route('/images/<int:image_id>/set-cover', methods=['POST'])
@login_required
@admin_required
def set_cover_image(image_id):
    """
    Establece una imagen como portada
    """
    image = LaptopImage.query.get_or_404(image_id)

    try:
        # Quitar portada de otras imagenes
        LaptopImage.query.filter_by(laptop_id=image.laptop_id, is_cover=True).update({'is_cover': False})

        # Establecer esta como portada
        image.is_cover = True
        db.session.commit()

        flash('âœ… Imagen de portada actualizada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'âŒ Error al actualizar portada: {str(e)}', 'error')

    return redirect(url_for('inventory.laptop_images', id=image.laptop_id))


# ===== ACCIONES MASIVAS =====

@inventory_bp.route('/bulk/publish', methods=['POST'])
@login_required
@admin_required
def bulk_publish():
    """
    Publica multiples laptops
    """
    laptop_ids = request.form.getlist('laptop_ids')

    if not laptop_ids:
        flash('âŒ No se seleccionaron laptops', 'error')
        return redirect(url_for('inventory.laptops_list'))

    try:
        Laptop.query.filter(Laptop.id.in_(laptop_ids)).update(
            {'is_published': True, 'updated_at': datetime.utcnow()},
            synchronize_session=False
        )
        db.session.commit()
        flash(f'âœ… {len(laptop_ids)} laptops publicadas', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'âŒ Error: {str(e)}', 'error')

    return redirect(url_for('inventory.laptops_list'))


@inventory_bp.route('/bulk/unpublish', methods=['POST'])
@login_required
@admin_required
def bulk_unpublish():
    """
    Despublica multiples laptops
    """
    laptop_ids = request.form.getlist('laptop_ids')

    if not laptop_ids:
        flash('âŒ No se seleccionaron laptops', 'error')
        return redirect(url_for('inventory.laptops_list'))

    try:
        Laptop.query.filter(Laptop.id.in_(laptop_ids)).update(
            {'is_published': False, 'updated_at': datetime.utcnow()},
            synchronize_session=False
        )
        db.session.commit()
        flash(f'âœ… {len(laptop_ids)} laptops despublicadas', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'âŒ Error: {str(e)}', 'error')

    return redirect(url_for('inventory.laptops_list'))
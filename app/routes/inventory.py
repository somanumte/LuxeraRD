# ============================================
# RUTAS DE INVENTARIO - LAPTOPS
# ============================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.laptop import Laptop, Brand, LaptopModel, Processor, OperatingSystem, Screen, GraphicsCard, StorageType, \
    RAMType, Store, Location
from app.forms.laptop_forms import LaptopForm, QuickSearchForm, FilterForm
from app.services.sku_service import SKUService
from app.services.financial_service import FinancialService
from app.services.inventory_service import InventoryService
from app.services.ai_service import AIService
from app.services.catalog_service import CatalogService
from app.utils.decorators import admin_required
from datetime import datetime
from sqlalchemy import or_

# Crear Blueprint
inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


# ===== RUTA PRINCIPAL: LISTADO DE LAPTOPS =====

@inventory_bp.route('/')
@login_required
def laptops_list():
    """
    Muestra el listado principal de laptops con filtros y búsqueda
    """
    # Obtener parámetros de filtros
    store_filter = request.args.get('store', type=int, default=0)
    brand_filter = request.args.get('brand', type=int, default=0)
    category_filter = request.args.get('category', '')
    processor_filter = request.args.get('processor', type=int, default=0)
    gpu_filter = request.args.get('gpu', type=int, default=0)
    screen_filter = request.args.get('screen', type=int, default=0)
    condition_filter = request.args.get('condition', '')
    min_price = request.args.get('min_price', type=float, default=0)
    max_price = request.args.get('max_price', type=float, default=0)

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Query base
    query = Laptop.query

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

    if min_price > 0:
        query = query.filter(Laptop.sale_price >= min_price)

    if max_price > 0:
        query = query.filter(Laptop.sale_price <= max_price)

    # Ordenar por fecha de ingreso (más recientes primero)
    query = query.order_by(Laptop.entry_date.desc())

    # Paginar
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    laptops = pagination.items

    # Calcular estadísticas GLOBALES (todas las laptops, no solo filtradas)
    all_laptops = Laptop.query.all()

    # VALOR TOTAL = suma del precio de venta * cantidad de TODAS las laptops
    total_inventory_value = sum(
        float(laptop.sale_price * laptop.quantity)
        for laptop in all_laptops
        if laptop.sale_price and laptop.quantity
    )

    stats = {
        'total': len(all_laptops),
        'total_value': total_inventory_value,
        'low_stock': len([l for l in all_laptops if l.quantity <= l.min_alert]),
        'slow_rotation': len([l for l in all_laptops if l.rotation_status == 'slow'])
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
        max_db_price=max_db_price
    )


# ===== AGREGAR NUEVA LAPTOP =====

@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def laptop_add():
    """
    Muestra el formulario y procesa la creación de una nueva laptop
    """
    form = LaptopForm()

    if form.validate_on_submit():
        try:
            # Procesar catálogos dinámicos (crear si son strings)
            catalog_data = CatalogService.process_laptop_form_data({
                'brand_id': form.brand_id.data,
                'model_id': form.model_id.data,
                'processor_id': form.processor_id.data,
                'os_id': form.os_id.data,
                'screen_id': form.screen_id.data,
                'graphics_card_id': form.graphics_card_id.data,
                'storage_id': form.storage_id.data,
                'ram_id': form.ram_id.data
            })

            # Generar SKU automáticamente
            sku = SKUService.generate_laptop_sku()

            # Calcular campos financieros
            financial_data = FinancialService.calculate_margin(
                form.purchase_cost.data,
                form.sale_price.data
            )

            # Crear nueva laptop
            laptop = Laptop(
                sku=sku,
                brand_id=catalog_data['brand_id'],
                model_id=catalog_data['model_id'],
                processor_id=catalog_data['processor_id'],
                os_id=catalog_data['os_id'],
                screen_id=catalog_data['screen_id'],
                graphics_card_id=catalog_data['graphics_card_id'],
                storage_id=catalog_data['storage_id'],
                storage_upgradeable=form.storage_upgradeable.data,
                ram_id=catalog_data['ram_id'],
                ram_upgradeable=form.ram_upgradeable.data,
                npu=form.npu.data,
                purchase_cost=form.purchase_cost.data,
                sale_price=form.sale_price.data,
                total_cost=financial_data['total_cost'],
                gross_profit=financial_data['gross_profit'],
                margin_percentage=financial_data['margin_percentage'],
                quantity=form.quantity.data,
                min_alert=form.min_alert.data,
                category=form.category.data,
                store_id=form.store_id.data if form.store_id.data != 0 else None,
                location_id=form.location_id.data if form.location_id.data != 0 else None,
                condition=form.condition.data,
                aesthetic_grade=form.aesthetic_grade.data if form.aesthetic_grade.data else None,
                entry_date=form.entry_date.data,
                sale_date=form.sale_date.data,
                notes=form.notes.data,
                created_by_id=current_user.id
            )

            # Calcular días en inventario
            laptop.days_in_inventory = InventoryService.calculate_days_in_inventory(
                laptop.entry_date,
                laptop.sale_date
            )

            # Determinar estado de rotación
            laptop.rotation_status = InventoryService.determine_rotation_status(
                laptop.days_in_inventory
            )

            # Generar recomendaciones IA
            recommendations = AIService.generate_recommendations(laptop)
            laptop.ai_recommendation = AIService.format_recommendations_text(recommendations)

            # Guardar en base de datos
            db.session.add(laptop)
            db.session.commit()

            flash(f'✅ Laptop {sku} agregada exitosamente', 'success')
            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
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

    # Recalcular datos en tiempo real
    laptop.days_in_inventory = InventoryService.calculate_days_in_inventory(
        laptop.entry_date,
        laptop.sale_date
    )
    laptop.rotation_status = InventoryService.determine_rotation_status(
        laptop.days_in_inventory
    )

    # Regenerar recomendaciones
    recommendations = AIService.generate_recommendations(laptop)
    laptop.ai_recommendation = AIService.format_recommendations_text(recommendations)

    # Obtener laptops similares (misma categoría y marca)
    similar_laptops = Laptop.query.filter(
        Laptop.category == laptop.category,
        Laptop.brand_id == laptop.brand_id,
        Laptop.id != laptop.id
    ).limit(5).all()

    # Análisis de precios
    price_analysis = AIService.analyze_pricing_strategy(laptop, similar_laptops)

    return render_template(
        'inventory/laptop_detail.html',
        laptop=laptop,
        recommendations=recommendations,
        similar_laptops=similar_laptops,
        price_analysis=price_analysis
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

    if form.validate_on_submit():
        try:
            # Procesar catálogos dinámicos (crear si son strings)
            catalog_data = CatalogService.process_laptop_form_data({
                'brand_id': form.brand_id.data,
                'model_id': form.model_id.data,
                'processor_id': form.processor_id.data,
                'os_id': form.os_id.data,
                'screen_id': form.screen_id.data,
                'graphics_card_id': form.graphics_card_id.data,
                'storage_id': form.storage_id.data,
                'ram_id': form.ram_id.data
            })

            # Actualizar campos
            laptop.brand_id = catalog_data['brand_id']
            laptop.model_id = catalog_data['model_id']
            laptop.processor_id = catalog_data['processor_id']
            laptop.os_id = catalog_data['os_id']
            laptop.screen_id = catalog_data['screen_id']
            laptop.graphics_card_id = catalog_data['graphics_card_id']
            laptop.storage_id = catalog_data['storage_id']
            laptop.storage_upgradeable = form.storage_upgradeable.data
            laptop.ram_id = catalog_data['ram_id']
            laptop.ram_upgradeable = form.ram_upgradeable.data
            laptop.npu = form.npu.data
            laptop.purchase_cost = form.purchase_cost.data
            laptop.sale_price = form.sale_price.data
            laptop.quantity = form.quantity.data
            laptop.min_alert = form.min_alert.data
            laptop.category = form.category.data
            laptop.store_id = form.store_id.data if form.store_id.data != 0 else None
            laptop.location_id = form.location_id.data if form.location_id.data != 0 else None
            laptop.condition = form.condition.data
            laptop.aesthetic_grade = form.aesthetic_grade.data if form.aesthetic_grade.data else None
            laptop.entry_date = form.entry_date.data
            laptop.sale_date = form.sale_date.data
            laptop.notes = form.notes.data

            # Recalcular campos financieros
            financial_data = FinancialService.calculate_margin(
                laptop.purchase_cost,
                laptop.sale_price
            )
            laptop.total_cost = financial_data['total_cost']
            laptop.gross_profit = financial_data['gross_profit']
            laptop.margin_percentage = financial_data['margin_percentage']

            # Recalcular rotación
            laptop.days_in_inventory = InventoryService.calculate_days_in_inventory(
                laptop.entry_date,
                laptop.sale_date
            )
            laptop.rotation_status = InventoryService.determine_rotation_status(
                laptop.days_in_inventory
            )

            # Regenerar recomendaciones
            recommendations = AIService.generate_recommendations(laptop)
            laptop.ai_recommendation = AIService.format_recommendations_text(recommendations)

            laptop.updated_at = datetime.utcnow()

            db.session.commit()

            flash(f'✅ Laptop {laptop.sku} actualizada exitosamente', 'success')
            return redirect(url_for('inventory.laptop_detail', id=laptop.id))

        except Exception as e:
            db.session.rollback()
            flash(f'❌ Error al actualizar laptop: {str(e)}', 'error')

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
    Elimina una laptop (borrado físico)
    """
    laptop = Laptop.query.get_or_404(id)
    sku = laptop.sku

    try:
        db.session.delete(laptop)
        db.session.commit()
        flash(f'🗑️ Laptop {sku} eliminada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al eliminar laptop: {str(e)}', 'error')

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

        # Crear copia
        duplicate = Laptop(
            sku=new_sku,
            brand_id=original.brand_id,
            model_id=original.model_id,
            processor_id=original.processor_id,
            os_id=original.os_id,
            screen_id=original.screen_id,
            graphics_card_id=original.graphics_card_id,
            storage_id=original.storage_id,
            storage_upgradeable=original.storage_upgradeable,
            ram_id=original.ram_id,
            ram_upgradeable=original.ram_upgradeable,
            npu=original.npu,
            purchase_cost=original.purchase_cost,
            sale_price=original.sale_price,
            total_cost=original.total_cost,
            gross_profit=original.gross_profit,
            margin_percentage=original.margin_percentage,
            quantity=1,  # Nueva laptop, cantidad 1
            min_alert=original.min_alert,
            category=original.category,
            store_id=original.store_id,
            location_id=original.location_id,
            condition=original.condition,
            aesthetic_grade=original.aesthetic_grade,
            entry_date=datetime.utcnow(),  # Fecha actual
            notes=f"Duplicado de {original.sku}",
            created_by_id=current_user.id
        )

        # Recalcular campos
        duplicate.days_in_inventory = 0
        duplicate.rotation_status = 'fast'

        recommendations = AIService.generate_recommendations(duplicate)
        duplicate.ai_recommendation = AIService.format_recommendations_text(recommendations)

        db.session.add(duplicate)
        db.session.commit()

        flash(f'✅ Laptop duplicada con SKU: {new_sku}', 'success')
        return redirect(url_for('inventory.laptop_detail', id=duplicate.id))

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Error al duplicar laptop: {str(e)}', 'error')
        return redirect(url_for('inventory.laptop_detail', id=id))
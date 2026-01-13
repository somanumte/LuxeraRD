# ============================================
# RUTAS DE FACTURACIÓN
# ============================================
# Actualizado para manejar NCF con secuencias independientes por tipo
# Según regulaciones DGII República Dominicana

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.invoice import (
    Invoice, InvoiceItem, InvoiceSettings, NCFSequence,
    NCF_TYPES, NCF_SALES_TYPES, get_ncf_types_for_sales,
    suggest_ncf_type_for_customer, initialize_default_ncf_sequences
)
from app.models.customer import Customer
from app.models.laptop import Laptop
from app.services.invoice_inventory_service import InvoiceInventoryService
from datetime import datetime, date
from decimal import Decimal
import csv
import io
import json
from sqlalchemy import or_, and_
import os
from werkzeug.utils import secure_filename
from flask import current_app

# ============================================
# CREAR BLUEPRINT DE FACTURACION
# ============================================

invoices_bp = Blueprint(
    'invoices',
    __name__,
    url_prefix='/invoices'
)


# ============================================
# RUTA: LISTA DE FACTURAS
# ============================================

@invoices_bp.route('/')
@login_required
def invoices_list():
    """
    Lista de todas las facturas con búsqueda y filtros

    URL: /invoices/
    """
    # Parámetros de búsqueda
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    ncf_type_filter = request.args.get('ncf_type', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    # Query base
    query = Invoice.query

    # Aplicar búsqueda
    if search_query:
        query = query.join(Customer).filter(
            or_(
                Invoice.invoice_number.ilike(f'%{search_query}%'),
                Invoice.ncf.ilike(f'%{search_query}%'),
                Customer.first_name.ilike(f'%{search_query}%'),
                Customer.last_name.ilike(f'%{search_query}%'),
                Customer.company_name.ilike(f'%{search_query}%'),
                Customer.id_number.ilike(f'%{search_query}%')
            )
        )

    # Aplicar filtro de estado
    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    # Aplicar filtro de tipo de NCF
    if ncf_type_filter:
        query = query.filter(Invoice.ncf_type == ncf_type_filter)

    # Aplicar filtro de fechas
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date >= date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date <= date_to_obj)
        except ValueError:
            pass

    # Ordenar por fecha descendente
    invoices = query.order_by(Invoice.invoice_date.desc(), Invoice.id.desc()).all()

    # Calcular estadísticas
    total_invoices = len(invoices)
    total_amount = sum(inv.total for inv in invoices)

    # Contar por estado
    status_counts = {
        'draft': sum(1 for inv in invoices if inv.status == 'draft'),
        'issued': sum(1 for inv in invoices if inv.status == 'issued'),
        'paid': sum(1 for inv in invoices if inv.status == 'paid'),
        'cancelled': sum(1 for inv in invoices if inv.status == 'cancelled'),
        'overdue': sum(1 for inv in invoices if inv.is_overdue)
    }

    # Contar por tipo de NCF
    ncf_type_counts = {}
    for ncf_type in NCF_SALES_TYPES:
        ncf_type_counts[ncf_type] = sum(1 for inv in invoices if inv.ncf_type == ncf_type)

    return render_template(
        'invoices/invoices_list.html',
        invoices=invoices,
        search_query=search_query,
        status_filter=status_filter,
        ncf_type_filter=ncf_type_filter,
        date_from=date_from,
        date_to=date_to,
        total_invoices=total_invoices,
        total_amount=total_amount,
        status_counts=status_counts,
        ncf_type_counts=ncf_type_counts,
        ncf_types=NCF_TYPES
    )


# ============================================
# RUTA: NUEVA FACTURA (FORMULARIO)
# ============================================

@invoices_bp.route('/new', methods=['GET'])
@login_required
def invoice_new():
    """
    Mostrar formulario para crear nueva factura

    URL: /invoices/new
    """
    # Obtener configuración
    settings = InvoiceSettings.get_settings()

    # Inicializar secuencias de NCF si no existen
    initialize_default_ncf_sequences()

    # Obtener clientes activos
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.first_name, Customer.company_name).all()

    # Obtener laptops disponibles y convertir a diccionarios para JSON
    laptops_query = Laptop.query.filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).order_by(Laptop.display_name).all()

    # Serializar laptops a diccionarios con todas las relaciones
    laptops = [laptop.to_dict(include_relationships=True) for laptop in laptops_query]

    # Obtener tipos de NCF disponibles para ventas
    ncf_types_list = get_ncf_types_for_sales()

    # Obtener secuencias activas con su estado
    ncf_sequences = {}
    for ncf_type in NCF_SALES_TYPES:
        sequence = NCFSequence.get_or_create(ncf_type)
        ncf_sequences[ncf_type] = {
            'next_preview': sequence.next_ncf_preview,
            'is_valid': sequence.is_valid,
            'is_expired': sequence.is_expired,
            'is_exhausted': sequence.is_exhausted,
            'remaining': sequence.remaining_count,
            'valid_until': sequence.valid_until.strftime('%d/%m/%Y') if sequence.valid_until else None
        }

    return render_template(
        'invoices/invoice_form.html',
        settings=settings,
        customers=customers,
        laptops=laptops,
        invoice=None,
        is_edit=False,
        ncf_types=ncf_types_list,
        ncf_sequences=ncf_sequences,
        default_ncf_type='B02'
    )


# ============================================
# RUTA: CREAR FACTURA (POST)
# ============================================

@invoices_bp.route('/create', methods=['POST'])
@login_required
def invoice_create():
    """
    Procesar creación de nueva factura

    URL: /invoices/create (POST)
    """
    try:
        # Obtener datos del formulario
        customer_id = request.form.get('customer_id')
        invoice_date = request.form.get('invoice_date')
        due_date = request.form.get('due_date')
        payment_method = request.form.get('payment_method', 'cash')
        notes = request.form.get('notes', '').strip()
        terms = request.form.get('terms', '').strip()
        status = request.form.get('status', 'draft')

        # ===== NUEVO: Obtener tipo de NCF y NCF manual =====
        ncf_type = request.form.get('ncf_type', '').strip().upper()
        manual_ncf = request.form.get('manual_ncf', '').strip().upper()
        use_manual_ncf = request.form.get('use_manual_ncf') == 'true'

        # Validaciones
        if not customer_id:
            flash('Debes seleccionar un cliente', 'error')
            return redirect(url_for('invoices.invoice_new'))

        customer = Customer.query.get_or_404(int(customer_id))

        # ===== LÓGICA DE ASIGNACIÓN DE NCF =====

        # Si no se especificó tipo de NCF, asignar automáticamente según el cliente
        if not ncf_type:
            ncf_type = Invoice.get_suggested_ncf_type(customer)

        # Validar que el tipo de NCF sea válido para ventas
        if ncf_type not in NCF_SALES_TYPES:
            flash(f'El tipo de comprobante "{ncf_type}" no es válido para facturas de venta. '
                  f'Tipos válidos: {", ".join(NCF_SALES_TYPES)}', 'error')
            return redirect(url_for('invoices.invoice_new'))

        # Validar que el NCF sea apropiado para el cliente (genera advertencias)
        is_valid, warning_msg = Invoice.validate_ncf_for_customer(ncf_type, customer)
        if not is_valid:
            flash(warning_msg, 'error')
            return redirect(url_for('invoices.invoice_new'))

        if warning_msg:
            flash(warning_msg, 'warning')

        # Obtener configuración
        settings = InvoiceSettings.get_settings()

        # ===== GENERAR O VALIDAR NCF =====
        if use_manual_ncf and manual_ncf:
            # El usuario ingresó un NCF manualmente
            is_valid, error_msg = settings.validate_manual_ncf(manual_ncf, ncf_type)
            if not is_valid:
                flash(f'Error en NCF manual:\n{error_msg}', 'error')
                return redirect(url_for('invoices.invoice_new'))
            ncf = manual_ncf
        else:
            # Generar NCF automáticamente de la secuencia
            try:
                ncf = settings.get_next_ncf(ncf_type)
            except ValueError as e:
                flash(f'Error al generar NCF: {str(e)}', 'error')
                return redirect(url_for('invoices.invoice_new'))

        # Procesar items del formulario
        items_data = []
        raw_items = request.form.getlist('items')

        for item_json in raw_items:
            item_data = json.loads(item_json)
            items_data.append(item_data)

        # VALIDAR STOCK antes de crear la factura
        if status == 'paid':  # Solo validar stock si se va a marcar como pagada inmediatamente
            is_valid, error_msg = InvoiceInventoryService.validate_stock_for_invoice_items(items_data)
            if not is_valid:
                flash(f'Error de stock: {error_msg}', 'error')
                return redirect(url_for('invoices.invoice_new'))

        # Generar número de factura
        invoice_number = settings.get_next_invoice_number()

        # Crear factura
        invoice = Invoice(
            invoice_number=invoice_number,
            ncf=ncf,
            ncf_type=ncf_type,  # ===== NUEVO CAMPO =====
            customer_id=customer.id,
            invoice_date=datetime.strptime(invoice_date, '%Y-%m-%d').date() if invoice_date else date.today(),
            due_date=datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None,
            payment_method=payment_method,
            notes=notes,
            terms=terms or settings.default_terms,
            status=status,
            created_by_id=current_user.id
        )

        db.session.add(invoice)
        db.session.flush()  # Para obtener el ID

        # Procesar items
        line_order = 0

        for item_data in items_data:
            item_type = item_data.get('type', 'custom')
            description = item_data.get('description', '').strip()
            quantity = int(item_data.get('quantity', 1))
            unit_price = Decimal(str(item_data.get('price', 0)))

            if not description or quantity <= 0 or unit_price <= 0:
                continue

            # Crear item
            item = InvoiceItem(
                invoice_id=invoice.id,
                item_type=item_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                line_order=line_order
            )

            # Si es laptop, vincular
            if item_type == 'laptop':
                laptop_id = item_data.get('laptop_id')
                if laptop_id:
                    item.laptop_id = int(laptop_id)

            item.calculate_line_total()
            db.session.add(item)
            line_order += 1

        # Calcular totales
        invoice.calculate_totals()

        # Si la factura se crea como pagada, descontar inventario
        if status == 'paid':
            success, error_msg = InvoiceInventoryService.update_inventory_for_invoice(invoice, action='subtract')
            if not success:
                db.session.rollback()
                flash(f'Error al actualizar inventario: {error_msg}', 'error')
                return redirect(url_for('invoices.invoice_new'))

        # Guardar configuración actualizada
        db.session.add(settings)
        db.session.commit()

        # Mensaje de éxito con información del NCF
        ncf_type_name = NCF_TYPES.get(ncf_type, {}).get('name', ncf_type)
        flash(f'Factura {invoice_number} creada exitosamente con {ncf_type_name} ({ncf})', 'success')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear factura: {str(e)}', 'error')
        return redirect(url_for('invoices.invoice_new'))


# ============================================
# RUTA: DETALLE DE FACTURA
# ============================================

@invoices_bp.route('/<int:invoice_id>')
@login_required
def invoice_detail(invoice_id):
    """
    Ver detalle de una factura

    URL: /invoices/<id>
    """
    invoice = Invoice.query.get_or_404(invoice_id)
    settings = InvoiceSettings.get_settings()

    # Obtener resumen de inventario para mostrar en el detalle
    inventory_summary = InvoiceInventoryService.get_inventory_summary_for_invoice(invoice)

    # Verificar disponibilidad de items
    availability_check = InvoiceInventoryService.check_invoice_items_availability(invoice)

    # Información del tipo de NCF
    ncf_type_info = NCF_TYPES.get(invoice.ncf_type, {})

    return render_template(
        'invoices/invoice_detail.html',
        invoice=invoice,
        settings=settings,
        inventory_summary=inventory_summary,
        availability_check=availability_check,
        ncf_type_info=ncf_type_info
    )


# ============================================
# RUTA: EDITAR FACTURA
# ============================================

@invoices_bp.route('/<int:invoice_id>/edit', methods=['GET'])
@login_required
def invoice_edit(invoice_id):
    """
    Mostrar formulario para editar factura

    URL: /invoices/<id>/edit
    """
    invoice = Invoice.query.get_or_404(invoice_id)

    # Solo se pueden editar facturas en borrador
    if invoice.status not in ['draft']:
        flash('Solo se pueden editar facturas en borrador', 'warning')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    settings = InvoiceSettings.get_settings()
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.first_name, Customer.company_name).all()

    # Obtener laptops disponibles y convertir a diccionarios para JSON
    laptops_query = Laptop.query.filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).order_by(Laptop.display_name).all()

    # Serializar laptops a diccionarios con todas las relaciones
    laptops = [laptop.to_dict(include_relationships=True) for laptop in laptops_query]

    # Obtener tipos de NCF disponibles para ventas
    ncf_types_list = get_ncf_types_for_sales()

    # Obtener secuencias activas con su estado
    ncf_sequences = {}
    for ncf_type in NCF_SALES_TYPES:
        sequence = NCFSequence.get_or_create(ncf_type)
        ncf_sequences[ncf_type] = {
            'next_preview': sequence.next_ncf_preview,
            'is_valid': sequence.is_valid,
            'is_expired': sequence.is_expired,
            'is_exhausted': sequence.is_exhausted,
            'remaining': sequence.remaining_count,
            'valid_until': sequence.valid_until.strftime('%d/%m/%Y') if sequence.valid_until else None
        }

    return render_template(
        'invoices/invoice_form.html',
        invoice=invoice,
        settings=settings,
        customers=customers,
        laptops=laptops,
        is_edit=True,
        ncf_types=ncf_types_list,
        ncf_sequences=ncf_sequences,
        default_ncf_type=invoice.ncf_type
    )


# ============================================
# RUTA: ACTUALIZAR FACTURA
# ============================================

@invoices_bp.route('/<int:invoice_id>/update', methods=['POST'])
@login_required
def invoice_update(invoice_id):
    """
    Actualizar factura existente

    URL: /invoices/<id>/update (POST)

    NOTA: El NCF no se puede cambiar una vez creada la factura,
    según regulaciones de la DGII.
    """
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.status not in ['draft']:
        flash('Solo se pueden editar facturas en borrador', 'warning')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    try:
        # Procesar items del formulario
        items_data = []
        raw_items = request.form.getlist('items')

        for item_json in raw_items:
            item_data = json.loads(item_json)
            items_data.append(item_data)

        # Obtener el nuevo estado del formulario
        new_status = request.form.get('status', 'draft')

        # Si se está cambiando a 'paid', validar stock
        if new_status == 'paid':
            is_valid, error_msg = InvoiceInventoryService.validate_stock_for_invoice_items(items_data)
            if not is_valid:
                flash(f'Error de stock: {error_msg}', 'error')
                return redirect(url_for('invoices.invoice_edit', invoice_id=invoice.id))

        # Actualizar datos básicos (NO se permite cambiar NCF ni tipo de NCF)
        invoice.invoice_date = datetime.strptime(request.form.get('invoice_date'), '%Y-%m-%d').date()
        due_date = request.form.get('due_date')
        invoice.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        invoice.payment_method = request.form.get('payment_method', 'cash')
        invoice.notes = request.form.get('notes', '').strip()
        invoice.terms = request.form.get('terms', '').strip()

        # Guardar el estado anterior para comparar
        old_status = invoice.status
        invoice.status = new_status

        # Eliminar items anteriores
        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()
        db.session.flush()

        # Agregar nuevos items
        line_order = 0

        for item_data in items_data:
            item_type = item_data.get('type', 'custom')
            description = item_data.get('description', '').strip()
            quantity = int(item_data.get('quantity', 1))
            unit_price = Decimal(str(item_data.get('price', 0)))

            if not description or quantity <= 0 or unit_price <= 0:
                continue

            item = InvoiceItem(
                invoice_id=invoice.id,
                item_type=item_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                line_order=line_order
            )

            if item_type == 'laptop':
                laptop_id = item_data.get('laptop_id')
                if laptop_id:
                    item.laptop_id = int(laptop_id)

            item.calculate_line_total()
            db.session.add(item)
            line_order += 1

        # Recalcular totales
        invoice.calculate_totals()

        # Manejar cambios de estado que afectan el inventario
        if old_status != new_status:
            # Si estaba pagada y ahora no (ej: cancelled), restaurar inventario
            if old_status == 'paid' and new_status != 'paid':
                success, error_msg = InvoiceInventoryService.update_inventory_for_invoice(invoice, action='add')
                if not success:
                    db.session.rollback()
                    flash(f'Error al restaurar inventario: {error_msg}', 'error')
                    return redirect(url_for('invoices.invoice_edit', invoice_id=invoice.id))

            # Si no estaba pagada y ahora sí, descontar inventario
            elif old_status != 'paid' and new_status == 'paid':
                success, error_msg = InvoiceInventoryService.update_inventory_for_invoice(invoice, action='subtract')
                if not success:
                    db.session.rollback()
                    flash(f'Error al actualizar inventario: {error_msg}', 'error')
                    return redirect(url_for('invoices.invoice_edit', invoice_id=invoice.id))

        db.session.commit()
        flash('Factura actualizada exitosamente', 'success')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar factura: {str(e)}', 'error')
        return redirect(url_for('invoices.invoice_edit', invoice_id=invoice.id))


# ============================================
# RUTA: CAMBIAR ESTADO DE FACTURA
# ============================================

@invoices_bp.route('/<int:invoice_id>/status', methods=['POST'])
@login_required
def invoice_change_status(invoice_id):
    """
    Cambiar estado de factura

    URL: /invoices/<id>/status (POST)
    """
    invoice = Invoice.query.get_or_404(invoice_id)
    new_status = request.form.get('status')
    old_status = invoice.status

    if new_status not in ['draft', 'issued', 'paid', 'cancelled', 'overdue']:
        flash('Estado inválido', 'error')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    try:
        # Validar stock si se va a marcar como pagada
        if new_status == 'paid' and old_status != 'paid':
            # Verificar disponibilidad de items
            availability = InvoiceInventoryService.check_invoice_items_availability(invoice)

            if not availability['can_process']:
                error_msg = "No se puede marcar como pagada: "
                if availability['unavailable_items']:
                    error_msg += "Algunos items no existen en inventario. "
                if availability['warnings']:
                    for warning in availability['warnings']:
                        error_msg += f"{warning['description']}: Stock insuficiente (disponible: {warning['available']}, solicitado: {warning['requested']}). "

                flash(error_msg, 'error')
                return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

        # Actualizar estado
        invoice.status = new_status

        # Manejar cambios de estado que afectan el inventario
        if old_status != new_status:
            # Si estaba pagada y ahora no (ej: cancelled), restaurar inventario
            if old_status == 'paid' and new_status != 'paid':
                success, error_msg = InvoiceInventoryService.update_inventory_for_invoice(invoice, action='add')
                if not success:
                    db.session.rollback()
                    flash(f'Error al restaurar inventario: {error_msg}', 'error')
                    return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

            # Si no estaba pagada y ahora sí, descontar inventario
            elif old_status != 'paid' and new_status == 'paid':
                success, error_msg = InvoiceInventoryService.update_inventory_for_invoice(invoice, action='subtract')
                if not success:
                    db.session.rollback()
                    flash(f'Error al actualizar inventario: {error_msg}', 'error')
                    return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

        db.session.commit()
        flash(f'Estado actualizado a {new_status}', 'success')

        # Si se marcó como pagada, mostrar resumen de inventario actualizado
        if new_status == 'paid':
            inventory_summary = InvoiceInventoryService.get_inventory_summary_for_invoice(invoice)
            if inventory_summary['has_laptops']:
                flash(f'Inventario actualizado: {inventory_summary["total_units"]} unidades vendidas', 'info')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'error')

    return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))


# ============================================
# RUTA: ELIMINAR FACTURA
# ============================================

@invoices_bp.route('/<int:invoice_id>/delete', methods=['POST'])
@login_required
def invoice_delete(invoice_id):
    """
    Eliminar factura

    URL: /invoices/<id>/delete (POST)
    """
    invoice = Invoice.query.get_or_404(invoice_id)

    # Solo se pueden eliminar facturas en borrador
    if invoice.status != 'draft':
        flash('Solo se pueden eliminar facturas en borrador', 'warning')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    # Si la factura tiene items de laptop y está pagada, restaurar inventario primero
    if invoice.status == 'paid':
        has_laptops = any(item.item_type == 'laptop' for item in invoice.items.all())
        if has_laptops:
            flash('No se puede eliminar una factura pagada con laptops. Primero cámbiale el estado a "cancelled"',
                  'error')
            return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    try:
        db.session.delete(invoice)
        db.session.commit()
        flash('Factura eliminada exitosamente', 'success')
        return redirect(url_for('invoices.invoices_list'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar factura: {str(e)}', 'error')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))


# ============================================
# RUTA: EXPORTAR FACTURAS A CSV
# ============================================

@invoices_bp.route('/export/csv')
@login_required
def export_csv():
    """
    Exportar facturas a CSV

    URL: /invoices/export/csv
    """
    # Aplicar los mismos filtros que en la lista
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    ncf_type_filter = request.args.get('ncf_type', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Invoice.query

    if search_query:
        query = query.join(Customer).filter(
            or_(
                Invoice.invoice_number.ilike(f'%{search_query}%'),
                Invoice.ncf.ilike(f'%{search_query}%'),
                Customer.first_name.ilike(f'%{search_query}%'),
                Customer.last_name.ilike(f'%{search_query}%'),
                Customer.company_name.ilike(f'%{search_query}%')
            )
        )

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    if ncf_type_filter:
        query = query.filter(Invoice.ncf_type == ncf_type_filter)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date >= date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date <= date_to_obj)
        except ValueError:
            pass

    invoices = query.order_by(Invoice.invoice_date.desc()).all()

    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Encabezados (incluye tipo de NCF)
    writer.writerow([
        'Número', 'NCF', 'Tipo NCF', 'Fecha', 'Cliente', 'RNC/Cédula',
        'Subtotal', 'ITBIS', 'Total', 'Estado', 'Método de Pago'
    ])

    # Datos
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.ncf,
            inv.ncf_type,
            inv.invoice_date.strftime('%Y-%m-%d'),
            inv.customer.full_name,
            inv.customer.id_number,
            f"{float(inv.subtotal):.2f}",
            f"{float(inv.tax_amount):.2f}",
            f"{float(inv.total):.2f}",
            inv.status,
            inv.payment_method
        ])

    # Preparar respuesta
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'facturas_{date.today()}.csv'
    )


# ============================================
# RUTA: CONFIGURACIÓN DE FACTURACIÓN
# ============================================

@invoices_bp.route('/settings', methods=['GET'])
@login_required
def settings():
    """
    Mostrar configuración de facturación

    URL: /invoices/settings
    """
    if not current_user.is_admin:
        flash('No tienes permiso para acceder a esta página', 'error')
        return redirect(url_for('invoices.invoices_list'))

    settings = InvoiceSettings.get_settings()

    # Inicializar y obtener todas las secuencias de NCF
    initialize_default_ncf_sequences()
    ncf_sequences = NCFSequence.get_all_active()

    return render_template(
        'invoices/settings.html',
        settings=settings,
        ncf_sequences=ncf_sequences,
        ncf_types=NCF_TYPES
    )


# ============================================
# RUTA: ACTUALIZAR CONFIGURACIÓN
# ============================================

@invoices_bp.route('/settings/update', methods=['POST'])
@login_required
def settings_update():
    """
    Actualizar configuración de facturación

    URL: /invoices/settings/update (POST)
    """
    if not current_user.is_admin:
        flash('No tienes permiso para realizar esta acción', 'error')
        return redirect(url_for('invoices.invoices_list'))

    settings = InvoiceSettings.get_settings()

    try:
        settings.company_name = request.form.get('company_name', '').strip()
        settings.company_rnc = request.form.get('company_rnc', '').strip()
        settings.company_address = request.form.get('company_address', '').strip()
        settings.company_phone = request.form.get('company_phone', '').strip()
        settings.company_email = request.form.get('company_email', '').strip()
        settings.invoice_prefix = request.form.get('invoice_prefix', 'INV').strip().upper()
        settings.default_terms = request.form.get('default_terms', '').strip()

        # Legacy: mantener ncf_prefix para compatibilidad
        settings.ncf_prefix = request.form.get('ncf_prefix', 'B02').strip().upper()

        ncf_valid_until = request.form.get('ncf_valid_until')
        if ncf_valid_until:
            settings.ncf_valid_until = datetime.strptime(ncf_valid_until, '%Y-%m-%d').date()

        db.session.commit()
        flash('Configuración actualizada exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar configuración: {str(e)}', 'error')

    return redirect(url_for('invoices.settings'))


# ============================================
# RUTA: ACTUALIZAR SECUENCIA NCF
# ============================================

@invoices_bp.route('/settings/ncf-sequence/<ncf_type>/update', methods=['POST'])
@login_required
def update_ncf_sequence(ncf_type):
    """
    Actualizar una secuencia de NCF específica

    URL: /invoices/settings/ncf-sequence/<tipo>/update (POST)
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'No tienes permisos'}), 403

    if ncf_type not in NCF_TYPES:
        return jsonify({'success': False, 'message': f'Tipo de NCF "{ncf_type}" no válido'}), 400

    try:
        sequence = NCFSequence.get_or_create(ncf_type)

        # Actualizar campos
        new_sequence = request.form.get('current_sequence')
        if new_sequence:
            sequence.current_sequence = int(new_sequence)

        range_start = request.form.get('range_start')
        if range_start:
            sequence.range_start = int(range_start)

        range_end = request.form.get('range_end')
        if range_end:
            sequence.range_end = int(range_end) if range_end.strip() else None

        valid_until = request.form.get('valid_until')
        if valid_until:
            sequence.valid_until = datetime.strptime(valid_until, '%Y-%m-%d').date()
        else:
            sequence.valid_until = None

        is_active = request.form.get('is_active')
        sequence.is_active = is_active == 'true' or is_active == '1'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Secuencia {ncf_type} actualizada exitosamente',
            'sequence': sequence.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# API: SUGERIR TIPO DE NCF PARA CLIENTE
# ============================================

@invoices_bp.route('/api/ncf/suggest/<int:customer_id>')
@login_required
def api_suggest_ncf_type(customer_id):
    """
    API para sugerir el tipo de NCF basado en el cliente

    URL: /invoices/api/ncf/suggest/<customer_id>

    Returns:
        JSON con el tipo de NCF sugerido y razón
    """
    customer = Customer.query.get(customer_id)

    if not customer:
        return jsonify({
            'success': False,
            'message': 'Cliente no encontrado'
        }), 404

    suggestion = suggest_ncf_type_for_customer(customer)

    # Obtener información de la secuencia actual
    sequence = NCFSequence.get_or_create(suggestion['suggested_type'])

    return jsonify({
        'success': True,
        'suggestion': {
            **suggestion,
            'next_ncf_preview': sequence.next_ncf_preview,
            'sequence_valid': sequence.is_valid,
            'sequence_remaining': sequence.remaining_count
        },
        'customer': {
            'id': customer.id,
            'name': customer.full_name,
            'id_type': customer.id_type,
            'id_number': customer.id_number
        }
    })


# ============================================
# API: OBTENER TIPOS DE NCF DISPONIBLES
# ============================================

@invoices_bp.route('/api/ncf/types')
@login_required
def api_get_ncf_types():
    """
    API para obtener los tipos de NCF disponibles para ventas

    URL: /invoices/api/ncf/types
    """
    ncf_types_list = get_ncf_types_for_sales()

    # Agregar información de secuencia a cada tipo
    for ncf_type in ncf_types_list:
        sequence = NCFSequence.get_or_create(ncf_type['code'])
        ncf_type['sequence'] = {
            'next_preview': sequence.next_ncf_preview,
            'is_valid': sequence.is_valid,
            'is_expired': sequence.is_expired,
            'is_exhausted': sequence.is_exhausted,
            'remaining': sequence.remaining_count,
            'valid_until': sequence.valid_until.isoformat() if sequence.valid_until else None
        }

    return jsonify({
        'success': True,
        'types': ncf_types_list
    })


# ============================================
# API: VALIDAR NCF MANUAL
# ============================================

@invoices_bp.route('/api/ncf/validate', methods=['POST'])
@login_required
def api_validate_ncf():
    """
    API para validar un NCF ingresado manualmente

    URL: /invoices/api/ncf/validate (POST)

    Body JSON:
        {
            "ncf": "B0100000001",
            "ncf_type": "B01"
        }
    """
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'valid': False,
            'message': 'No se recibieron datos'
        }), 400

    ncf = data.get('ncf', '').strip().upper()
    ncf_type = data.get('ncf_type', '').strip().upper()

    if not ncf:
        return jsonify({
            'success': True,
            'valid': False,
            'message': 'El NCF no puede estar vacío'
        })

    if not ncf_type:
        return jsonify({
            'success': True,
            'valid': False,
            'message': 'Debe especificar el tipo de NCF'
        })

    settings = InvoiceSettings.get_settings()
    is_valid, error_msg = settings.validate_manual_ncf(ncf, ncf_type)

    return jsonify({
        'success': True,
        'valid': is_valid,
        'message': error_msg if error_msg else 'NCF válido y disponible'
    })


# ============================================
# API: BUSCAR CLIENTES (PARA AUTOCOMPLETAR)
# ============================================

@invoices_bp.route('/api/customers/search')
@login_required
def api_search_customers():
    """
    API para buscar clientes (autocompletar)

    URL: /invoices/api/customers/search?q=<query>
    """
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    customers = Customer.query.filter(
        and_(
            Customer.is_active == True,
            or_(
                Customer.first_name.ilike(f'%{query}%'),
                Customer.last_name.ilike(f'%{query}%'),
                Customer.company_name.ilike(f'%{query}%'),
                Customer.id_number.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()

    # Incluir información para sugerir tipo de NCF
    results = []
    for c in customers:
        suggestion = suggest_ncf_type_for_customer(c)
        results.append({
            'id': c.id,
            'name': c.full_name,
            'id_number': c.id_number,
            'id_type': c.id_type,
            'email': c.email,
            'phone': c.phone_primary,
            'suggested_ncf_type': suggestion['suggested_type'],
            'suggested_ncf_name': suggestion['type_name']
        })

    return jsonify(results)


# ============================================
# API: BUSCAR LAPTOPS (PARA AUTOCOMPLETAR)
# ============================================

@invoices_bp.route('/api/laptops/search')
@login_required
def api_search_laptops():
    """
    API para buscar laptops (autocompletar)

    URL: /invoices/api/laptops/search?q=<query>
    """
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    laptops = Laptop.query.filter(
        and_(
            Laptop.is_published == True,
            Laptop.quantity > 0,
            or_(
                Laptop.display_name.ilike(f'%{query}%'),
                Laptop.sku.ilike(f'%{query}%')
            )
        )
    ).limit(10).all()

    return jsonify([{
        'id': l.id,
        'name': l.display_name,
        'sku': l.sku,
        'price': float(l.sale_price),
        'description': l.short_description,
        'quantity': l.quantity
    } for l in laptops])


# ============================================
# RUTA: SUBIR LOGO
# ============================================

@invoices_bp.route('/settings/upload-logo', methods=['POST'])
@login_required
def upload_logo():
    """
    Subir logo para facturas

    URL: /invoices/settings/upload-logo (POST)
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'No tienes permisos'}), 403

    settings = InvoiceSettings.get_settings()

    # Validar que se envió un archivo
    if 'logo' not in request.files:
        return jsonify({'success': False, 'message': 'No se envió ningún archivo'}), 400

    file = request.files['logo']

    # Validar que tenga nombre
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No se seleccionó archivo'}), 400

    # Validar extensiones permitidas
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
    if '.' not in file.filename or \
            file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({
            'success': False,
            'message': 'Formato no permitido. Use PNG, JPG, GIF, SVG o WebP'
        }), 400

    # Validar tamaño (máximo 2MB)
    if len(file.read()) > 2 * 1024 * 1024:
        file.seek(0)
        return jsonify({
            'success': False,
            'message': 'Archivo muy grande. Máximo 2MB'
        }), 400

    file.seek(0)

    try:
        # Crear directorio si no existe
        logo_dir = os.path.join(current_app.root_path, 'static', 'logos')
        os.makedirs(logo_dir, exist_ok=True)

        # Eliminar logo anterior si existe
        if settings.logo_path:
            old_logo_path = os.path.join(logo_dir, settings.logo_path)
            if os.path.exists(old_logo_path):
                os.remove(old_logo_path)

        # Generar nombre único para el archivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"logo_{timestamp}{ext}"

        # Guardar archivo
        file_path = os.path.join(logo_dir, unique_filename)
        file.save(file_path)

        # Actualizar configuración
        settings.logo_path = unique_filename
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Logo subido exitosamente',
            'logo_url': settings.get_logo_url()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al subir logo: {str(e)}'
        }), 500


# ============================================
# RUTA: ELIMINAR LOGO
# ============================================

@invoices_bp.route('/settings/remove-logo', methods=['POST'])
@login_required
def remove_logo():
    """
    Eliminar logo actual

    URL: /invoices/settings/remove-logo (POST)
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'No tienes permisos'}), 403

    settings = InvoiceSettings.get_settings()

    try:
        if settings.logo_path:
            # Eliminar archivo físico
            logo_dir = os.path.join(current_app.root_path, 'static', 'logos')
            logo_path = os.path.join(logo_dir, settings.logo_path)

            if os.path.exists(logo_path):
                os.remove(logo_path)

            # Limpiar campo en la base de datos
            settings.logo_path = None
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Logo eliminado exitosamente'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar logo: {str(e)}'
        }), 500
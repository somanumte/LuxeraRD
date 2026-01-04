# ============================================
# RUTAS DE FACTURACIÓN
# ============================================

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.invoice import Invoice, InvoiceItem, InvoiceSettings
from app.models.customer import Customer
from app.models.laptop import Laptop
from datetime import datetime, date
from decimal import Decimal
import csv
import io
from sqlalchemy import or_, and_

# ============================================
# CREAR BLUEPRINT DE FACTURACIÓN
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

    return render_template(
        'invoices/invoices_list.html',
        invoices=invoices,
        search_query=search_query,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        total_invoices=total_invoices,
        total_amount=total_amount,
        status_counts=status_counts
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

    # Obtener clientes activos
    customers = Customer.query.filter_by(is_active=True).order_by(Customer.first_name, Customer.company_name).all()

    # Obtener laptops disponibles y convertir a diccionarios para JSON
    laptops_query = Laptop.query.filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).order_by(Laptop.display_name).all()

    # Serializar laptops a diccionarios con todas las relaciones
    laptops = [laptop.to_dict(include_relationships=True) for laptop in laptops_query]

    return render_template(
        'invoices/invoice_form.html',
        settings=settings,
        customers=customers,
        laptops=laptops,
        invoice=None,
        is_edit=False
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

        # Validaciones
        if not customer_id:
            flash('Debes seleccionar un cliente', 'error')
            return redirect(url_for('invoices.invoice_new'))

        customer = Customer.query.get_or_404(int(customer_id))

        # Obtener configuración y generar números
        settings = InvoiceSettings.get_settings()
        invoice_number = settings.get_next_invoice_number()
        ncf = settings.get_next_ncf()

        # Crear factura
        invoice = Invoice(
            invoice_number=invoice_number,
            ncf=ncf,
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
        items_data = request.form.getlist('items')
        line_order = 0

        for item_json in items_data:
            import json
            item_data = json.loads(item_json)

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

        # Guardar configuración actualizada
        db.session.add(settings)
        db.session.commit()

        flash(f'Factura {invoice_number} creada exitosamente', 'success')
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

    return render_template(
        'invoices/invoice_detail.html',
        invoice=invoice,
        settings=settings
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

    # Serializar laptops a diccionarios
    laptops = [{
        'id': laptop.id,
        'display_name': laptop.display_name,
        'sku': laptop.sku,
        'sale_price': float(laptop.sale_price),
        'quantity': laptop.quantity,
        'short_description': laptop.short_description or ''
    } for laptop in laptops_query]

    return render_template(
        'invoices/invoice_form.html',
        invoice=invoice,
        settings=settings,
        customers=customers,
        laptops=laptops,
        is_edit=True
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
    """
    invoice = Invoice.query.get_or_404(invoice_id)

    if invoice.status not in ['draft']:
        flash('Solo se pueden editar facturas en borrador', 'warning')
        return redirect(url_for('invoices.invoice_detail', invoice_id=invoice.id))

    try:
        # Actualizar datos básicos
        invoice.invoice_date = datetime.strptime(request.form.get('invoice_date'), '%Y-%m-%d').date()
        due_date = request.form.get('due_date')
        invoice.due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        invoice.payment_method = request.form.get('payment_method', 'cash')
        invoice.notes = request.form.get('notes', '').strip()
        invoice.terms = request.form.get('terms', '').strip()
        invoice.status = request.form.get('status', 'draft')

        # Eliminar items anteriores
        InvoiceItem.query.filter_by(invoice_id=invoice.id).delete()

        # Agregar nuevos items
        items_data = request.form.getlist('items')
        line_order = 0

        for item_json in items_data:
            import json
            item_data = json.loads(item_json)

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

    if new_status in ['draft', 'issued', 'paid', 'cancelled', 'overdue']:
        invoice.status = new_status
        db.session.commit()
        flash(f'Estado actualizado a {new_status}', 'success')
    else:
        flash('Estado inválido', 'error')

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

    # Encabezados
    writer.writerow([
        'Número', 'NCF', 'Fecha', 'Cliente', 'RNC/Cédula',
        'Subtotal', 'ITBIS', 'Total', 'Estado', 'Método de Pago'
    ])

    # Datos
    for inv in invoices:
        writer.writerow([
            inv.invoice_number,
            inv.ncf,
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
    return render_template('invoices/settings.html', settings=settings)


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
        settings.ncf_prefix = request.form.get('ncf_prefix', 'B02').strip().upper()
        settings.invoice_prefix = request.form.get('invoice_prefix', 'INV').strip().upper()
        settings.default_terms = request.form.get('default_terms', '').strip()

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

    return jsonify([{
        'id': c.id,
        'name': c.full_name,
        'id_number': c.id_number,
        'email': c.email,
        'phone': c.phone_primary
    } for c in customers])


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
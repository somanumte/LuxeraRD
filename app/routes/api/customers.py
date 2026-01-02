# ============================================
# RUTAS DE CLIENTES
# ============================================

import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.customer import Customer
from app.forms.customer_forms import CustomerForm, QuickSearchForm, FilterForm
from app.utils.decorators import admin_required
from sqlalchemy import or_
import re

# Configurar logging
logger = logging.getLogger(__name__)

# Crear Blueprint
customers_bp = Blueprint('customers', __name__, url_prefix='/customers')


# ===== UTILIDADES =====

def clean_id_number(id_number):
    """Limpia un número de identificación (quita guiones y espacios)"""
    return re.sub(r'[-\s]', '', str(id_number)) if id_number else ''


# ===== RUTA PRINCIPAL: LISTADO DE CLIENTES =====

@customers_bp.route('/')
@login_required
def customers_list():
    """
    Muestra el listado principal de clientes con filtros y búsqueda
    """
    # Obtener parámetros de filtros
    customer_type_filter = request.args.get('customer_type', '')
    province_filter = request.args.get('province', '')
    is_active_filter = request.args.get('is_active', '')
    search_query = request.args.get('q', '').strip()

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Query base
    query = Customer.query

    # Búsqueda por texto
    if search_query:
        # Limpiar búsqueda para cédula/RNC
        clean_search = clean_id_number(search_query)

        search_pattern = f'%{search_query}%'
        query = query.filter(
            or_(
                Customer.first_name.ilike(search_pattern),
                Customer.last_name.ilike(search_pattern),
                Customer.company_name.ilike(search_pattern),
                Customer.email.ilike(search_pattern),
                Customer.id_number.like(f'%{clean_search}%'),
                Customer.phone_primary.like(search_pattern)
            )
        )

    # Aplicar filtros
    if customer_type_filter:
        query = query.filter(Customer.customer_type == customer_type_filter)

    if province_filter:
        query = query.filter(Customer.province == province_filter)

    if is_active_filter:
        query = query.filter(Customer.is_active == (is_active_filter == '1'))

    # Ordenar por nombre
    query = query.order_by(Customer.created_at.desc())

    # Paginar
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items

    # Estadísticas
    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(is_active=True).count()
    person_customers = Customer.query.filter_by(customer_type='person').count()
    company_customers = Customer.query.filter_by(customer_type='company').count()

    stats = {
        'total': total_customers,
        'active': active_customers,
        'persons': person_customers,
        'companies': company_customers
    }

    # Formularios
    filter_form = FilterForm()
    search_form = QuickSearchForm()

    return render_template(
        'customers/customers_list.html',
        customers=customers,
        pagination=pagination,
        stats=stats,
        filter_form=filter_form,
        search_form=search_form,
        search_query=search_query
    )


# ===== AGREGAR NUEVO CLIENTE =====

@customers_bp.route('/add', methods=['GET', 'POST'])
@login_required
def customer_add():
    """
    Muestra el formulario y procesa la creación de un nuevo cliente
    """
    form = CustomerForm()

    if form.validate_on_submit():
        try:
            # Limpiar número de identificación
            clean_id = clean_id_number(form.id_number.data)

            # Crear nuevo cliente
            customer = Customer(
                customer_type=form.customer_type.data,
                first_name=form.first_name.data if form.customer_type.data == 'person' else None,
                last_name=form.last_name.data if form.customer_type.data == 'person' else None,
                company_name=form.company_name.data if form.customer_type.data == 'company' else None,
                id_number=clean_id,
                id_type=form.id_type.data,
                email=form.email.data,
                phone_primary=form.phone_primary.data,
                phone_secondary=form.phone_secondary.data,
                whatsapp=form.whatsapp.data,
                address_line1=form.address_line1.data,
                address_line2=form.address_line2.data,
                city=form.city.data,
                province=form.province.data,
                postal_code=form.postal_code.data,
                credit_limit=form.credit_limit.data if form.credit_limit.data else 0,
                notes=form.notes.data,
                is_active=form.is_active.data,
                created_by_id=current_user.id
            )

            # Guardar en base de datos
            db.session.add(customer)
            db.session.commit()

            flash(f'✅ Cliente {customer.display_name} agregado exitosamente', 'success')
            return redirect(url_for('customers.customer_detail', id=customer.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al agregar cliente: {str(e)}', exc_info=True)
            flash(f'❌ Error al agregar cliente: {str(e)}', 'error')

    # Si hay errores en el formulario
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')

    return render_template('customers/customer_form.html', form=form, mode='add')


# ===== VER DETALLE DE CLIENTE =====

@customers_bp.route('/<int:id>')
@login_required
def customer_detail(id):
    """
    Muestra el detalle completo de un cliente
    """
    customer = Customer.query.get_or_404(id)

    return render_template(
        'customers/customer_detail.html',
        customer=customer
    )


# ===== EDITAR CLIENTE =====

@customers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def customer_edit(id):
    """
    Edita un cliente existente
    """
    customer = Customer.query.get_or_404(id)
    form = CustomerForm(obj=customer)

    # Pasar ID para validación de unicidad
    form.customer_id = customer.id

    if form.validate_on_submit():
        try:
            # Limpiar número de identificación
            clean_id = clean_id_number(form.id_number.data)

            # Actualizar campos
            customer.customer_type = form.customer_type.data
            customer.first_name = form.first_name.data if form.customer_type.data == 'person' else None
            customer.last_name = form.last_name.data if form.customer_type.data == 'person' else None
            customer.company_name = form.company_name.data if form.customer_type.data == 'company' else None
            customer.id_number = clean_id
            customer.id_type = form.id_type.data
            customer.email = form.email.data
            customer.phone_primary = form.phone_primary.data
            customer.phone_secondary = form.phone_secondary.data
            customer.whatsapp = form.whatsapp.data
            customer.address_line1 = form.address_line1.data
            customer.address_line2 = form.address_line2.data
            customer.city = form.city.data
            customer.province = form.province.data
            customer.postal_code = form.postal_code.data
            customer.credit_limit = form.credit_limit.data if form.credit_limit.data else 0
            customer.notes = form.notes.data
            customer.is_active = form.is_active.data

            db.session.commit()

            flash(f'✅ Cliente {customer.display_name} actualizado exitosamente', 'success')
            return redirect(url_for('customers.customer_detail', id=customer.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error al actualizar cliente {customer.id}: {str(e)}', exc_info=True)
            flash(f'❌ Error al actualizar cliente: {str(e)}', 'error')

    # Si hay errores en el formulario
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')

    return render_template('customers/customer_form.html', form=form, mode='edit', customer=customer)


# ===== DESACTIVAR CLIENTE =====

@customers_bp.route('/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def customer_toggle_status(id):
    """
    Activa/Desactiva un cliente (soft delete)
    """
    customer = Customer.query.get_or_404(id)

    try:
        customer.is_active = not customer.is_active
        db.session.commit()

        status = 'activado' if customer.is_active else 'desactivado'
        flash(f'✅ Cliente {customer.display_name} {status} exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        logger.error(f'Error al cambiar estado del cliente {customer.id}: {str(e)}', exc_info=True)
        flash(f'❌ Error al cambiar estado: {str(e)}', 'error')

    return redirect(url_for('customers.customer_detail', id=id))


# ===== API: BÚSQUEDA RÁPIDA (AJAX) =====

@customers_bp.route('/api/search')
@login_required
def api_search():
    """
    Búsqueda rápida de clientes para autocompletado
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query or len(query) < 2:
        return jsonify({'results': []})

    # Limpiar búsqueda
    clean_search = clean_id_number(query)
    search_pattern = f'%{query}%'

    customers = Customer.query.filter(
        Customer.is_active == True,
        or_(
            Customer.first_name.ilike(search_pattern),
            Customer.last_name.ilike(search_pattern),
            Customer.company_name.ilike(search_pattern),
            Customer.id_number.like(f'%{clean_search}%')
        )
    ).limit(limit).all()

    results = [
        {
            'id': c.id,
            'text': c.display_name,
            'id_number': c.formatted_id,
            'customer_type': c.customer_type
        }
        for c in customers
    ]

    return jsonify({'results': results})
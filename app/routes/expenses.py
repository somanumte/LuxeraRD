from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_
import csv
import io

bp = Blueprint('expenses', __name__, url_prefix='/expenses')


@bp.route('/')
@login_required
def expenses_list():
    # Obtener parámetros de filtro
    expense_type = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    category_id = request.args.get('category', '', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    max_amount = request.args.get('max_amount', '', type=float)

    # Construir query base
    query = Expense.query.filter_by(created_by=current_user.id)

    # Aplicar filtros
    if expense_type == 'fixed':
        query = query.filter_by(is_recurring=False)
    elif expense_type == 'recurring':
        query = query.filter_by(is_recurring=True)

    if status_filter == 'pending':
        query = query.filter_by(is_paid=False).filter(Expense.due_date >= date.today())
    elif status_filter == 'paid':
        query = query.filter_by(is_paid=True)
    elif status_filter == 'overdue':
        query = query.filter_by(is_paid=False).filter(Expense.due_date < date.today())

    if category_id:
        query = query.filter_by(category_id=category_id)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Expense.due_date >= date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Expense.due_date <= date_to_obj)
        except ValueError:
            pass

    if max_amount:
        query = query.filter(Expense.amount <= max_amount)

    # Ordenar por fecha de vencimiento
    expenses = query.order_by(Expense.due_date).all()

    # Obtener categorías
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()

    # Calcular estadísticas
    total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter_by(
        created_by=current_user.id
    ).scalar() or 0

    fixed_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter_by(
        created_by=current_user.id, is_recurring=False
    ).scalar() or 0

    recurring_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter_by(
        created_by=current_user.id, is_recurring=True
    ).scalar() or 0

    # Contar gastos por tipo
    total_count = Expense.query.filter_by(created_by=current_user.id).count()
    fixed_count = Expense.query.filter_by(created_by=current_user.id, is_recurring=False).count()
    recurring_count = Expense.query.filter_by(created_by=current_user.id, is_recurring=True).count()

    # Gastos próximos (7 días)
    seven_days_later = date.today() + timedelta(days=7)
    upcoming_expenses = Expense.query.filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == False,
        Expense.due_date.between(date.today(), seven_days_later)
    ).order_by(Expense.due_date).all()

    # Resumen por categoría
    category_summary = db.session.query(
        ExpenseCategory.id,
        ExpenseCategory.name,
        ExpenseCategory.color,
        func.count(Expense.id).label('count'),
        func.coalesce(func.sum(Expense.amount), 0).label('total')
    ).outerjoin(
        Expense, and_(
            Expense.category_id == ExpenseCategory.id,
            Expense.created_by == current_user.id
        )
    ).group_by(
        ExpenseCategory.id,
        ExpenseCategory.name,
        ExpenseCategory.color
    ).order_by(
        func.coalesce(func.sum(Expense.amount), 0).desc()
    ).all()

    stats = {
        'total_expenses': float(total_expenses),
        'fixed_expenses': float(fixed_expenses),
        'recurring_expenses': float(recurring_expenses),
        'total_count': total_count,
        'fixed_count': fixed_count,
        'recurring_count': recurring_count,
        'upcoming_count': len(upcoming_expenses)
    }

    return render_template(
        'expenses_list.html',
        expenses=expenses,
        categories=categories,
        category_summary=category_summary,
        upcoming_expenses=upcoming_expenses,
        stats=stats,
        date_from=date_from,
        date_to=date_to
    )


@bp.route('/create', methods=['POST'])
@login_required
def expense_create():
    try:
        # Obtener datos del formulario
        description = request.form.get('description', '').strip()
        amount = float(request.form.get('amount', 0))
        category_id = int(request.form.get('category_id', 0))
        due_date_str = request.form.get('due_date', '')
        is_recurring = request.form.get('is_recurring') == 'on'
        frequency = request.form.get('frequency', 'monthly')
        advance_days = int(request.form.get('advance_days', 7))
        auto_renew = request.form.get('auto_renew') == 'on'
        notes = request.form.get('notes', '').strip()

        # Validaciones
        if not description:
            flash('La descripción es requerida', 'error')
            return redirect(url_for('expenses.expenses_list'))

        if amount <= 0:
            flash('El monto debe ser mayor a 0', 'error')
            return redirect(url_for('expenses.expenses_list'))

        if not category_id:
            flash('La categoría es requerida', 'error')
            return redirect(url_for('expenses.expenses_list'))

        if not due_date_str:
            flash('La fecha de vencimiento es requerida', 'error')
            return redirect(url_for('expenses.expenses_list'))

        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

        # Crear gasto
        expense = Expense(
            description=description,
            amount=amount,
            category_id=category_id,
            due_date=due_date,
            is_paid=False,
            is_recurring=is_recurring,
            frequency=frequency if is_recurring else None,
            advance_days=advance_days if is_recurring else None,
            auto_renew=auto_renew if is_recurring else None,
            notes=notes,
            created_by=current_user.id
        )

        db.session.add(expense)
        db.session.commit()

        flash('Gasto creado exitosamente', 'success')

    except ValueError as e:
        db.session.rollback()
        flash(f'Error en los datos: {str(e)}', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el gasto: {str(e)}', 'error')

    return redirect(url_for('expenses.expenses_list'))


@bp.route('/<int:expense_id>/update', methods=['POST'])
@login_required
def expense_update(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    # Verificar permisos
    if expense.created_by != current_user.id and not current_user.is_admin:
        flash('No tienes permiso para editar este gasto', 'error')
        return redirect(url_for('expenses.expenses_list'))

    try:
        expense.description = request.form.get('description', '').strip()
        expense.amount = float(request.form.get('amount', 0))
        expense.category_id = int(request.form.get('category_id', 0))
        due_date_str = request.form.get('due_date', '')

        if due_date_str:
            expense.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()

        expense.is_recurring = request.form.get('is_recurring') == 'on'
        expense.frequency = request.form.get('frequency', 'monthly') if expense.is_recurring else None
        expense.notes = request.form.get('notes', '').strip()

        db.session.commit()
        flash('Gasto actualizado exitosamente', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar el gasto: {str(e)}', 'error')

    return redirect(url_for('expenses.expenses_list'))


@bp.route('/<int:expense_id>/pay', methods=['POST'])
@login_required
def expense_pay(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    # Verificar permisos
    if expense.created_by != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'No tienes permiso'}), 403

    try:
        expense.is_paid = True
        expense.paid_date = date.today()

        # Si es recurrente y tiene auto_renew, crear el siguiente gasto
        if expense.is_recurring and expense.auto_renew and expense.next_due_date:
            new_expense = Expense(
                description=expense.description,
                amount=expense.amount,
                category_id=expense.category_id,
                due_date=expense.next_due_date,
                is_paid=False,
                is_recurring=True,
                frequency=expense.frequency,
                advance_days=expense.advance_days,
                auto_renew=True,
                notes=expense.notes,
                created_by=current_user.id
            )
            db.session.add(new_expense)

        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': 'Gasto marcado como pagado'})
        else:
            flash('Gasto marcado como pagado', 'success')

    except Exception as e:
        db.session.rollback()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': str(e)}), 500
        else:
            flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('expenses.expenses_list'))


@bp.route('/<int:expense_id>/delete', methods=['POST'])
@login_required
def expense_delete(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    # Verificar permisos
    if expense.created_by != current_user.id and not current_user.is_admin:
        flash('No tienes permiso para eliminar este gasto', 'error')
        return redirect(url_for('expenses.expenses_list'))

    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Gasto eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el gasto: {str(e)}', 'error')

    return redirect(url_for('expenses.expenses_list'))


@bp.route('/export')
@login_required
def expense_export():
    # Obtener gastos del usuario
    expenses = Expense.query.filter_by(created_by=current_user.id).order_by(Expense.due_date).all()

    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)

    # Escribir encabezados
    writer.writerow(['Descripción', 'Monto', 'Categoría', 'Fecha Vencimiento', 'Estado', 'Tipo', 'Frecuencia', 'Notas'])

    # Escribir datos
    for expense in expenses:
        estado = 'Pagado' if expense.is_paid else ('Vencido' if expense.is_overdue else 'Pendiente')
        tipo = 'Recurrente' if expense.is_recurring else 'Fijo'
        frecuencia = expense.frequency if expense.frequency else 'N/A'

        writer.writerow([
            expense.description,
            f'RD$ {expense.amount:.2f}',
            expense.category.name if expense.category else 'N/A',
            expense.due_date.strftime('%d/%m/%Y'),
            estado,
            tipo,
            frecuencia,
            expense.notes or ''
        ])

    # Preparar respuesta
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'gastos_{date.today().strftime("%Y%m%d")}.csv'
    )


@bp.route('/categories')
@login_required
def categories_list():
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()
    return jsonify([{
        'id': cat.id,
        'name': cat.name,
        'color': cat.color
    } for cat in categories])


@bp.route('/categories/create', methods=['POST'])
@login_required
def category_create():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Solo administradores pueden crear categorías'}), 403

    try:
        name = request.json.get('name', '').strip()
        color = request.json.get('color', 'bg-blue-100 text-blue-800')

        if not name:
            return jsonify({'success': False, 'message': 'El nombre es requerido'}), 400

        category = ExpenseCategory(name=name, color=color)
        db.session.add(category)
        db.session.commit()

        return jsonify({'success': True, 'category': {
            'id': category.id,
            'name': category.name,
            'color': category.color
        }})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# Ruta para crear algunas categorías por defecto al inicio
def create_default_categories():
    default_categories = [
        {'name': 'Alquiler', 'color': 'bg-red-100 text-red-800'},
        {'name': 'Servicios', 'color': 'bg-blue-100 text-blue-800'},
        {'name': 'Salarios', 'color': 'bg-green-100 text-green-800'},
        {'name': 'Marketing', 'color': 'bg-purple-100 text-purple-800'},
        {'name': 'Suministros', 'color': 'bg-yellow-100 text-yellow-800'},
        {'name': 'Mantenimiento', 'color': 'bg-indigo-100 text-indigo-800'},
        {'name': 'Impuestos', 'color': 'bg-pink-100 text-pink-800'},
        {'name': 'Transporte', 'color': 'bg-gray-100 text-gray-800'},
    ]

    for cat_data in default_categories:
        if not ExpenseCategory.query.filter_by(name=cat_data['name']).first():
            category = ExpenseCategory(name=cat_data['name'], color=cat_data['color'])
            db.session.add(category)

    db.session.commit()
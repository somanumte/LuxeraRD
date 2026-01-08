from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense, ExpenseCategory
from app.models.user import User
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, or_, extract
import csv
import io
import json

bp = Blueprint('expenses', __name__, url_prefix='/expenses')


# ============================================
# RUTAS PRINCIPALES (IMPLEMENTAR EXISTENTES)
# ============================================

@bp.route('/')
@login_required
def expenses_list():
    """Página principal de gastos"""
    # Obtener parámetros de filtrado
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    category_id = request.args.get('category_id', 'all')
    search = request.args.get('search', '')

    # Construir query base
    query = Expense.query.filter_by(created_by=current_user.id)

    # Aplicar filtros
    if status == 'pending':
        query = query.filter_by(is_paid=False).filter(Expense.due_date >= date.today())
    elif status == 'overdue':
        query = query.filter_by(is_paid=False).filter(Expense.due_date < date.today())
    elif status == 'paid':
        query = query.filter_by(is_paid=True)

    if category_id != 'all' and category_id.isdigit():
        query = query.filter_by(category_id=int(category_id))

    if search:
        query = query.filter(
            or_(
                Expense.description.ilike(f'%{search}%'),
                Expense.notes.ilike(f'%{search}%')
            )
        )

    # Paginación
    expenses = query.order_by(Expense.due_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # Obtener categorías para el filtro
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()

    # Estadísticas rápidas
    total_expenses = query.count()
    total_amount = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.created_by == current_user.id
    ).scalar() or 0

    return render_template(
        'Expenses/expenses_list.html',
        expenses=expenses,
        categories=categories,
        current_status=status,
        current_category=category_id,
        search_query=search,
        total_expenses=total_expenses,
        total_amount=float(total_amount)
    )


@bp.route('/create', methods=['POST'])
@login_required
def expense_create():
    """Crear un nuevo gasto"""
    try:
        data = request.form

        # Validar campos requeridos
        required_fields = ['description', 'amount', 'category_id', 'due_date']
        for field in required_fields:
            if not data.get(field):
                flash(f'El campo {field} es requerido', 'error')
                return redirect(url_for('expenses.expenses_list'))

        # Crear gasto
        expense = Expense(
            description=data['description'],
            amount=float(data['amount']),
            category_id=int(data['category_id']),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            is_paid=data.get('is_paid') == 'on',
            is_recurring=data.get('is_recurring') == 'on',
            frequency=data.get('frequency'),
            advance_days=int(data.get('advance_days', 7)),
            auto_renew=data.get('auto_renew') == 'on',
            notes=data.get('notes'),
            created_by=current_user.id
        )

        # Si está pagado, establecer fecha de pago
        if expense.is_paid:
            expense.paid_date = date.today()

        db.session.add(expense)
        db.session.commit()

        flash('Gasto creado exitosamente', 'success')
        return redirect(url_for('expenses.expenses_list'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear el gasto: {str(e)}', 'error')
        return redirect(url_for('expenses.expenses_list'))


# ============================================
# NUEVAS APIS RESTFUL (EXISTING CODE - KEEP AS IS)
# ============================================

@bp.route('/api/expenses/<int:expense_id>')
@login_required
def expense_get(expense_id):
    """API para obtener datos de un gasto específico"""
    expense = Expense.query.get_or_404(expense_id)

    # Verificar permisos
    if expense.created_by != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'No tienes permiso'}), 403

    return jsonify(expense.to_dict())


@bp.route('/api/expenses/bulk', methods=['POST'])
@login_required
def expense_bulk_action():
    """API para acciones en lote"""
    data = request.get_json()
    action = data.get('action')
    expense_ids = data.get('expense_ids', [])

    if not expense_ids:
        return jsonify({'error': 'No hay gastos seleccionados'}), 400

    # Verificar permisos para todos los gastos
    expenses = Expense.query.filter(
        Expense.id.in_(expense_ids),
        Expense.created_by == current_user.id
    ).all()

    if len(expenses) != len(expense_ids):
        return jsonify({'error': 'No tienes permiso para algunos gastos'}), 403

    try:
        if action == 'mark_paid':
            for expense in expenses:
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

        elif action == 'delete':
            for expense in expenses:
                db.session.delete(expense)

        elif action == 'mark_pending':
            for expense in expenses:
                expense.is_paid = False
                expense.paid_date = None

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{len(expenses)} gastos procesados',
            'processed': len(expenses)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/api/dashboard')
@login_required
def dashboard_data():
    """API para datos del dashboard con gráficos"""

    # Fechas para cálculos
    today = date.today()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    start_of_year = today.replace(month=1, day=1)

    # 1. Gastos por día del mes actual (para gráfico de líneas)
    daily_expenses = db.session.query(
        extract('day', Expense.due_date).label('day'),
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.created_by == current_user.id,
        Expense.due_date >= start_of_month,
        Expense.due_date <= end_of_month,
        Expense.is_paid == True
    ).group_by(
        extract('day', Expense.due_date)
    ).order_by('day').all()

    # Preparar datos para gráfico
    days_in_month = [i for i in range(1, 32)]
    daily_data = {day: {'total': 0, 'count': 0} for day in days_in_month}

    for expense in daily_expenses:
        daily_data[int(expense.day)] = {
            'total': float(expense.total) if expense.total else 0,
            'count': expense.count or 0
        }

    # 2. Resumen por categoría para gráfico de pastel
    category_chart = db.session.query(
        ExpenseCategory.name,
        ExpenseCategory.color,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).join(
        Expense, Expense.category_id == ExpenseCategory.id
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == True,
        Expense.due_date >= start_of_month,
        Expense.due_date <= end_of_month
    ).group_by(
        ExpenseCategory.name,
        ExpenseCategory.color
    ).order_by(func.sum(Expense.amount).desc()).all()

    # 3. Comparación mes anterior vs mes actual
    if start_of_month.month == 1:
        prev_month_start = date(start_of_month.year - 1, 12, 1)
    else:
        prev_month_start = date(start_of_month.year, start_of_month.month - 1, 1)

    prev_month_end = start_of_month - timedelta(days=1)

    current_month_total = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == True,
        Expense.due_date >= start_of_month,
        Expense.due_date <= end_of_month
    ).scalar() or 0

    prev_month_total = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == True,
        Expense.due_date >= prev_month_start,
        Expense.due_date <= prev_month_end
    ).scalar() or 0

    # Calcular porcentaje de cambio
    if prev_month_total > 0:
        percentage_change = ((current_month_total - prev_month_total) / prev_month_total) * 100
    else:
        percentage_change = 100 if current_month_total > 0 else 0

    # 4. Tendencias por tipo (fijo vs recurrente)
    type_trends = db.session.query(
        Expense.is_recurring,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == True,
        Expense.due_date >= start_of_year
    ).group_by(Expense.is_recurring).all()

    fixed_total = 0
    recurring_total = 0

    for trend in type_trends:
        if trend.is_recurring:
            recurring_total = float(trend.total) if trend.total else 0
        else:
            fixed_total = float(trend.total) if trend.total else 0

    return jsonify({
        'daily_expenses': {
            'labels': days_in_month,
            'data': [daily_data[day]['total'] for day in days_in_month],
            'counts': [daily_data[day]['count'] for day in days_in_month]
        },
        'category_chart': [{
            'name': cat.name,
            'color': cat.color or '#2D64B3',
            'total': float(cat.total) if cat.total else 0,
            'count': cat.count or 0
        } for cat in category_chart],
        'monthly_comparison': {
            'current_month': float(current_month_total),
            'previous_month': float(prev_month_total),
            'percentage_change': float(percentage_change),
            'trend': 'up' if percentage_change > 0 else 'down'
        },
        'type_trends': {
            'fixed': fixed_total,
            'recurring': recurring_total,
            'total': fixed_total + recurring_total
        }
    })


@bp.route('/api/expenses/summary')
@login_required
def expenses_summary():
    """Resumen de gastos para tarjetas del dashboard"""
    today = date.today()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Gastos del mes actual
    current_month = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.due_date >= start_of_month,
        Expense.due_date <= end_of_month
    ).scalar() or 0

    # Gastos pendientes del mes
    pending_month = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == False,
        Expense.due_date >= start_of_month,
        Expense.due_date <= end_of_month
    ).scalar() or 0

    # Gastos vencidos
    overdue_total = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == False,
        Expense.due_date < today
    ).scalar() or 0

    # Gastos fijos vs recurrentes
    fixed_total = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_recurring == False,
        Expense.due_date >= start_of_month,
        Expense.due_date <= end_of_month
    ).scalar() or 0

    recurring_total = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_recurring == True,
        Expense.due_date >= start_of_month,
        Expense.due_date <= end_of_month
    ).scalar() or 0

    # Gastos por pagar en próximos 7 días
    next_week = today + timedelta(days=7)
    upcoming_total = db.session.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == False,
        Expense.due_date.between(today, next_week)
    ).scalar() or 0

    return jsonify({
        'current_month': float(current_month),
        'pending_month': float(pending_month),
        'overdue_total': float(overdue_total),
        'fixed_total': float(fixed_total),
        'recurring_total': float(recurring_total),
        'upcoming_total': float(upcoming_total),
        'month_name': start_of_month.strftime('%B %Y')
    })


@bp.route('/api/notifications')
@login_required
def expense_notifications():
    """Notificaciones de gastos próximos y vencidos"""
    today = date.today()
    next_week = today + timedelta(days=7)

    # Gastos próximos (próximos 7 días)
    upcoming = Expense.query.filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == False,
        Expense.due_date.between(today, next_week)
    ).order_by(Expense.due_date).limit(10).all()

    # Gastos vencidos
    overdue = Expense.query.filter(
        Expense.created_by == current_user.id,
        Expense.is_paid == False,
        Expense.due_date < today
    ).order_by(Expense.due_date).limit(10).all()

    # Gastos recurrentes próximos a renovar
    renewing_soon = Expense.query.filter(
        Expense.created_by == current_user.id,
        Expense.is_recurring == True,
        Expense.auto_renew == True,
        Expense.due_date <= next_week
    ).limit(5).all()

    return jsonify({
        'upcoming': [{
            'id': e.id,
            'description': e.description,
            'amount': float(e.amount),
            'due_date': e.due_date.isoformat(),
            'days_until': e.days_until,
            'category': e.category_ref.name if e.category_ref else 'Sin categoría'
        } for e in upcoming],
        'overdue': [{
            'id': e.id,
            'description': e.description,
            'amount': float(e.amount),
            'due_date': e.due_date.isoformat(),
            'days_overdue': abs(e.days_until) if e.days_until < 0 else 0,
            'category': e.category_ref.name if e.category_ref else 'Sin categoría'
        } for e in overdue],
        'renewing_soon': [{
            'id': e.id,
            'description': e.description,
            'amount': float(e.amount),
            'due_date': e.due_date.isoformat(),
            'next_due_date': e.next_due_date.isoformat() if e.next_due_date else None,
            'frequency': e.frequency
        } for e in renewing_soon],
        'total_notifications': len(upcoming) + len(overdue)
    })


@bp.route('/api/search')
@login_required
def expense_search():
    """Búsqueda en tiempo real de gastos"""
    query = request.args.get('q', '')
    category_id = request.args.get('category_id', '')
    status = request.args.get('status', '')

    if not query or len(query) < 2:
        return jsonify([])

    # Construir query base
    search_query = Expense.query.filter(
        Expense.created_by == current_user.id,
        or_(
            Expense.description.ilike(f'%{query}%'),
            Expense.notes.ilike(f'%{query}%')
        )
    )

    # Aplicar filtros adicionales
    if category_id:
        search_query = search_query.filter_by(category_id=int(category_id))

    if status == 'pending':
        search_query = search_query.filter_by(is_paid=False).filter(Expense.due_date >= date.today())
    elif status == 'paid':
        search_query = search_query.filter_by(is_paid=True)
    elif status == 'overdue':
        search_query = search_query.filter_by(is_paid=False).filter(Expense.due_date < date.today())

    # Ejecutar búsqueda
    results = search_query.order_by(Expense.due_date.desc()).limit(20).all()

    return jsonify([{
        'id': e.id,
        'description': e.description,
        'amount': float(e.amount),
        'due_date': e.due_date.isoformat(),
        'is_paid': e.is_paid,
        'is_overdue': e.is_overdue,
        'category': {
            'id': e.category_id,
            'name': e.category_ref.name if e.category_ref else 'Sin categoría',
            'color': e.category_ref.color if e.category_ref else None
        },
        'type': 'Recurrente' if e.is_recurring else 'Fijo',
        'notes': e.notes or ''
    } for e in results])


@bp.route('/api/analytics/monthly')
@login_required
def monthly_analytics():
    """Análisis mensual de gastos"""
    year = request.args.get('year', date.today().year, type=int)

    monthly_data = []

    for month in range(1, 13):
        month_start = date(year, month, 1)

        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        # Gastos pagados
        paid_total = db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.created_by == current_user.id,
            Expense.is_paid == True,
            Expense.due_date >= month_start,
            Expense.due_date <= month_end
        ).scalar() or 0

        # Gastos pendientes
        pending_total = db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.created_by == current_user.id,
            Expense.is_paid == False,
            Expense.due_date >= month_start,
            Expense.due_date <= month_end
        ).scalar() or 0

        # Total gastos
        total_expenses = paid_total + pending_total

        # Conteo de gastos
        expense_count = Expense.query.filter(
            Expense.created_by == current_user.id,
            Expense.due_date >= month_start,
            Expense.due_date <= month_end
        ).count()

        monthly_data.append({
            'month': month_start.strftime('%B'),
            'month_number': month,
            'paid': float(paid_total),
            'pending': float(pending_total),
            'total': float(total_expenses),
            'count': expense_count
        })

    return jsonify({
        'year': year,
        'monthly_data': monthly_data,
        'annual_total': sum(item['total'] for item in monthly_data),
        'annual_paid': sum(item['paid'] for item in monthly_data)
    })


@bp.route('/api/categories/stats')
@login_required
def categories_stats():
    """Estadísticas detalladas por categoría"""
    start_date = request.args.get('start_date', date.today().replace(day=1).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())

    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        start_date_obj = date.today().replace(day=1)
        end_date_obj = date.today()

    # Obtener estadísticas por categoría
    category_stats = db.session.query(
        ExpenseCategory.id,
        ExpenseCategory.name,
        ExpenseCategory.color,
        func.count(Expense.id).label('expense_count'),
        func.coalesce(func.sum(Expense.amount), 0).label('total_amount'),
        func.avg(Expense.amount).label('average_amount'),
        func.max(Expense.amount).label('max_amount'),
        func.min(Expense.amount).label('min_amount')
    ).outerjoin(
        Expense, and_(
            Expense.category_id == ExpenseCategory.id,
            Expense.created_by == current_user.id,
            Expense.due_date >= start_date_obj,
            Expense.due_date <= end_date_obj
        )
    ).group_by(
        ExpenseCategory.id,
        ExpenseCategory.name,
        ExpenseCategory.color
    ).order_by(
        func.coalesce(func.sum(Expense.amount), 0).desc()
    ).all()

    # Calcular porcentajes
    grand_total = sum(stat.total_amount or 0 for stat in category_stats)

    result = []
    for stat in category_stats:
        percentage = (stat.total_amount / grand_total * 100) if grand_total > 0 else 0

        result.append({
            'id': stat.id,
            'name': stat.name,
            'color': stat.color or '#2D64B3',
            'expense_count': stat.expense_count or 0,
            'total_amount': float(stat.total_amount) if stat.total_amount else 0,
            'average_amount': float(stat.average_amount) if stat.average_amount else 0,
            'max_amount': float(stat.max_amount) if stat.max_amount else 0,
            'min_amount': float(stat.min_amount) if stat.min_amount else 0,
            'percentage': round(percentage, 2)
        })

    return jsonify({
        'categories': result,
        'period': {
            'start_date': start_date_obj.isoformat(),
            'end_date': end_date_obj.isoformat()
        },
        'totals': {
            'grand_total': float(grand_total),
            'total_expenses': sum(item['expense_count'] for item in result)
        }
    })


# ============================================
# RUTAS EXISTENTES (IMPLEMENTAR)
# ============================================

@bp.route('/export')
@login_required
def expense_export():
    """Exportar gastos a CSV"""
    try:
        # Obtener todos los gastos del usuario
        expenses = Expense.query.filter_by(created_by=current_user.id).all()

        # Crear output en memoria
        output = io.StringIO()
        writer = csv.writer(output)

        # Escribir encabezados
        writer.writerow([
            'ID', 'Descripción', 'Monto', 'Categoría', 'Fecha Vencimiento',
            'Pagado', 'Fecha Pago', 'Recurrente', 'Frecuencia', 'Notas'
        ])

        # Escribir datos
        for expense in expenses:
            writer.writerow([
                expense.id,
                expense.description,
                float(expense.amount),
                expense.category_ref.name if expense.category_ref else '',
                expense.due_date.strftime('%Y-%m-%d') if expense.due_date else '',
                'Sí' if expense.is_paid else 'No',
                expense.paid_date.strftime('%Y-%m-%d') if expense.paid_date else '',
                'Sí' if expense.is_recurring else 'No',
                expense.frequency or '',
                expense.notes or ''
            ])

        # Preparar respuesta
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'gastos_export_{timestamp}.csv'

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f'Error al exportar: {str(e)}', 'error')
        return redirect(url_for('expenses.expenses_list'))


@bp.route('/categories')
@login_required
def categories_list():
    """Listar categorías de gastos"""
    categories = ExpenseCategory.query.order_by(ExpenseCategory.name).all()

    # Obtener estadísticas por categoría
    category_stats = []
    for category in categories:
        expense_count = Expense.query.filter_by(
            category_id=category.id,
            created_by=current_user.id
        ).count()

        total_amount = db.session.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.category_id == category.id,
            Expense.created_by == current_user.id
        ).scalar() or 0

        category_stats.append({
            'category': category,
            'expense_count': expense_count,
            'total_amount': float(total_amount)
        })

    return render_template(
        'expenses/categories.html',  # Necesitarás crear este template
        categories=category_stats
    )


@bp.route('/categories/create', methods=['POST'])
@login_required
def category_create():
    """Crear nueva categoría de gastos"""
    try:
        name = request.form.get('name')
        color = request.form.get('color')
        description = request.form.get('description')

        if not name:
            flash('El nombre de la categoría es requerido', 'error')
            return redirect(url_for('expenses.categories_list'))

        # Verificar si ya existe
        existing = ExpenseCategory.query.filter_by(name=name).first()
        if existing:
            flash('Ya existe una categoría con ese nombre', 'error')
            return redirect(url_for('expenses.categories_list'))

        # Crear categoría
        category = ExpenseCategory(
            name=name,
            color=color,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        flash('Categoría creada exitosamente', 'success')
        return redirect(url_for('expenses.categories_list'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear categoría: {str(e)}', 'error')
        return redirect(url_for('expenses.categories_list'))


# Función para crear categorías por defecto
def create_default_categories():
    """Crear categorías por defecto si no existen"""
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
            category = ExpenseCategory(
                name=cat_data['name'],
                color=cat_data['color']
            )
            db.session.add(category)

    db.session.commit()
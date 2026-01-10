# ============================================
# DASHBOARD MEJORADO - ADAPTADO A TU PROYECTO
# ============================================
# Dashboard avanzado compatible con tus modelos exactos

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, abort
from flask_login import login_required, current_user
from app import db
from app.models.laptop import Laptop, Brand
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from app.models.user import User
from sqlalchemy import func, and_, or_, case, desc
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

# Crear Blueprint
main_bp = Blueprint('main', __name__)


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def calculate_percentage_change(current, previous):
    """Calcula el cambio porcentual entre dos valores"""
    if previous == 0 or previous is None:
        return 100 if current > 0 else 0
    return ((current - previous) / previous) * 100


def get_date_range(period='month'):
    """Obtiene rango de fechas según el período"""
    today = datetime.now()

    if period == 'today':
        return today.replace(hour=0, minute=0, second=0), today
    elif period == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday.replace(hour=0, minute=0, second=0), yesterday.replace(hour=23, minute=59, second=59)
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start.replace(hour=0, minute=0, second=0), today
    elif period == 'month':
        start = today.replace(day=1, hour=0, minute=0, second=0)
        return start, today
    elif period == 'quarter':
        quarter = (today.month - 1) // 3
        start = today.replace(month=quarter * 3 + 1, day=1, hour=0, minute=0, second=0)
        return start, today
    elif period == 'year':
        start = today.replace(month=1, day=1, hour=0, minute=0, second=0)
        return start, today

    return today.replace(day=1, hour=0, minute=0, second=0), today

def get_growth_indicator(change):
    """Retorna indicador de crecimiento con color"""
    if change > 0:
        return {
            'icon': 'arrow-up',
            'color': 'green',
            'text': f'+{change:.1f}%'
        }
    elif change < 0:
        return {
            'icon': 'arrow-down',
            'color': 'red',
            'text': f'{change:.1f}%'
        }
    else:
        return {
            'icon': 'minus',
            'color': 'gray',
            'text': '0%'
        }


def get_time_ago(dt):
    """Calcula tiempo transcurrido en formato legible"""
    now = datetime.now()
    diff = now - dt

    if diff.days > 0:
        if diff.days == 1:
            return 'hace 1 día'
        return f'hace {diff.days} días'

    hours = diff.seconds // 3600
    if hours > 0:
        if hours == 1:
            return 'hace 1 hora'
        return f'hace {hours} horas'

    minutes = diff.seconds // 60
    if minutes > 0:
        if minutes == 1:
            return 'hace 1 minuto'
        return f'hace {minutes} minutos'

    return 'hace un momento'


# ============================================
# RUTA PRINCIPAL DEL DASHBOARD
# ============================================

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard principal mejorado estilo Shopify
    Adaptado a tus modelos específicos
    """

    # ===== PERÍODO DE ANÁLISIS =====
    period = request.args.get('period', 'month')
    start_date, end_date = get_date_range(period)

    # Período anterior para comparaciones
    days_diff = (end_date - start_date).days
    prev_start = start_date - timedelta(days=days_diff)
    prev_end = start_date - timedelta(seconds=1)

    # ===== 1. MÉTRICAS DE INVENTARIO =====

    # Total de laptops
    total_laptops = Laptop.query.count()

    # Disponibles (con quantity > 0)
    total_available = db.session.query(
        func.count(Laptop.id)
    ).filter(Laptop.quantity > 0).scalar() or 0

    # Laptops con stock bajo (quantity <= min_alert)
    low_stock_laptops = Laptop.query.filter(
        Laptop.quantity <= Laptop.min_alert,
        Laptop.quantity > 0
    ).all()
    low_stock_count = len(low_stock_laptops)

    # Sin stock
    out_of_stock_count = Laptop.query.filter_by(quantity=0).count()

    # Reservados
    total_reserved = db.session.query(
        func.sum(Laptop.reserved_quantity)
    ).scalar() or 0

    # Valor del inventario (costo)
    inventory_cost = db.session.query(
        func.sum(Laptop.quantity * Laptop.purchase_cost)
    ).scalar() or 0

    # Valor del inventario (precio de venta)
    inventory_value = db.session.query(
        func.sum(Laptop.quantity * Laptop.sale_price)
    ).scalar() or 0

    # Ganancia potencial
    potential_profit = float(inventory_value) - float(inventory_cost)

    # Margen promedio
    avg_margin = (potential_profit / float(inventory_cost) * 100) if inventory_cost > 0 else 0

    # ===== 2. MÉTRICAS DE VENTAS E INGRESOS =====

    # Ventas del período actual
    current_period_invoices = Invoice.query.filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
        Invoice.status.in_(['paid', 'completed'])
    ).all()

    revenue_current = sum(float(inv.total) for inv in current_period_invoices)
    orders_current = len(current_period_invoices)

    # Ventas del período anterior
    previous_period_invoices = Invoice.query.filter(
        Invoice.created_at >= prev_start,
        Invoice.created_at <= prev_end,
        Invoice.status.in_(['paid', 'completed'])
    ).all()

    revenue_previous = sum(float(inv.total) for inv in previous_period_invoices)
    orders_previous = len(previous_period_invoices)

    # Cambios porcentuales
    revenue_change = calculate_percentage_change(revenue_current, revenue_previous)
    orders_change = calculate_percentage_change(orders_current, orders_previous)

    # AOV (Average Order Value)
    aov_current = revenue_current / orders_current if orders_current > 0 else 0
    aov_previous = revenue_previous / orders_previous if orders_previous > 0 else 0
    aov_change = calculate_percentage_change(aov_current, aov_previous)

    # Unidades vendidas
    units_sold_current = sum(
        item.quantity for inv in current_period_invoices
        for item in inv.items.all()
    )
    units_sold_previous = sum(
        item.quantity for inv in previous_period_invoices
        for item in inv.items.all()
    )
    units_change = calculate_percentage_change(units_sold_current, units_sold_previous)

    # ===== 3. GANANCIA REAL =====

    gross_profit_current = 0
    for invoice in current_period_invoices:
        for item in invoice.items.all():
            if item.laptop_id:
                laptop = Laptop.query.get(item.laptop_id)
                if laptop:
                    cost = float(laptop.purchase_cost) * item.quantity
                    revenue_item = float(item.unit_price) * item.quantity
                    gross_profit_current += (revenue_item - cost)

    gross_profit_previous = 0
    for invoice in previous_period_invoices:
        for item in invoice.items.all():
            if item.laptop_id:
                laptop = Laptop.query.get(item.laptop_id)
                if laptop:
                    cost = float(laptop.purchase_cost) * item.quantity
                    revenue_item = float(item.unit_price) * item.quantity
                    gross_profit_previous += (revenue_item - cost)

    profit_change = calculate_percentage_change(gross_profit_current, gross_profit_previous)

    # Margen bruto %
    gross_margin_current = (gross_profit_current / revenue_current * 100) if revenue_current > 0 else 0
    gross_margin_previous = (gross_profit_previous / revenue_previous * 100) if revenue_previous > 0 else 0

    # ===== 4. CLIENTES =====

    total_customers = Customer.query.count()

    # Clientes nuevos del período
    new_customers_current = Customer.query.filter(
        Customer.created_at >= start_date,
        Customer.created_at <= end_date
    ).count()

    new_customers_previous = Customer.query.filter(
        Customer.created_at >= prev_start,
        Customer.created_at <= prev_end
    ).count()

    customers_change = calculate_percentage_change(new_customers_current, new_customers_previous)

    # Clientes activos
    active_customers = db.session.query(
        func.count(func.distinct(Invoice.customer_id))
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
        Invoice.status.in_(['paid', 'completed'])
    ).scalar() or 0

    # Tasa de conversión
    conversion_rate = (active_customers / total_customers * 100) if total_customers > 0 else 0

    # CLV promedio
    avg_customer_value = revenue_current / active_customers if active_customers > 0 else 0

    # ===== 5. VENTAS POR DÍA =====

    daily_sales = []
    for i in range(29, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0)
        day_end = day.replace(hour=23, minute=59, second=59)

        day_invoices = Invoice.query.filter(
            Invoice.created_at >= day_start,
            Invoice.created_at <= day_end,
            Invoice.status.in_(['paid', 'completed'])
        ).all()

        day_revenue = sum(float(inv.total) for inv in day_invoices)

        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'full_date': day.strftime('%Y-%m-%d'),
            'amount': float(day_revenue),
            'orders': len(day_invoices)
        })

    avg_daily_sales = sum(d['amount'] for d in daily_sales) / len(daily_sales) if daily_sales else 0

    # ===== 6. TOP PRODUCTOS =====

    top_products_query = db.session.query(
        Laptop.id,
        Laptop.display_name,
        Laptop.sku,
        Laptop.category,
        Laptop.sale_price,
        Laptop.purchase_cost,
        Laptop.quantity,
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue'),
        func.count(func.distinct(Invoice.id)).label('orders')
    ).join(
        InvoiceItem, InvoiceItem.laptop_id == Laptop.id
    ).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
        Invoice.status.in_(['paid', 'completed'])
    ).group_by(
        Laptop.id
    ).order_by(
        desc('units_sold')
    ).limit(10).all()

    top_products = []
    for product in top_products_query:
        profit_per_unit = float(product.sale_price) - float(product.purchase_cost)
        total_profit = profit_per_unit * product.units_sold
        margin = (profit_per_unit / float(product.purchase_cost) * 100) if product.purchase_cost > 0 else 0

        top_products.append({
            'id': product.id,
            'name': product.display_name,
            'sku': product.sku,
            'category': product.category,
            'units_sold': product.units_sold,
            'revenue': float(product.revenue),
            'profit': total_profit,
            'margin': margin,
            'orders': product.orders,
            'stock': product.quantity,
            'status': 'in_stock' if product.quantity > 0 else 'out_of_stock'
        })

    # ===== 7. CATEGORÍAS =====

    categories = db.session.query(
        Laptop.category,
        func.count(Laptop.id).label('products'),
        func.sum(Laptop.quantity).label('units_in_stock'),
        func.sum(Laptop.quantity * Laptop.sale_price).label('stock_value')
    ).group_by(
        Laptop.category
    ).all()

    category_sales = db.session.query(
        Laptop.category,
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue')
    ).join(
        InvoiceItem, InvoiceItem.laptop_id == Laptop.id
    ).join(
        Invoice, Invoice.id == InvoiceItem.invoice_id
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
        Invoice.status.in_(['paid', 'completed'])
    ).group_by(
        Laptop.category
    ).all()

    category_data = {}
    for cat in categories:
        category_data[cat.category] = {
            'category': cat.category,
            'products': cat.products,
            'units_in_stock': cat.units_in_stock or 0,
            'stock_value': float(cat.stock_value) if cat.stock_value else 0,
            'units_sold': 0,
            'revenue': 0
        }

    for sale in category_sales:
        if sale.category in category_data:
            category_data[sale.category]['units_sold'] = sale.units_sold or 0
            category_data[sale.category]['revenue'] = float(sale.revenue) if sale.revenue else 0

    category_distribution = sorted(
        category_data.values(),
        key=lambda x: x['revenue'],
        reverse=True
    )

    # ===== 8. MARCAS =====

    brand_sales = db.session.query(
        Brand.id,
        Brand.name,
        func.count(Laptop.id).label('products'),
        func.sum(Laptop.quantity).label('units_in_stock'),
        func.sum(InvoiceItem.quantity).label('units_sold'),
        func.sum(InvoiceItem.quantity * InvoiceItem.unit_price).label('revenue')
    ).join(
        Laptop, Laptop.brand_id == Brand.id
    ).outerjoin(
        InvoiceItem, InvoiceItem.laptop_id == Laptop.id
    ).outerjoin(
        Invoice, and_(
            Invoice.id == InvoiceItem.invoice_id,
            Invoice.created_at >= start_date,
            Invoice.created_at <= end_date,
            Invoice.status.in_(['paid', 'completed'])
        )
    ).group_by(
        Brand.id
    ).order_by(
        desc('revenue')
    ).limit(8).all()

    brand_distribution = []
    for brand in brand_sales:
        brand_distribution.append({
            'id': brand.id,
            'name': brand.name,
            'products': brand.products,
            'units_in_stock': brand.units_in_stock or 0,
            'units_sold': brand.units_sold or 0,
            'revenue': float(brand.revenue) if brand.revenue else 0
        })

    # ===== 9. ÓRDENES RECIENTES =====

    recent_orders = Invoice.query.order_by(
        Invoice.created_at.desc()
    ).limit(10).all()

    recent_invoices = []
    for invoice in recent_orders:
        items_count = invoice.items.count()

        recent_invoices.append({
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'customer_name': invoice.customer.full_name if invoice.customer else 'N/A',
            'total': float(invoice.total),
            'status': invoice.status,
            'items_count': items_count,
            'created_at': invoice.created_at,
            'time_ago': get_time_ago(invoice.created_at)
        })

    # ===== 10. ESTADO DE FACTURAS =====

    orders_by_status = db.session.query(
        Invoice.status,
        func.count(Invoice.id).label('count'),
        func.sum(Invoice.total).label('total_amount')
    ).filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date
    ).group_by(
        Invoice.status
    ).all()

    status_breakdown = {}
    for status in orders_by_status:
        status_breakdown[status.status] = {
            'count': status.count,
            'amount': float(status.total_amount) if status.total_amount else 0
        }

    pending_invoices = status_breakdown.get('issued', {}).get('count', 0)
    pending_amount = status_breakdown.get('issued', {}).get('amount', 0)

    overdue_invoices = Invoice.query.filter(
        Invoice.due_date < datetime.now().date(),
        Invoice.status.in_(['issued', 'pending'])
    ).count()

    # ===== 11. ALERTAS =====

    alerts = []

    if out_of_stock_count > 0:
        alerts.append({
            'type': 'danger',
            'priority': 'high',
            'icon': 'times-circle',
            'title': 'Productos sin stock',
            'message': f'{out_of_stock_count} producto(s) agotado(s)',
            'action': 'Reabastecer ahora',
            'link': 'inventory.laptops_list',
            'filters': '?status=out_of_stock'
        })

    if low_stock_count > 0:
        alerts.append({
            'type': 'warning',
            'priority': 'medium',
            'icon': 'exclamation-triangle',
            'title': 'Stock bajo',
            'message': f'{low_stock_count} producto(s) con stock mínimo',
            'action': 'Ver productos',
            'link': 'inventory.laptops_list',
            'filters': '?status=low_stock'
        })

    if overdue_invoices > 0:
        alerts.append({
            'type': 'danger',
            'priority': 'high',
            'icon': 'clock',
            'title': 'Facturas vencidas',
            'message': f'{overdue_invoices} factura(s) vencida(s)',
            'action': 'Gestionar cobros',
            'link': 'invoices.invoices_list',
            'filters': '?status=overdue'
        })

    if pending_invoices > 5:
        alerts.append({
            'type': 'info',
            'priority': 'low',
            'icon': 'file-invoice',
            'title': 'Facturas pendientes',
            'message': f'{pending_invoices} facturas por cobrar (${pending_amount:,.2f})',
            'action': 'Ver facturas',
            'link': 'invoices.invoices_list',
            'filters': '?status=pending'
        })

    if revenue_change < -10:
        alerts.append({
            'type': 'warning',
            'priority': 'medium',
            'icon': 'chart-line',
            'title': 'Ventas descendentes',
            'message': f'Las ventas han bajado {abs(revenue_change):.1f}%',
            'action': 'Analizar tendencia',
            'link': 'main.dashboard'
        })

    if gross_margin_current < 20:
        alerts.append({
            'type': 'warning',
            'priority': 'medium',
            'icon': 'percentage',
            'title': 'Margen bajo',
            'message': f'El margen bruto es {gross_margin_current:.1f}%',
            'action': 'Revisar precios',
            'link': 'inventory.laptops_list'
        })

    # ===== 12. INSIGHTS =====

    insights = []

    if daily_sales:
        best_day = max(daily_sales, key=lambda x: x['amount'])
        if best_day['amount'] > 0:
            insights.append({
                'icon': 'star',
                'type': 'success',
                'title': 'Mejor día del mes',
                'message': f'El {best_day["full_date"]} vendiste ${best_day["amount"]:,.2f}',
                'suggestion': 'Analiza qué factores contribuyeron a este éxito'
            })

    if top_products:
        star_product = top_products[0]
        insights.append({
            'icon': 'trophy',
            'type': 'info',
            'title': 'Producto estrella',
            'message': f'{star_product["name"]} vendió {star_product["units_sold"]} unidades',
            'suggestion': 'Considera aumentar stock o productos similares'
        })

    if customers_change > 20:
        insights.append({
            'icon': 'users',
            'type': 'success',
            'title': 'Crecimiento acelerado',
            'message': f'Nuevos clientes +{customers_change:.1f}%',
            'suggestion': 'Enfócate en retención para maximizar valor'
        })

    # ===== INDICADORES DE CRECIMIENTO =====

    growth_indicators = {
        'revenue': get_growth_indicator(revenue_change),
        'orders': get_growth_indicator(orders_change),
        'customers': get_growth_indicator(customers_change),
        'aov': get_growth_indicator(aov_change),
        'profit': get_growth_indicator(profit_change),
        'units': get_growth_indicator(units_change)
    }

    # ===== RENDERIZAR =====

    return render_template(
        'dashboard.html',
        # Config
        current_period=period,
        start_date=start_date,
        end_date=end_date,

        # Inventario
        total_laptops=total_laptops,
        total_available=int(total_available),
        total_reserved=int(total_reserved),
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        inventory_cost=float(inventory_cost),
        inventory_value=float(inventory_value),
        potential_profit=potential_profit,
        avg_margin=avg_margin,

        # Ventas
        revenue_current=revenue_current,
        revenue_previous=revenue_previous,
        revenue_change=revenue_change,
        orders_current=orders_current,
        orders_previous=orders_previous,
        orders_change=orders_change,
        aov_current=aov_current,
        aov_previous=aov_previous,
        aov_change=aov_change,
        units_sold_current=units_sold_current,
        units_change=units_change,

        # Rentabilidad
        gross_profit_current=gross_profit_current,
        gross_profit_previous=gross_profit_previous,
        profit_change=profit_change,
        gross_margin_current=gross_margin_current,
        gross_margin_previous=gross_margin_previous,

        # Clientes
        total_customers=total_customers,
        new_customers_current=new_customers_current,
        customers_change=customers_change,
        active_customers=active_customers,
        conversion_rate=conversion_rate,
        avg_customer_value=avg_customer_value,

        # Temporal
        daily_sales=daily_sales,
        avg_daily_sales=avg_daily_sales,

        # Productos
        top_products=top_products,
        category_distribution=category_distribution,
        brand_distribution=brand_distribution,

        # Actividad
        recent_invoices=recent_invoices,
        status_breakdown=status_breakdown,
        pending_invoices=pending_invoices,
        pending_amount=pending_amount,
        overdue_invoices=overdue_invoices,

        # Alertas e insights
        alerts=sorted(alerts, key=lambda x: {'high': 0, 'medium': 1, 'low': 2}[x['priority']]),
        insights=insights,

        # Indicadores
        growth_indicators=growth_indicators
    )


# ============================================
# API ENDPOINTS
# ============================================

@main_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """API para stats en tiempo real"""
    period = request.args.get('period', 'month')
    start_date, end_date = get_date_range(period)

    total_laptops = Laptop.query.count()
    total_customers = Customer.query.count()

    invoices = Invoice.query.filter(
        Invoice.created_at >= start_date,
        Invoice.created_at <= end_date,
        Invoice.status.in_(['paid', 'completed'])
    ).all()

    revenue = sum(float(inv.total) for inv in invoices)

    return jsonify({
        'success': True,
        'data': {
            'inventory': {
                'total_laptops': total_laptops,
                'available': Laptop.query.filter(Laptop.quantity > 0).count(),
                'low_stock': Laptop.query.filter(Laptop.quantity <= Laptop.min_alert).count()
            },
            'sales': {
                'revenue': revenue,
                'orders': len(invoices),
                'customers': total_customers
            },
            'timestamp': datetime.now().isoformat()
        }
    })


# ============================================
# RUTAS DE ADMIN (COMPATIBILIDAD)
# ============================================

@main_bp.route('/admin')
@login_required
def admin_panel():
    """
    Panel de administración
    """
    if not current_user.is_admin:
        abort(403)

    # Obtener estadísticas de usuarios
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()

    # Usuarios recientes (últimos 10 registrados)
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    # Obtener la fecha actual para el pie de página
    now = datetime.now()

    return render_template(
        'admin/panel.html',
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        recent_users=recent_users,
        now=now
    )


@main_bp.route('/admin/users')
@login_required
def admin_users():
    """
    Lista de usuarios (placeholder para compatibilidad)
    """
    if not current_user.is_admin:
        abort(403)

    users = User.query.order_by(User.created_at.desc()).all()

    return render_template(
        'admin/users.html',
        users=users
    )


@main_bp.route('/about')
def about():
    """Página Acerca de"""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """Página de contacto"""
    return render_template('contact.html')


# ============================================
# MANEJADORES DE ERRORES
# ============================================

def register_error_handlers(app):
    """
    Registra los manejadores de errores personalizados
    Se llama desde app/__init__.py
    """

    @app.errorhandler(403)
    def forbidden(error):
        """Error 403: Acceso prohibido"""
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(error):
        """Error 404: Página no encontrada"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        """Error 500: Error interno del servidor"""
        db.session.rollback()  # Revertir cualquier transacción pendiente
        return render_template('errors/500.html'), 500
# ============================================
# RUTAS DE DASHBOARD
# ============================================
# Dashboard principal con métricas e insights del negocio

from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.laptop import Laptop, Brand
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceItem
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta, date
from decimal import Decimal

# Crear Blueprint
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


# ============================================
# UTILIDADES Y FUNCIONES AUXILIARES
# ============================================

def get_date_range(period='month'):
    """
    Obtiene el rango de fechas para filtros
    
    Args:
        period: 'today', 'week', 'month', 'year'
    
    Returns:
        tuple: (start_date, end_date)
    """
    today = date.today()
    
    if period == 'today':
        return today, today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == 'month':
        start = today.replace(day=1)
        return start, today
    elif period == 'year':
        start = today.replace(month=1, day=1)
        return start, today
    
    return today.replace(day=1), today


def calculate_percentage_change(current, previous):
    """
    Calcula el cambio porcentual entre dos valores
    
    Args:
        current: Valor actual
        previous: Valor anterior
    
    Returns:
        float: Porcentaje de cambio
    """
    if previous == 0 or previous is None:
        return 0 if current == 0 else 100
    
    return ((current - previous) / previous) * 100


# ============================================
# RUTA PRINCIPAL DEL DASHBOARD
# ============================================

@dashboard_bp.route('/')
@login_required
def index():
    """
    Dashboard principal con todas las métricas
    
    Muestra:
    - Resumen de inventario
    - Métricas financieras
    - Actividad reciente
    - Gráficos de tendencias
    """
    
    # ===== 1. MÉTRICAS DE INVENTARIO =====
    
    # Total de laptops
    total_laptops = Laptop.query.count()
    total_available = db.session.query(
        func.sum(Laptop.quantity - Laptop.reserved_quantity)
    ).scalar() or 0
    
    # Laptops con stock bajo
    low_stock_count = Laptop.query.filter(
        Laptop.quantity - Laptop.reserved_quantity <= Laptop.min_alert
    ).count()
    
    # Valor total del inventario (basado en precio de venta)
    inventory_value = db.session.query(
        func.sum(Laptop.sale_price * Laptop.quantity)
    ).scalar() or 0
    
    # Valor total del inventario (basado en costo de compra)
    inventory_cost = db.session.query(
        func.sum(Laptop.purchase_cost * Laptop.quantity)
    ).scalar() or 0
    
    # Ganancia potencial
    potential_profit = float(inventory_value) - float(inventory_cost)
    
    # ===== 2. MÉTRICAS DE CLIENTES =====
    
    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(is_active=True).count()
    
    # Clientes nuevos este mes
    start_of_month, _ = get_date_range('month')
    new_customers_month = Customer.query.filter(
        Customer.created_at >= start_of_month
    ).count()
    
    # ===== 3. MÉTRICAS DE VENTAS E INGRESOS =====
    
    # Total de facturas
    total_invoices = Invoice.query.count()
    
    # Facturas del mes actual
    invoices_this_month = Invoice.query.filter(
        Invoice.invoice_date >= start_of_month
    ).count()
    
    # Ingresos del mes
    revenue_this_month = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        Invoice.invoice_date >= start_of_month,
        Invoice.status.in_(['issued', 'paid'])
    ).scalar() or 0
    
    # Ingresos mes anterior
    start_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_last_month = start_of_month - timedelta(days=1)
    
    revenue_last_month = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        Invoice.invoice_date >= start_last_month,
        Invoice.invoice_date <= end_last_month,
        Invoice.status.in_(['issued', 'paid'])
    ).scalar() or 0
    
    # Calcular cambio porcentual
    revenue_change = calculate_percentage_change(
        float(revenue_this_month),
        float(revenue_last_month)
    )
    
    # Facturas pendientes de pago
    pending_invoices = Invoice.query.filter_by(status='issued').count()
    pending_amount = db.session.query(
        func.sum(Invoice.total)
    ).filter_by(status='issued').scalar() or 0
    
    # Facturas vencidas
    overdue_invoices = Invoice.query.filter(
        Invoice.status == 'issued',
        Invoice.due_date < date.today()
    ).count()
    
    # ===== 4. ACTIVIDAD RECIENTE =====
    
    # Últimas 5 facturas
    recent_invoices = Invoice.query.order_by(
        Invoice.created_at.desc()
    ).limit(5).all()
    
    # Últimas 5 laptops agregadas
    recent_laptops = Laptop.query.order_by(
        Laptop.created_at.desc()
    ).limit(5).all()
    
    # Últimos 5 clientes registrados
    recent_customers = Customer.query.order_by(
        Customer.created_at.desc()
    ).limit(5).all()
    
    # ===== 5. PRODUCTOS MÁS VENDIDOS =====
    
    # Top 5 laptops más vendidas (por cantidad en facturas)
    top_products = db.session.query(
        Laptop.display_name,
        Laptop.sku,
        func.sum(InvoiceItem.quantity).label('total_sold')
    ).join(
        InvoiceItem, Laptop.id == InvoiceItem.laptop_id
    ).join(
        Invoice, InvoiceItem.invoice_id == Invoice.id
    ).filter(
        Invoice.status.in_(['issued', 'paid'])
    ).group_by(
        Laptop.id, Laptop.display_name, Laptop.sku
    ).order_by(
        desc('total_sold')
    ).limit(5).all()
    
    # ===== 6. DISTRIBUCIÓN POR CATEGORÍA =====
    
    category_distribution = db.session.query(
        Laptop.category,
        func.count(Laptop.id).label('count'),
        func.sum(Laptop.quantity).label('total_quantity')
    ).group_by(
        Laptop.category
    ).all()
    
    # ===== 7. DISTRIBUCIÓN POR MARCA =====
    
    brand_distribution = db.session.query(
        Brand.name,
        func.count(Laptop.id).label('count'),
        func.sum(Laptop.quantity).label('total_quantity')
    ).join(
        Laptop, Brand.id == Laptop.brand_id
    ).group_by(
        Brand.name
    ).order_by(
        desc('count')
    ).limit(5).all()
    
    # ===== 8. VENTAS ÚLTIMOS 7 DÍAS =====
    
    daily_sales = []
    for i in range(6, -1, -1):
        day = date.today() - timedelta(days=i)
        sales = db.session.query(
            func.sum(Invoice.total)
        ).filter(
            Invoice.invoice_date == day,
            Invoice.status.in_(['issued', 'paid'])
        ).scalar() or 0
        
        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'amount': float(sales)
        })
    
    # ===== 9. ACCIONES RÁPIDAS Y ALERTAS =====
    
    alerts = []
    
    # Alerta de stock bajo
    if low_stock_count > 0:
        alerts.append({
            'type': 'warning',
            'icon': 'exclamation-triangle',
            'message': f'{low_stock_count} producto(s) con stock bajo',
            'action': 'Ver inventario',
            'link': 'inventory.laptops_list'
        })
    
    # Alerta de facturas vencidas
    if overdue_invoices > 0:
        alerts.append({
            'type': 'danger',
            'icon': 'exclamation-circle',
            'message': f'{overdue_invoices} factura(s) vencida(s)',
            'action': 'Ver facturas',
            'link': 'invoices.invoices_list'
        })
    
    # Alerta de facturas pendientes
    if pending_invoices > 5:
        alerts.append({
            'type': 'info',
            'icon': 'info-circle',
            'message': f'{pending_invoices} facturas pendientes de pago',
            'action': 'Ver facturas',
            'link': 'invoices.invoices_list'
        })
    
    # ===== RENDERIZAR TEMPLATE =====
    
    return render_template(
        'dashboard/index.html',
        # Métricas de inventario
        total_laptops=total_laptops,
        total_available=int(total_available),
        low_stock_count=low_stock_count,
        inventory_value=float(inventory_value),
        inventory_cost=float(inventory_cost),
        potential_profit=potential_profit,
        
        # Métricas de clientes
        total_customers=total_customers,
        active_customers=active_customers,
        new_customers_month=new_customers_month,
        
        # Métricas de ventas
        total_invoices=total_invoices,
        invoices_this_month=invoices_this_month,
        revenue_this_month=float(revenue_this_month),
        revenue_last_month=float(revenue_last_month),
        revenue_change=revenue_change,
        pending_invoices=pending_invoices,
        pending_amount=float(pending_amount),
        overdue_invoices=overdue_invoices,
        
        # Actividad reciente
        recent_invoices=recent_invoices,
        recent_laptops=recent_laptops,
        recent_customers=recent_customers,
        
        # Productos y distribución
        top_products=top_products,
        category_distribution=category_distribution,
        brand_distribution=brand_distribution,
        
        # Datos para gráficos
        daily_sales=daily_sales,
        
        # Alertas
        alerts=alerts
    )


# ============================================
# API ENDPOINTS PARA DATOS DINÁMICOS
# ============================================

@dashboard_bp.route('/api/metrics')
@login_required
def api_metrics():
    """
    Endpoint API para obtener métricas en formato JSON
    Útil para actualizar el dashboard sin recargar la página
    """
    
    total_laptops = Laptop.query.count()
    total_customers = Customer.query.count()
    total_invoices = Invoice.query.count()
    
    start_of_month, _ = get_date_range('month')
    revenue_this_month = db.session.query(
        func.sum(Invoice.total)
    ).filter(
        Invoice.invoice_date >= start_of_month,
        Invoice.status.in_(['issued', 'paid'])
    ).scalar() or 0
    
    return jsonify({
        'inventory': {
            'total_laptops': total_laptops,
            'total_customers': total_customers,
        },
        'sales': {
            'total_invoices': total_invoices,
            'revenue_this_month': float(revenue_this_month)
        }
    })


@dashboard_bp.route('/api/sales-chart/<period>')
@login_required
def api_sales_chart(period='week'):
    """
    Endpoint para obtener datos del gráfico de ventas
    
    Args:
        period: 'week', 'month', 'year'
    """
    
    if period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    else:
        days = 365
    
    sales_data = []
    for i in range(days - 1, -1, -1):
        day = date.today() - timedelta(days=i)
        sales = db.session.query(
            func.sum(Invoice.total)
        ).filter(
            Invoice.invoice_date == day,
            Invoice.status.in_(['issued', 'paid'])
        ).scalar() or 0
        
        sales_data.append({
            'date': day.isoformat(),
            'amount': float(sales)
        })
    
    return jsonify(sales_data)

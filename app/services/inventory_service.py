# ============================================
# INVENTORY SERVICE - Gestión de Inventario
# ============================================
# Responsabilidad: rotación, días en inventario, alertas

from datetime import datetime, timedelta


class InventoryService:
    """Servicio para análisis de inventario"""

    @staticmethod
    def calculate_days_in_inventory(entry_date, sale_date=None):
        """
        Calcula los días que una laptop ha estado en inventario

        Args:
            entry_date: Fecha de ingreso (datetime.date o datetime.datetime)
            sale_date: Fecha de venta (datetime.date o datetime.datetime), opcional

        Returns:
            int: Días en inventario
        """
        from datetime import datetime, date

        if not entry_date:
            return 0

        # Convertir entry_date a date si es datetime
        if isinstance(entry_date, datetime):
            entry_date = entry_date.date()

        # Si hay fecha de venta, calcular días hasta la venta
        if sale_date:
            # Convertir sale_date a date si es datetime
            if isinstance(sale_date, datetime):
                sale_date = sale_date.date()

            delta = sale_date - entry_date
            return delta.days

        # Si no hay fecha de venta, calcular días hasta hoy
        today = date.today()
        delta = today - entry_date
        return delta.days

    @staticmethod
    def determine_rotation_status(days_in_inventory):
        """
        Determina el estado de rotación

        Args:
            days_in_inventory: Días en inventario

        Returns:
            str: 'fast', 'medium', 'slow'
        """
        if days_in_inventory <= 30:
            return 'fast'
        elif days_in_inventory <= 60:
            return 'medium'
        else:
            return 'slow'

    @staticmethod
    def check_stock_alert(quantity, min_alert):
        """
        Verifica si hay alerta de stock bajo

        Returns:
            tuple (needs_reorder, message)
        """
        if quantity <= 0:
            return True, "⚠️ SIN STOCK - Reordenar urgentemente"
        elif quantity <= min_alert:
            return True, f"⚠️ Stock bajo ({quantity} unidades) - Considere reordenar"
        else:
            return False, f"✅ Stock suficiente ({quantity} unidades)"

    @staticmethod
    def get_inventory_health_score(laptops_list):
        """
        Calcula un "score" de salud del inventario

        Args:
            laptops_list: Lista de laptops

        Returns:
            dict con métricas de salud
        """
        if not laptops_list:
            return {
                'score': 0,
                'total': 0,
                'fast_rotation': 0,
                'slow_rotation': 0,
                'low_stock': 0
            }

        total = len(laptops_list)
        fast_count = sum(1 for l in laptops_list if l.rotation_status == 'fast')
        slow_count = sum(1 for l in laptops_list if l.rotation_status == 'slow')
        low_stock_count = sum(1 for l in laptops_list if l.quantity <= l.min_alert)

        # Score: 100 puntos base - penalizaciones
        score = 100
        score -= (slow_count / total) * 30  # Penalizar rotación lenta
        score -= (low_stock_count / total) * 20  # Penalizar stock bajo

        return {
            'score': round(max(score, 0), 2),
            'total': total,
            'fast_rotation': fast_count,
            'slow_rotation': slow_count,
            'low_stock': low_stock_count
        }
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
        Calcula días en inventario

        Args:
            entry_date: Fecha de ingreso
            sale_date: Fecha de venta (None si aún no se vendió)

        Returns:
            Número de días
        """
        if sale_date:
            delta = sale_date - entry_date
        else:
            delta = datetime.utcnow() - entry_date

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
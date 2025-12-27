# ============================================
# FINANCIAL SERVICE - Cálculos Financieros
# ============================================
# Responsabilidad única: cálculos de costos, precios, márgenes

from decimal import Decimal


class FinancialService:
    """Servicio para cálculos financieros"""

    @staticmethod
    def calculate_margin(purchase_cost, sale_price):
        """
        Calcula el margen de ganancia

        Returns:
            dict con total_cost, gross_profit, margin_percentage
        """
        purchase_cost = Decimal(str(purchase_cost)) if purchase_cost else Decimal('0')
        sale_price = Decimal(str(sale_price)) if sale_price else Decimal('0')

        # Por ahora, total_cost = purchase_cost
        # Aquí se pueden agregar costos adicionales (envío, impuestos, etc.)
        total_cost = purchase_cost

        # Ganancia bruta
        gross_profit = sale_price - total_cost

        # Margen porcentual
        if sale_price > 0:
            margin_percentage = (gross_profit / sale_price) * 100
        else:
            margin_percentage = Decimal('0')

        return {
            'total_cost': round(total_cost, 2),
            'gross_profit': round(gross_profit, 2),
            'margin_percentage': round(margin_percentage, 2)
        }

    @staticmethod
    def validate_prices(purchase_cost, sale_price):
        """
        Valida que el precio de venta no sea menor al costo

        Returns:
            tuple (is_valid, error_message)
        """
        if not purchase_cost or not sale_price:
            return False, "Costos y precios son requeridos"

        if sale_price < purchase_cost:
            return False, "El precio de venta no puede ser menor al costo de compra"

        return True, None

    @staticmethod
    def suggest_sale_price(purchase_cost, target_margin_percentage=25):
        """
        Sugiere un precio de venta basado en un margen objetivo

        Args:
            purchase_cost: Costo de compra
            target_margin_percentage: Margen objetivo (default 25%)

        Returns:
            Precio de venta sugerido
        """
        purchase_cost = Decimal(str(purchase_cost))
        target_margin = Decimal(str(target_margin_percentage)) / 100

        # Fórmula: precio_venta = costo / (1 - margen)
        suggested_price = purchase_cost / (1 - target_margin)

        return round(suggested_price, 2)
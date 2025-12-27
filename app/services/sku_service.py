# ============================================
# SKU SERVICE - Generación de SKU
# ============================================
# Responsabilidad única: generar SKUs únicos

from datetime import datetime
from app import db


class SKUService:
    """Servicio para generar SKUs únicos"""

    @staticmethod
    def generate_laptop_sku():
        """
        Genera un SKU único para laptops
        Formato: LX-YYYYMMDD-XXXX
        Ejemplo: LX-20250101-0001
        """
        from app.models.laptop import Laptop

        # Obtener fecha actual
        date_str = datetime.utcnow().strftime('%Y%m%d')
        prefix = 'LX'

        # Buscar el último SKU del día
        last_laptop = Laptop.query.filter(
            Laptop.sku.like(f'{prefix}-{date_str}-%')
        ).order_by(Laptop.sku.desc()).first()

        if last_laptop:
            # Extraer el número secuencial y sumar 1
            last_number = int(last_laptop.sku.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        # Formatear con 4 dígitos
        return f'{prefix}-{date_str}-{new_number:04d}'

    @staticmethod
    def validate_sku(sku):
        """Valida el formato de un SKU"""
        import re
        pattern = r'^LX-\d{8}-\d{4}$'
        return bool(re.match(pattern, sku))
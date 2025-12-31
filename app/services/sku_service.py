# ============================================
# SKU SERVICE - Generación de SKU
# ============================================
# Responsabilidad única: generar SKUs únicos
# Actualizado al nuevo modelo de datos

from datetime import datetime
from app import db
import re


class SKUService:
    """Servicio para generar SKUs únicos"""

    @staticmethod
    def generate_laptop_sku(prefix='LX'):
        """
        Genera un SKU único para laptops
        Formato: LX-YYYYMMDD-XXXX
        Ejemplo: LX-20250101-0001

        Args:
            prefix: Prefijo del SKU (default: 'LX')

        Returns:
            str: SKU único generado
        """
        from app.models.laptop import Laptop

        # Obtener fecha actual
        date_str = datetime.utcnow().strftime('%Y%m%d')

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
    def generate_custom_sku(prefix, category_code=None):
        """
        Genera un SKU personalizado con código de categoría opcional

        Formato: PREFIX-CAT-YYYYMMDD-XXXX
        Ejemplo: LX-GAM-20250101-0001 (para gaming)

        Args:
            prefix: Prefijo del SKU
            category_code: Código de categoría (3 letras)

        Returns:
            str: SKU único generado
        """
        from app.models.laptop import Laptop

        date_str = datetime.utcnow().strftime('%Y%m%d')

        if category_code:
            pattern = f'{prefix}-{category_code}-{date_str}-%'
            sku_format = f'{prefix}-{category_code}-{date_str}-{{:04d}}'
        else:
            pattern = f'{prefix}-{date_str}-%'
            sku_format = f'{prefix}-{date_str}-{{:04d}}'

        last_laptop = Laptop.query.filter(
            Laptop.sku.like(pattern)
        ).order_by(Laptop.sku.desc()).first()

        if last_laptop:
            last_number = int(last_laptop.sku.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1

        return sku_format.format(new_number)

    @staticmethod
    def get_category_code(category):
        """
        Obtiene el código de categoría para SKU

        Args:
            category: Nombre de la categoría

        Returns:
            str: Código de 3 letras
        """
        category_codes = {
            'laptop': 'LAP',
            'workstation': 'WKS',
            'gaming': 'GAM'
        }
        return category_codes.get(category, 'GEN')

    @staticmethod
    def validate_sku(sku):
        """
        Valida el formato de un SKU

        Args:
            sku: SKU a validar

        Returns:
            bool: True si el formato es válido
        """
        # Patrón básico: XX-YYYYMMDD-XXXX
        basic_pattern = r'^[A-Z]{2}-\d{8}-\d{4}$'

        # Patrón con categoría: XX-XXX-YYYYMMDD-XXXX
        category_pattern = r'^[A-Z]{2}-[A-Z]{3}-\d{8}-\d{4}$'

        return bool(re.match(basic_pattern, sku) or re.match(category_pattern, sku))

    @staticmethod
    def parse_sku(sku):
        """
        Parsea un SKU y extrae sus componentes

        Args:
            sku: SKU a parsear

        Returns:
            dict: Componentes del SKU o None si es inválido
        """
        if not SKUService.validate_sku(sku):
            return None

        parts = sku.split('-')

        if len(parts) == 3:
            # Formato básico: LX-YYYYMMDD-XXXX
            return {
                'prefix': parts[0],
                'category_code': None,
                'date': parts[1],
                'sequence': int(parts[2])
            }
        elif len(parts) == 4:
            # Formato con categoría: LX-GAM-YYYYMMDD-XXXX
            return {
                'prefix': parts[0],
                'category_code': parts[1],
                'date': parts[2],
                'sequence': int(parts[3])
            }

        return None

    @staticmethod
    def is_sku_available(sku):
        """
        Verifica si un SKU está disponible (no existe en la base de datos)

        Args:
            sku: SKU a verificar

        Returns:
            bool: True si el SKU está disponible
        """
        from app.models.laptop import Laptop

        existing = Laptop.query.filter_by(sku=sku).first()
        return existing is None

    @staticmethod
    def get_next_sequence_number(prefix, date_str=None, category_code=None):
        """
        Obtiene el siguiente número de secuencia disponible

        Args:
            prefix: Prefijo del SKU
            date_str: Fecha en formato YYYYMMDD (default: hoy)
            category_code: Código de categoría opcional

        Returns:
            int: Siguiente número de secuencia
        """
        from app.models.laptop import Laptop

        if date_str is None:
            date_str = datetime.utcnow().strftime('%Y%m%d')

        if category_code:
            pattern = f'{prefix}-{category_code}-{date_str}-%'
        else:
            pattern = f'{prefix}-{date_str}-%'

        last_laptop = Laptop.query.filter(
            Laptop.sku.like(pattern)
        ).order_by(Laptop.sku.desc()).first()

        if last_laptop:
            return int(last_laptop.sku.split('-')[-1]) + 1
        return 1
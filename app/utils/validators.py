# ============================================
# VALIDADORES PERSONALIZADOS
# ============================================
# Validadores reutilizables para WTForms

from wtforms.validators import ValidationError
from decimal import Decimal
import re


class PositiveNumber:
    """
    Valida que un número sea positivo (mayor a 0)

    Uso en formularios:
        price = DecimalField('Precio', validators=[
            DataRequired(),
            PositiveNumber(message='El precio debe ser mayor a 0')
        ])
    """

    def __init__(self, message=None):
        if not message:
            message = 'El valor debe ser mayor a 0'
        self.message = message

    def __call__(self, form, field):
        if field.data is None:
            return

        try:
            value = Decimal(str(field.data))
            if value <= 0:
                raise ValidationError(self.message)
        except (ValueError, TypeError):
            raise ValidationError('Valor numérico inválido')


class PositiveOrZero:
    """
    Valida que un número sea positivo o cero (>= 0)

    Útil para cantidad, stock, etc.
    """

    def __init__(self, message=None):
        if not message:
            message = 'El valor debe ser mayor o igual a 0'
        self.message = message

    def __call__(self, form, field):
        if field.data is None:
            return

        try:
            value = Decimal(str(field.data)) if isinstance(field.data, (str, float)) else int(field.data)
            if value < 0:
                raise ValidationError(self.message)
        except (ValueError, TypeError):
            raise ValidationError('Valor numérico inválido')


class PriceValidator:
    """
    Valida precios con límites min/max

    Uso:
        sale_price = DecimalField('Precio Venta', validators=[
            DataRequired(),
            PriceValidator(min_price=1, max_price=10000)
        ])
    """

    def __init__(self, min_price=0, max_price=None, message=None):
        self.min_price = Decimal(str(min_price))
        self.max_price = Decimal(str(max_price)) if max_price else None
        self.message = message

    def __call__(self, form, field):
        if field.data is None:
            return

        try:
            price = Decimal(str(field.data))

            if price < self.min_price:
                raise ValidationError(
                    self.message or f'El precio debe ser mayor o igual a ${self.min_price}'
                )

            if self.max_price and price > self.max_price:
                raise ValidationError(
                    self.message or f'El precio no puede exceder ${self.max_price}'
                )

        except (ValueError, TypeError):
            raise ValidationError('Precio inválido')


class SalePriceValidator:
    """
    Valida que el precio de venta sea mayor al costo de compra

    Uso:
        sale_price = DecimalField('Precio Venta', validators=[
            DataRequired(),
            SalePriceValidator('purchase_cost')
        ])

    Args:
        purchase_cost_field: Nombre del campo de costo de compra
    """

    def __init__(self, purchase_cost_field='purchase_cost', message=None):
        self.purchase_cost_field = purchase_cost_field
        if not message:
            message = 'El precio de venta no puede ser menor al costo de compra'
        self.message = message

    def __call__(self, form, field):
        if field.data is None:
            return

        # Obtener el campo de costo de compra
        purchase_cost = getattr(form, self.purchase_cost_field, None)

        if purchase_cost is None or purchase_cost.data is None:
            return  # No validar si no hay costo de compra

        try:
            sale_price = Decimal(str(field.data))
            cost = Decimal(str(purchase_cost.data))

            if sale_price < cost:
                raise ValidationError(self.message)

        except (ValueError, TypeError):
            raise ValidationError('Valores numéricos inválidos')


class MinimumMarginValidator:
    """
    Valida que haya un margen mínimo de ganancia

    Uso:
        sale_price = DecimalField('Precio Venta', validators=[
            DataRequired(),
            MinimumMarginValidator('purchase_cost', min_margin=10)
        ])

    Args:
        purchase_cost_field: Nombre del campo de costo
        min_margin: Margen mínimo en porcentaje
    """

    def __init__(self, purchase_cost_field='purchase_cost', min_margin=5, message=None):
        self.purchase_cost_field = purchase_cost_field
        self.min_margin = Decimal(str(min_margin))
        self.message = message

    def __call__(self, form, field):
        if field.data is None:
            return

        purchase_cost = getattr(form, self.purchase_cost_field, None)

        if purchase_cost is None or purchase_cost.data is None:
            return

        try:
            sale_price = Decimal(str(field.data))
            cost = Decimal(str(purchase_cost.data))

            if sale_price <= 0:
                return  # Otro validador se encargará

            # Calcular margen: ((venta - costo) / venta) * 100
            margin = ((sale_price - cost) / sale_price) * 100

            if margin < self.min_margin:
                raise ValidationError(
                    self.message or f'El margen debe ser al menos {self.min_margin}%. Margen actual: {margin:.1f}%'
                )

        except (ValueError, TypeError, ZeroDivisionError):
            raise ValidationError('Error al calcular margen')


class QuantityValidator:
    """
    Valida cantidades de inventario
    """

    def __init__(self, min_quantity=0, max_quantity=9999, message=None):
        self.min_quantity = min_quantity
        self.max_quantity = max_quantity
        self.message = message

    def __call__(self, form, field):
        if field.data is None:
            return

        try:
            quantity = int(field.data)

            if quantity < self.min_quantity:
                raise ValidationError(
                    self.message or f'La cantidad debe ser al menos {self.min_quantity}'
                )

            if quantity > self.max_quantity:
                raise ValidationError(
                    self.message or f'La cantidad no puede exceder {self.max_quantity}'
                )

        except (ValueError, TypeError):
            raise ValidationError('Cantidad inválida')


class SKUValidator:
    """
    Valida el formato del SKU
    Formato esperado: LX-YYYYMMDD-XXXX
    """

    def __init__(self, message=None):
        if not message:
            message = 'Formato de SKU inválido. Esperado: LX-YYYYMMDD-XXXX'
        self.message = message
        self.pattern = re.compile(r'^LX-\d{8}-\d{4}$')

    def __call__(self, form, field):
        if not field.data:
            return  # Permitir vacío si no es requerido

        if not self.pattern.match(field.data):
            raise ValidationError(self.message)


class AlphanumericValidator:
    """
    Valida que solo contenga caracteres alfanuméricos y espacios
    """

    def __init__(self, allow_spaces=True, allow_dashes=False, message=None):
        self.allow_spaces = allow_spaces
        self.allow_dashes = allow_dashes

        # Construir patrón regex
        pattern = r'^[a-zA-Z0-9'
        if allow_spaces:
            pattern += r'\s'
        if allow_dashes:
            pattern += r'\-'
        pattern += r']+$'

        self.pattern = re.compile(pattern)

        if not message:
            allowed = 'alfanuméricos'
            if allow_spaces:
                allowed += ', espacios'
            if allow_dashes:
                allowed += ', guiones'
            message = f'Solo se permiten caracteres {allowed}'

        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        if not self.pattern.match(field.data):
            raise ValidationError(self.message)


class UniqueValue:
    """
    Valida que un valor sea único en la base de datos

    Uso:
        name = StringField('Nombre', validators=[
            DataRequired(),
            UniqueValue(Brand, Brand.name, message='Esta marca ya existe')
        ])

    Args:
        model: Modelo de SQLAlchemy
        field: Campo del modelo a verificar
        message: Mensaje de error personalizado
        exclude_id: ID a excluir de la búsqueda (para ediciones)
    """

    def __init__(self, model, field, message=None, exclude_id=None):
        self.model = model
        self.field = field
        self.exclude_id = exclude_id
        if not message:
            message = 'Este valor ya existe'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        # Construir query
        query = self.model.query.filter(self.field == field.data)

        # Excluir ID si es una edición
        if self.exclude_id:
            query = query.filter(self.model.id != self.exclude_id)

        # Verificar si existe
        if query.first():
            raise ValidationError(self.message)


class DateRangeValidator:
    """
    Valida que una fecha esté dentro de un rango
    """

    def __init__(self, min_date=None, max_date=None, message=None):
        self.min_date = min_date
        self.max_date = max_date
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        if self.min_date and field.data < self.min_date:
            raise ValidationError(
                self.message or f'La fecha debe ser posterior a {self.min_date}'
            )

        if self.max_date and field.data > self.max_date:
            raise ValidationError(
                self.message or f'La fecha debe ser anterior a {self.max_date}'
            )


class ConditionalRequired:
    """
    Campo requerido solo si se cumple una condición

    Uso:
        aesthetic_grade = StringField('Grado Estético', validators=[
            ConditionalRequired('condition', 'refurbished',
                message='El grado estético es requerido para productos refurbished')
        ])

    Args:
        other_field: Nombre del otro campo
        value: Valor que debe tener el otro campo
    """

    def __init__(self, other_field, value, message=None):
        self.other_field = other_field
        self.value = value
        if not message:
            message = 'Este campo es requerido'
        self.message = message

    def __call__(self, form, field):
        other = getattr(form, self.other_field, None)

        if other is None:
            return

        if other.data == self.value:
            if not field.data or (isinstance(field.data, str) and not field.data.strip()):
                raise ValidationError(self.message)


class FileExtensionValidator:
    """
    Valida la extensión de un archivo

    Uso:
        image = FileField('Imagen', validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'gif'])
        ])
    """

    def __init__(self, allowed_extensions, message=None):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]
        if not message:
            message = f'Solo se permiten archivos: {", ".join(self.allowed_extensions)}'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        filename = field.data.filename

        if '.' not in filename:
            raise ValidationError('El archivo debe tener una extensión')

        extension = filename.rsplit('.', 1)[1].lower()

        if extension not in self.allowed_extensions:
            raise ValidationError(self.message)


class MaxFileSizeValidator:
    """
    Valida el tamaño máximo de un archivo

    Uso:
        image = FileField('Imagen', validators=[
            MaxFileSizeValidator(max_size_mb=5)
        ])
    """

    def __init__(self, max_size_mb=5, message=None):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        if not message:
            message = f'El archivo no puede exceder {max_size_mb}MB'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        # Leer tamaño del archivo
        field.data.seek(0, 2)  # Ir al final
        size = field.data.tell()
        field.data.seek(0)  # Volver al inicio

        if size > self.max_size_bytes:
            raise ValidationError(self.message)
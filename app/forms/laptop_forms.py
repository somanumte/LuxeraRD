# ============================================
# FORMULARIOS DE INVENTARIO DE LAPTOPS
# ============================================

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, DecimalField, IntegerField,
    TextAreaField, BooleanField, SubmitField, HiddenField,
    DateField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from app.utils.validators import (
    PositiveNumber, PositiveOrZero, SalePriceValidator,
    MinimumMarginValidator, QuantityValidator, SKUValidator
)
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, StorageType, RAMType, Store, Location
)


class LaptopForm(FlaskForm):
    """
    Formulario principal para agregar/editar laptops
    """

    # ===== SKU (autogenerado o manual) =====
    sku = StringField(
        'SKU',
        validators=[Optional(), SKUValidator()],
        render_kw={
            'placeholder': 'Se generará automáticamente',
            'class': 'form-input',
            'readonly': True
        }
    )

    # ===== ESPECIFICACIONES TÉCNICAS =====
    # Todos los dropdowns con Select2 para búsqueda y creación dinámica

    brand_id = SelectField(
        'Marca',
        coerce=int,
        validators=[DataRequired(message='La marca es requerida')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Selecciona o crea una marca',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/brands'
        }
    )

    model_id = SelectField(
        'Modelo',
        coerce=int,
        validators=[DataRequired(message='El modelo es requerido')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Selecciona o crea un modelo',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/models'
        }
    )

    processor_id = SelectField(
        'Procesador',
        coerce=int,
        validators=[DataRequired(message='El procesador es requerido')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: Intel Core i7-12700H',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/processors'
        }
    )

    os_id = SelectField(
        'Sistema Operativo',
        coerce=int,
        validators=[DataRequired(message='El sistema operativo es requerido')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: Windows 11 Pro',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/operating-systems'
        }
    )

    screen_id = SelectField(
        'Pantalla',
        coerce=int,
        validators=[DataRequired(message='La pantalla es requerida')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: 15.6" FHD IPS',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/screens'
        }
    )

    graphics_card_id = SelectField(
        'Tarjeta Gráfica',
        coerce=int,
        validators=[DataRequired(message='La tarjeta gráfica es requerida')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: NVIDIA RTX 4060',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/graphics-cards'
        }
    )

    storage_id = SelectField(
        'Almacenamiento',
        coerce=int,
        validators=[DataRequired(message='El almacenamiento es requerido')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: 512GB SSD NVMe',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/storage-types'
        }
    )

    storage_upgradeable = BooleanField(
        'Almacenamiento ampliable',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    ram_id = SelectField(
        'RAM',
        coerce=int,
        validators=[DataRequired(message='La RAM es requerida')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: 16GB DDR5',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/ram-types'
        }
    )

    ram_upgradeable = BooleanField(
        'RAM ampliable',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    npu = StringField(
        'NPU (Neural Processing Unit)',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'placeholder': 'Ej: Intel AI Boost, AMD Ryzen AI',
            'class': 'form-input'
        }
    )

    # ===== PRECIOS Y COSTOS =====

    purchase_cost = DecimalField(
        'Costo de Compra ($)',
        places=2,
        validators=[
            DataRequired(message='El costo de compra es requerido'),
            PositiveNumber(message='El costo debe ser mayor a 0')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0.01',
            'id': 'purchase_cost'
        }
    )

    sale_price = DecimalField(
        'Precio de Venta ($)',
        places=2,
        validators=[
            DataRequired(message='El precio de venta es requerido'),
            PositiveNumber(message='El precio debe ser mayor a 0'),
            SalePriceValidator('purchase_cost')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0.01',
            'id': 'sale_price'
        }
    )

    # Campo oculto para mostrar el margen (calculado por JavaScript)
    margin_percentage = HiddenField('Margen %')

    # ===== INVENTARIO =====

    quantity = IntegerField(
        'Cantidad',
        validators=[
            DataRequired(message='La cantidad es requerida'),
            QuantityValidator(min_quantity=0, max_quantity=9999)
        ],
        default=1,
        render_kw={
            'placeholder': '1',
            'class': 'form-input',
            'min': '0',
            'max': '9999'
        }
    )

    min_alert = IntegerField(
        'Alerta Mínima',
        validators=[
            DataRequired(message='La alerta mínima es requerida'),
            PositiveOrZero(message='La alerta debe ser 0 o mayor')
        ],
        default=1,
        render_kw={
            'placeholder': '1',
            'class': 'form-input',
            'min': '0'
        }
    )

    # ===== CATEGORÍA =====

    category = SelectField(
        'Categoría',
        choices=[
            ('', 'Selecciona una categoría'),
            ('gamer', '🎮 Gamer'),
            ('working', '💼 Trabajo/Productividad'),
            ('home', '🏠 Uso Doméstico')
        ],
        validators=[DataRequired(message='La categoría es requerida')],
        render_kw={
            'class': 'form-input'
        }
    )

    # ===== UBICACIÓN =====

    store_id = SelectField(
        'Tienda',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Selecciona o crea una tienda',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/stores'
        }
    )

    location_id = SelectField(
        'Ubicación',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: Estante A-1, Vitrina 3',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/locations'
        }
    )

    # ===== CONDICIÓN Y ESTADO =====

    condition = SelectField(
        'Condición',
        choices=[
            ('', 'Selecciona condición'),
            ('new', '✨ Nuevo'),
            ('used', '📦 Usado'),
            ('refurbished', '♻️ Refurbished')
        ],
        validators=[DataRequired(message='La condición es requerida')],
        render_kw={
            'class': 'form-input',
            'id': 'condition'
        }
    )

    aesthetic_grade = SelectField(
        'Grado Estético',
        choices=[
            ('', 'Selecciona grado'),
            ('A+', 'A+ (Excelente)'),
            ('A', 'A (Muy Bueno)'),
            ('B', 'B (Bueno)'),
            ('C', 'C (Aceptable)')
        ],
        validators=[Optional()],
        render_kw={
            'class': 'form-input',
            'id': 'aesthetic_grade'
        }
    )

    # ===== FECHAS =====

    entry_date = DateField(
        'Fecha de Ingreso',
        validators=[DataRequired(message='La fecha de ingreso es requerida')],
        format='%Y-%m-%d',
        render_kw={
            'class': 'form-input',
            'type': 'date'
        }
    )

    sale_date = DateField(
        'Fecha de Venta',
        validators=[Optional()],
        format='%Y-%m-%d',
        render_kw={
            'class': 'form-input',
            'type': 'date'
        }
    )

    # ===== NOTAS =====

    notes = TextAreaField(
        'Notas Adicionales',
        validators=[Optional(), Length(max=1000)],
        render_kw={
            'placeholder': 'Información adicional, observaciones, etc.',
            'class': 'form-input',
            'rows': '4'
        }
    )

    # ===== SUBMIT =====

    submit = SubmitField(
        'Guardar Laptop',
        render_kw={
            'class': 'w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300'
        }
    )

    def __init__(self, *args, **kwargs):
        """Inicializa el formulario y carga las opciones de los selectores"""
        super(LaptopForm, self).__init__(*args, **kwargs)

        # Cargar opciones para los SelectFields desde la base de datos
        # Solo cargamos las opciones iniciales, Select2 manejará la búsqueda dinámica

        # Brands
        self.brand_id.choices = [(0, 'Selecciona o crea una marca')] + [
            (b.id, b.name) for b in Brand.query.filter_by(is_active=True).order_by(Brand.name).all()
        ]

        # Models
        self.model_id.choices = [(0, 'Selecciona o crea un modelo')] + [
            (m.id, m.name) for m in LaptopModel.query.filter_by(is_active=True).order_by(LaptopModel.name).all()
        ]

        # Processors
        self.processor_id.choices = [(0, 'Selecciona o crea un procesador')] + [
            (p.id, p.name) for p in Processor.query.filter_by(is_active=True).order_by(Processor.name).all()
        ]

        # Operating Systems
        self.os_id.choices = [(0, 'Selecciona o crea un SO')] + [
            (os.id, os.name) for os in
            OperatingSystem.query.filter_by(is_active=True).order_by(OperatingSystem.name).all()
        ]

        # Screens
        self.screen_id.choices = [(0, 'Selecciona o crea una pantalla')] + [
            (s.id, s.name) for s in Screen.query.filter_by(is_active=True).order_by(Screen.name).all()
        ]

        # Graphics Cards
        self.graphics_card_id.choices = [(0, 'Selecciona o crea una GPU')] + [
            (g.id, g.name) for g in GraphicsCard.query.filter_by(is_active=True).order_by(GraphicsCard.name).all()
        ]

        # Storage Types
        self.storage_id.choices = [(0, 'Selecciona o crea almacenamiento')] + [
            (st.id, st.name) for st in StorageType.query.filter_by(is_active=True).order_by(StorageType.name).all()
        ]

        # RAM Types
        self.ram_id.choices = [(0, 'Selecciona o crea RAM')] + [
            (r.id, r.name) for r in RAMType.query.filter_by(is_active=True).order_by(RAMType.name).all()
        ]

        # Stores
        self.store_id.choices = [(0, 'Selecciona o crea una tienda')] + [
            (s.id, s.name) for s in Store.query.filter_by(is_active=True).order_by(Store.name).all()
        ]

        # Locations
        self.location_id.choices = [(0, 'Selecciona o crea una ubicación')] + [
            (l.id, l.name) for l in Location.query.filter_by(is_active=True).order_by(Location.name).all()
        ]

    def validate_sale_date(self, field):
        """Valida que la fecha de venta sea posterior a la de ingreso"""
        if field.data and self.entry_date.data:
            if field.data < self.entry_date.data:
                raise ValidationError('La fecha de venta no puede ser anterior a la fecha de ingreso')

    def validate_aesthetic_grade(self, field):
        """El grado estético solo es requerido para productos refurbished"""
        if self.condition.data == 'refurbished':
            if not field.data or field.data == '':
                raise ValidationError('El grado estético es requerido para productos refurbished')


class QuickSearchForm(FlaskForm):
    """Formulario de búsqueda rápida"""

    search = StringField(
        'Buscar',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Buscar por SKU, marca, modelo...',
            'class': 'form-input',
            'autocomplete': 'off'
        }
    )

    submit = SubmitField('Buscar')


class FilterForm(FlaskForm):
    """Formulario de filtros avanzados"""

    store_id = SelectField(
        'Tienda',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    brand_id = SelectField(
        'Marca',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    category = SelectField(
        'Categoría',
        choices=[
            ('', 'Todas'),
            ('gamer', '🎮 Gamer'),
            ('working', '💼 Trabajo'),
            ('home', '🏠 Hogar')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    processor_id = SelectField(
        'Procesador',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    graphics_card_id = SelectField(
        'Tarjeta Gráfica',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    # NUEVO: Filtro por pantalla
    screen_id = SelectField(
        'Pantalla',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
    condition = SelectField(
        'Condición',
        choices=[
            ('', 'Todas'),
            ('new', '✨ Nuevo'),
            ('used', '📦 Usado'),
            ('refurbished', '♻️ Refurbished')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    min_price = DecimalField(
        'Precio Mínimo',
        places=2,
        validators=[Optional(), PositiveOrZero()],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01'
        }
    )

    max_price = DecimalField(
        'Precio Máximo',
        places=2,
        validators=[Optional(), PositiveOrZero()],
        render_kw={
            'placeholder': '9999.99',
            'class': 'form-input',
            'step': '0.01'
        }
    )

    submit = SubmitField('Filtrar', render_kw={'class': 'btn-primary'})

    def __init__(self, *args, **kwargs):
        super(FilterForm, self).__init__(*args, **kwargs)

        # Cargar tiendas
        self.store_id.choices = [(0, 'Todas las tiendas')] + [
            (s.id, s.name) for s in Store.query.filter_by(is_active=True).order_by(Store.name).all()
        ]

        # Cargar marcas
        self.brand_id.choices = [(0, 'Todas las marcas')] + [
            (b.id, b.name) for b in Brand.query.filter_by(is_active=True).order_by(Brand.name).all()
        ]

        # Cargar procesadores
        self.processor_id.choices = [(0, 'Todos los procesadores')] + [
            (p.id, p.name) for p in Processor.query.filter_by(is_active=True).order_by(Processor.name).all()
        ]

        # Cargar tarjetas gráficas
        self.graphics_card_id.choices = [(0, 'Todas las GPUs')] + [
            (g.id, g.name) for g in GraphicsCard.query.filter_by(is_active=True).order_by(GraphicsCard.name).all()
        ]
        # Cargar pantallas
        self.screen_id.choices = [(0, 'Todas las pantallas')] + [
            (s.id, s.name) for s in Screen.query.filter_by(is_active=True).order_by(Screen.name).all()
        ]

# Importar ValidationError al final para evitar importación circular
from wtforms.validators import ValidationError
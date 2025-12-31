# ============================================
# FORMULARIOS DE INVENTARIO DE LAPTOPS
# ============================================
# Actualizado al nuevo modelo de datos

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, SelectField, DecimalField, IntegerField,
    TextAreaField, BooleanField, SubmitField, HiddenField,
    DateField, SelectMultipleField, FieldList, FormField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError, URL, Regexp
from app.utils.validators import (
    PositiveNumber, PositiveOrZero, SalePriceValidator,
    MinimumMarginValidator, QuantityValidator, SKUValidator
)
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)


# ===== OPCIONES DE PUERTOS DE CONECTIVIDAD =====
CONNECTIVITY_PORTS_CHOICES = [
    ('usb_a_2', 'USB-A 2.0'),
    ('usb_a_3', 'USB-A 3.0'),
    ('usb_a_31', 'USB-A 3.1'),
    ('usb_c', 'USB-C'),
    ('usb_c_thunderbolt', 'USB-C Thunderbolt'),
    ('hdmi', 'HDMI'),
    ('hdmi_21', 'HDMI 2.1'),
    ('displayport', 'DisplayPort'),
    ('mini_displayport', 'Mini DisplayPort'),
    ('ethernet', 'Ethernet RJ-45'),
    ('sd_card', 'Lector SD'),
    ('microsd', 'Lector MicroSD'),
    ('audio_jack', 'Jack Audio 3.5mm'),
    ('vga', 'VGA'),
    ('dvi', 'DVI'),
]

# ===== OPCIONES DE KEYBOARD LAYOUT =====
KEYBOARD_LAYOUT_CHOICES = [
    ('US', 'US - Ingles'),
    ('UK', 'UK - Ingles britanico'),
    ('ES', 'ES - Espanol Espana'),
    ('LATAM', 'LATAM - Espanol Latinoamerica'),
    ('DE', 'DE - Aleman'),
    ('FR', 'FR - Frances'),
    ('IT', 'IT - Italiano'),
    ('PT', 'PT - Portugues'),
    ('BR', 'BR - Portugues Brasil'),
    ('JP', 'JP - Japones'),
    ('KR', 'KR - Coreano'),
    ('CN', 'CN - Chino'),
]


class LaptopForm(FlaskForm):
    """
    Formulario principal para agregar/editar laptops
    """

    # ===== 1. IDENTIFICADORES =====
    sku = StringField(
        'SKU',
        validators=[Optional(), SKUValidator()],
        render_kw={
            'placeholder': 'Se generara automaticamente',
            'class': 'form-input',
            'readonly': True
        }
    )

    slug = StringField(
        'Slug (URL amigable)',
        validators=[
            Optional(),
            Length(max=255),
            Regexp(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', message='Solo letras minusculas, numeros y guiones')
        ],
        render_kw={
            'placeholder': 'Se generara automaticamente del nombre',
            'class': 'form-input'
        }
    )

    # ===== 2. MARKETING Y WEB (SEO) =====
    display_name = StringField(
        'Nombre Comercial',
        validators=[
            DataRequired(message='El nombre comercial es requerido'),
            Length(max=200)
        ],
        render_kw={
            'placeholder': 'Ej: Dell XPS 15 - Intel i7 - 16GB RAM - 512GB SSD',
            'class': 'form-input'
        }
    )

    short_description = TextAreaField(
        'Descripcion Corta',
        validators=[Optional(), Length(max=300)],
        render_kw={
            'placeholder': 'Descripcion breve para tarjetas de producto (max. 300 caracteres)',
            'class': 'form-input',
            'rows': '2'
        }
    )

    long_description_html = TextAreaField(
        'Descripcion Completa (HTML/Markdown)',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Descripcion detallada del producto. Soporta HTML y Markdown.',
            'class': 'form-input',
            'rows': '6'
        }
    )

    is_published = BooleanField(
        'Publicado',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    is_featured = BooleanField(
        'Destacado',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    seo_title = StringField(
        'Titulo SEO',
        validators=[Optional(), Length(max=70)],
        render_kw={
            'placeholder': 'Titulo para motores de busqueda (max. 70 caracteres)',
            'class': 'form-input'
        }
    )

    seo_description = StringField(
        'Descripcion SEO',
        validators=[Optional(), Length(max=160)],
        render_kw={
            'placeholder': 'Meta descripcion para SEO (max. 160 caracteres)',
            'class': 'form-input'
        }
    )

    # ===== 3. ESPECIFICACIONES TA‰CNICAS =====
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
        'Tarjeta Grafica',
        coerce=int,
        validators=[DataRequired(message='La tarjeta grafica es requerida')],
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
            'data-endpoint': '/api/catalog/storage'
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
            'data-endpoint': '/api/catalog/ram'
        }
    )

    ram_upgradeable = BooleanField(
        'RAM ampliable',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    # ===== 4. DETALLES TA‰CNICOS ESPECAFICOS =====
    npu = BooleanField(
        'Tiene NPU (Procesador de IA)',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    keyboard_layout = SelectField(
        'Distribucion del Teclado',
        choices=KEYBOARD_LAYOUT_CHOICES,
        default='US',
        validators=[DataRequired(message='La distribucion del teclado es requerida')],
        render_kw={
            'class': 'form-input'
        }
    )

    connectivity_ports = SelectMultipleField(
        'Puertos de Conectividad',
        choices=CONNECTIVITY_PORTS_CHOICES,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-multiple',
            'data-placeholder': 'Selecciona los puertos disponibles',
            'multiple': 'multiple'
        }
    )

    # ===== 5. ESTADO Y CATEGORAA =====
    category = SelectField(
        'Categoria',
        choices=[
            ('', 'Selecciona una categoria'),
            ('laptop', ' Laptop'),
            ('workstation', ' Workstation'),
            ('gaming', ' Gaming')
        ],
        validators=[DataRequired(message='La categoria es requerida')],
        render_kw={
            'class': 'form-input'
        }
    )

    condition = SelectField(
        'Condicion',
        choices=[
            ('', 'Selecciona condicion'),
            ('new', ' Nuevo'),
            ('used', ' Usado'),
            ('refurbished', ' Reacondicionado')
        ],
        validators=[DataRequired(message='La condicion es requerida')],
        default='used',
        render_kw={
            'class': 'form-input',
            'id': 'condition'
        }
    )

    # ===== 6. FINANCIEROS =====
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

    discount_price = DecimalField(
        'Precio con Descuento ($)',
        places=2,
        validators=[
            Optional(),
            PositiveOrZero(message='El precio de descuento debe ser 0 o mayor')
        ],
        render_kw={
            'placeholder': '0.00 (dejar vacio si no hay descuento)',
            'class': 'form-input',
            'step': '0.01',
            'min': '0'
        }
    )

    tax_percent = DecimalField(
        'Impuesto (%)',
        places=2,
        default=0.00,
        validators=[
            Optional(),
            NumberRange(min=0, max=100, message='El impuesto debe estar entre 0 y 100%')
        ],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0',
            'max': '100'
        }
    )

    # Campo oculto para mostrar el margen (calculado por JavaScript)
    margin_percentage = HiddenField('Margen %')

    # ===== 7. INVENTARIO =====
    quantity = IntegerField(
        'Cantidad Total',
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

    reserved_quantity = IntegerField(
        'Cantidad Reservada',
        validators=[
            Optional(),
            PositiveOrZero(message='La cantidad reservada debe ser 0 o mayor')
        ],
        default=0,
        render_kw={
            'placeholder': '0',
            'class': 'form-input',
            'min': '0'
        }
    )

    min_alert = IntegerField(
        'Alerta Minima',
        validators=[
            DataRequired(message='La alerta minima es requerida'),
            PositiveOrZero(message='La alerta debe ser 0 o mayor')
        ],
        default=1,
        render_kw={
            'placeholder': '1',
            'class': 'form-input',
            'min': '0'
        }
    )

    # ===== UBICACIA“N Y LOGASTICA =====
    store_id = SelectField(
        'Tienda',
        coerce=int,
        validators=[DataRequired(message='La tienda es requerida')],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Selecciona o crea una tienda',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/stores'
        }
    )

    location_id = SelectField(
        'Ubicacion',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Ej: Estante A-1, Vitrina 3',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/locations'
        }
    )

    supplier_id = SelectField(
        'Proveedor',
        coerce=int,
        validators=[Optional()],
        render_kw={
            'class': 'form-input select2-dynamic',
            'data-placeholder': 'Selecciona o crea un proveedor',
            'data-allow-clear': 'true',
            'data-endpoint': '/api/catalog/suppliers'
        }
    )

    # ===== 8. TIMESTAMPS =====
    # entry_date se establece automaticamente en el backend (date.today())
    # sale_date se establece cuando se realiza una venta

    # ===== NOTAS =====
    internal_notes = TextAreaField(
        'Notas Internas',
        validators=[Optional(), Length(max=2000)],
        render_kw={
            'placeholder': 'Notas internas, observaciones, etc. (no visibles al publico)',
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
        # Solo cargamos las opciones iniciales, Select2 manejara la busqueda dinamica

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

        # Storage
        self.storage_id.choices = [(0, 'Selecciona o crea almacenamiento')] + [
            (st.id, st.name) for st in Storage.query.filter_by(is_active=True).order_by(Storage.name).all()
        ]

        # RAM
        self.ram_id.choices = [(0, 'Selecciona o crea RAM')] + [
            (r.id, r.name) for r in Ram.query.filter_by(is_active=True).order_by(Ram.name).all()
        ]

        # Stores
        self.store_id.choices = [(0, 'Selecciona o crea una tienda')] + [
            (s.id, s.name) for s in Store.query.filter_by(is_active=True).order_by(Store.name).all()
        ]

        # Locations
        self.location_id.choices = [(0, 'Selecciona o crea una ubicacion')] + [
            (l.id, l.name) for l in Location.query.filter_by(is_active=True).order_by(Location.name).all()
        ]

        # Suppliers
        self.supplier_id.choices = [(0, 'Selecciona o crea un proveedor')] + [
            (s.id, s.name) for s in Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
        ]

    def validate_reserved_quantity(self, field):
        """Valida que la cantidad reservada no exceda la cantidad total"""
        if field.data and self.quantity.data:
            if field.data > self.quantity.data:
                raise ValidationError('La cantidad reservada no puede ser mayor que la cantidad total')

    def validate_discount_price(self, field):
        """Valida que el precio de descuento sea menor al precio de venta"""
        if field.data and self.sale_price.data:
            if field.data >= self.sale_price.data:
                raise ValidationError('El precio de descuento debe ser menor al precio de venta')


class LaptopImageForm(FlaskForm):
    """Formulario para agregar imagenes a una laptop"""

    image = FileField(
        'Imagen',
        validators=[
            DataRequired(message='La imagen es requerida'),
            FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'gif'], 'Solo imagenes (jpg, png, webp, gif)')
        ]
    )

    alt_text = StringField(
        'Texto Alternativo (SEO)',
        validators=[Optional(), Length(max=255)],
        render_kw={
            'placeholder': 'Descripcion de la imagen para SEO',
            'class': 'form-input'
        }
    )

    is_cover = BooleanField(
        'Es imagen de portada',
        default=False,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    submit = SubmitField('Subir Imagen')


class QuickSearchForm(FlaskForm):
    """Formulario de busqueda rapida"""

    search = StringField(
        'Buscar',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Buscar por SKU, nombre, marca, modelo...',
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
        'Categoria',
        choices=[
            ('', 'Todas'),
            ('laptop', ' Laptop'),
            ('workstation', ' Workstation'),
            ('gaming', ' Gaming')
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
        'Tarjeta Grafica',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    screen_id = SelectField(
        'Pantalla',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    condition = SelectField(
        'Condicion',
        choices=[
            ('', 'Todas'),
            ('new', ' Nuevo'),
            ('used', ' Usado'),
            ('refurbished', ' Reacondicionado')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    is_published = SelectField(
        'Estado de Publicacion',
        choices=[
            ('', 'Todos'),
            ('1', 'Publicados'),
            ('0', 'No publicados')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    is_featured = SelectField(
        'Destacados',
        choices=[
            ('', 'Todos'),
            ('1', 'Solo destacados'),
            ('0', 'No destacados')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    supplier_id = SelectField(
        'Proveedor',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    min_price = DecimalField(
        'Precio Minimo',
        places=2,
        validators=[Optional(), PositiveOrZero()],
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01'
        }
    )

    max_price = DecimalField(
        'Precio Maximo',
        places=2,
        validators=[Optional(), PositiveOrZero()],
        render_kw={
            'placeholder': '9999.99',
            'class': 'form-input',
            'step': '0.01'
        }
    )

    has_npu = SelectField(
        'Tiene NPU',
        choices=[
            ('', 'Todos'),
            ('1', 'Con NPU'),
            ('0', 'Sin NPU')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
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

        # Cargar tarjetas graficas
        self.graphics_card_id.choices = [(0, 'Todas las GPUs')] + [
            (g.id, g.name) for g in GraphicsCard.query.filter_by(is_active=True).order_by(GraphicsCard.name).all()
        ]

        # Cargar pantallas
        self.screen_id.choices = [(0, 'Todas las pantallas')] + [
            (s.id, s.name) for s in Screen.query.filter_by(is_active=True).order_by(Screen.name).all()
        ]

        # Cargar proveedores
        self.supplier_id.choices = [(0, 'Todos los proveedores')] + [
            (s.id, s.name) for s in Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
        ]


class SupplierForm(FlaskForm):
    """Formulario para gestionar proveedores"""

    name = StringField(
        'Nombre del Proveedor',
        validators=[
            DataRequired(message='El nombre es requerido'),
            Length(max=100)
        ],
        render_kw={
            'placeholder': 'Nombre de la empresa proveedora',
            'class': 'form-input'
        }
    )

    contact_name = StringField(
        'Nombre de Contacto',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Persona de contacto',
            'class': 'form-input'
        }
    )

    email = StringField(
        'Email',
        validators=[Optional(), Length(max=120)],
        render_kw={
            'placeholder': 'email@proveedor.com',
            'class': 'form-input',
            'type': 'email'
        }
    )

    phone = StringField(
        'Telefono',
        validators=[Optional(), Length(max=20)],
        render_kw={
            'placeholder': '+1 234 567 8900',
            'class': 'form-input'
        }
    )

    address = TextAreaField(
        'Direccion',
        validators=[Optional(), Length(max=300)],
        render_kw={
            'placeholder': 'Direccion completa',
            'class': 'form-input',
            'rows': '2'
        }
    )

    website = StringField(
        'Sitio Web',
        validators=[Optional(), Length(max=200), URL(message='URL invalida')],
        render_kw={
            'placeholder': 'https://www.proveedor.com',
            'class': 'form-input'
        }
    )

    notes = TextAreaField(
        'Notas',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Notas adicionales sobre el proveedor',
            'class': 'form-input',
            'rows': '3'
        }
    )

    submit = SubmitField('Guardar Proveedor')
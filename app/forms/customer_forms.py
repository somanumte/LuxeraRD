# ============================================
# FORMULARIOS DE CLIENTES
# ============================================

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SelectField, TextAreaField, BooleanField,
    SubmitField, DecimalField, HiddenField
)
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from app.utils.dominican_validators import (
    CedulaValidator, RNCValidator, DominicanPhoneValidator
)
from app.models.customer import Customer

# ===== OPCIONES DE PROVINCIAS DOMINICANAS =====
DOMINICAN_PROVINCES = [
    ('', 'Selecciona una provincia'),
    ('Azua', 'Azua'),
    ('Baoruco', 'Baoruco'),
    ('Barahona', 'Barahona'),
    ('Dajabón', 'Dajabón'),
    ('Distrito Nacional', 'Distrito Nacional'),
    ('Duarte', 'Duarte'),
    ('El Seibo', 'El Seibo'),
    ('Elías Piña', 'Elías Piña'),
    ('Espaillat', 'Espaillat'),
    ('Hato Mayor', 'Hato Mayor'),
    ('Hermanas Mirabal', 'Hermanas Mirabal'),
    ('Independencia', 'Independencia'),
    ('La Altagracia', 'La Altagracia'),
    ('La Romana', 'La Romana'),
    ('La Vega', 'La Vega'),
    ('María Trinidad Sánchez', 'María Trinidad Sánchez'),
    ('Monseñor Nouel', 'Monseñor Nouel'),
    ('Monte Cristi', 'Monte Cristi'),
    ('Monte Plata', 'Monte Plata'),
    ('Pedernales', 'Pedernales'),
    ('Peravia', 'Peravia'),
    ('Puerto Plata', 'Puerto Plata'),
    ('Samaná', 'Samaná'),
    ('San Cristóbal', 'San Cristóbal'),
    ('San José de Ocoa', 'San José de Ocoa'),
    ('San Juan', 'San Juan'),
    ('San Pedro de Macorís', 'San Pedro de Macorís'),
    ('Sánchez Ramírez', 'Sánchez Ramírez'),
    ('Santiago', 'Santiago'),
    ('Santiago Rodríguez', 'Santiago Rodríguez'),
    ('Santo Domingo', 'Santo Domingo'),
    ('Valverde', 'Valverde'),
]


# ===== FORMULARIO PRINCIPAL DE CLIENTE =====

class CustomerForm(FlaskForm):
    """
    Formulario para crear/editar clientes
    Soporta personas y empresas
    """

    # ===== TIPO DE CLIENTE =====
    customer_type = SelectField(
        'Tipo de Cliente',
        choices=[
            ('person', '👤 Persona Física'),
            ('company', '🏢 Empresa')
        ],
        validators=[DataRequired(message='Selecciona el tipo de cliente')],
        render_kw={
            'class': 'form-input',
            'id': 'customer_type'
        }
    )

    # ===== INFORMACIÓN PERSONAL (Para personas) =====
    first_name = StringField(
        'Nombre',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Juan',
            'class': 'form-input',
            'id': 'first_name'
        }
    )

    last_name = StringField(
        'Apellido',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Pérez',
            'class': 'form-input',
            'id': 'last_name'
        }
    )

    # ===== INFORMACIÓN EMPRESA (Para empresas) =====
    company_name = StringField(
        'Nombre de la Empresa',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'placeholder': 'Empresa S.R.L.',
            'class': 'form-input',
            'id': 'company_name'
        }
    )

    # ===== IDENTIFICACIÓN FISCAL =====
    id_type = SelectField(
        'Tipo de Identificación',
        choices=[
            ('cedula', '🪪 Cédula'),
            ('rnc', '🏢 RNC')
        ],
        validators=[DataRequired(message='Selecciona el tipo de identificación')],
        render_kw={
            'class': 'form-input',
            'id': 'id_type'
        }
    )

    id_number = StringField(
        'Número de Identificación',
        validators=[DataRequired(message='El número de identificación es requerido')],
        render_kw={
            'placeholder': 'XXX-XXXXXXX-X o XXXXXXXXX',
            'class': 'form-input',
            'id': 'id_number'
        }
    )

    # ===== CONTACTO =====
    email = StringField(
        'Email',
        validators=[Optional(), Email(message='Email inválido'), Length(max=120)],
        render_kw={
            'placeholder': 'cliente@email.com',
            'class': 'form-input',
            'type': 'email'
        }
    )

    phone_primary = StringField(
        'Teléfono Principal',
        validators=[Optional(), DominicanPhoneValidator()],
        render_kw={
            'placeholder': '(809) 555-5555',
            'class': 'form-input'
        }
    )

    phone_secondary = StringField(
        'Teléfono Secundario',
        validators=[Optional(), DominicanPhoneValidator()],
        render_kw={
            'placeholder': '(829) 555-5555',
            'class': 'form-input'
        }
    )

    whatsapp = StringField(
        'WhatsApp',
        validators=[Optional(), DominicanPhoneValidator()],
        render_kw={
            'placeholder': '(849) 555-5555',
            'class': 'form-input'
        }
    )

    # ===== DIRECCIÓN =====
    address_line1 = StringField(
        'Dirección Línea 1',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'placeholder': 'Calle, Número, Sector',
            'class': 'form-input'
        }
    )

    address_line2 = StringField(
        'Dirección Línea 2',
        validators=[Optional(), Length(max=200)],
        render_kw={
            'placeholder': 'Apartamento, Edificio (opcional)',
            'class': 'form-input'
        }
    )

    city = StringField(
        'Ciudad',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Santo Domingo',
            'class': 'form-input'
        }
    )

    province = SelectField(
        'Provincia',
        choices=DOMINICAN_PROVINCES,
        validators=[Optional()],
        render_kw={
            'class': 'form-input'
        }
    )

    postal_code = StringField(
        'Código Postal',
        validators=[Optional(), Length(max=10)],
        render_kw={
            'placeholder': '10100',
            'class': 'form-input'
        }
    )

    # ===== INFORMACIÓN ADICIONAL =====
    credit_limit = DecimalField(
        'Límite de Crédito ($)',
        places=2,
        validators=[Optional()],
        default=0.00,
        render_kw={
            'placeholder': '0.00',
            'class': 'form-input',
            'step': '0.01',
            'min': '0'
        }
    )

    notes = TextAreaField(
        'Notas',
        validators=[Optional()],
        render_kw={
            'placeholder': 'Notas adicionales sobre el cliente...',
            'class': 'form-input',
            'rows': '4'
        }
    )

    is_active = BooleanField(
        'Cliente Activo',
        default=True,
        render_kw={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }
    )

    # ===== SUBMIT =====
    submit = SubmitField(
        'Guardar Cliente',
        render_kw={
            'class': 'w-full py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transition-all duration-300'
        }
    )

    # ===== VALIDACIONES PERSONALIZADAS =====

    def validate_id_number(self, field):
        """Valida cédula o RNC según el tipo"""
        import re

        if not field.data:
            raise ValidationError('El número de identificación es requerido')

        # Limpiar el número
        clean_id = re.sub(r'[-\s]', '', str(field.data))

        # Validar según el tipo
        if self.id_type.data == 'cedula':
            validator = CedulaValidator()
            validator(self, field)
        elif self.id_type.data == 'rnc':
            validator = RNCValidator()
            validator(self, field)

        # Verificar unicidad (excepto en edición)
        existing = Customer.query.filter_by(id_number=clean_id).first()
        if existing:
            # Si estamos editando, verificar que no sea otro cliente
            if hasattr(self, 'customer_id') and self.customer_id:
                if existing.id != self.customer_id:
                    raise ValidationError('Este número de identificación ya está registrado')
            else:
                raise ValidationError('Este número de identificación ya está registrado')

    def validate_first_name(self, field):
        """Nombre requerido para personas"""
        if self.customer_type.data == 'person' and not field.data:
            raise ValidationError('El nombre es requerido para personas')

    def validate_last_name(self, field):
        """Apellido requerido para personas"""
        if self.customer_type.data == 'person' and not field.data:
            raise ValidationError('El apellido es requerido para personas')

    def validate_company_name(self, field):
        """Nombre de empresa requerido para empresas"""
        if self.customer_type.data == 'company' and not field.data:
            raise ValidationError('El nombre de la empresa es requerido')


# ===== FORMULARIO DE BÚSQUEDA RÁPIDA =====

class QuickSearchForm(FlaskForm):
    """Formulario simple para búsqueda rápida"""
    q = StringField(
        'Buscar',
        validators=[Optional(), Length(max=100)],
        render_kw={
            'placeholder': 'Buscar por nombre, cédula, RNC...',
            'class': 'form-input'
        }
    )
    submit = SubmitField('Buscar')


# ===== FORMULARIO DE FILTROS =====

class FilterForm(FlaskForm):
    """Formulario para filtrar clientes"""

    customer_type = SelectField(
        'Tipo',
        choices=[
            ('', 'Todos'),
            ('person', 'Personas'),
            ('company', 'Empresas')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    province = SelectField(
        'Provincia',
        choices=DOMINICAN_PROVINCES,
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )

    is_active = SelectField(
        'Estado',
        choices=[
            ('', 'Todos'),
            ('1', 'Activos'),
            ('0', 'Inactivos')
        ],
        validators=[Optional()],
        render_kw={'class': 'form-input'}
    )
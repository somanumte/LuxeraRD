# ============================================
# MODELO DE FACTURAS CON NCF POR TIPO
# ============================================
# Sistema actualizado con secuencias independientes por tipo de NCF
# Según regulaciones DGII República Dominicana

from app import db
from app.models.mixins import TimestampMixin
from datetime import datetime, date
from decimal import Decimal

# ============================================
# DICCIONARIO DE TIPOS DE NCF
# ============================================
# Según DGII República Dominicana

NCF_TYPES = {
    # === COMPROBANTES DE VENTAS ===
    'B01': {
        'name': 'Crédito Fiscal',
        'description': 'Para contribuyentes que pueden deducir gastos. Requiere RNC del cliente.',
        'category': 'ventas',
        'requires_id': True,
        'default_for': 'rnc',
    },
    'B02': {
        'name': 'Consumo',
        'description': 'Para consumidores finales. No permite deducción de gastos.',
        'category': 'ventas',
        'requires_id': False,
        'default_for': 'cedula',
    },
    'B03': {
        'name': 'Nota de Débito',
        'description': 'Para aumentar el valor de una factura emitida previamente.',
        'category': 'ventas',
        'requires_id': True,
        'default_for': None,
    },
    'B04': {
        'name': 'Nota de Crédito',
        'description': 'Para disminuir el valor o anular una factura emitida previamente.',
        'category': 'ventas',
        'requires_id': True,
        'default_for': None,
    },
    'B14': {
        'name': 'Regímenes Especiales',
        'description': 'Para ventas a zonas francas, embajadas, organismos internacionales.',
        'category': 'ventas',
        'requires_id': True,
        'default_for': None,
    },
    'B15': {
        'name': 'Gubernamental',
        'description': 'Para ventas al gobierno y entidades estatales.',
        'category': 'ventas',
        'requires_id': True,
        'default_for': None,
    },
    'B16': {
        'name': 'Exportaciones',
        'description': 'Para ventas de bienes y servicios al exterior.',
        'category': 'ventas',
        'requires_id': False,
        'default_for': None,
    },

    # === COMPROBANTES DE GASTOS/COMPRAS ===
    'B11': {
        'name': 'Compras (Proveedores Informales)',
        'description': 'Para compras a proveedores sin RNC.',
        'category': 'gastos',
        'requires_id': False,
        'default_for': None,
    },
    'B12': {
        'name': 'Gastos Menores',
        'description': 'Para gastos menores sin comprobante fiscal.',
        'category': 'gastos',
        'requires_id': False,
        'default_for': None,
    },
    'B13': {
        'name': 'Pagos al Exterior',
        'description': 'Para pagos a proveedores del exterior.',
        'category': 'gastos',
        'requires_id': False,
        'default_for': None,
    },
}

# Tipos de NCF válidos para facturas de venta
NCF_SALES_TYPES = ['B01', 'B02', 'B03', 'B04', 'B14', 'B15', 'B16']

# Tipos de NCF para gastos/compras
NCF_EXPENSE_TYPES = ['B11', 'B12', 'B13']


# ============================================
# MODELO: SECUENCIAS DE NCF
# ============================================

class NCFSequence(TimestampMixin, db.Model):
    """
    Modelo para manejar secuencias independientes de NCF por tipo.

    Cada tipo de NCF (B01, B02, etc.) tiene su propia secuencia
    con su rango autorizado y fecha de vencimiento.
    """
    __tablename__ = 'ncf_sequences'

    id = db.Column(db.Integer, primary_key=True)

    # Tipo de NCF (B01, B02, B03, etc.)
    ncf_type = db.Column(db.String(3), unique=True, nullable=False, index=True)

    # Nombre descriptivo
    name = db.Column(db.String(100), nullable=False)

    # Secuencia actual (próximo número a usar)
    current_sequence = db.Column(db.Integer, nullable=False, default=1)

    # Rango autorizado por DGII
    range_start = db.Column(db.Integer, nullable=False, default=1)
    range_end = db.Column(db.Integer, nullable=True)  # NULL = sin límite

    # Fecha de vencimiento de la autorización
    valid_until = db.Column(db.Date, nullable=True)

    # Estado
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # ===== PROPIEDADES =====

    @property
    def is_expired(self):
        """Verifica si la secuencia está vencida"""
        if self.valid_until:
            return date.today() > self.valid_until
        return False

    @property
    def is_exhausted(self):
        """Verifica si se agotó el rango de NCF"""
        if self.range_end:
            return self.current_sequence > self.range_end
        return False

    @property
    def is_valid(self):
        """Verifica si la secuencia puede usarse"""
        return self.is_active and not self.is_expired and not self.is_exhausted

    @property
    def remaining_count(self):
        """Cantidad de NCF disponibles en el rango"""
        if self.range_end:
            remaining = self.range_end - self.current_sequence + 1
            return max(0, remaining)
        return None  # Sin límite

    @property
    def next_ncf_preview(self):
        """Vista previa del próximo NCF que se generará"""
        return f"{self.ncf_type}{str(self.current_sequence).zfill(8)}"

    @property
    def type_info(self):
        """Obtiene la información del tipo de NCF"""
        return NCF_TYPES.get(self.ncf_type, {})

    # ===== MÉTODOS =====

    def get_next_ncf(self):
        """
        Genera el siguiente NCF de esta secuencia.

        Returns:
            str: El NCF generado (ej: 'B0100000001')

        Raises:
            ValueError: Si la secuencia no es válida
        """
        if not self.is_active:
            raise ValueError(f"La secuencia {self.ncf_type} está desactivada")

        if self.is_expired:
            raise ValueError(
                f"La secuencia {self.ncf_type} está vencida desde {self.valid_until}. "
                f"Solicite una nueva autorización a la DGII."
            )

        if self.is_exhausted:
            raise ValueError(
                f"Se agotó el rango de NCF para {self.ncf_type} "
                f"(máximo: {self.range_end}). Solicite más NCF a la DGII."
            )

        # Generar NCF
        ncf = f"{self.ncf_type}{str(self.current_sequence).zfill(8)}"

        # Incrementar secuencia
        self.current_sequence += 1

        return ncf

    def to_dict(self):
        """Serializa a diccionario"""
        return {
            'id': self.id,
            'ncf_type': self.ncf_type,
            'name': self.name,
            'current_sequence': self.current_sequence,
            'range_start': self.range_start,
            'range_end': self.range_end,
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'is_exhausted': self.is_exhausted,
            'is_valid': self.is_valid,
            'remaining_count': self.remaining_count,
            'next_ncf_preview': self.next_ncf_preview
        }

    # ===== MÉTODOS DE CLASE =====

    @classmethod
    def get_or_create(cls, ncf_type):
        """
        Obtiene o crea una secuencia para el tipo de NCF especificado.

        Args:
            ncf_type: Código del tipo de NCF (ej: 'B01')

        Returns:
            NCFSequence: La secuencia existente o recién creada
        """
        sequence = cls.query.filter_by(ncf_type=ncf_type).first()

        if not sequence:
            type_info = NCF_TYPES.get(ncf_type, {})
            sequence = cls(
                ncf_type=ncf_type,
                name=type_info.get('name', f'Tipo {ncf_type}'),
                current_sequence=1,
                range_start=1,
                range_end=99999999,
                is_active=True
            )
            db.session.add(sequence)
            db.session.commit()

        return sequence

    @classmethod
    def get_sales_sequences(cls):
        """Obtiene todas las secuencias de tipos de venta activas"""
        return cls.query.filter(
            cls.ncf_type.in_(NCF_SALES_TYPES),
            cls.is_active == True
        ).all()

    @classmethod
    def get_all_active(cls):
        """Obtiene todas las secuencias activas"""
        return cls.query.filter_by(is_active=True).order_by(cls.ncf_type).all()

    @staticmethod
    def validate_ncf_format(ncf):
        """
        Valida el formato de un NCF.

        Args:
            ncf: El NCF a validar (ej: 'B0100000001')

        Returns:
            tuple: (is_valid, error_message)
        """
        if not ncf:
            return False, "El NCF no puede estar vacío"

        ncf = ncf.strip().upper()

        if len(ncf) != 11:
            return False, f"El NCF debe tener 11 caracteres. Tiene {len(ncf)}."

        prefix = ncf[:3]
        sequence = ncf[3:]

        if prefix not in NCF_TYPES:
            return False, f"El prefijo '{prefix}' no es un tipo de NCF válido."

        if not sequence.isdigit():
            return False, "Los últimos 8 caracteres deben ser numéricos."

        return True, None

    def __repr__(self):
        return f'<NCFSequence {self.ncf_type}: {self.current_sequence}>'


# ============================================
# MODELO: FACTURA
# ============================================

class Invoice(TimestampMixin, db.Model):
    """
    Modelo de Factura

    Representa una factura con sus items, cliente, totales y NCF.
    """
    __tablename__ = 'invoices'

    # ===== IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)

    # Número de factura (generado automáticamente)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # NCF (Número de Comprobante Fiscal) - RD
    ncf = db.Column(db.String(19), unique=True, nullable=False, index=True)

    # ===== NUEVO: Tipo de NCF =====
    ncf_type = db.Column(db.String(3), nullable=True, default='B02', index=True)

    # ===== RELACIONES =====
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer', backref='invoices')

    # ===== FECHAS =====
    invoice_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    due_date = db.Column(db.Date, nullable=True)

    # ===== MÉTODO DE PAGO =====
    payment_method = db.Column(db.String(50), default='cash')

    # ===== TOTALES =====
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)

    # ===== ESTADO =====
    status = db.Column(db.String(20), nullable=False, default='draft', index=True)

    # ===== INFORMACIÓN ADICIONAL =====
    notes = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)

    # ===== AUDITORÍA =====
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # Relación con items
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')

    # ===== PROPIEDADES =====

    @property
    def formatted_invoice_number(self):
        """Número de factura formateado"""
        return self.invoice_number

    @property
    def formatted_ncf(self):
        """NCF formateado"""
        return self.ncf

    @property
    def ncf_type_name(self):
        """Nombre del tipo de NCF"""
        if self.ncf_type and self.ncf_type in NCF_TYPES:
            return NCF_TYPES[self.ncf_type]['name']
        return 'Desconocido'

    @property
    def ncf_type_info(self):
        """Información completa del tipo de NCF"""
        return NCF_TYPES.get(self.ncf_type, {})

    @property
    def is_overdue(self):
        """Verifica si la factura está vencida"""
        if self.due_date and self.status not in ['paid', 'cancelled']:
            return date.today() > self.due_date
        return False

    @property
    def days_until_due(self):
        """Días hasta el vencimiento"""
        if self.due_date:
            delta = self.due_date - date.today()
            return delta.days
        return None

    # ===== MÉTODOS =====

    def calculate_totals(self):
        """Calcula los totales de la factura"""
        self.subtotal = sum(item.line_total for item in self.items)
        self.tax_amount = self.subtotal * Decimal('0.18')
        self.total = self.subtotal + self.tax_amount

    def to_dict(self):
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'ncf': self.ncf,
            'ncf_type': self.ncf_type,
            'ncf_type_name': self.ncf_type_name,
            'customer_id': self.customer_id,
            'customer_name': self.customer.full_name if self.customer else None,
            'customer_rnc': self.customer.id_number if self.customer else None,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'payment_method': self.payment_method,
            'subtotal': float(self.subtotal) if self.subtotal else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'total': float(self.total) if self.total else 0,
            'status': self.status,
            'notes': self.notes,
            'terms': self.terms,
            'is_overdue': self.is_overdue,
            'days_until_due': self.days_until_due,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by_id': self.created_by_id,
            'items': [item.to_dict() for item in self.items]
        }

    # ===== MÉTODOS ESTÁTICOS PARA ASIGNACIÓN DE NCF =====

    @staticmethod
    def get_suggested_ncf_type(customer):
        """
        Sugiere el tipo de NCF apropiado según el cliente.

        Args:
            customer: Objeto Customer

        Returns:
            str: Código del tipo de NCF sugerido ('B01' o 'B02')
        """
        if customer and hasattr(customer, 'id_type'):
            if customer.id_type == 'rnc':
                return 'B01'  # Crédito Fiscal para empresas
        return 'B02'  # Consumo por defecto

    @staticmethod
    def validate_ncf_for_customer(ncf_type, customer):
        """
        Valida que el tipo de NCF sea apropiado para el cliente.

        Args:
            ncf_type: Código del tipo de NCF
            customer: Objeto Customer

        Returns:
            tuple: (is_valid, warning_message)
        """
        if ncf_type not in NCF_TYPES:
            return False, f"El tipo de NCF '{ncf_type}' no es válido."

        type_info = NCF_TYPES[ncf_type]

        # Verificar si requiere identificación
        if type_info.get('requires_id', False):
            if not customer or not customer.id_number:
                return False, (
                    f"El comprobante {ncf_type} ({type_info['name']}) "
                    f"requiere que el cliente tenga RNC o Cédula registrado."
                )

        # Advertencias (no bloquean, solo informan)
        warning = None

        if ncf_type == 'B01' and customer:
            if hasattr(customer, 'id_type') and customer.id_type == 'cedula':
                warning = (
                    f"El cliente tiene cédula. El comprobante B01 (Crédito Fiscal) "
                    f"normalmente se usa con RNC. Si el cliente es contribuyente "
                    f"registrado en DGII, puede proceder."
                )

        elif ncf_type == 'B02' and customer:
            if hasattr(customer, 'id_type') and customer.id_type == 'rnc':
                warning = (
                    f"El cliente tiene RNC y podría beneficiarse de un "
                    f"comprobante B01 (Crédito Fiscal) para deducir gastos. "
                    f"¿Desea continuar con B02 (Consumo)?"
                )

        return True, warning

    def __repr__(self):
        return f'<Invoice {self.invoice_number} - {self.customer.full_name if self.customer else "No customer"}>'

    # ===== ÍNDICES =====
    __table_args__ = (
        db.Index('idx_invoice_date_status', 'invoice_date', 'status'),
        db.Index('idx_invoice_customer', 'customer_id', 'status'),
        db.Index('idx_invoice_ncf_type', 'ncf_type'),
    )


# ============================================
# MODELO: ITEM DE FACTURA
# ============================================

class InvoiceItem(db.Model):
    """
    Modelo de Item de Factura
    """
    __tablename__ = 'invoice_items'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False, default='laptop')
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id'), nullable=True)
    laptop = db.relationship('Laptop')
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)
    line_order = db.Column(db.Integer, default=0)

    def calculate_line_total(self):
        """Calcula el total de la línea"""
        self.line_total = Decimal(str(self.quantity)) * self.unit_price

    def to_dict(self):
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'item_type': self.item_type,
            'laptop_id': self.laptop_id,
            'laptop_sku': self.laptop.sku if self.laptop else None,
            'laptop_name': self.laptop.display_name if self.laptop else None,
            'description': self.description,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else 0,
            'line_total': float(self.line_total) if self.line_total else 0,
            'line_order': self.line_order
        }

    def __repr__(self):
        return f'<InvoiceItem {self.id} - {self.description[:30]}>'


# ============================================
# MODELO: CONFIGURACIÓN DE FACTURACIÓN
# ============================================

class InvoiceSettings(db.Model):
    """
    Configuración global de facturación
    """
    __tablename__ = 'invoice_settings'

    id = db.Column(db.Integer, primary_key=True)

    # Información de la empresa
    company_name = db.Column(db.String(200), nullable=False, default='LuxeraRD')
    company_rnc = db.Column(db.String(20), nullable=True)
    company_address = db.Column(db.Text, nullable=True)
    company_phone = db.Column(db.String(20), nullable=True)
    company_email = db.Column(db.String(120), nullable=True)

    # Configuración de NCF (legacy - mantener para compatibilidad)
    ncf_prefix = db.Column(db.String(3), nullable=False, default='B02')
    ncf_sequence = db.Column(db.Integer, nullable=False, default=1)

    # Configuración de numeración
    invoice_prefix = db.Column(db.String(10), nullable=False, default='INV')
    invoice_sequence = db.Column(db.Integer, nullable=False, default=1)

    # Términos y condiciones
    default_terms = db.Column(db.Text, nullable=True)

    # Validez del NCF (legacy)
    ncf_valid_until = db.Column(db.Date, nullable=True)

    # Logo
    logo_path = db.Column(db.String(255), nullable=True)

    # ===== MÉTODOS =====

    def get_logo_url(self):
        """Obtiene la URL completa del logo"""
        if self.logo_path:
            return f"/static/logos/{self.logo_path}"
        return None

    def has_logo(self):
        """Verifica si existe un logo configurado"""
        import os
        from flask import current_app

        if not self.logo_path:
            return False

        logo_full_path = os.path.join(
            current_app.root_path,
            'static',
            'logos',
            self.logo_path
        )
        return os.path.exists(logo_full_path)

    def get_next_invoice_number(self):
        """Genera el siguiente número de factura"""
        number = f"{self.invoice_prefix}-{str(self.invoice_sequence).zfill(8)}"
        self.invoice_sequence += 1
        return number

    def get_next_ncf(self, ncf_type=None):
        """
        Genera el siguiente NCF del tipo especificado.

        Args:
            ncf_type: Tipo de NCF ('B01', 'B02', etc.). Si es None, usa el tipo por defecto.

        Returns:
            str: El NCF generado

        Raises:
            ValueError: Si la secuencia no es válida
        """
        if ncf_type is None:
            ncf_type = self.ncf_prefix or 'B02'

        # Obtener la secuencia correspondiente
        sequence = NCFSequence.get_or_create(ncf_type)

        # Generar el NCF (esto valida y lanza excepciones si hay problemas)
        return sequence.get_next_ncf()

    def validate_manual_ncf(self, ncf, ncf_type):
        """
        Valida un NCF ingresado manualmente.

        Args:
            ncf: El NCF a validar
            ncf_type: El tipo de NCF esperado

        Returns:
            tuple: (is_valid, error_message)
        """
        # Validar formato
        is_valid, error = NCFSequence.validate_ncf_format(ncf)
        if not is_valid:
            return False, error

        ncf = ncf.strip().upper()

        # Validar que coincida con el tipo esperado
        if not ncf.startswith(ncf_type):
            return False, (
                f"El NCF debe comenzar con '{ncf_type}'. "
                f"El valor ingresado comienza con '{ncf[:3]}'."
            )

        # Validar que no exista (duplicado)
        existing = Invoice.query.filter_by(ncf=ncf).first()
        if existing:
            return False, (
                f"El NCF '{ncf}' ya está registrado.\n\n"
                f"• Factura: {existing.invoice_number}\n"
                f"• Cliente: {existing.customer.full_name if existing.customer else 'N/A'}\n"
                f"• Fecha: {existing.invoice_date.strftime('%d/%m/%Y') if existing.invoice_date else 'N/A'}\n"
                f"• Estado: {existing.status}"
            )

        return True, None

    @classmethod
    def get_settings(cls):
        """Obtiene la configuración (crea una por defecto si no existe)"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def to_dict(self):
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'company_name': self.company_name,
            'company_rnc': self.company_rnc,
            'company_address': self.company_address,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'ncf_prefix': self.ncf_prefix,
            'ncf_sequence': self.ncf_sequence,
            'invoice_prefix': self.invoice_prefix,
            'invoice_sequence': self.invoice_sequence,
            'default_terms': self.default_terms,
            'ncf_valid_until': self.ncf_valid_until.isoformat() if self.ncf_valid_until else None,
            'logo_path': self.logo_path
        }

    def __repr__(self):
        return f'<InvoiceSettings {self.company_name}>'


# ============================================
# FUNCIONES HELPER
# ============================================

def get_ncf_types_for_sales():
    """
    Obtiene la lista de tipos de NCF disponibles para ventas.

    Returns:
        list: Lista de diccionarios con información de cada tipo
    """
    result = []
    for code in NCF_SALES_TYPES:
        info = NCF_TYPES.get(code, {})
        result.append({
            'code': code,
            'name': info.get('name', code),
            'description': info.get('description', ''),
            'requires_id': info.get('requires_id', False),
            'default_for': info.get('default_for'),
        })
    return result


def suggest_ncf_type_for_customer(customer):
    """
    Sugiere el tipo de NCF para un cliente y proporciona contexto.

    Args:
        customer: Objeto Customer

    Returns:
        dict: {
            'suggested_type': código del tipo sugerido,
            'type_name': nombre del tipo,
            'reason': razón de la sugerencia,
            'can_change': si el usuario puede cambiar la selección
        }
    """
    suggested = Invoice.get_suggested_ncf_type(customer)
    type_info = NCF_TYPES.get(suggested, {})

    if customer and hasattr(customer, 'id_type') and customer.id_type == 'rnc':
        reason = (
            f"El cliente tiene RNC, lo que permite emitir Crédito Fiscal "
            f"para deducción de gastos e ITBIS."
        )
    else:
        reason = (
            f"Factura de consumo para cliente final. "
            f"Si el cliente es contribuyente registrado, puede cambiar a Crédito Fiscal (B01)."
        )

    return {
        'suggested_type': suggested,
        'type_name': type_info.get('name', suggested),
        'reason': reason,
        'can_change': True
    }


def initialize_default_ncf_sequences():
    """
    Inicializa las secuencias de NCF por defecto si no existen.
    Llamar esto al iniciar la aplicación o cuando se necesite.
    """
    from datetime import timedelta

    default_valid_until = date.today() + timedelta(days=730)  # 2 años

    for code in NCF_SALES_TYPES:
        try:
            existing = NCFSequence.query.filter_by(ncf_type=code).first()
            if not existing:
                info = NCF_TYPES.get(code, {})
                sequence = NCFSequence(
                    ncf_type=code,
                    name=info.get('name', f'Tipo {code}'),
                    current_sequence=1,
                    range_start=1,
                    range_end=99999999,
                    valid_until=default_valid_until,
                    is_active=True
                )
                db.session.add(sequence)
        except Exception:
            pass

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
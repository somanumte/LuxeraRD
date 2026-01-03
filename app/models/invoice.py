# ============================================
# MODELO DE FACTURAS
# ============================================

from app import db
from app.models.mixins import TimestampMixin
from datetime import datetime, date
from decimal import Decimal


class Invoice(TimestampMixin, db.Model):
    """
    Modelo de Factura

    Representa una factura con sus items, cliente, y totales
    """
    __tablename__ = 'invoices'

    # ===== IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)

    # Número de factura (generado automáticamente)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # NCF (Número de Comprobante Fiscal) - RD
    ncf = db.Column(db.String(19), unique=True, nullable=False, index=True)

    # ===== RELACIONES =====
    # Cliente (obligatorio)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    customer = db.relationship('Customer', backref='invoices')

    # ===== FECHAS =====
    invoice_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    due_date = db.Column(db.Date, nullable=True)

    # ===== MÉTODO DE PAGO =====
    payment_method = db.Column(db.String(50), default='cash')  # cash, card, transfer, credit

    # ===== TOTALES =====
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)
    tax_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)  # ITBIS 18%
    total = db.Column(db.Numeric(12, 2), nullable=False, default=0.00)

    # ===== ESTADO =====
    status = db.Column(db.String(20), nullable=False, default='draft', index=True)
    # draft, issued, paid, cancelled, overdue

    # ===== INFORMACIÓN ADICIONAL =====
    notes = db.Column(db.Text, nullable=True)
    terms = db.Column(db.Text, nullable=True)  # Términos y condiciones

    # ===== AUDITORÍA =====
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # Relación con items de factura
    items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')

    # ===== PROPIEDADES CALCULADAS =====

    @property
    def formatted_invoice_number(self):
        """Número de factura formateado"""
        return self.invoice_number

    @property
    def formatted_ncf(self):
        """NCF formateado"""
        return self.ncf

    @property
    def is_overdue(self):
        """Verifica si la factura está vencida"""
        if self.due_date and self.status not in ['paid', 'cancelled']:
            return date.today() > self.due_date
        return False

    @property
    def days_until_due(self):
        """Días hasta el vencimiento (negativo si está vencida)"""
        if self.due_date:
            delta = self.due_date - date.today()
            return delta.days
        return None

    # ===== MÉTODOS =====

    def calculate_totals(self):
        """Calcula los totales de la factura basándose en los items"""
        self.subtotal = sum(item.line_total for item in self.items)
        self.tax_amount = self.subtotal * Decimal('0.18')  # ITBIS 18%
        self.total = self.subtotal + self.tax_amount

    def to_dict(self):
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'ncf': self.ncf,
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

    def __repr__(self):
        return f'<Invoice {self.invoice_number} - {self.customer.full_name if self.customer else "No customer"}>'

    # ===== ÍNDICES COMPUESTOS =====
    __table_args__ = (
        db.Index('idx_invoice_date_status', 'invoice_date', 'status'),
        db.Index('idx_invoice_customer', 'customer_id', 'status'),
    )


class InvoiceItem(db.Model):
    """
    Modelo de Item de Factura

    Representa cada línea/producto en una factura
    """
    __tablename__ = 'invoice_items'

    # ===== IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)

    # Factura a la que pertenece
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)

    # ===== TIPO DE ITEM =====
    # 'laptop' o 'custom' (para items personalizados)
    item_type = db.Column(db.String(20), nullable=False, default='laptop')

    # Referencia a laptop (si es tipo laptop)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id'), nullable=True)
    laptop = db.relationship('Laptop')

    # ===== DESCRIPCIÓN =====
    # Si es laptop, se toma del laptop. Si es custom, se escribe manualmente
    description = db.Column(db.Text, nullable=False)

    # ===== CANTIDADES Y PRECIOS =====
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)

    # Total de la línea (quantity * unit_price)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)

    # ===== ORDEN =====
    line_order = db.Column(db.Integer, default=0)  # Para ordenar los items

    # ===== MÉTODOS =====

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


class InvoiceSettings(db.Model):
    """
    Configuración global de facturación

    Solo debe existir un registro en esta tabla
    """
    __tablename__ = 'invoice_settings'

    id = db.Column(db.Integer, primary_key=True)

    # ===== INFORMACIÓN DE LA EMPRESA =====
    company_name = db.Column(db.String(200), nullable=False, default='LuxeraRD')
    company_rnc = db.Column(db.String(20), nullable=True)
    company_address = db.Column(db.Text, nullable=True)
    company_phone = db.Column(db.String(20), nullable=True)
    company_email = db.Column(db.String(120), nullable=True)

    # ===== CONFIGURACIÓN DE NCF =====
    ncf_prefix = db.Column(db.String(3), nullable=False, default='B02')  # B01=Crédito Fiscal, B02=Consumo
    ncf_sequence = db.Column(db.Integer, nullable=False, default=1)

    # ===== CONFIGURACIÓN DE NUMERACIÓN =====
    invoice_prefix = db.Column(db.String(10), nullable=False, default='INV')
    invoice_sequence = db.Column(db.Integer, nullable=False, default=1)

    # ===== TÉRMINOS Y CONDICIONES POR DEFECTO =====
    default_terms = db.Column(db.Text, nullable=True)

    # ===== VALIDEZ DEL NCF =====
    ncf_valid_until = db.Column(db.Date, nullable=True)

    # ===== LOGO =====
    logo_path = db.Column(db.String(255), nullable=True)

    # ===== MÉTODOS =====

    def get_next_invoice_number(self):
        """Genera el siguiente número de factura"""
        number = f"{self.invoice_prefix}-{str(self.invoice_sequence).zfill(8)}"
        self.invoice_sequence += 1
        return number

    def get_next_ncf(self):
        """Genera el siguiente NCF"""
        ncf = f"{self.ncf_prefix}{str(self.ncf_sequence).zfill(8)}"
        self.ncf_sequence += 1
        return ncf

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
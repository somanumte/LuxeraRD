# ============================================
# MODELO DE CLIENTES
# ============================================

from app import db
from app.models.mixins import TimestampMixin
from datetime import datetime


class Customer(TimestampMixin, db.Model):
    """
    Modelo de Cliente

    Soporta tanto personas físicas (con cédula) como empresas (con RNC)
    """
    __tablename__ = 'customers'

    # ===== IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)

    # Tipo de cliente: 'person' o 'company'
    customer_type = db.Column(db.String(20), nullable=False, default='person', index=True)

    # ===== INFORMACIÓN PERSONAL/EMPRESA =====
    first_name = db.Column(db.String(100), nullable=True)  # Nombre (persona)
    last_name = db.Column(db.String(100), nullable=True)  # Apellido (persona)
    company_name = db.Column(db.String(200), nullable=True, index=True)  # Nombre empresa

    # ===== IDENTIFICACIÓN FISCAL =====
    # Para personas: cédula (11 dígitos, formato: XXX-XXXXXXX-X)
    # Para empresas: RNC (9 u 11 dígitos)
    id_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    id_type = db.Column(db.String(20), nullable=False)  # 'cedula' o 'rnc'

    # ===== CONTACTO =====
    email = db.Column(db.String(120), nullable=True, index=True)
    phone_primary = db.Column(db.String(20), nullable=True)
    phone_secondary = db.Column(db.String(20), nullable=True)
    whatsapp = db.Column(db.String(20), nullable=True)

    # ===== DIRECCIÓN =====
    address_line1 = db.Column(db.String(200), nullable=True)
    address_line2 = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    province = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    country = db.Column(db.String(100), default='República Dominicana')

    # ===== INFORMACIÓN ADICIONAL =====
    notes = db.Column(db.Text, nullable=True)
    credit_limit = db.Column(db.Numeric(12, 2), default=0.00)  # Límite de crédito
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # ===== AUDITORÍA =====
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # ===== PROPIEDADES CALCULADAS =====

    @property
    def full_name(self):
        """Nombre completo del cliente"""
        if self.customer_type == 'company':
            return self.company_name or 'Sin nombre'
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or 'Sin nombre'

    @property
    def display_name(self):
        """Nombre para mostrar en UI"""
        return self.full_name

    @property
    def formatted_id(self):
        """Número de identificación formateado"""
        if self.id_type == 'cedula' and len(self.id_number) == 11:
            # Formato: XXX-XXXXXXX-X
            return f"{self.id_number[:3]}-{self.id_number[3:10]}-{self.id_number[10]}"
        return self.id_number

    @property
    def full_address(self):
        """Dirección completa formateada"""
        parts = []
        if self.address_line1:
            parts.append(self.address_line1)
        if self.address_line2:
            parts.append(self.address_line2)
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)

        return ', '.join(parts) if parts else 'Sin dirección'

    # ===== MÉTODOS =====

    def to_dict(self):
        """Serializar a diccionario"""
        return {
            'id': self.id,
            'customer_type': self.customer_type,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'company_name': self.company_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'id_number': self.id_number,
            'id_type': self.id_type,
            'formatted_id': self.formatted_id,
            'email': self.email,
            'phone_primary': self.phone_primary,
            'phone_secondary': self.phone_secondary,
            'whatsapp': self.whatsapp,
            'address_line1': self.address_line1,
            'address_line2': self.address_line2,
            'city': self.city,
            'province': self.province,
            'postal_code': self.postal_code,
            'country': self.country,
            'full_address': self.full_address,
            'notes': self.notes,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by_id': self.created_by_id
        }

    def __repr__(self):
        return f'<Customer {self.id} - {self.display_name}>'

    # ===== ÍNDICES COMPUESTOS =====
    __table_args__ = (
        db.Index('idx_customer_type_active', 'customer_type', 'is_active'),
        db.Index('idx_customer_name', 'first_name', 'last_name'),
    )
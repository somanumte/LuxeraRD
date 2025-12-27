# ============================================
# MODELOS DE INVENTARIO DE LAPTOPS
# ============================================
# Solo datos y relaciones, la lógica está en Services

from app import db
from app.models.mixins import TimestampMixin, CatalogMixin
from datetime import datetime


# ===== MODELOS DE CATÁLOGO (usan CatalogMixin) =====

class Brand(CatalogMixin, db.Model):
    """
    Marcas de laptops (Dell, HP, Lenovo, etc.)
    Usa CatalogMixin: id, name, is_active, timestamps, métodos get_active() y get_or_create()
    """
    __tablename__ = 'brands'

    # Relaciones
    laptops = db.relationship('Laptop', backref='brand', lazy='dynamic')


class LaptopModel(CatalogMixin, db.Model):
    """
    Modelos de laptops (Inspiron 15, ThinkPad X1, etc.)
    """
    __tablename__ = 'laptop_models'

    # Campo adicional: referencia a marca (opcional)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=True)

    # Relaciones
    laptops = db.relationship('Laptop', backref='model', lazy='dynamic')


class Processor(CatalogMixin, db.Model):
    """
    Procesadores (Intel Core i7-12700H, AMD Ryzen 7 5700U, etc.)
    """
    __tablename__ = 'processors'

    # Relaciones
    laptops = db.relationship('Laptop', backref='processor', lazy='dynamic')


class OperatingSystem(CatalogMixin, db.Model):
    """
    Sistemas Operativos (Windows 11 Pro, macOS, Ubuntu, etc.)
    """
    __tablename__ = 'operating_systems'

    # Relaciones
    laptops = db.relationship('Laptop', backref='operating_system', lazy='dynamic')


class Screen(CatalogMixin, db.Model):
    """
    Pantallas (15.6" FHD IPS, 14" 2K OLED, etc.)
    """
    __tablename__ = 'screens'

    # Relaciones
    laptops = db.relationship('Laptop', backref='screen', lazy='dynamic')


class GraphicsCard(CatalogMixin, db.Model):
    """
    Tarjetas Gráficas (NVIDIA RTX 4060, Intel Iris Xe, etc.)
    """
    __tablename__ = 'graphics_cards'

    # Relaciones
    laptops = db.relationship('Laptop', backref='graphics_card', lazy='dynamic')


class StorageType(CatalogMixin, db.Model):
    """
    Tipos de Almacenamiento (512GB SSD NVMe, 1TB HDD, etc.)
    """
    __tablename__ = 'storage_types'

    # Relaciones
    laptops = db.relationship('Laptop', backref='storage_type', lazy='dynamic')


class RAMType(CatalogMixin, db.Model):
    """
    Tipos de RAM (16GB DDR5, 32GB DDR4, etc.)
    """
    __tablename__ = 'ram_types'

    # Relaciones
    laptops = db.relationship('Laptop', backref='ram_type', lazy='dynamic')


class Store(CatalogMixin, db.Model):
    """
    Tiendas (Tienda Principal, Sucursal Centro, etc.)
    """
    __tablename__ = 'stores'

    # Campos adicionales específicos de tiendas
    address = db.Column(db.String(300))
    phone = db.Column(db.String(20))

    # Relaciones
    laptops = db.relationship('Laptop', backref='store', lazy='dynamic')
    locations = db.relationship('Location', backref='store_ref', lazy='dynamic')


class Location(CatalogMixin, db.Model):
    """
    Ubicaciones dentro de tiendas (Estante A-1, Vitrina 3, Bodega, etc.)
    """
    __tablename__ = 'locations'

    # Relación con tienda (opcional)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)

    # Relaciones
    laptops = db.relationship('Laptop', backref='location', lazy='dynamic')


# ===== MODELO PRINCIPAL: LAPTOP =====

class Laptop(TimestampMixin, db.Model):
    """
    Modelo principal de inventario de laptops

    Responsabilidad: SOLO almacenar datos
    Lógica de negocio: en Services (SKUService, FinancialService, etc.)
    """
    __tablename__ = 'laptops'

    # ===== IDENTIFICACIÓN =====
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)

    # ===== RELACIONES CON CATÁLOGOS =====
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False, index=True)
    model_id = db.Column(db.Integer, db.ForeignKey('laptop_models.id'), nullable=False, index=True)
    processor_id = db.Column(db.Integer, db.ForeignKey('processors.id'), nullable=False)
    os_id = db.Column(db.Integer, db.ForeignKey('operating_systems.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    graphics_card_id = db.Column(db.Integer, db.ForeignKey('graphics_cards.id'), nullable=False)
    storage_id = db.Column(db.Integer, db.ForeignKey('storage_types.id'), nullable=False)
    ram_id = db.Column(db.Integer, db.ForeignKey('ram_types.id'), nullable=False)

    # ===== CARACTERÍSTICAS TÉCNICAS ADICIONALES =====
    npu = db.Column(db.String(200), nullable=True)  # Neural Processing Unit
    storage_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    ram_upgradeable = db.Column(db.Boolean, default=False, nullable=False)

    # ===== PRECIOS Y COSTOS =====
    purchase_cost = db.Column(db.Numeric(10, 2), nullable=False)
    sale_price = db.Column(db.Numeric(10, 2), nullable=False)

    # Campos calculados (actualizados por FinancialService)
    total_cost = db.Column(db.Numeric(10, 2))
    gross_profit = db.Column(db.Numeric(10, 2))
    margin_percentage = db.Column(db.Numeric(5, 2))

    # ===== INVENTARIO =====
    quantity = db.Column(db.Integer, default=1, nullable=False)
    min_alert = db.Column(db.Integer, default=1, nullable=False)

    # ===== CATEGORÍA =====
    category = db.Column(db.String(20), nullable=False, index=True)
    # Valores: 'gamer', 'working', 'home'

    # ===== UBICACIÓN =====
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)

    # ===== ESTADO Y CONDICIÓN =====
    condition = db.Column(db.String(20), nullable=False, index=True)
    # Valores: 'new', 'used', 'refurbished'

    aesthetic_grade = db.Column(db.String(2), nullable=True)
    # Valores: 'A+', 'A', 'B', 'C'

    # ===== FECHAS =====
    entry_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    sale_date = db.Column(db.DateTime, nullable=True)
    # created_at y updated_at vienen de TimestampMixin

    # ===== CAMPOS CALCULADOS (actualizados por InventoryService) =====
    days_in_inventory = db.Column(db.Integer, default=0)
    rotation_status = db.Column(db.String(20), index=True)
    # Valores: 'fast', 'medium', 'slow'

    # ===== RECOMENDACIÓN IA (actualizada por AIService) =====
    ai_recommendation = db.Column(db.Text, nullable=True)

    # ===== NOTAS =====
    notes = db.Column(db.Text, nullable=True)

    # ===== AUDITORÍA =====
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by = db.relationship('User', backref='laptops_created', foreign_keys=[created_by_id])

    # ===== MÉTODOS DE SERIALIZACIÓN =====

    def to_dict(self, include_relationships=True):
        """
        Serializa el objeto a diccionario (para JSON)

        Args:
            include_relationships: Si incluir datos de relaciones (más pesado)

        Returns:
            dict con todos los datos del laptop
        """
        data = {
            'id': self.id,
            'sku': self.sku,
            'npu': self.npu,
            'storage_upgradeable': self.storage_upgradeable,
            'ram_upgradeable': self.ram_upgradeable,
            'purchase_cost': float(self.purchase_cost) if self.purchase_cost else 0,
            'sale_price': float(self.sale_price) if self.sale_price else 0,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'gross_profit': float(self.gross_profit) if self.gross_profit else 0,
            'margin_percentage': float(self.margin_percentage) if self.margin_percentage else 0,
            'quantity': self.quantity,
            'min_alert': self.min_alert,
            'category': self.category,
            'condition': self.condition,
            'aesthetic_grade': self.aesthetic_grade,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'days_in_inventory': self.days_in_inventory,
            'rotation_status': self.rotation_status,
            'ai_recommendation': self.ai_recommendation,
            'notes': self.notes
        }

        # Incluir relaciones si se solicita
        if include_relationships:
            data.update({
                'brand': self.brand.name if self.brand else None,
                'brand_id': self.brand_id,
                'model': self.model.name if self.model else None,
                'model_id': self.model_id,
                'processor': self.processor.name if self.processor else None,
                'processor_id': self.processor_id,
                'operating_system': self.operating_system.name if self.operating_system else None,
                'os_id': self.os_id,
                'screen': self.screen.name if self.screen else None,
                'screen_id': self.screen_id,
                'graphics_card': self.graphics_card.name if self.graphics_card else None,
                'graphics_card_id': self.graphics_card_id,
                'storage_type': self.storage_type.name if self.storage_type else None,
                'storage_id': self.storage_id,
                'ram_type': self.ram_type.name if self.ram_type else None,
                'ram_id': self.ram_id,
                'store': self.store.name if self.store else None,
                'store_id': self.store_id,
                'location': self.location.name if self.location else None,
                'location_id': self.location_id,
                'created_by_username': self.created_by.username if self.created_by else None
            })

        return data

    def __repr__(self):
        """Representación en string del objeto"""
        return f'<Laptop {self.sku} - {self.brand.name if self.brand else "N/A"} {self.model.name if self.model else "N/A"}>'

    # ===== ÍNDICES COMPUESTOS (para optimización de queries) =====
    __table_args__ = (
        db.Index('idx_laptop_brand_category', 'brand_id', 'category'),
        db.Index('idx_laptop_rotation_quantity', 'rotation_status', 'quantity'),
        db.Index('idx_laptop_entry_date', 'entry_date'),
    )
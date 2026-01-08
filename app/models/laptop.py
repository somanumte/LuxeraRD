# ============================================
# MODELOS DE INVENTARIO DE LAPTOPS
# ============================================
# Actualizado al nuevo modelo de datos

from app import db
from app.models.mixins import TimestampMixin, CatalogMixin
from datetime import datetime, date


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


class Storage(CatalogMixin, db.Model):
    """
    Tipos de Almacenamiento (512GB SSD NVMe, 1TB HDD, etc.)
    """
    __tablename__ = 'storage'

    # Relaciones
    laptops = db.relationship('Laptop', backref='storage', lazy='dynamic')


class Ram(CatalogMixin, db.Model):
    """
    Tipos de RAM (16GB DDR5, 32GB DDR4, etc.)
    """
    __tablename__ = 'ram'

    # Relaciones
    laptops = db.relationship('Laptop', backref='ram', lazy='dynamic')


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


class Supplier(CatalogMixin, db.Model):
    """
    Proveedores de laptops
    """
    __tablename__ = 'suppliers'

    # Campos adicionales específicos de proveedores
    contact_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    website = db.Column(db.String(200))
    notes = db.Column(db.Text)

    # Relaciones
    laptops = db.relationship('Laptop', backref='supplier', lazy='dynamic')


# ===== MODELO PRINCIPAL: LAPTOP =====

class Laptop(TimestampMixin, db.Model):
    """
    Modelo principal de inventario de laptops

    Responsabilidad: SOLO almacenar datos
    Lógica de negocio: en Services (SKUService, FinancialService, etc.)
    """
    __tablename__ = 'laptops'

    # ===== 1. IDENTIFICADORES =====
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)

    # ===== 2. MARKETING Y WEB (SEO) =====
    display_name = db.Column(db.String(200), nullable=False)
    short_description = db.Column(db.String(300), nullable=True)
    long_description_html = db.Column(db.Text, nullable=True)
    is_published = db.Column(db.Boolean, default=False, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    seo_title = db.Column(db.String(70), nullable=True)
    seo_description = db.Column(db.String(160), nullable=True)

    # ===== 3. RELACIONES CON CATÁLOGOS =====
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False, index=True)
    model_id = db.Column(db.Integer, db.ForeignKey('laptop_models.id'), nullable=False, index=True)
    processor_id = db.Column(db.Integer, db.ForeignKey('processors.id'), nullable=False)
    os_id = db.Column(db.Integer, db.ForeignKey('operating_systems.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screens.id'), nullable=False)
    graphics_card_id = db.Column(db.Integer, db.ForeignKey('graphics_cards.id'), nullable=False)
    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'), nullable=False)
    ram_id = db.Column(db.Integer, db.ForeignKey('ram.id'), nullable=False)

    # Logística
    store_id = db.Column(db.Integer, db.ForeignKey('stores.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    # ===== 4. DETALLES TÉCNICOS ESPECÍFICOS =====
    npu = db.Column(db.Boolean, default=False, nullable=False)  # Tiene NPU (AI)
    storage_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    ram_upgradeable = db.Column(db.Boolean, default=False, nullable=False)
    keyboard_layout = db.Column(db.String(20), default='US', nullable=False)
    connectivity_ports = db.Column(db.JSON, default=dict, nullable=True)  # Múltiples valores

    # ===== 5. ESTADO Y CATEGORÍA =====
    # Valores de category: 'laptop', 'workstation', 'gaming'
    category = db.Column(db.String(20), nullable=False, default='laptop', index=True)
    # Valores de condition: 'new', 'used', 'refurbished'
    condition = db.Column(db.String(20), nullable=False, default='used', index=True)

    # ===== 6. FINANCIEROS =====
    purchase_cost = db.Column(db.Numeric(12, 2), nullable=False)
    sale_price = db.Column(db.Numeric(12, 2), nullable=False)
    discount_price = db.Column(db.Numeric(12, 2), nullable=True)
    tax_percent = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)

    # ===== 7. INVENTARIO =====
    quantity = db.Column(db.Integer, default=1, nullable=False)
    reserved_quantity = db.Column(db.Integer, default=0, nullable=False)
    min_alert = db.Column(db.Integer, default=1, nullable=False)

    # ===== 8. TIMESTAMPS =====
    entry_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    sale_date = db.Column(db.Date, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    # created_at y updated_at vienen de TimestampMixin

    # ===== RELACIÓN CON USUARIO CREADOR =====
    created_by = db.relationship('User', backref='laptops_created', foreign_keys=[created_by_id])

    # ===== PROPIEDADES CALCULADAS =====

    @property
    def available_quantity(self):
        """Cantidad disponible (total - reservada)"""
        return self.quantity - self.reserved_quantity

    @property
    def effective_price(self):
        """Precio efectivo (con descuento si existe)"""
        if self.discount_price and self.discount_price > 0:
            return self.discount_price
        return self.sale_price

    @property
    def gross_profit(self):
        """Ganancia bruta por unidad"""
        return float(self.effective_price) - float(self.purchase_cost)

    @property
    def margin_percentage(self):
        """Porcentaje de margen"""
        if float(self.purchase_cost) > 0:
            return (self.gross_profit / float(self.purchase_cost)) * 100
        return 0

    @property
    def price_with_tax(self):
        """Precio con impuesto incluido"""
        return float(self.effective_price) * (1 + float(self.tax_percent) / 100)

    @property
    def is_low_stock(self):
        """Indica si el stock está bajo el mínimo de alerta"""
        return self.available_quantity <= self.min_alert

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
            # Identificadores
            'id': self.id,
            'sku': self.sku,
            'slug': self.slug,

            # Marketing y SEO
            'display_name': self.display_name,
            'short_description': self.short_description,
            'long_description_html': self.long_description_html,
            'is_published': self.is_published,
            'is_featured': self.is_featured,
            'seo_title': self.seo_title,
            'seo_description': self.seo_description,

            # Detalles técnicos
            'npu': self.npu,
            'storage_upgradeable': self.storage_upgradeable,
            'ram_upgradeable': self.ram_upgradeable,
            'keyboard_layout': self.keyboard_layout,
            'connectivity_ports': self.connectivity_ports,

            # Estado y categoría
            'category': self.category,
            'condition': self.condition,

            # Financieros
            'purchase_cost': float(self.purchase_cost) if self.purchase_cost else 0,
            'sale_price': float(self.sale_price) if self.sale_price else 0,
            'discount_price': float(self.discount_price) if self.discount_price else None,
            'tax_percent': float(self.tax_percent) if self.tax_percent else 0,
            'effective_price': float(self.effective_price) if self.effective_price else 0,
            'gross_profit': self.gross_profit,
            'margin_percentage': self.margin_percentage,
            'price_with_tax': self.price_with_tax,

            # Inventario
            'quantity': self.quantity,
            'reserved_quantity': self.reserved_quantity,
            'available_quantity': self.available_quantity,
            'min_alert': self.min_alert,
            'is_low_stock': self.is_low_stock,

            # Timestamps
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'sale_date': self.sale_date.isoformat() if self.sale_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,

            # Notas
            'internal_notes': self.internal_notes
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
                'storage': self.storage.name if self.storage else None,
                'storage_id': self.storage_id,
                'ram': self.ram.name if self.ram else None,
                'ram_id': self.ram_id,
                'store': self.store.name if self.store else None,
                'store_id': self.store_id,
                'location': self.location.name if self.location else None,
                'location_id': self.location_id,
                'supplier': self.supplier.name if self.supplier else None,
                'supplier_id': self.supplier_id,
                'created_by_username': self.created_by.username if self.created_by else None,
                'images': [img.to_dict() for img in self.images.all()] if hasattr(self, 'images') else []
            })

        return data

    def __repr__(self):
        """Representación en string del objeto"""
        return f'<Laptop {self.sku} - {self.display_name}>'

    # ===== ÍNDICES COMPUESTOS (para optimización de queries) =====
    __table_args__ = (
        db.Index('idx_laptop_brand_category', 'brand_id', 'category'),
        db.Index('idx_laptop_published_featured', 'is_published', 'is_featured'),
        db.Index('idx_laptop_entry_date', 'entry_date'),
        db.Index('idx_laptop_store_location', 'store_id', 'location_id'),
    )


# ===== MODELO DE IMÁGENES =====

class LaptopImage(TimestampMixin, db.Model):
    """
    Galería de imágenes vinculada a una Laptop específica.
    """
    __tablename__ = 'laptop_images'

    id = db.Column(db.Integer, primary_key=True)
    laptop_id = db.Column(db.Integer, db.ForeignKey('laptops.id', ondelete='CASCADE'), nullable=False)
    image_path = db.Column(db.String(500), nullable=False)  # Ruta de la imagen
    position = db.Column(db.Integer, default=0, nullable=False)  # Posición en galería
    alt_text = db.Column(db.String(255), nullable=True)  # SEO alt text
    is_cover = db.Column(db.Boolean, default=False, nullable=False)  # Es portada
    ordering = db.Column(db.Integer, default=0, nullable=False)

    # Relación - CAMBIADO: de lazy='dynamic' a lazy='select' para permitir eager loading
    laptop = db.relationship('Laptop', backref=db.backref('images', lazy='select', cascade='all, delete-orphan'))

    def to_dict(self):
        """Serializa la imagen a diccionario"""
        return {
            'id': self.id,
            'laptop_id': self.laptop_id,
            'image_path': self.image_path,
            'position': self.position,
            'alt_text': self.alt_text,
            'is_cover': self.is_cover,
            'ordering': self.ordering,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<LaptopImage {self.id} - Laptop {self.laptop_id}>'

    __table_args__ = (
        db.Index('idx_laptop_image_laptop_cover', 'laptop_id', 'is_cover'),
    )
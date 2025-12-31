# ============================================
# EXPORTACIÓN DE MODELOS
# ============================================
# Actualizado al nuevo modelo de datos

from app.models.user import User
from app.models.mixins import TimestampMixin, SoftDeleteMixin, AuditMixin, CatalogMixin
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram,
    Store, Location, Supplier, Laptop, LaptopImage
)

__all__ = [
    # User
    'User',

    # Mixins
    'TimestampMixin',
    'SoftDeleteMixin',
    'AuditMixin',
    'CatalogMixin',

    # Laptop Catalogs
    'Brand',
    'LaptopModel',
    'Processor',
    'OperatingSystem',
    'Screen',
    'GraphicsCard',
    'Storage',      # Renombrado de StorageType
    'Ram',          # Renombrado de RAMType
    'Store',
    'Location',
    'Supplier',     # Nuevo modelo

    # Main Models
    'Laptop',
    'LaptopImage'   # Nuevo modelo
]
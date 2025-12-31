"""
Servicio para manejar la creación dinámica de catálogos
Actualizado al nuevo modelo de datos
"""
from app import db
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, Storage, Ram, Store, Location, Supplier
)


class CatalogService:
    """Servicio para gestión dinámica de catálogos"""

    @staticmethod
    def _get_or_create_generic(model, value, **extra_fields):
        """
        Método genérico para obtener o crear items de catálogo

        Args:
            model: Modelo de SQLAlchemy
            value: ID (int) o nombre (str)
            **extra_fields: Campos adicionales para el modelo

        Returns:
            int: ID del item, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        # Si es un ID existente
        if isinstance(value, int) and value > 0:
            return value

        # Si es un string (nuevo valor)
        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            # Buscar si ya existe (case-insensitive)
            existing = model.query.filter(
                db.func.lower(model.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            # Crear nuevo item
            new_item = model(name=name, is_active=True, **extra_fields)
            db.session.add(new_item)
            db.session.flush()  # Para obtener el ID sin commit
            return new_item.id

        return None

    @staticmethod
    def get_or_create_brand(value):
        """
        Obtiene o crea una marca

        Args:
            value: ID (int) o nombre (str) de la marca

        Returns:
            int: ID de la marca, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Brand, value)

    @staticmethod
    def get_or_create_model(value, brand_id=None):
        """
        Obtiene o crea un modelo

        Args:
            value: ID (int) o nombre (str) del modelo
            brand_id: ID de la marca asociada

        Returns:
            int: ID del modelo, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        # Si es un ID existente
        if isinstance(value, int) and value > 0:
            return value

        # Si es un string (nuevo valor)
        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            # Buscar si ya existe con la misma marca
            query = LaptopModel.query.filter(
                db.func.lower(LaptopModel.name) == name.lower()
            )

            if brand_id:
                query = query.filter(LaptopModel.brand_id == brand_id)

            existing = query.first()

            if existing:
                return existing.id

            # Crear nuevo modelo
            new_model = LaptopModel(name=name, brand_id=brand_id, is_active=True)
            db.session.add(new_model)
            db.session.flush()
            return new_model.id

        return None

    @staticmethod
    def get_or_create_processor(value):
        """
        Obtiene o crea un procesador

        Args:
            value: ID (int) o nombre (str) del procesador

        Returns:
            int: ID del procesador, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Processor, value)

    @staticmethod
    def get_or_create_os(value):
        """
        Obtiene o crea un sistema operativo

        Args:
            value: ID (int) o nombre (str) del sistema operativo

        Returns:
            int: ID del sistema operativo, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(OperatingSystem, value)

    @staticmethod
    def get_or_create_screen(value):
        """
        Obtiene o crea una pantalla

        Args:
            value: ID (int) o nombre (str) de la pantalla

        Returns:
            int: ID de la pantalla, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Screen, value)

    @staticmethod
    def get_or_create_graphics_card(value):
        """
        Obtiene o crea una tarjeta gráfica

        Args:
            value: ID (int) o nombre (str) de la tarjeta gráfica

        Returns:
            int: ID de la tarjeta gráfica, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(GraphicsCard, value)

    @staticmethod
    def get_or_create_storage(value):
        """
        Obtiene o crea un tipo de almacenamiento

        Args:
            value: ID (int) o nombre (str) del almacenamiento

        Returns:
            int: ID del almacenamiento, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Storage, value)

    @staticmethod
    def get_or_create_ram(value):
        """
        Obtiene o crea un tipo de RAM

        Args:
            value: ID (int) o nombre (str) de la RAM

        Returns:
            int: ID de la RAM, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Ram, value)

    @staticmethod
    def get_or_create_store(value):
        """
        Obtiene o crea una tienda

        Args:
            value: ID (int) o nombre (str) de la tienda

        Returns:
            int: ID de la tienda, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Store, value)

    @staticmethod
    def get_or_create_location(value, store_id=None):
        """
        Obtiene o crea una ubicación

        Args:
            value: ID (int) o nombre (str) de la ubicación
            store_id: ID de la tienda asociada

        Returns:
            int: ID de la ubicación, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        # Si es un ID existente
        if isinstance(value, int) and value > 0:
            return value

        # Si es un string (nuevo valor)
        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            # Buscar si ya existe en la misma tienda
            query = Location.query.filter(
                db.func.lower(Location.name) == name.lower()
            )

            if store_id:
                query = query.filter(Location.store_id == store_id)

            existing = query.first()

            if existing:
                return existing.id

            # Crear nueva ubicación
            new_location = Location(name=name, store_id=store_id, is_active=True)
            db.session.add(new_location)
            db.session.flush()
            return new_location.id

        return None

    @staticmethod
    def get_or_create_supplier(value):
        """
        Obtiene o crea un proveedor

        Args:
            value: ID (int) o nombre (str) del proveedor

        Returns:
            int: ID del proveedor, o None si value es inválido
        """
        return CatalogService._get_or_create_generic(Supplier, value)

    @staticmethod
    def process_laptop_form_data(form_data):
        """
        Procesa todos los campos de catálogo del formulario
        Convierte strings a IDs (creando registros si es necesario)

        Args:
            form_data: Diccionario con los datos del formulario

        Returns:
            dict: Diccionario con los IDs procesados
        """
        processed_data = {}

        # Procesar marca primero (se necesita para el modelo)
        brand_id = CatalogService.get_or_create_brand(form_data.get('brand_id'))
        processed_data['brand_id'] = brand_id

        # Procesar modelo (puede necesitar brand_id)
        model_id = CatalogService.get_or_create_model(
            form_data.get('model_id'),
            brand_id
        )
        processed_data['model_id'] = model_id

        # Procesar otros catálogos de especificaciones
        processed_data['processor_id'] = CatalogService.get_or_create_processor(
            form_data.get('processor_id')
        )

        processed_data['os_id'] = CatalogService.get_or_create_os(
            form_data.get('os_id')
        )

        processed_data['screen_id'] = CatalogService.get_or_create_screen(
            form_data.get('screen_id')
        )

        processed_data['graphics_card_id'] = CatalogService.get_or_create_graphics_card(
            form_data.get('graphics_card_id')
        )

        processed_data['storage_id'] = CatalogService.get_or_create_storage(
            form_data.get('storage_id')
        )

        processed_data['ram_id'] = CatalogService.get_or_create_ram(
            form_data.get('ram_id')
        )

        # Procesar tienda primero (se necesita para ubicación)
        store_id = CatalogService.get_or_create_store(form_data.get('store_id'))
        processed_data['store_id'] = store_id

        # Procesar ubicación (puede necesitar store_id)
        location_id = CatalogService.get_or_create_location(
            form_data.get('location_id'),
            store_id
        )
        processed_data['location_id'] = location_id

        # Procesar proveedor
        processed_data['supplier_id'] = CatalogService.get_or_create_supplier(
            form_data.get('supplier_id')
        )

        return processed_data

    @staticmethod
    def get_catalog_stats():
        """
        Obtiene estadísticas de todos los catálogos

        Returns:
            dict: Diccionario con conteos de cada catálogo
        """
        return {
            'brands': Brand.query.filter_by(is_active=True).count(),
            'models': LaptopModel.query.filter_by(is_active=True).count(),
            'processors': Processor.query.filter_by(is_active=True).count(),
            'operating_systems': OperatingSystem.query.filter_by(is_active=True).count(),
            'screens': Screen.query.filter_by(is_active=True).count(),
            'graphics_cards': GraphicsCard.query.filter_by(is_active=True).count(),
            'storage': Storage.query.filter_by(is_active=True).count(),
            'ram': Ram.query.filter_by(is_active=True).count(),
            'stores': Store.query.filter_by(is_active=True).count(),
            'locations': Location.query.filter_by(is_active=True).count(),
            'suppliers': Supplier.query.filter_by(is_active=True).count()
        }

    @staticmethod
    def deactivate_item(model, item_id):
        """
        Desactiva un item de catálogo (soft delete)

        Args:
            model: Modelo de SQLAlchemy
            item_id: ID del item a desactivar

        Returns:
            bool: True si se desactivó exitosamente
        """
        item = model.query.get(item_id)
        if item:
            item.is_active = False
            db.session.commit()
            return True
        return False

    @staticmethod
    def reactivate_item(model, item_id):
        """
        Reactiva un item de catálogo

        Args:
            model: Modelo de SQLAlchemy
            item_id: ID del item a reactivar

        Returns:
            bool: True si se reactivó exitosamente
        """
        item = model.query.get(item_id)
        if item:
            item.is_active = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def merge_items(model, source_id, target_id, update_laptops=True):
        """
        Fusiona dos items de catálogo, moviendo todas las referencias
        del source al target y desactivando el source

        Args:
            model: Modelo de SQLAlchemy
            source_id: ID del item a fusionar (será desactivado)
            target_id: ID del item destino
            update_laptops: Si actualizar las laptops que referencian al source

        Returns:
            int: Número de laptops actualizadas
        """
        from app.models.laptop import Laptop

        source = model.query.get(source_id)
        target = model.query.get(target_id)

        if not source or not target:
            return 0

        updated_count = 0

        if update_laptops:
            # Determinar el campo de FK basado en el modelo
            field_mapping = {
                Brand: 'brand_id',
                LaptopModel: 'model_id',
                Processor: 'processor_id',
                OperatingSystem: 'os_id',
                Screen: 'screen_id',
                GraphicsCard: 'graphics_card_id',
                Storage: 'storage_id',
                Ram: 'ram_id',
                Store: 'store_id',
                Location: 'location_id',
                Supplier: 'supplier_id'
            }

            field_name = field_mapping.get(model)
            if field_name:
                # Actualizar todas las laptops que usan el source
                updated_count = Laptop.query.filter(
                    getattr(Laptop, field_name) == source_id
                ).update({field_name: target_id}, synchronize_session=False)

        # Desactivar el source
        source.is_active = False
        db.session.commit()

        return updated_count
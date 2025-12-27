"""
Servicio para manejar la creación dinámica de catálogos
"""
from app import db
from app.models.laptop import (
    Brand, LaptopModel, Processor, OperatingSystem,
    Screen, GraphicsCard, StorageType, RAMType
)


class CatalogService:
    """Servicio para gestión dinámica de catálogos"""

    @staticmethod
    def get_or_create_brand(value):
        """
        Obtiene o crea una marca

        Args:
            value: ID (int) o nombre (str) de la marca

        Returns:
            int: ID de la marca, o None si value es inválido
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
            existing = Brand.query.filter(
                db.func.lower(Brand.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            # Crear nueva marca
            new_brand = Brand(name=name, is_active=True)
            db.session.add(new_brand)
            db.session.flush()  # Para obtener el ID sin commit
            return new_brand.id

        return None

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
        if not value or value == 0 or value == '0':
            return None

        if isinstance(value, int) and value > 0:
            return value

        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            existing = Processor.query.filter(
                db.func.lower(Processor.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            new_processor = Processor(name=name, is_active=True)
            db.session.add(new_processor)
            db.session.flush()
            return new_processor.id

        return None

    @staticmethod
    def get_or_create_os(value):
        """
        Obtiene o crea un sistema operativo

        Args:
            value: ID (int) o nombre (str) del sistema operativo

        Returns:
            int: ID del sistema operativo, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        if isinstance(value, int) and value > 0:
            return value

        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            existing = OperatingSystem.query.filter(
                db.func.lower(OperatingSystem.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            new_os = OperatingSystem(name=name, is_active=True)
            db.session.add(new_os)
            db.session.flush()
            return new_os.id

        return None

    @staticmethod
    def get_or_create_screen(value):
        """
        Obtiene o crea una pantalla

        Args:
            value: ID (int) o nombre (str) de la pantalla

        Returns:
            int: ID de la pantalla, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        if isinstance(value, int) and value > 0:
            return value

        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            existing = Screen.query.filter(
                db.func.lower(Screen.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            new_screen = Screen(name=name, is_active=True)
            db.session.add(new_screen)
            db.session.flush()
            return new_screen.id

        return None

    @staticmethod
    def get_or_create_graphics_card(value):
        """
        Obtiene o crea una tarjeta gráfica

        Args:
            value: ID (int) o nombre (str) de la tarjeta gráfica

        Returns:
            int: ID de la tarjeta gráfica, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        if isinstance(value, int) and value > 0:
            return value

        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            existing = GraphicsCard.query.filter(
                db.func.lower(GraphicsCard.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            new_gpu = GraphicsCard(name=name, is_active=True)
            db.session.add(new_gpu)
            db.session.flush()
            return new_gpu.id

        return None

    @staticmethod
    def get_or_create_storage(value):
        """
        Obtiene o crea un tipo de almacenamiento

        Args:
            value: ID (int) o nombre (str) del almacenamiento

        Returns:
            int: ID del almacenamiento, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        if isinstance(value, int) and value > 0:
            return value

        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            existing = StorageType.query.filter(
                db.func.lower(StorageType.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            new_storage = StorageType(name=name, is_active=True)
            db.session.add(new_storage)
            db.session.flush()
            return new_storage.id

        return None

    @staticmethod
    def get_or_create_ram(value):
        """
        Obtiene o crea un tipo de RAM

        Args:
            value: ID (int) o nombre (str) de la RAM

        Returns:
            int: ID de la RAM, o None si value es inválido
        """
        if not value or value == 0 or value == '0':
            return None

        if isinstance(value, int) and value > 0:
            return value

        if isinstance(value, str):
            name = value.strip()

            if not name:
                return None

            existing = RAMType.query.filter(
                db.func.lower(RAMType.name) == name.lower()
            ).first()

            if existing:
                return existing.id

            new_ram = RAMType(name=name, is_active=True)
            db.session.add(new_ram)
            db.session.flush()
            return new_ram.id

        return None

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

        # Procesar otros catálogos
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

        return processed_data
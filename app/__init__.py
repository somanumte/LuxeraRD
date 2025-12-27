# ============================================
# INICIALIZACIÓN DE LA APLICACIÓN FLASK
# ============================================

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import logging
from logging.handlers import RotatingFileHandler
import os

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app(config_name='development'):
    """
    Factory pattern para crear la aplicación Flask

    Args:
        config_name: Nombre de la configuración a usar ('development', 'production', 'testing', 'default')

    Returns:
        Flask app configurada
    """
    from config import config

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Configurar Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # User loader para Flask-Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.inventory import inventory_bp
    from app.routes.api.catalog_api import catalog_api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(catalog_api_bp)

    # Registrar manejadores de errores
    from app.routes.main import register_error_handlers
    register_error_handlers(app)

    # Configurar logging (solo en producción)
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            'logs/luxera.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Luxera startup')

    # Context processor global (variables disponibles en todos los templates)
    @app.context_processor
    def inject_global_vars():
        """Inyecta variables globales en todos los templates"""
        return {
            'app_name': 'Luxera',
            'app_version': '1.0.0',
            'allow_registration': app.config.get('ALLOW_REGISTRATION', False)
        }

    # Comandos CLI personalizados
    register_cli_commands(app)

    return app


def register_cli_commands(app):
    """
    Registra comandos CLI personalizados
    """

    @app.cli.command()
    def init_db():
        """Inicializa la base de datos creando todas las tablas"""
        with app.app_context():
            db.create_all()
            print("✅ Base de datos inicializada exitosamente")

    @app.cli.command()
    def drop_db():
        """PELIGRO: Elimina todas las tablas de la base de datos"""
        with app.app_context():
            if input("⚠️  ¿Estás seguro? Esto eliminará TODOS los datos (yes/no): ") == 'yes':
                db.drop_all()
                print("🗑️  Base de datos eliminada")
            else:
                print("❌ Operación cancelada")

    @app.cli.command()
    def create_admin():
        """Crea un usuario administrador"""
        from app.models.user import User

        with app.app_context():
            # Verificar si ya existe
            existing = User.query.filter_by(email='admin@luxera.com').first()

            if existing:
                print("⚠️  El usuario admin ya existe")
                return

            # Crear admin
            admin = User(
                username='admin',
                email='admin@luxera.com',
                full_name='Administrador',
                is_admin=True,
                is_active=True
            )
            admin.set_password('admin123')

            db.session.add(admin)
            db.session.commit()

            print("✅ Usuario admin creado exitosamente")
            print("   Email: admin@luxera.com")
            print("   Password: admin123")
            print("   ⚠️  CAMBIAR PASSWORD en producción!")

    @app.cli.command()
    def seed_catalog():
        """Pobla los catálogos con datos de ejemplo"""
        from app.models.laptop import (
            Brand, LaptopModel, Processor, OperatingSystem,
            Screen, GraphicsCard, StorageType, RAMType, Store, Location
        )

        with app.app_context():
            print("📦 Poblando catálogos...")

            # Brands
            brands_data = ['Dell', 'HP', 'Lenovo', 'ASUS', 'Acer', 'MSI', 'Apple', 'Samsung']
            for name in brands_data:
                if not Brand.query.filter_by(name=name).first():
                    db.session.add(Brand(name=name))

            # Processors
            processors_data = [
                'Intel Core i3-1215U', 'Intel Core i5-1235U', 'Intel Core i7-1255U',
                'Intel Core i5-12500H', 'Intel Core i7-12700H', 'Intel Core i9-12900H',
                'AMD Ryzen 5 5500U', 'AMD Ryzen 7 5700U', 'AMD Ryzen 9 5900HX',
                'Apple M1', 'Apple M2', 'Apple M3'
            ]
            for name in processors_data:
                if not Processor.query.filter_by(name=name).first():
                    db.session.add(Processor(name=name))

            # Operating Systems
            os_data = [
                'Windows 11 Home', 'Windows 11 Pro', 'Windows 10 Pro',
                'macOS Sonoma', 'Ubuntu 22.04 LTS', 'Chrome OS'
            ]
            for name in os_data:
                if not OperatingSystem.query.filter_by(name=name).first():
                    db.session.add(OperatingSystem(name=name))

            # Screens
            screens_data = [
                '13.3" FHD IPS', '14" FHD IPS', '15.6" FHD IPS',
                '15.6" 2K IPS', '16" 2.5K OLED', '17.3" FHD IPS',
                '14" 2.8K OLED', '15.6" 4K OLED'
            ]
            for name in screens_data:
                if not Screen.query.filter_by(name=name).first():
                    db.session.add(Screen(name=name))

            # Graphics Cards
            gpus_data = [
                'Intel Iris Xe', 'Intel UHD Graphics',
                'NVIDIA GeForce MX550', 'NVIDIA GeForce RTX 3050',
                'NVIDIA GeForce RTX 4060', 'NVIDIA GeForce RTX 4070',
                'AMD Radeon Graphics', 'AMD Radeon RX 6600M'
            ]
            for name in gpus_data:
                if not GraphicsCard.query.filter_by(name=name).first():
                    db.session.add(GraphicsCard(name=name))

            # Storage
            storage_data = [
                '256GB SSD NVMe', '512GB SSD NVMe', '1TB SSD NVMe',
                '1TB HDD + 256GB SSD', '2TB SSD NVMe'
            ]
            for name in storage_data:
                if not StorageType.query.filter_by(name=name).first():
                    db.session.add(StorageType(name=name))

            # RAM
            ram_data = [
                '8GB DDR4', '16GB DDR4', '32GB DDR4',
                '8GB DDR5', '16GB DDR5', '32GB DDR5', '64GB DDR5'
            ]
            for name in ram_data:
                if not RAMType.query.filter_by(name=name).first():
                    db.session.add(RAMType(name=name))

            # Stores
            stores_data = ['Tienda Principal', 'Sucursal Centro', 'Sucursal Plaza']
            for name in stores_data:
                if not Store.query.filter_by(name=name).first():
                    db.session.add(Store(name=name))

            # Locations
            locations_data = [
                'Estante A-1', 'Estante A-2', 'Estante B-1',
                'Vitrina Principal', 'Bodega', 'Almacén'
            ]
            for name in locations_data:
                if not Location.query.filter_by(name=name).first():
                    db.session.add(Location(name=name))

            db.session.commit()
            print("✅ Catálogos poblados exitosamente")

    @app.cli.command()
    def create_sample_laptop():
        """Crea una laptop de ejemplo"""
        from app.models.laptop import (
            Laptop, Brand, LaptopModel, Processor, OperatingSystem,
            Screen, GraphicsCard, StorageType, RAMType
        )
        from app.services.sku_service import SKUService
        from datetime import datetime

        with app.app_context():
            # Verificar que existan catálogos
            if not Brand.query.first():
                print("⚠️  Primero ejecuta: flask seed-catalog")
                return

            # Obtener datos de catálogos
            brand = Brand.query.filter_by(name='Dell').first()
            processor = Processor.query.filter(Processor.name.like('%i7%')).first()
            os = OperatingSystem.query.filter_by(name='Windows 11 Pro').first()
            screen = Screen.query.filter(Screen.name.like('%15.6%')).first()
            gpu = GraphicsCard.query.filter(GraphicsCard.name.like('%RTX%')).first()
            storage = StorageType.query.filter(StorageType.name.like('%512GB%')).first()
            ram = RAMType.query.filter(RAMType.name.like('%16GB%')).first()

            # Crear modelo si no existe
            model = LaptopModel.query.filter_by(name='Inspiron 15 3000').first()
            if not model:
                model = LaptopModel(name='Inspiron 15 3000', brand_id=brand.id)
                db.session.add(model)
                db.session.commit()

            # Crear laptop
            laptop = Laptop(
                sku=SKUService.generate_laptop_sku(),
                brand_id=brand.id,
                model_id=model.id,
                processor_id=processor.id,
                os_id=os.id,
                screen_id=screen.id,
                graphics_card_id=gpu.id,
                storage_id=storage.id,
                ram_id=ram.id,
                purchase_cost=800,
                sale_price=1100,
                quantity=5,
                min_alert=2,
                category='working',
                condition='new',
                aesthetic_grade='A+',
                entry_date=datetime.utcnow()
            )

            db.session.add(laptop)
            db.session.commit()

            print(f"✅ Laptop de ejemplo creada: {laptop.sku}")
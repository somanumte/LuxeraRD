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
import click
from datetime import date, timedelta
import random
import re

# Inicializar extensiones
db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app(config_name='development'):
    """
    Factory pattern para crear la aplicación Flask
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
    from app.routes.api.customers import customers_bp
    from app.routes.invoices import invoices_bp  # ← NUEVA LÍNEA


    app.register_blueprint(customers_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(catalog_api_bp)
    app.register_blueprint(invoices_bp)  # ← NUEVA LÍNEA

    # Registrar manejadores de errores
    from app.routes.main import register_error_handlers
    register_error_handlers(app)

    # Configurar logging (solo en producción)
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            'logs/luxera.log',
            maxBytes=10240000,
            backupCount=10
        )

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Luxera startup')

    # Context processor global
    @app.context_processor
    def inject_global_vars():
        return {
            'app_name': 'Luxera',
            'app_version': '1.0.0',
            'allow_registration': app.config.get('ALLOW_REGISTRATION', False)
        }

    # Registrar comandos CLI
    register_cli_commands(app)

    return app


def register_cli_commands(app):
    """
    Registra todos los comandos CLI personalizados
    """
    from app.models.invoice import Invoice, InvoiceItem, InvoiceSettings
    from app.models.user import User
    from app.models.laptop import (
        Laptop, LaptopImage, Brand, LaptopModel, Processor,
        OperatingSystem, Screen, GraphicsCard, Storage, Ram,
        Store, Location, Supplier
    )
    from app.services.sku_service import SKUService

    # ===== COMANDO: reset-db =====
    @app.cli.command('reset-db')
    def reset_db():
        """⚠️ PELIGRO: Borra TODA la base de datos y la recrea vacía"""
        confirm = input("⚠️  ¿Estás seguro? Esto BORRARÁ TODOS los datos (yes/no): ").strip()

        if confirm.lower() != 'yes':
            click.echo("❌ Operación cancelada")
            return

        click.echo("🗑️  Eliminando todas las tablas...")
        db.drop_all()

        click.echo("🔨 Creando nuevas tablas...")
        db.create_all()

        click.echo("✅ Base de datos reiniciada correctamente")

    # ===== COMANDO: setup-fresh =====
    @app.cli.command('setup-fresh')
    def setup_fresh():
        """⚠️ Reinicia la BD y carga admin + catálogos + 50 laptops"""
        confirm = input("⚠️  Esto BORRARÁ TODO y creará datos nuevos. ¿Continuar? (yes/no): ").strip()

        if confirm.lower() != 'yes':
            click.echo("❌ Operación cancelada")
            return

        click.echo("\n" + "=" * 60)
        click.echo("🔄 CONFIGURACIÓN INICIAL DE LUXERA")
        click.echo("=" * 60)

        # 1. Reset DB
        click.echo("\n📦 Paso 1/5: Reiniciando base de datos...")
        db.drop_all()
        db.create_all()
        click.echo("   ✅ Base de datos creada")

        # 2. Crear Admin
        click.echo("\n👤 Paso 2/5: Creando usuario administrador...")
        admin = User(
            username='admin',
            email='felixjosemartinezbrito@gmail.com',
            full_name='Felix Jose Martinez Brito',
            is_admin=True,
            is_active=True
        )
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()
        click.echo("   ✅ Admin creado: felixjosemartinezbrito@gmail.com")

        # 3. Crear Catálogos
        click.echo("\n📚 Paso 3/5: Creando catálogos...")
        _create_catalogs()
        click.echo("   ✅ Catálogos creados")

        # 4. Crear Laptops
        click.echo("\n💻 Paso 4/5: Creando 50 laptops de prueba...")
        _create_sample_laptops(admin.id)
        click.echo("   ✅ 50 laptops creadas")

        # 5. Resumen
        click.echo("\n📊 Paso 5/5: Verificando datos...")
        laptops_count = Laptop.query.count()
        brands_count = Brand.query.count()

        click.echo("\n" + "=" * 60)
        click.echo("✅ CONFIGURACIÓN COMPLETADA")
        click.echo("=" * 60)
        click.echo(f"   👤 Admin: felixjosemartinezbrito@gmail.com")
        click.echo(f"   🔑 Password: 1234")
        click.echo(f"   💻 Laptops: {laptops_count}")
        click.echo(f"   🏭 Marcas: {brands_count}")
        click.echo("=" * 60 + "\n")

    # ===== COMANDO: init-db =====
    @app.cli.command('init-db')
    def init_db():
        """Inicializa la base de datos (crea tablas sin borrar)"""
        db.create_all()
        click.echo("✅ Base de datos inicializada")

    # ===== COMANDO: create-admin =====
    @app.cli.command('create-admin')
    def create_admin():
        """Crea el usuario administrador"""
        existing = User.query.filter_by(email='felixjosemartinezbrito@gmail.com').first()

        if existing:
            click.echo("⚠️  El admin ya existe")
            return

        admin = User(
            username='admin',
            email='felixjosemartinezbrito@gmail.com',
            full_name='Felix Jose Martinez Brito',
            is_admin=True,
            is_active=True
        )
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()

        click.echo("✅ Admin creado: felixjosemartinezbrito@gmail.com / 1234")

    # ===== COMANDO: seed-catalog =====
    @app.cli.command('seed-catalog')
    def seed_catalog():
        """Pobla los catálogos con datos"""
        _create_catalogs()
        click.echo("✅ Catálogos poblados exitosamente")

    # ===== COMANDO: seed-laptops =====
    @app.cli.command('seed-laptops')
    def seed_laptops():
        """Crea 50 laptops de prueba"""
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            click.echo("❌ Primero crea un admin con: flask create-admin")
            return

        _create_sample_laptops(admin.id)
        click.echo("✅ 50 laptops creadas")

    # ===== COMANDO: list-users =====
    @app.cli.command('list-users')
    def list_users():
        """Lista todos los usuarios"""
        users = User.query.order_by(User.created_at.desc()).all()

        if not users:
            click.echo("🔭 No hay usuarios registrados")
            return

        click.echo(f"\n📋 Total de usuarios: {len(users)}")
        click.echo("\n" + "=" * 80)
        click.echo(f"{'ID':<5} {'Username':<15} {'Email':<35} {'Admin':<8}")
        click.echo("=" * 80)

        for user in users:
            click.echo(f"{user.id:<5} {user.username:<15} {user.email:<35} {'Sí' if user.is_admin else 'No':<8}")

        click.echo("=" * 80 + "\n")

    # ===== COMANDO: list-laptops =====
    @app.cli.command('list-laptops')
    def list_laptops():
        """Lista las laptops del inventario"""
        laptops = Laptop.query.order_by(Laptop.entry_date.desc()).all()

        if not laptops:
            click.echo("🔭 No hay laptops en el inventario")
            return

        total_value = sum(float(l.sale_price * l.quantity) for l in laptops)

        click.echo(f"\n💻 Total: {len(laptops)} laptops | Valor: ${total_value:,.2f}")
        click.echo("\n" + "=" * 100)
        click.echo(f"{'SKU':<18} {'Marca':<8} {'Modelo':<30} {'Precio':<10} {'Cant.':<6}")
        click.echo("=" * 100)

        for laptop in laptops[:25]:
            model_name = laptop.model.name[:28] if laptop.model else 'N/A'
            brand_name = laptop.brand.name[:6] if laptop.brand else 'N/A'
            click.echo(f"{laptop.sku:<18} {brand_name:<8} {model_name:<30} ${float(laptop.sale_price):>7,.0f} {laptop.quantity:>4}")

        if len(laptops) > 25:
            click.echo(f"\n... y {len(laptops) - 25} más")

        click.echo("=" * 100 + "\n")

    # ===== COMANDO: inventory-stats =====
    @app.cli.command('inventory-stats')
    def inventory_stats():
        """Muestra estadísticas del inventario"""
        laptops = Laptop.query.all()

        if not laptops:
            click.echo("🔭 No hay laptops")
            return

        click.echo("\n" + "=" * 50)
        click.echo("📊 ESTADÍSTICAS DEL INVENTARIO")
        click.echo("=" * 50)

        total_units = sum(l.quantity for l in laptops)
        total_value = sum(float(l.sale_price * l.quantity) for l in laptops)
        total_cost = sum(float(l.purchase_cost * l.quantity) for l in laptops)

        click.echo(f"\n💰 FINANCIERO")
        click.echo(f"   Valor de venta: ${total_value:,.2f}")
        click.echo(f"   Costo total: ${total_cost:,.2f}")
        click.echo(f"   Ganancia potencial: ${total_value - total_cost:,.2f}")

        click.echo(f"\n📦 INVENTARIO")
        click.echo(f"   SKUs: {len(laptops)}")
        click.echo(f"   Unidades: {total_units}")
        click.echo(f"   Publicadas: {len([l for l in laptops if l.is_published])}")
        click.echo(f"   Destacadas: {len([l for l in laptops if l.is_featured])}")

        click.echo(f"\n🏷️ POR CATEGORÍA")
        for cat in ['laptop', 'workstation', 'gaming']:
            count = len([l for l in laptops if l.category == cat])
            click.echo(f"   {cat.capitalize()}: {count}")

        click.echo(f"\n🏭 POR MARCA")
        brands_stats = {}
        for l in laptops:
            name = l.brand.name if l.brand else 'N/A'
            brands_stats[name] = brands_stats.get(name, 0) + l.quantity
        for name, qty in sorted(brands_stats.items(), key=lambda x: -x[1]):
            click.echo(f"   {name}: {qty} unidades")

        click.echo("\n" + "=" * 50 + "\n")

    # ===== FUNCIONES HELPER =====

    def _create_catalogs():
        """Crea todos los catálogos necesarios"""

        # === MARCAS ===
        brands = ['Dell', 'Lenovo', 'HP', 'ASUS', 'Acer', 'MSI']
        for name in brands:
            if not Brand.query.filter_by(name=name).first():
                db.session.add(Brand(name=name, is_active=True))

        # === PROCESADORES ===
        processors = [
            'Intel Core i3-1215U', 'Intel Core i5-1235U', 'Intel Core i7-1255U',
            'Intel Core i5-12450H', 'Intel Core i5-12500H', 'Intel Core i7-12650H',
            'Intel Core i7-12700H', 'Intel Core i9-12900H',
            'Intel Core i5-1335U', 'Intel Core i7-1355U', 'Intel Core i7-1365U',
            'Intel Core i5-1340P', 'Intel Core i7-1260P',
            'Intel Core i5-13420H', 'Intel Core i5-13450H', 'Intel Core i5-13500H',
            'Intel Core i7-13620H', 'Intel Core i7-13650HX', 'Intel Core i7-13700H',
            'Intel Core i7-13700HX', 'Intel Core i9-13900H', 'Intel Core i9-13900HX',
            'Intel Core i9-13950HX', 'Intel Core i9-13980HX',
            'AMD Ryzen 5 6600H', 'AMD Ryzen 7 6800H', 'AMD Ryzen 9 6900HX',
            'AMD Ryzen 5 7530U', 'AMD Ryzen 5 7535HS', 'AMD Ryzen 7 7735HS',
            'AMD Ryzen 7 7840HS', 'AMD Ryzen 9 7940HS', 'AMD Ryzen 9 7945HX',
        ]
        for name in processors:
            if not Processor.query.filter_by(name=name).first():
                db.session.add(Processor(name=name, is_active=True))

        # === SISTEMAS OPERATIVOS ===
        operating_systems = [
            'Windows 11 Home', 'Windows 11 Pro', 'Windows 10 Pro',
            'FreeDOS', 'Sin Sistema Operativo'
        ]
        for name in operating_systems:
            if not OperatingSystem.query.filter_by(name=name).first():
                db.session.add(OperatingSystem(name=name, is_active=True))

        # === PANTALLAS ===
        screens = [
            '14" FHD IPS (1920x1080)', '14" FHD IPS 144Hz',
            '14" QHD IPS 165Hz (2560x1440)',
            '15.6" FHD IPS (1920x1080)', '15.6" FHD IPS 120Hz', '15.6" FHD IPS 144Hz',
            '15.6" FHD VA 144Hz', '15.6" QHD IPS 165Hz (2560x1440)',
            '16" FHD+ IPS (1920x1200)', '16" WQXGA IPS (2560x1600)',
            '16" QHD+ 165Hz (2560x1600)', '16" QHD IPS 165Hz (2560x1440)',
            '17.3" FHD IPS (1920x1080)', '17.3" FHD IPS 144Hz',
            '17.3" QHD IPS 165Hz (2560x1440)',
            '14" 2.8K OLED 90Hz', '15.6" 4K OLED (3840x2160)',
            '16" 4K OLED HDR', '18" QHD+ 240Hz (2560x1600)',
        ]
        for name in screens:
            if not Screen.query.filter_by(name=name).first():
                db.session.add(Screen(name=name, is_active=True))

        # === TARJETAS GRÁFICAS ===
        graphics_cards = [
            'Intel UHD Graphics', 'Intel Iris Xe Graphics',
            'AMD Radeon Graphics', 'AMD Radeon 680M',
            'NVIDIA GeForce GTX 1650', 'NVIDIA GeForce GTX 1660 Ti',
            'NVIDIA GeForce RTX 3050', 'NVIDIA GeForce RTX 3050 Ti',
            'NVIDIA GeForce RTX 3060', 'NVIDIA GeForce RTX 3070', 'NVIDIA GeForce RTX 3080',
            'NVIDIA GeForce RTX 4050', 'NVIDIA GeForce RTX 4060',
            'NVIDIA GeForce RTX 4070', 'NVIDIA GeForce RTX 4080', 'NVIDIA GeForce RTX 4090',
        ]
        for name in graphics_cards:
            if not GraphicsCard.query.filter_by(name=name).first():
                db.session.add(GraphicsCard(name=name, is_active=True))

        # === ALMACENAMIENTO ===
        storage_types = [
            '256GB SSD NVMe', '512GB SSD NVMe', '512GB SSD NVMe PCIe 4.0',
            '1TB SSD NVMe', '1TB SSD NVMe PCIe 4.0', '2TB SSD NVMe PCIe 4.0',
            '256GB SSD + 1TB HDD', '512GB SSD + 1TB HDD',
        ]
        for name in storage_types:
            if not Storage.query.filter_by(name=name).first():
                db.session.add(Storage(name=name, is_active=True))

        # === RAM ===
        ram_types = [
            '8GB DDR4 3200MHz', '16GB DDR4 3200MHz', '32GB DDR4 3200MHz',
            '8GB DDR5 4800MHz', '16GB DDR5 4800MHz', '16GB DDR5 5200MHz',
            '32GB DDR5 4800MHz', '32GB DDR5 5200MHz', '64GB DDR5 5200MHz',
        ]
        for name in ram_types:
            if not Ram.query.filter_by(name=name).first():
                db.session.add(Ram(name=name, is_active=True))

        # === TIENDAS ===
        stores = [
            ('Tienda Principal', 'Av. Principal #123', '809-555-0001'),
            ('Sucursal Centro', 'Calle El Conde #456', '809-555-0002'),
            ('Sucursal Plaza', 'Plaza Central Local 23', '809-555-0003'),
        ]
        for name, address, phone in stores:
            if not Store.query.filter_by(name=name).first():
                db.session.add(Store(name=name, address=address, phone=phone, is_active=True))

        # === UBICACIONES ===
        locations = [
            'Vitrina Principal', 'Vitrina Gaming', 'Estante A-1', 'Estante A-2',
            'Estante B-1', 'Estante B-2', 'Bodega', 'Almacén'
        ]
        for name in locations:
            if not Location.query.filter_by(name=name).first():
                db.session.add(Location(name=name, is_active=True))

        # === PROVEEDORES ===
        suppliers = [
            ('TechDistributor RD', 'Juan Pérez', 'ventas@techdist.com', '809-555-1001'),
            ('CompuMaster', 'María García', 'info@compumaster.com', '809-555-1002'),
            ('Digital Import', 'Carlos López', 'sales@digitalimport.com', '809-555-1003'),
            ('MegaTech Supplies', 'Ana Rodríguez', 'orders@megatech.com', '809-555-1004'),
        ]
        for name, contact, email, phone in suppliers:
            if not Supplier.query.filter_by(name=name).first():
                db.session.add(Supplier(
                    name=name, contact_name=contact, email=email, phone=phone, is_active=True
                ))

        db.session.commit()

    def _create_sample_laptops(admin_id):
        """Crea 50 laptops reales de prueba"""

        # Obtener referencias
        brands = {b.name: b.id for b in Brand.query.all()}
        processors = {p.name: p.id for p in Processor.query.all()}
        screens = {s.name: s.id for s in Screen.query.all()}
        gpus = {g.name: g.id for g in GraphicsCard.query.all()}
        storage = {s.name: s.id for s in Storage.query.all()}
        ram = {r.name: r.id for r in Ram.query.all()}
        os_list = {o.name: o.id for o in OperatingSystem.query.all()}
        stores = list(Store.query.all())
        locations = list(Location.query.all())
        suppliers = list(Supplier.query.all())

        # 50 laptops reales
        laptops_data = [
            # DELL (10)
            {'brand': 'Dell', 'model': 'Inspiron 15 3520', 'processor': 'Intel Core i5-1235U', 'ram': '8GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 450, 'price': 599},
            {'brand': 'Dell', 'model': 'Inspiron 15 3530', 'processor': 'Intel Core i7-1355U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 550, 'price': 749},
            {'brand': 'Dell', 'model': 'Latitude 5540', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 750, 'price': 999},
            {'brand': 'Dell', 'model': 'Latitude 7440', 'processor': 'Intel Core i7-1355U', 'ram': '16GB DDR5 5200MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 950, 'price': 1299},
            {'brand': 'Dell', 'model': 'XPS 15 9530', 'processor': 'Intel Core i7-13700H', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 1200, 'price': 1599},
            {'brand': 'Dell', 'model': 'XPS 15 9530 OLED', 'processor': 'Intel Core i7-13700H', 'ram': '32GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '15.6" 4K OLED (3840x2160)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 1600, 'price': 2199},
            {'brand': 'Dell', 'model': 'G15 5530', 'processor': 'Intel Core i5-13450H', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050', 'screen': '15.6" FHD IPS 120Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 700, 'price': 949},
            {'brand': 'Dell', 'model': 'G15 5535', 'processor': 'AMD Ryzen 7 7840HS', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 850, 'price': 1149},
            {'brand': 'Dell', 'model': 'G16 7630', 'processor': 'Intel Core i7-13650HX', 'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '16" QHD+ 165Hz (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1100, 'price': 1449},
            {'brand': 'Dell', 'model': 'Alienware m16 R1', 'processor': 'Intel Core i9-13900HX', 'ram': '32GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4080', 'screen': '16" QHD+ 165Hz (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2200, 'price': 2899},
            # LENOVO (10)
            {'brand': 'Lenovo', 'model': 'IdeaPad 3 15IAU7', 'processor': 'Intel Core i3-1215U', 'ram': '8GB DDR4 3200MHz', 'storage': '256GB SSD NVMe', 'gpu': 'Intel UHD Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 320, 'price': 449},
            {'brand': 'Lenovo', 'model': 'IdeaPad 5 15IAL7', 'processor': 'Intel Core i5-1235U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 480, 'price': 649},
            {'brand': 'Lenovo', 'model': 'ThinkPad E15 Gen 4', 'processor': 'Intel Core i5-1235U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 620, 'price': 849},
            {'brand': 'Lenovo', 'model': 'ThinkPad T14 Gen 4', 'processor': 'Intel Core i7-1355U', 'ram': '16GB DDR5 5200MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 900, 'price': 1249},
            {'brand': 'Lenovo', 'model': 'ThinkPad X1 Carbon Gen 11', 'processor': 'Intel Core i7-1365U', 'ram': '16GB DDR5 5200MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" 2.8K OLED 90Hz', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 1300, 'price': 1799},
            {'brand': 'Lenovo', 'model': 'IdeaPad Gaming 3 15IAH7', 'processor': 'Intel Core i5-12500H', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050', 'screen': '15.6" FHD IPS 120Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 600, 'price': 799},
            {'brand': 'Lenovo', 'model': 'LOQ 15IRH8', 'processor': 'Intel Core i5-13420H', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 750, 'price': 999},
            {'brand': 'Lenovo', 'model': 'Legion 5 15IAH7H', 'processor': 'Intel Core i7-12700H', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 950, 'price': 1299},
            {'brand': 'Lenovo', 'model': 'Legion Pro 5 16IRX8', 'processor': 'Intel Core i7-13700HX', 'ram': '32GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4070', 'screen': '16" WQXGA IPS (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1400, 'price': 1899},
            {'brand': 'Lenovo', 'model': 'Legion Pro 7 16IRX8H', 'processor': 'Intel Core i9-13900HX', 'ram': '32GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4080', 'screen': '16" WQXGA IPS (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2000, 'price': 2699},
            # HP (10)
            {'brand': 'HP', 'model': 'HP 15-fd0xxx', 'processor': 'Intel Core i3-1215U', 'ram': '8GB DDR4 3200MHz', 'storage': '256GB SSD NVMe', 'gpu': 'Intel UHD Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 300, 'price': 399},
            {'brand': 'HP', 'model': 'HP 15-fc0xxx', 'processor': 'AMD Ryzen 5 7530U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'AMD Radeon Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 420, 'price': 549},
            {'brand': 'HP', 'model': 'HP Pavilion 15-eg3xxx', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 500, 'price': 699},
            {'brand': 'HP', 'model': 'HP ProBook 450 G10', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 650, 'price': 899},
            {'brand': 'HP', 'model': 'HP EliteBook 840 G10', 'processor': 'Intel Core i7-1355U', 'ram': '16GB DDR5 5200MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" FHD IPS (1920x1080)', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 950, 'price': 1349},
            {'brand': 'HP', 'model': 'HP Spectre x360 14', 'processor': 'Intel Core i7-1355U', 'ram': '16GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" 2.8K OLED 90Hz', 'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 1150, 'price': 1599},
            {'brand': 'HP', 'model': 'HP Victus 15-fa0xxx', 'processor': 'Intel Core i5-12450H', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 580, 'price': 779},
            {'brand': 'HP', 'model': 'HP Victus 16-r0xxx', 'processor': 'Intel Core i5-13500H', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '16" FHD+ IPS (1920x1200)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 750, 'price': 999},
            {'brand': 'HP', 'model': 'HP OMEN 16-wf0xxx', 'processor': 'Intel Core i7-13700HX', 'ram': '16GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '16" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1050, 'price': 1399},
            {'brand': 'HP', 'model': 'HP OMEN 17-ck2xxx', 'processor': 'Intel Core i9-13900HX', 'ram': '32GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4080', 'screen': '17.3" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1900, 'price': 2499},
            # ASUS (10)
            {'brand': 'ASUS', 'model': 'ASUS Vivobook 15 X1502ZA', 'processor': 'Intel Core i3-1215U', 'ram': '8GB DDR4 3200MHz', 'storage': '256GB SSD NVMe', 'gpu': 'Intel UHD Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 340, 'price': 449},
            {'brand': 'ASUS', 'model': 'ASUS Vivobook 15 X1504VA', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 480, 'price': 649},
            {'brand': 'ASUS', 'model': 'ASUS Zenbook 14 UX3402VA', 'processor': 'Intel Core i5-1340P', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" 2.8K OLED 90Hz', 'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 800, 'price': 1099},
            {'brand': 'ASUS', 'model': 'ASUS Zenbook Pro 14 OLED', 'processor': 'Intel Core i7-13700H', 'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '14" 2.8K OLED 90Hz', 'os': 'Windows 11 Pro', 'category': 'workstation', 'cost': 1200, 'price': 1649},
            {'brand': 'ASUS', 'model': 'ASUS TUF Gaming F15 FX507ZC', 'processor': 'Intel Core i5-12500H', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 620, 'price': 849},
            {'brand': 'ASUS', 'model': 'ASUS TUF Gaming A15 FA507NV', 'processor': 'AMD Ryzen 7 7735HS', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 850, 'price': 1149},
            {'brand': 'ASUS', 'model': 'ASUS ROG Strix G15 G513RW', 'processor': 'AMD Ryzen 9 6900HX', 'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 3070', 'screen': '15.6" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1100, 'price': 1499},
            {'brand': 'ASUS', 'model': 'ASUS ROG Strix G16 G614JV', 'processor': 'Intel Core i7-13650HX', 'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '16" FHD+ IPS (1920x1200)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1000, 'price': 1349},
            {'brand': 'ASUS', 'model': 'ASUS ROG Zephyrus G14 GA402XV', 'processor': 'AMD Ryzen 9 7940HS', 'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '14" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1250, 'price': 1699},
            {'brand': 'ASUS', 'model': 'ASUS ROG Strix SCAR 18 G834JY', 'processor': 'Intel Core i9-13980HX', 'ram': '32GB DDR5 5200MHz', 'storage': '2TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4090', 'screen': '18" QHD+ 240Hz (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2800, 'price': 3699},
            # ACER (5)
            {'brand': 'Acer', 'model': 'Acer Aspire 3 A315-59', 'processor': 'Intel Core i5-1235U', 'ram': '8GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 380, 'price': 499},
            {'brand': 'Acer', 'model': 'Acer Aspire 5 A515-57', 'processor': 'Intel Core i7-1255U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 520, 'price': 699},
            {'brand': 'Acer', 'model': 'Acer Swift 3 SF314-512', 'processor': 'Intel Core i7-1260P', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe PCIe 4.0', 'gpu': 'Intel Iris Xe Graphics', 'screen': '14" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'workstation', 'cost': 680, 'price': 899},
            {'brand': 'Acer', 'model': 'Acer Nitro 5 AN515-58', 'processor': 'Intel Core i5-12500H', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 3050', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 600, 'price': 799},
            {'brand': 'Acer', 'model': 'Acer Predator Helios 16 PH16-71', 'processor': 'Intel Core i7-13700HX', 'ram': '16GB DDR5 4800MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4070', 'screen': '16" WQXGA IPS (2560x1600)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 1350, 'price': 1799},
            # MSI (5)
            {'brand': 'MSI', 'model': 'MSI Modern 15 B13M', 'processor': 'Intel Core i5-1335U', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'Intel Iris Xe Graphics', 'screen': '15.6" FHD IPS (1920x1080)', 'os': 'Windows 11 Home', 'category': 'laptop', 'cost': 500, 'price': 679},
            {'brand': 'MSI', 'model': 'MSI Thin GF63 12VE', 'processor': 'Intel Core i5-12450H', 'ram': '16GB DDR4 3200MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4050', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 680, 'price': 899},
            {'brand': 'MSI', 'model': 'MSI Cyborg 15 A12VF', 'processor': 'Intel Core i7-12650H', 'ram': '16GB DDR5 4800MHz', 'storage': '512GB SSD NVMe', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 900, 'price': 1199},
            {'brand': 'MSI', 'model': 'MSI Katana 15 B13VFK', 'processor': 'Intel Core i7-13620H', 'ram': '16GB DDR5 5200MHz', 'storage': '1TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4060', 'screen': '15.6" FHD IPS 144Hz', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 950, 'price': 1299},
            {'brand': 'MSI', 'model': 'MSI Raider GE78 HX 13VH', 'processor': 'Intel Core i9-13950HX', 'ram': '32GB DDR5 5200MHz', 'storage': '2TB SSD NVMe PCIe 4.0', 'gpu': 'NVIDIA GeForce RTX 4080', 'screen': '17.3" QHD IPS 165Hz (2560x1440)', 'os': 'Windows 11 Home', 'category': 'gaming', 'cost': 2300, 'price': 2999},
        ]

        # Crear modelos primero
        for laptop_data in laptops_data:
            brand_id = brands.get(laptop_data['brand'])
            laptop_model = LaptopModel.query.filter_by(name=laptop_data['model']).first()
            if not laptop_model:
                laptop_model = LaptopModel(name=laptop_data['model'], brand_id=brand_id, is_active=True)
                db.session.add(laptop_model)
                db.session.flush()

        db.session.commit()

        # Recargar modelos
        models = {m.name: m.id for m in LaptopModel.query.all()}

        # Variables aleatorias
        conditions = ['new', 'used', 'refurbished']
        keyboard_layouts = ['US', 'ES', 'LATAM']
        connectivity_options = [
            {'usb_a_3': 2, 'usb_c': 1, 'hdmi': 1, 'audio_jack': 1},
            {'usb_a_3': 3, 'usb_c': 2, 'hdmi': 1, 'ethernet': 1, 'audio_jack': 1},
            {'usb_a_31': 2, 'usb_c_thunderbolt': 2, 'hdmi_21': 1, 'sd_card': 1, 'audio_jack': 1},
        ]

        # Crear laptops
        for i, laptop_data in enumerate(laptops_data):
            sku = SKUService.generate_laptop_sku()

            slug_base = f"{laptop_data['brand']}-{laptop_data['model']}".lower()
            slug_base = slug_base.replace(' ', '-').replace('/', '-').replace('.', '-')
            slug = re.sub(r'[^a-z0-9-]', '', slug_base)
            slug = re.sub(r'-+', '-', slug).strip('-')

            existing = Laptop.query.filter_by(slug=slug).first()
            if existing:
                slug = f"{slug}-{i+1}"

            laptop = Laptop(
                sku=sku,
                slug=slug,
                display_name=f"{laptop_data['brand']} {laptop_data['model']}",
                short_description=f"Laptop {laptop_data['category']} con {laptop_data['processor']} y {laptop_data['ram']}",
                is_published=random.choice([True, True, True, False]),
                is_featured=random.choice([True, False, False, False, False]),
                brand_id=brands[laptop_data['brand']],
                model_id=models[laptop_data['model']],
                processor_id=processors.get(laptop_data['processor']),
                ram_id=ram.get(laptop_data['ram']),
                storage_id=storage.get(laptop_data['storage']),
                graphics_card_id=gpus.get(laptop_data['gpu']),
                screen_id=screens.get(laptop_data['screen']),
                os_id=os_list.get(laptop_data['os']),
                store_id=random.choice(stores).id,
                location_id=random.choice(locations).id,
                supplier_id=random.choice(suppliers).id,
                category=laptop_data['category'],
                condition=random.choice(conditions),
                keyboard_layout=random.choice(keyboard_layouts),
                connectivity_ports=random.choice(connectivity_options),
                npu=random.choice([True, False, False, False]),
                storage_upgradeable=random.choice([True, True, False]),
                ram_upgradeable=random.choice([True, True, False]),
                purchase_cost=laptop_data['cost'],
                sale_price=laptop_data['price'],
                discount_price=laptop_data['price'] * 0.9 if random.random() < 0.2 else None,
                tax_percent=18.00,
                quantity=random.randint(1, 8),
                reserved_quantity=0,
                min_alert=2,
                entry_date=date.today() - timedelta(days=random.randint(1, 90)),
                created_by_id=admin_id,
            )

            db.session.add(laptop)

        db.session.commit()
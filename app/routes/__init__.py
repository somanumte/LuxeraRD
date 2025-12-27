from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.routes.inventory import inventory_bp
from app.routes.api.catalog_api import catalog_api_bp

__all__ = [
    'auth_bp',
    'main_bp',
    'inventory_bp',
    'catalog_api_bp'
]
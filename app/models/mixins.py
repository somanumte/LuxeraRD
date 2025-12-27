# ============================================
# MIXINS - Funcionalidad Reutilizable
# ============================================
# Estos mixins se pueden usar en cualquier modelo

from datetime import datetime
from app import db


class TimestampMixin:
    """
    Agrega campos de timestamp a cualquier modelo
    Uso: class MyModel(TimestampMixin, db.Model)
    """
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SoftDeleteMixin:
    """
    Permite "borrado suave" (soft delete)
    Los registros no se eliminan, solo se marcan como eliminados
    """
    deleted_at = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)

    def soft_delete(self):
        """Marca el registro como eliminado"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def restore(self):
        """Restaura un registro eliminado"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """
    Auditoría: quién creó y quién modificó
    """
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Nota: Las relaciones se deben definir en el modelo específico
    # para evitar conflictos con foreign_keys


class CatalogMixin(TimestampMixin):
    """
    Mixin para todos los modelos de catálogo
    Incluye: name, timestamps, métodos comunes
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    @classmethod
    def get_active(cls):
        """Obtiene todos los registros activos"""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()

    @classmethod
    def get_or_create(cls, name):
        """
        Obtiene un registro por nombre, o lo crea si no existe
        Perfecto para los dropdowns con "crear nuevo"
        """
        instance = cls.query.filter_by(name=name).first()
        if instance:
            return instance, False
        else:
            instance = cls(name=name)
            db.session.add(instance)
            db.session.commit()
            return instance, True

    def to_dict(self):
        """Serializa a diccionario (para JSON)"""
        return {
            'id': self.id,
            'name': self.name,
            'is_active': self.is_active
        }

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}>'
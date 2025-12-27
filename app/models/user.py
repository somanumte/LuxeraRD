# ============================================
# MODELO DE USUARIO
# ============================================
# Define la estructura de la tabla 'user' en PostgreSQL
# Maneja toda la lógica relacionada con usuarios

from datetime import datetime
from flask_login import UserMixin
from app import db, bcrypt


# ============================================
# CLASE USER - MODELO DE USUARIO
# ============================================

class User(UserMixin, db.Model):
    """
    Modelo de Usuario para el sistema de autenticación

    Hereda de:
    - UserMixin: Proporciona implementaciones por defecto para Flask-Login
      (is_authenticated, is_active, is_anonymous, get_id)
    - db.Model: Clase base de SQLAlchemy para modelos

    Tabla en PostgreSQL: 'user'
    """

    # ===== CONFIGURACIÓN DE LA TABLA =====
    __tablename__ = 'user'
    # Nombre explícito de la tabla en la base de datos
    # Sin esto, SQLAlchemy usaría 'user' de todas formas (nombre de la clase en minúsculas)

    # ===== COLUMNAS DE LA TABLA =====

    # ID - Clave primaria
    id = db.Column(db.Integer, primary_key=True)
    # primary_key=True: Esta es la clave única que identifica cada usuario
    # db.Integer: Tipo de dato entero (1, 2, 3, 4...)
    # PostgreSQL lo convierte en SERIAL (auto-incremento)

    # Username - Nombre de usuario único
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # db.String(80): Texto con máximo 80 caracteres
    # unique=True: No puede haber dos usuarios con el mismo username
    # nullable=False: Este campo es obligatorio (no puede estar vacío)
    # index=True: Crea un índice en PostgreSQL para búsquedas rápidas

    # Email - Correo electrónico único
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # db.String(120): Texto con máximo 120 caracteres
    # unique=True: No puede haber dos usuarios con el mismo email
    # nullable=False: Este campo es obligatorio
    # index=True: Índice para búsquedas rápidas por email

    # Password Hash - Contraseña encriptada
    password_hash = db.Column(db.String(200), nullable=False)
    # db.String(200): Bcrypt genera hashes de ~60 caracteres, 200 da margen
    # nullable=False: Todo usuario DEBE tener contraseña
    # NUNCA guardamos la contraseña en texto plano

    # Nombre completo (opcional)
    full_name = db.Column(db.String(150), nullable=True)
    # nullable=True: Este campo es opcional
    # Útil para mostrar "Bienvenido, Juan Pérez" en lugar de "Bienvenido, juanp123"

    # Estado activo
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # db.Boolean: Verdadero o Falso
    # default=True: Por defecto, los usuarios están activos
    # Útil para "desactivar" usuarios sin eliminarlos
    # Si is_active=False, el usuario no puede hacer login

    # Es administrador
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    # default=False: Por defecto, los usuarios NO son admin
    # Útil para dar permisos especiales

    # Fecha de creación
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # db.DateTime: Fecha y hora
    # default=datetime.utcnow: Automáticamente guarda la fecha/hora de creación
    # utcnow (sin paréntesis) pasa la función, no la ejecuta
    # nullable=False: Siempre debe tener fecha de creación

    # Última actualización
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    # default=datetime.utcnow: Fecha/hora de creación
    # onupdate=datetime.utcnow: Se actualiza automáticamente cada vez que modificas el usuario

    # Último login
    last_login = db.Column(db.DateTime, nullable=True)
    # nullable=True: Puede ser None (cuando el usuario nunca ha hecho login)
    # Lo actualizamos manualmente cuando el usuario hace login

    # Intentos de login fallidos
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    # Contador de intentos fallidos
    # Útil para bloquear usuarios después de X intentos
    # default=0: Empieza en cero

    # Fecha de bloqueo por intentos fallidos
    locked_until = db.Column(db.DateTime, nullable=True)

    # Si el usuario falla muchos logins, bloqueamos temporalmente
    # nullable=True: Solo tiene valor si está bloqueado

    # ===== MÉTODOS DE LA CLASE =====

    def __repr__(self):
        """
        Representación del objeto User

        ¿Para qué sirve?
        - Cuando imprimes un usuario: print(user)
        - En el debugger de PyCharm
        - En logs

        Returns:
            str: Representación legible del usuario
        """
        return f'<User {self.username}>'
        # Ejemplo: <User felix>

    def set_password(self, password):
        """
        Encripta y guarda la contraseña

        ¿Cómo funciona bcrypt?
        1. Toma la contraseña en texto plano
        2. Genera un "salt" aleatorio (sal)
        3. Combina password + salt
        4. Aplica hashing múltiples veces
        5. Resultado: Hash imposible de revertir

        Args:
            password (str): Contraseña en texto plano

        Ejemplo:
            user = User(username='felix')
            user.set_password('miPassword123')
            # user.password_hash = '$2b$12$KIXz...' (60 caracteres)
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        # generate_password_hash() retorna bytes
        # .decode('utf-8') convierte a string para guardar en la DB

    def check_password(self, password):
        """
        Verifica si una contraseña es correcta

        ¿Cómo funciona?
        1. Usuario ingresa contraseña en el login
        2. Tomamos el hash guardado en la DB
        3. bcrypt extrae el salt del hash
        4. Aplica el mismo proceso a la contraseña ingresada
        5. Compara ambos hashes

        Args:
            password (str): Contraseña a verificar

        Returns:
            bool: True si la contraseña es correcta, False si no

        Ejemplo:
            if user.check_password('miPassword123'):
                login_user(user)  # Correcto
            else:
                flash('Contraseña incorrecta')  # Incorrecto
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    def increment_failed_login(self):
        """
        Incrementa el contador de intentos fallidos

        ¿Cuándo usar?
        - Cada vez que el usuario falla el login

        ¿Para qué?
        - Prevenir ataques de fuerza bruta
        - Bloquear temporalmente después de X intentos
        """
        self.failed_login_attempts += 1

        # Si supera el máximo de intentos, bloquear temporalmente
        from datetime import timedelta
        from config import Config

        max_attempts = Config.MAX_LOGIN_ATTEMPTS  # 5 intentos
        lockout_time = Config.LOGIN_LOCKOUT_TIME  # 15 minutos

        if self.failed_login_attempts >= max_attempts:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lockout_time)

        db.session.commit()

    def reset_failed_login(self):
        """
        Reinicia el contador de intentos fallidos

        ¿Cuándo usar?
        - Después de un login exitoso
        - Cuando el admin desbloquea al usuario
        """
        self.failed_login_attempts = 0
        self.locked_until = None
        db.session.commit()

    def is_locked(self):
        """
        Verifica si el usuario está bloqueado temporalmente

        Returns:
            bool: True si está bloqueado, False si puede hacer login

        Ejemplo:
            if user.is_locked():
                flash('Cuenta bloqueada temporalmente')
                return redirect(url_for('auth.login'))
        """
        if self.locked_until is None:
            return False

        # Si la fecha de bloqueo ya pasó, desbloquear
        if datetime.utcnow() > self.locked_until:
            self.reset_failed_login()
            return False

        return True

    def update_last_login(self):
        """
        Actualiza la fecha del último login

        ¿Cuándo usar?
        - Inmediatamente después de un login exitoso
        """
        self.last_login = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """
        Convierte el usuario a un diccionario

        ¿Para qué sirve?
        - APIs REST (retornar JSON)
        - Logging
        - Debugging

        Returns:
            dict: Diccionario con información del usuario (sin contraseña)

        Ejemplo:
            user_data = user.to_dict()
            return jsonify(user_data)
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        # NUNCA incluir password_hash en el diccionario (seguridad)

    @staticmethod
    def create_user(username, email, password, full_name=None, is_admin=False):
        """
        Método estático para crear un usuario completo

        ¿Qué es un método estático?
        - No requiere una instancia de la clase
        - Se llama directamente: User.create_user(...)

        Args:
            username (str): Nombre de usuario
            email (str): Email
            password (str): Contraseña en texto plano
            full_name (str, optional): Nombre completo
            is_admin (bool, optional): Si es administrador

        Returns:
            User: Usuario creado y guardado en la DB

        Raises:
            ValueError: Si el username o email ya existen

        Ejemplo:
            try:
                new_user = User.create_user(
                    username='felix',
                    email='felix@luxera.com',
                    password='miPassword123',
                    full_name='Felix Rodriguez'
                )
                flash('Usuario creado exitosamente')
            except ValueError as e:
                flash(str(e))
        """
        # Verificar si el username ya existe
        if User.query.filter_by(username=username).first():
            raise ValueError(f'El username "{username}" ya está en uso')

        # Verificar si el email ya existe
        if User.query.filter_by(email=email).first():
            raise ValueError(f'El email "{email}" ya está registrado')

        # Crear el usuario
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_admin=is_admin
        )

        # Establecer contraseña (se encripta automáticamente)
        user.set_password(password)

        # Guardar en la base de datos
        db.session.add(user)
        db.session.commit()

        return user


# ============================================
# EVENTOS DE SQLAlchemy
# ============================================
# Funciones que se ejecutan automáticamente antes/después de operaciones

from sqlalchemy import event


@event.listens_for(User, 'before_update')
def receive_before_update(mapper, connection, target):
    """
    Se ejecuta automáticamente ANTES de actualizar un usuario

    ¿Para qué sirve?
    - Actualizar updated_at automáticamente
    - Validaciones adicionales
    - Logging de cambios

    Args:
        mapper: Metadata de SQLAlchemy
        connection: Conexión a la DB
        target: El objeto User que se está actualizando
    """
    target.updated_at = datetime.utcnow()
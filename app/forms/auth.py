# ============================================
# FORMULARIOS DE AUTENTICACIÓN
# ============================================
# Define los formularios de Login y Registro con validaciones

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    ValidationError,
    Regexp
)
from app.models.user import User


# ============================================
# FORMULARIO DE LOGIN
# ============================================

class LoginForm(FlaskForm):
    """
    Formulario para iniciar sesión

    Campos:
    - Email
    - Contraseña
    - Recordarme (checkbox)
    - Botón de submit
    """

    # ===== CAMPO DE EMAIL =====
    email = StringField(
        'Email',
        # StringField = Campo de texto simple
        # 'Email' = Label que se muestra al usuario

        validators=[
            DataRequired(message='El email es requerido'),
            # DataRequired: El campo NO puede estar vacío
            # message: Mensaje personalizado si falla la validación

            Email(message='Ingresa un email válido')
            # Email: Valida que tenga formato de email (algo@algo.com)
            # Rechaza: "usuario", "usuario@", "usuario@com"
            # Acepta: "usuario@email.com", "felix@luxera.do"
        ],

        render_kw={
            'placeholder': 'tu@email.com',
            'class': 'form-input',
            'autocomplete': 'email'
        }
        # render_kw: Atributos HTML adicionales
        # placeholder: Texto de ejemplo dentro del campo
        # class: Clase CSS para estilizar con Tailwind
        # autocomplete: Le dice al navegador que puede autocompletar
    )

    # ===== CAMPO DE CONTRASEÑA =====
    password = PasswordField(
        'Contraseña',
        # PasswordField = Campo de contraseña (oculta los caracteres)

        validators=[
            DataRequired(message='La contraseña es requerida')
        ],

        render_kw={
            'placeholder': '••••••••',
            'class': 'form-input',
            'autocomplete': 'current-password'
        }
        # current-password: Le dice al navegador que es una contraseña existente
    )

    # ===== CHECKBOX "RECORDARME" =====
    remember_me = BooleanField(
        'Recordarme',
        # BooleanField = Checkbox (True/False)
        # Si está marcado: True
        # Si no está marcado: False

        default=False
        # Por defecto no está marcado
    )

    # ===== BOTÓN DE SUBMIT =====
    submit = SubmitField('Iniciar Sesión')

    # SubmitField = Botón de envío
    # 'Iniciar Sesión' = Texto del botón

    # ===== VALIDACIÓN PERSONALIZADA DE EMAIL =====
    def validate_email(self, field):
        """
        Validación personalizada que se ejecuta automáticamente

        ¿Cuándo se ejecuta?
        - Cuando el usuario envía el formulario
        - Después de las validaciones básicas (DataRequired, Email)

        ¿Para qué sirve?
        - Verificar si el email existe en la base de datos
        - Verificar si el usuario está activo

        Args:
            field: El campo email del formulario

        Raises:
            ValidationError: Si el email no existe o el usuario está inactivo

        Nota:
        Flask-WTF busca automáticamente métodos llamados validate_<campo>
        Por eso se llama validate_email (para el campo email)
        """
        # Buscar usuario por email
        user = User.query.filter_by(email=field.data).first()

        # Si no existe el usuario, mostrar error
        if not user:
            raise ValidationError('Email no registrado')

        # Si el usuario está inactivo, mostrar error
        if not user.is_active:
            raise ValidationError('Esta cuenta ha sido desactivada')

        # Si el usuario está bloqueado temporalmente
        if user.is_locked():
            raise ValidationError(
                f'Cuenta bloqueada temporalmente. '
                f'Intenta de nuevo más tarde.'
            )


# ============================================
# FORMULARIO DE REGISTRO
# ============================================

class RegisterForm(FlaskForm):
    """
    Formulario para registrar un nuevo usuario

    Campos:
    - Username
    - Email
    - Nombre completo (opcional)
    - Contraseña
    - Confirmar contraseña
    - Botón de submit

    Nota:
    Este formulario solo se muestra si ALLOW_REGISTRATION=True en config.py
    """

    # ===== CAMPO DE USERNAME =====
    username = StringField(
        'Nombre de usuario',

        validators=[
            DataRequired(message='El nombre de usuario es requerido'),

            Length(
                min=4,
                max=20,
                message='El username debe tener entre 4 y 20 caracteres'
            ),
            # Length: Valida la longitud del texto
            # min=4: Mínimo 4 caracteres
            # max=20: Máximo 20 caracteres

            Regexp(
                r'^[a-zA-Z0-9_]+$',
                message='Solo letras, números y guión bajo (_)'
            )
            # Regexp: Validación con expresiones regulares
            # r'^[a-zA-Z0-9_]+$' significa:
            # ^ = inicio del texto
            # [a-zA-Z0-9_]+ = uno o más caracteres de: letras, números, _
            # $ = fin del texto
            # Acepta: "felix", "user_123", "JohnDoe"
            # Rechaza: "user name" (espacios), "user@123" (caracteres especiales)
        ],

        render_kw={
            'placeholder': 'usuario123',
            'class': 'form-input',
            'autocomplete': 'username'
        }
    )

    # ===== CAMPO DE EMAIL =====
    email = StringField(
        'Email',

        validators=[
            DataRequired(message='El email es requerido'),
            Email(message='Ingresa un email válido'),
            Length(max=120, message='El email es demasiado largo')
        ],

        render_kw={
            'placeholder': 'tu@email.com',
            'class': 'form-input',
            'autocomplete': 'email'
        }
    )

    # ===== CAMPO DE NOMBRE COMPLETO (OPCIONAL) =====
    full_name = StringField(
        'Nombre completo',

        validators=[
            Length(max=150, message='El nombre es demasiado largo')
        ],
        # Sin DataRequired: Este campo es OPCIONAL

        render_kw={
            'placeholder': 'Juan Pérez (opcional)',
            'class': 'form-input',
            'autocomplete': 'name'
        }
    )

    # ===== CAMPO DE CONTRASEÑA =====
    password = PasswordField(
        'Contraseña',

        validators=[
            DataRequired(message='La contraseña es requerida'),

            Length(
                min=6,
                max=50,
                message='La contraseña debe tener entre 6 y 50 caracteres'
            ),

            Regexp(
                r'^(?=.*[A-Za-z])(?=.*\d)',
                message='La contraseña debe contener al menos una letra y un número'
            )
            # Esta regex valida:
            # (?=.*[A-Za-z]) = al menos una letra
            # (?=.*\d) = al menos un número
            # Acepta: "password123", "abc123def", "MiClave2024"
            # Rechaza: "password" (sin números), "123456" (sin letras)
        ],

        render_kw={
            'placeholder': 'Mínimo 6 caracteres',
            'class': 'form-input',
            'autocomplete': 'new-password'
        }
        # new-password: Le dice al navegador que es una contraseña nueva
    )

    # ===== CAMPO DE CONFIRMAR CONTRASEÑA =====
    confirm_password = PasswordField(
        'Confirmar contraseña',

        validators=[
            DataRequired(message='Confirma tu contraseña'),

            EqualTo('password', message='Las contraseñas no coinciden')
            # EqualTo: Valida que este campo sea igual a otro
            # 'password': Nombre del campo con el que debe coincidir
            # Si password="abc123" y confirm_password="abc124" → Error
            # Si ambos son "abc123" → OK
        ],

        render_kw={
            'placeholder': 'Repite tu contraseña',
            'class': 'form-input',
            'autocomplete': 'new-password'
        }
    )

    # ===== BOTÓN DE SUBMIT =====
    submit = SubmitField('Registrarse')

    # ===== VALIDACIONES PERSONALIZADAS =====

    def validate_username(self, field):
        """
        Valida que el username no exista ya en la base de datos

        ¿Cuándo se ejecuta?
        - Automáticamente cuando el usuario envía el formulario
        - Después de las validaciones básicas

        Args:
            field: El campo username del formulario

        Raises:
            ValidationError: Si el username ya está en uso
        """
        # Buscar si ya existe un usuario con ese username
        user = User.query.filter_by(username=field.data).first()

        if user:
            raise ValidationError(
                'Este nombre de usuario ya está en uso. '
                'Por favor elige otro.'
            )

    def validate_email(self, field):
        """
        Valida que el email no exista ya en la base de datos

        Args:
            field: El campo email del formulario

        Raises:
            ValidationError: Si el email ya está registrado
        """
        # Buscar si ya existe un usuario con ese email
        user = User.query.filter_by(email=field.data).first()

        if user:
            raise ValidationError(
                'Este email ya está registrado. '
                'Usa otro email o intenta iniciar sesión.'
            )

    def validate_password(self, field):
        """
        Validación adicional de seguridad de contraseña

        Verifica que la contraseña no sea demasiado común o débil

        Args:
            field: El campo password del formulario

        Raises:
            ValidationError: Si la contraseña es demasiado débil
        """
        # Lista de contraseñas comunes que están prohibidas
        common_passwords = [
            'password', '123456', '12345678', 'qwerty', 'abc123',
            'password123', '111111', '123123', 'admin', 'letmein'
        ]

        # Si la contraseña está en la lista de prohibidas
        if field.data.lower() in common_passwords:
            raise ValidationError(
                'Esta contraseña es demasiado común. '
                'Por favor elige una más segura.'
            )

        # Verificar que no sea solo números
        if field.data.isdigit():
            raise ValidationError(
                'La contraseña no puede ser solo números. '
                'Debe incluir letras.'
            )

        # Verificar que no sea solo letras
        if field.data.isalpha():
            raise ValidationError(
                'La contraseña no puede ser solo letras. '
                'Debe incluir números.'
            )
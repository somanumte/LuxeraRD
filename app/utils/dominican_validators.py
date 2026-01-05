# ============================================
# VALIDADORES PARA REPÚBLICA DOMINICANA
# ============================================
# Validadores de Cédula y RNC dominicanos

from wtforms.validators import ValidationError
import re


class CedulaValidator:
    """
    Valida formato de cédulas de identidad dominicanas
    Formato: XXX-XXXXXXX-X (11 dígitos)
    Solo valida formato, no el dígito verificador
    """

    def __init__(self, message=None):
        if not message:
            message = 'Formato de cédula inválido. Debe tener 11 dígitos: XXX-XXXXXXX-X'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        # Limpiar cédula (quitar guiones y espacios)
        cedula = re.sub(r'[-\s]', '', str(field.data))

        # Debe tener exactamente 11 dígitos
        if not cedula.isdigit() or len(cedula) != 11:
            raise ValidationError(self.message)


class RNCValidator:
    """
    Valida formato de RNC (Registro Nacional de Contribuyentes) dominicano
    Puede ser de 9 u 11 dígitos
    Solo valida formato, no el dígito verificador
    """

    def __init__(self, message=None):
        if not message:
            message = 'Formato de RNC inválido. Debe tener 9 u 11 dígitos'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        # Limpiar RNC (quitar guiones y espacios)
        rnc = re.sub(r'[-\s]', '', str(field.data))

        # Debe tener 9 u 11 dígitos
        if not rnc.isdigit() or len(rnc) not in [9, 11]:
            raise ValidationError(self.message)


class DominicanIDValidator:
    """
    Validador genérico que acepta tanto cédula como RNC
    Solo valida formato básico
    """

    def __init__(self, message=None):
        if not message:
            message = 'Identificación inválida'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        # Limpiar
        id_number = re.sub(r'[-\s]', '', str(field.data))

        if not id_number.isdigit():
            raise ValidationError('La identificación debe contener solo números')

        length = len(id_number)

        # Validar según longitud
        if length not in [9, 11]:
            raise ValidationError('La identificación debe tener 9 (RNC) u 11 (Cédula/RNC) dígitos')


class DominicanPhoneValidator:
    """
    Valida números telefónicos dominicanos
    Formatos aceptados:
    - (809) 555-5555
    - 809-555-5555
    - 8095555555
    - 555-5555 (sin código de área)
    """

    def __init__(self, message=None):
        if not message:
            message = 'Número telefónico inválido'
        self.message = message

        # Códigos de área válidos en RD: 809, 829, 849
        self.valid_area_codes = ['809', '829', '849']

    def __call__(self, form, field):
        if not field.data:
            return

        # Limpiar número (quitar caracteres no numéricos)
        phone = re.sub(r'[^\d]', '', str(field.data))

        # Debe tener 7 dígitos (local) o 10 dígitos (con área)
        if len(phone) == 7:
            # Número local válido
            return
        elif len(phone) == 10:
            # Verificar código de área
            area_code = phone[:3]
            if area_code not in self.valid_area_codes:
                raise ValidationError(f'Código de área inválido. Use: {", ".join(self.valid_area_codes)}')
        else:
            raise ValidationError('El número debe tener 7 o 10 dígitos')
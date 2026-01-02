# ============================================
# VALIDADORES PARA REPÚBLICA DOMINICANA
# ============================================
# Validadores de Cédula y RNC dominicanos

from wtforms.validators import ValidationError
import re


class CedulaValidator:
    """
    Valida cédulas de identidad dominicanas
    Formato: XXX-XXXXXXX-X (11 dígitos)
    """

    def __init__(self, message=None):
        if not message:
            message = 'Cédula inválida. Formato: XXX-XXXXXXX-X (11 dígitos)'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        # Limpiar cédula (quitar guiones y espacios)
        cedula = re.sub(r'[-\s]', '', str(field.data))

        # Debe tener exactamente 11 dígitos
        if not cedula.isdigit() or len(cedula) != 11:
            raise ValidationError(self.message)

        # Validación del dígito verificador (algoritmo de Luhn modificado)
        if not self._validate_cedula_checksum(cedula):
            raise ValidationError('Cédula inválida: dígito verificador incorrecto')

    def _validate_cedula_checksum(self, cedula):
        """
        Valida el dígito verificador de la cédula dominicana
        Usa el algoritmo de módulo 10
        """
        # Los primeros 10 dígitos
        digits = cedula[:10]
        check_digit = int(cedula[10])

        # Multiplicadores alternados: 1, 2, 1, 2, ...
        total = 0
        for i, digit in enumerate(digits):
            n = int(digit)
            if i % 2 == 1:  # Posiciones impares (1, 3, 5, 7, 9)
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        # El dígito verificador debe hacer que el total sea múltiplo de 10
        calculated_check = (10 - (total % 10)) % 10

        return calculated_check == check_digit


class RNCValidator:
    """
    Valida RNC (Registro Nacional de Contribuyentes) dominicano
    Puede ser de 9 u 11 dígitos
    """

    def __init__(self, message=None):
        if not message:
            message = 'RNC inválido. Debe tener 9 u 11 dígitos'
        self.message = message

    def __call__(self, form, field):
        if not field.data:
            return

        # Limpiar RNC (quitar guiones y espacios)
        rnc = re.sub(r'[-\s]', '', str(field.data))

        # Debe tener 9 u 11 dígitos
        if not rnc.isdigit() or len(rnc) not in [9, 11]:
            raise ValidationError(self.message)

        # RNC de 11 dígitos usa el mismo algoritmo que la cédula
        if len(rnc) == 11:
            cedula_validator = CedulaValidator(message='RNC inválido: dígito verificador incorrecto')
            try:
                cedula_validator._validate_cedula_checksum(rnc)
            except:
                raise ValidationError('RNC inválido: dígito verificador incorrecto')


class DominicanIDValidator:
    """
    Validador genérico que acepta tanto cédula como RNC
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
        if length == 11:
            # Puede ser cédula o RNC
            cedula_validator = CedulaValidator()
            try:
                cedula_validator._validate_cedula_checksum(id_number)
            except:
                raise ValidationError('Identificación inválida: dígito verificador incorrecto')
        elif length == 9:
            # Es RNC de 9 dígitos (no tiene validación de checksum)
            pass
        else:
            raise ValidationError('La identificación debe tener 9 u 11 dígitos')


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
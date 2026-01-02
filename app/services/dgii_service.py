# ============================================
# SERVICIO DE CONSULTA A LA DGII OFICIAL
# ============================================
# Ubicación: app/services/dgii_service.py

import requests
from bs4 import BeautifulSoup
import logging
import re
from typing import Dict

logger = logging.getLogger(__name__)


class DGIIService:
    """
    Servicio para consultar información de RNC/Cédula en la DGII oficial
    """

    DGII_URL = "https://dgii.gov.do/herramientas/consultas/Paginas/RNC.aspx"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'es-ES,es;q=0.9',
    }

    @classmethod
    def validate_and_get_info(cls, id_number: str, id_type: str = 'cedula') -> Dict:
        """Valida y obtiene información desde DGII oficial"""
        try:
            clean_id = id_number.replace('-', '').replace(' ', '').strip()

            logger.info(f"Consultando DGII: {id_type} {clean_id}")

            # Validar formato
            if id_type == 'cedula':
                if not re.match(r'^\d{11}$', clean_id):
                    return {'success': False, 'error': 'Cédula debe tener 11 dígitos'}
            else:
                if not re.match(r'^(\d{9}|\d{11})$', clean_id):
                    return {'success': False, 'error': 'RNC debe tener 9 u 11 dígitos'}

            # Consultar DGII
            result = cls._scrape_dgii(clean_id, id_type)
            return result

        except Exception as e:
            logger.error(f"Error: {str(e)}", exc_info=True)
            return {'success': False, 'error': 'Error al consultar DGII'}

    @classmethod
    def _scrape_dgii(cls, id_number: str, id_type: str) -> Dict:
        """Hace scraping de DGII con múltiples intentos"""
        try:
            session = requests.Session()
            session.headers.update(cls.HEADERS)

            logger.info(f"🌐 Consultando DGII para {id_type}: {id_number}")

            # Paso 1: Obtener página inicial
            response = session.get(cls.DGII_URL, timeout=15)

            if response.status_code != 200:
                logger.warning(f"⚠️ Status code {response.status_code}")
                return cls._local_validation(id_number, id_type)

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extraer campos hidden de ASP.NET
            form_data = {}
            for hidden_field in soup.find_all('input', {'type': 'hidden'}):
                name = hidden_field.get('name')
                value = hidden_field.get('value', '')
                if name:
                    form_data[name] = value

            # Formatear ID
            formatted_id = cls._format_id(id_number, id_type)

            # Buscar campo de búsqueda
            possible_fields = [
                'ctl00$cphMain$txtRNCCedula',
                'txtRNCCedula',
                'txtRNC',
                'txtCedula'
            ]

            search_field = None
            for field_name in possible_fields:
                if soup.find('input', {'name': field_name}):
                    search_field = field_name
                    break

            if not search_field:
                text_inputs = soup.find_all('input', {'type': 'text'})
                if text_inputs:
                    search_field = text_inputs[0].get('name')

            if not search_field:
                return cls._local_validation(id_number, id_type)

            # Buscar botón
            possible_buttons = [
                'ctl00$cphMain$btnBuscarPorRNC',
                'btnBuscarPorRNC',
                'btnBuscar'
            ]

            search_button = None
            for button_name in possible_buttons:
                if soup.find('input', {'name': button_name}):
                    search_button = button_name
                    break

            # Agregar datos de búsqueda
            form_data[search_field] = formatted_id
            if search_button:
                form_data[search_button] = 'Buscar'

            # Enviar formulario
            response = session.post(cls.DGII_URL, data=form_data, timeout=15)

            if response.status_code != 200:
                return cls._local_validation(id_number, id_type)

            # Parsear resultados
            soup = BeautifulSoup(response.text, 'html.parser')
            result = cls._parse_results(soup, id_number, id_type)

            return result or cls._local_validation(id_number, id_type)

        except requests.Timeout:
            logger.warning("⏱️ Timeout")
            return cls._local_validation(id_number, id_type)
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            return cls._local_validation(id_number, id_type)

    @classmethod
    def _parse_results(cls, soup: BeautifulSoup, id_number: str, id_type: str) -> Dict:
        """Parsea resultados de DGII"""
        try:
            nombre = None
            estado = None

            # Buscar en tablas
            for row in soup.find_all('tr'):
                cells = row.find_all('td')

                if len(cells) >= 2:
                    label = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()

                    if 'nombre' in label or 'razón' in label:
                        if value and value not in ['', '-', 'N/A']:
                            nombre = value

                    if 'estado' in label:
                        if value and value not in ['', '-', 'N/A']:
                            estado = value

            # Buscar en spans
            if not nombre:
                nombre_elements = soup.find_all('span',
                                                {'id': lambda x: x and ('nombre' in x.lower() or 'razon' in x.lower())})
                for elem in nombre_elements:
                    text = elem.get_text().strip()
                    if text and text not in ['', '-', 'N/A']:
                        nombre = text
                        break

            if not estado:
                estado = 'ACTIVO'

            if nombre:
                if id_type == 'cedula':
                    parts = nombre.split()
                    mid = len(parts) // 2
                    first_name = ' '.join(parts[:mid]) if parts else ''
                    last_name = ' '.join(parts[mid:]) if len(parts) > 1 else ''

                    return {
                        'success': True,
                        'id_number': id_number,
                        'id_type': 'cedula',
                        'first_name': first_name,
                        'last_name': last_name,
                        'full_name': nombre,
                        'status': estado,
                        'validation_mode': 'dgii'
                    }
                else:
                    return {
                        'success': True,
                        'id_number': id_number,
                        'id_type': 'rnc',
                        'company_name': nombre,
                        'status': estado,
                        'validation_mode': 'dgii'
                    }

            return {
                'success': False,
                'error': 'No encontrado en DGII'
            }

        except Exception as e:
            logger.error(f"❌ Error parsing: {str(e)}")
            return {
                'success': False,
                'error': 'Error procesando respuesta'
            }

    @classmethod
    def _format_id(cls, id_number: str, id_type: str) -> str:
        """Formatea ID para consulta"""
        if id_type == 'cedula' and len(id_number) == 11:
            return f"{id_number[:3]}-{id_number[3:10]}-{id_number[10]}"
        elif id_type == 'rnc':
            if len(id_number) == 9:
                return f"{id_number[:1]}-{id_number[1:3]}-{id_number[3:8]}-{id_number[8]}"
            elif len(id_number) == 11:
                return f"{id_number[:3]}-{id_number[3:10]}-{id_number[10]}"
        return id_number

    @classmethod
    def _local_validation(cls, id_number: str, id_type: str) -> Dict:
        """Validación local como fallback"""
        return {
            'success': True,
            'id_number': id_number,
            'id_type': id_type,
            'first_name': '' if id_type == 'cedula' else None,
            'last_name': '' if id_type == 'cedula' else None,
            'company_name': '' if id_type == 'rnc' else None,
            'validation_mode': 'local',
            'message': 'Formato válido - Complete datos manualmente'
        }
# ============================================
# IMAGE BACKGROUND SERVICE - Eliminación automática de fondo
# ============================================
# Responsabilidad: Procesamiento de imágenes con IA para remover fondos
# Dependencias: rembg, Pillow

import os
import logging
from datetime import datetime
from pathlib import Path
from PIL import Image
import tempfile

# Configurar logging
logger = logging.getLogger(__name__)

# Intento de importar rembg (dependencia opcional)
try:
    from rembg import remove

    REMBG_AVAILABLE = True
    logger.info("✅ rembg disponible para eliminación de fondos")
except ImportError:
    REMBG_AVAILABLE = False
    logger.warning("⚠️  rembg no está instalado. La eliminación de fondos no estará disponible.")


class ImageBackgroundService:
    """
    Servicio para procesamiento automático de eliminación de fondos en imágenes
    Usa la librería rembg con modelo U^2-Net
    """

    # Configuraciones
    MAX_IMAGE_SIZE_MB = 10  # Rechazar imágenes > 10MB
    PROCESSING_TIMEOUT = 30  # Segundos máximos de procesamiento
    SUPPORTED_INPUT_FORMATS = {'jpg', 'jpeg', 'png', 'webp', 'bmp'}
    OUTPUT_FORMAT = 'PNG'  # Siempre PNG para transparencia

    @classmethod
    def is_available(cls):
        """
        Verifica si el servicio está disponible (rembg instalado)

        Returns:
            bool: True si rembg está disponible
        """
        return REMBG_AVAILABLE

    @classmethod
    def remove_background(cls, image_path, backup_original=True):
        """
        Elimina el fondo de una imagen usando IA

        Args:
            image_path (str): Ruta absoluta al archivo de imagen
            backup_original (bool): Si True, crea backup de la original

        Returns:
            tuple: (success, processed_path, backup_path, error_message)
        """
        # Verificar disponibilidad
        if not cls.is_available():
            return False, None, None, "rembg no está instalado"

        # Validar ruta
        if not os.path.exists(image_path):
            return False, None, None, f"Archivo no encontrado: {image_path}"

        # Validar tamaño
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if file_size_mb > cls.MAX_IMAGE_SIZE_MB:
            return False, None, None, f"Imagen muy grande ({file_size_mb:.1f}MB). Máximo: {cls.MAX_IMAGE_SIZE_MB}MB"

        # Validar formato
        file_ext = Path(image_path).suffix.lower()[1:]  # Sin el punto
        if file_ext not in cls.SUPPORTED_INPUT_FORMATS:
            return False, None, None, f"Formato no soportado: .{file_ext}"

        try:
            logger.info(f"🎨 Procesando eliminación de fondo: {image_path}")
            start_time = datetime.now()

            # 1. Crear backup de la imagen original si se solicita
            backup_path = None
            if backup_original:
                backup_path = cls._create_backup(image_path)
                logger.info(f"💾 Backup creado: {backup_path}")

            # 2. Leer imagen
            with open(image_path, 'rb') as input_file:
                input_image = input_file.read()

            # 3. Procesar con rembg
            logger.info("🔄 Eliminando fondo con IA...")
            output_image = remove(input_image)

            # 4. Guardar imagen procesada (sobrescribir original)
            processed_path = image_path
            with open(processed_path, 'wb') as output_file:
                output_file.write(output_image)

            # 5. Convertir a PNG si no lo es ya
            if not processed_path.lower().endswith('.png'):
                png_path = cls._convert_to_png(processed_path)
                if png_path:
                    # Reemplazar archivo original con PNG
                    os.remove(processed_path)
                    processed_path = png_path
                    logger.info(f"🔄 Convertido a PNG: {processed_path}")

            # 6. Validar que la imagen procesada es válida
            if not cls._validate_image(processed_path):
                # Restaurar desde backup si existe
                if backup_path and os.path.exists(backup_path):
                    cls._restore_from_backup(backup_path, image_path)
                    return False, None, backup_path, "Imagen procesada inválida - Restaurado desde backup"
                return False, None, backup_path, "Imagen procesada inválida"

            # 7. Registrar éxito
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Fondo eliminado exitosamente en {processing_time:.2f}s: {processed_path}")

            return True, processed_path, backup_path, None

        except Exception as e:
            logger.error(f"❌ Error al eliminar fondo: {str(e)}", exc_info=True)

            # Intentar restaurar desde backup si existe
            if backup_path and os.path.exists(backup_path):
                try:
                    cls._restore_from_backup(backup_path, image_path)
                    logger.info(f"🔄 Restaurado desde backup: {backup_path}")
                except Exception as restore_error:
                    logger.error(f"❌ Error al restaurar desde backup: {str(restore_error)}")

            return False, None, backup_path, f"Error de procesamiento: {str(e)}"

    @classmethod
    def batch_remove_background(cls, image_paths, backup_original=True):
        """
        Elimina fondo de múltiples imágenes

        Args:
            image_paths (list): Lista de rutas a imágenes
            backup_original (bool): Crear backups de originales

        Returns:
            dict: Resultados por imagen
        """
        results = {
            'total': len(image_paths),
            'success': 0,
            'failed': 0,
            'details': {}
        }

        for idx, image_path in enumerate(image_paths, 1):
            logger.info(f"🔄 Procesando imagen {idx}/{len(image_paths)}: {image_path}")

            success, processed_path, backup_path, error = cls.remove_background(
                image_path, backup_original
            )

            results['details'][image_path] = {
                'success': success,
                'processed_path': processed_path,
                'backup_path': backup_path,
                'error': error
            }

            if success:
                results['success'] += 1
            else:
                results['failed'] += 1

        logger.info(f"✅ Proceso por lotes completado: {results['success']} éxitos, {results['failed']} fallos")
        return results

    @classmethod
    def _create_backup(cls, image_path):
        """
        Crea una copia de seguridad de la imagen original

        Args:
            image_path: Ruta a la imagen original

        Returns:
            str: Ruta del archivo de backup
        """
        try:
            path_obj = Path(image_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{path_obj.stem}_original_{timestamp}{path_obj.suffix}"
            backup_path = str(path_obj.parent / backup_name)

            # Copiar archivo
            import shutil
            shutil.copy2(image_path, backup_path)

            return backup_path
        except Exception as e:
            logger.error(f"❌ Error al crear backup: {str(e)}")
            return None

    @classmethod
    def _convert_to_png(cls, image_path):
        """
        Convierte una imagen a formato PNG manteniendo transparencia

        Args:
            image_path: Ruta a la imagen original

        Returns:
            str: Nueva ruta en PNG o None si falla
        """
        try:
            path_obj = Path(image_path)
            png_path = str(path_obj.parent / f"{path_obj.stem}.png")

            # Abrir imagen y guardar como PNG
            with Image.open(image_path) as img:
                # Convertir a RGBA para mantener transparencia
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                img.save(png_path, 'PNG')

            return png_path
        except Exception as e:
            logger.error(f"❌ Error al convertir a PNG: {str(e)}")
            return None

    @classmethod
    def _validate_image(cls, image_path):
        """
        Valida que una imagen procesada sea válida

        Args:
            image_path: Ruta a la imagen

        Returns:
            bool: True si la imagen es válida
        """
        try:
            with Image.open(image_path) as img:
                img.verify()  # Verificar integridad
                width, height = img.size

                # Validaciones básicas
                if width == 0 or height == 0:
                    return False

                # Verificar que tiene canal alpha (transparencia)
                if img.mode == 'RGBA':
                    # Verificar que realmente tiene transparencia
                    alpha = img.getchannel('A')
                    # Si todos los píxeles son opacos (255), podría no haberse removido el fondo
                    # pero igual es una imagen válida
                    pass

                return True
        except Exception as e:
            logger.error(f"❌ Imagen inválida: {str(e)}")
            return False

    @classmethod
    def _restore_from_backup(cls, backup_path, original_path):
        """
        Restaura una imagen desde su backup

        Args:
            backup_path: Ruta del backup
            original_path: Ruta donde restaurar

        Returns:
            bool: True si se restauró exitosamente
        """
        try:
            import shutil
            shutil.copy2(backup_path, original_path)
            logger.info(f"🔄 Restaurado: {backup_path} -> {original_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error al restaurar desde backup: {str(e)}")
            return False

    @classmethod
    def cleanup_old_backups(cls, image_path, keep_recent=1):
        """
        Elimina backups antiguos, manteniendo solo los N más recientes

        Args:
            image_path: Ruta a la imagen original (para encontrar backups)
            keep_recent: Número de backups recientes a mantener

        Returns:
            int: Número de backups eliminados
        """
        try:
            path_obj = Path(image_path)
            backup_pattern = f"{path_obj.stem}_original_*.{path_obj.suffix[1:]}"
            backups = list(path_obj.parent.glob(backup_pattern))

            # Ordenar por fecha de creación (más reciente primero)
            backups.sort(key=lambda x: x.stat().st_ctime, reverse=True)

            # Mantener solo los N más recientes
            to_delete = backups[keep_recent:]

            for backup in to_delete:
                try:
                    os.remove(str(backup))
                    logger.info(f"🧹 Backup eliminado: {backup}")
                except Exception as e:
                    logger.error(f"❌ Error al eliminar backup {backup}: {str(e)}")

            return len(to_delete)
        except Exception as e:
            logger.error(f"❌ Error en limpieza de backups: {str(e)}")
            return 0

    @classmethod
    def get_image_info(cls, image_path):
        """
        Obtiene información sobre una imagen, incluyendo si tiene fondo removido

        Args:
            image_path: Ruta a la imagen

        Returns:
            dict: Información de la imagen
        """
        try:
            path_obj = Path(image_path)

            # Verificar si existe
            if not path_obj.exists():
                return {'exists': False}

            # Información básica
            info = {
                'exists': True,
                'path': str(image_path),
                'filename': path_obj.name,
                'extension': path_obj.suffix.lower(),
                'size_mb': os.path.getsize(image_path) / (1024 * 1024),
                'is_png': path_obj.suffix.lower() == '.png',
                'has_background_removed': False,
                'backups': []
            }

            # Buscar backups
            backup_pattern = f"{path_obj.stem}_original_*{path_obj.suffix}"
            backups = list(path_obj.parent.glob(backup_pattern))
            info['backups'] = sorted([str(b) for b in backups], reverse=True)

            # Determinar si tiene fondo removido
            # Criterio: es PNG y tiene al menos un backup
            if info['is_png'] and info['backups']:
                info['has_background_removed'] = True

            # Información de Pillow si está disponible
            try:
                with Image.open(image_path) as img:
                    info['dimensions'] = img.size
                    info['mode'] = img.mode
                    info['has_alpha'] = img.mode in ('RGBA', 'LA', 'PA')
            except:
                pass

            return info

        except Exception as e:
            logger.error(f"❌ Error al obtener info de imagen: {str(e)}")
            return {'exists': False, 'error': str(e)}


# Instancia global del servicio
background_service = ImageBackgroundService()
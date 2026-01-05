# INVOICE INVENTORY SERVICE - Gestión de Inventario en Facturas
# ============================================
# Responsabilidad: control de stock al vender/restaurar laptops

from app import db
from app.models.laptop import Laptop
from app.models.invoice import InvoiceItem
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InvoiceInventoryService:
    """Servicio para manejar inventario en operaciones de facturación"""

    @staticmethod
    def validate_stock_for_invoice_items(items_data):
        """
        Valida que haya suficiente stock para todos los items de laptop antes de crear/actualizar factura

        Args:
            items_data: Lista de diccionarios con datos de items (JSON parseado)

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            for item in items_data:
                if item.get('type') == 'laptop' and item.get('laptop_id'):
                    laptop_id = int(item['laptop_id'])
                    quantity = int(item.get('quantity', 1))

                    laptop = Laptop.query.get(laptop_id)
                    if not laptop:
                        return False, f'Laptop ID {laptop_id} no encontrada'

                    if laptop.quantity < quantity:
                        return False, (
                            f'Stock insuficiente para {laptop.display_name}. '
                            f'Disponible: {laptop.quantity}, Solicitado: {quantity}'
                        )

            return True, None

        except Exception as e:
            logger.error(f'Error validando stock: {str(e)}')
            return False, f'Error validando stock: {str(e)}'

    @staticmethod
    def update_inventory_for_invoice(invoice, action='subtract'):
        """
        Actualiza el inventario basado en los items de una factura

        Args:
            invoice: Objeto Invoice
            action: 'subtract' para vender, 'add' para restaurar (cancelación/devolución)

        Returns:
            tuple: (success, error_message)
        """
        try:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"📦 ACTUALIZANDO INVENTARIO - Factura {invoice.invoice_number}")
            logger.info(f"   Acción: {action}")
            logger.info(f"   Items: {invoice.items.count()}")
            logger.info(f"{'=' * 60}")

            for item in invoice.items.all():
                if item.item_type == 'laptop' and item.laptop_id:
                    laptop = Laptop.query.get(item.laptop_id)
                    if not laptop:
                        logger.error(f"❌ Laptop ID {item.laptop_id} no encontrada")
                        return False, f'Laptop ID {item.laptop_id} no encontrada'

                    old_quantity = laptop.quantity

                    if action == 'subtract':
                        # Validar stock antes de descontar
                        if laptop.quantity < item.quantity:
                            error_msg = (
                                f'Stock insuficiente para {laptop.display_name}. '
                                f'Disponible: {laptop.quantity}, Intentado vender: {item.quantity}'
                            )
                            logger.error(f"❌ {error_msg}")
                            return False, error_msg

                        laptop.quantity -= item.quantity
                        new_quantity = laptop.quantity

                        # Registrar fecha de venta si es la última unidad
                        if new_quantity == 0:
                            laptop.sale_date = datetime.now().date()
                            logger.info(f"   📅 Última unidad vendida - Fecha de venta actualizada")

                        logger.info(f"   ✅ {laptop.sku}: {old_quantity} → {new_quantity} (-{item.quantity})")

                    elif action == 'add':
                        laptop.quantity += item.quantity
                        new_quantity = laptop.quantity

                        # Si se restaura stock, limpiar fecha de venta
                        if old_quantity == 0 and new_quantity > 0:
                            laptop.sale_date = None
                            logger.info(f"   🔄 Stock restaurado - Fecha de venta limpiada")

                        logger.info(f"   ✅ {laptop.sku}: {old_quantity} → {new_quantity} (+{item.quantity})")

                    else:
                        return False, f'Acción no válida: {action}'

                    # Actualizar timestamps
                    laptop.updated_at = datetime.utcnow()
                    db.session.add(laptop)

                    # Registrar movimiento de inventario
                    InvoiceInventoryService.log_inventory_movement(
                        laptop=laptop,
                        invoice=invoice,
                        quantity_change=-item.quantity if action == 'subtract' else item.quantity,
                        action=action
                    )

            db.session.flush()
            logger.info(f"✅ Inventario actualizado exitosamente")
            logger.info(f"{'=' * 60}\n")
            return True, None

        except Exception as e:
            logger.error(f"❌ Error actualizando inventario: {str(e)}", exc_info=True)
            db.session.rollback()
            return False, f'Error actualizando inventario: {str(e)}'

    @staticmethod
    def log_inventory_movement(laptop, invoice, quantity_change, action):
        """
        Registra un movimiento de inventario (para auditoría)

        Args:
            laptop: Objeto Laptop
            invoice: Objeto Invoice
            quantity_change: Cambio en cantidad (positivo o negativo)
            action: 'subtract' o 'add'
        """
        try:
            # Aquí podrías guardar en una tabla de movimientos de inventario
            # Por ahora, solo lo logueamos
            movement_type = 'VENTA' if action == 'subtract' else 'DEVOLUCIÓN'

            logger.info(f"   📝 Movimiento: {movement_type} - {laptop.sku}")
            logger.info(f"   📝 Factura: {invoice.invoice_number}")
            logger.info(f"   📝 Cantidad: {abs(quantity_change)} unidades")
            logger.info(f"   📝 Stock resultante: {laptop.quantity}")

        except Exception as e:
            logger.error(f"Error registrando movimiento: {str(e)}")

    @staticmethod
    def check_invoice_items_availability(invoice):
        """
        Verifica disponibilidad de todos los items de una factura

        Args:
            invoice: Objeto Invoice

        Returns:
            dict: Diccionario con resultados de verificación
        """
        unavailable_items = []
        warnings = []

        for item in invoice.items.all():
            if item.item_type == 'laptop' and item.laptop_id:
                laptop = Laptop.query.get(item.laptop_id)
                if not laptop:
                    unavailable_items.append({
                        'item_id': item.id,
                        'description': item.description,
                        'reason': 'Laptop no encontrada en inventario'
                    })
                elif laptop.quantity < item.quantity:
                    warnings.append({
                        'item_id': item.id,
                        'description': item.description,
                        'available': laptop.quantity,
                        'requested': item.quantity,
                        'shortage': item.quantity - laptop.quantity
                    })

        return {
            'has_availability_issues': len(unavailable_items) > 0 or len(warnings) > 0,
            'unavailable_items': unavailable_items,
            'warnings': warnings,
            'can_process': len(unavailable_items) == 0  # Solo podemos procesar si todos los items existen
        }

    @staticmethod
    def get_inventory_summary_for_invoice(invoice):
        """
        Obtiene un resumen del impacto en inventario de una factura

        Args:
            invoice: Objeto Invoice

        Returns:
            dict: Resumen del impacto
        """
        total_laptops = 0
        total_units = 0
        items_summary = []

        for item in invoice.items.all():
            if item.item_type == 'laptop' and item.laptop_id:
                laptop = Laptop.query.get(item.laptop_id)
                if laptop:
                    total_laptops += 1
                    total_units += item.quantity

                    items_summary.append({
                        'sku': laptop.sku,
                        'name': laptop.display_name,
                        'current_stock': laptop.quantity,
                        'quantity_to_sell': item.quantity,
                        'will_be_out_of_stock': (laptop.quantity - item.quantity) <= 0,
                        'stock_after_sale': laptop.quantity - item.quantity
                    })

        return {
            'total_laptops': total_laptops,
            'total_units': total_units,
            'items': items_summary,
            'has_laptops': total_laptops > 0
        }
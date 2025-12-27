# ============================================
# AI SERVICE - Recomendaciones Inteligentes
# ============================================
# Responsabilidad: Generar recomendaciones basadas en datos

from decimal import Decimal


class AIService:
    """Servicio de Inteligencia Artificial para recomendaciones"""

    @staticmethod
    def generate_recommendations(laptop):
        """
        Genera recomendaciones basadas en el análisis de la laptop

        Args:
            laptop: Objeto Laptop

        Returns:
            list: Lista de diccionarios con recomendaciones
        """
        recommendations = []

        # Validar que laptop tenga los datos mínimos
        if not laptop:
            return recommendations

        # 1. Análisis de margen
        if laptop.margin_percentage is not None:
            if laptop.margin_percentage < 15:
                recommendations.append({
                    'level': 'danger',
                    'title': 'Margen Muy Bajo',
                    'message': f'El margen de {laptop.margin_percentage:.1f}% está por debajo del mínimo recomendado (15%).',
                    'action': 'Considera aumentar el precio de venta o negociar mejor precio de compra.'
                })
            elif laptop.margin_percentage < 25:
                recommendations.append({
                    'level': 'warning',
                    'title': 'Margen Aceptable',
                    'message': f'El margen de {laptop.margin_percentage:.1f}% está en rango aceptable pero puede mejorar.',
                    'action': 'Busca oportunidades para optimizar costos o ajustar precio.'
                })
            else:
                recommendations.append({
                    'level': 'success',
                    'title': 'Margen Excelente',
                    'message': f'El margen de {laptop.margin_percentage:.1f}% está muy bien posicionado.',
                    'action': 'Mantén esta estrategia de precios.'
                })

        # 2. Análisis de stock
        if laptop.quantity is not None and laptop.min_alert is not None:
            if laptop.quantity <= 0:
                recommendations.append({
                    'level': 'danger',
                    'title': 'Sin Stock',
                    'message': 'El producto está agotado.',
                    'action': 'Reabastece urgentemente si hay demanda.'
                })
            elif laptop.quantity <= laptop.min_alert:
                recommendations.append({
                    'level': 'warning',
                    'title': 'Stock Bajo',
                    'message': f'Solo quedan {laptop.quantity} unidades (mínimo: {laptop.min_alert}).',
                    'action': 'Planifica reabastecimiento pronto.'
                })

        # 3. Análisis de rotación
        if laptop.rotation_status:
            if laptop.rotation_status == 'slow' and laptop.days_in_inventory:
                recommendations.append({
                    'level': 'warning',
                    'title': 'Rotación Lenta',
                    'message': f'El producto lleva {laptop.days_in_inventory} días en inventario.',
                    'action': 'Considera promociones o descuentos para acelerar la venta.'
                })
            elif laptop.rotation_status == 'fast':
                recommendations.append({
                    'level': 'success',
                    'title': 'Alta Rotación',
                    'message': 'El producto se vende rápidamente.',
                    'action': 'Asegura disponibilidad constante de este modelo.'
                })

        # 4. Análisis de categoría vs especificaciones
        if laptop.category:
            category_name = laptop.category

            # Para laptops gamer
            if category_name == 'gamer':
                # Verificar GPU
                if laptop.graphics_card and laptop.graphics_card.name:
                    gpu_name = laptop.graphics_card.name.lower()
                    if 'integrated' in gpu_name or 'intel' in gpu_name or 'uhd' in gpu_name or 'iris' in gpu_name:
                        recommendations.append({
                            'level': 'info',
                            'title': 'GPU No Óptima para Gaming',
                            'message': 'La GPU integrada puede no ser ideal para gaming exigente.',
                            'action': 'Considera recategorizar o ajustar precio según rendimiento real.'
                        })

                # Verificar RAM - CORREGIDO CON TRY-EXCEPT
                if laptop.ram_type and laptop.ram_type.name:
                    try:
                        ram_str = ''.join(filter(str.isdigit, laptop.ram_type.name))
                        if ram_str:
                            ram_value = int(ram_str)
                            if ram_value < 16:
                                recommendations.append({
                                    'level': 'info',
                                    'title': 'RAM Limitada para Gaming',
                                    'message': f'{laptop.ram_type.name} puede ser insuficiente para gaming moderno.',
                                    'action': 'Recomienda upgrade de RAM si es posible.'
                                })
                    except (ValueError, AttributeError):
                        pass  # Si no se puede extraer el valor, ignorar

            # Para laptops de trabajo
            elif category_name == 'working':
                if laptop.processor and laptop.processor.name:
                    proc_name = laptop.processor.name.lower()
                    if 'i3' in proc_name or 'ryzen 3' in proc_name or 'celeron' in proc_name or 'pentium' in proc_name:
                        recommendations.append({
                            'level': 'info',
                            'title': 'Procesador de Nivel Básico',
                            'message': 'El procesador es adecuado para tareas básicas de oficina.',
                            'action': 'Enfoca marketing en uso ligero de oficina.'
                        })

        # 5. Análisis de condición vs precio
        if laptop.condition and laptop.sale_price:
            if laptop.condition == 'used' and laptop.margin_percentage and laptop.margin_percentage > 35:
                recommendations.append({
                    'level': 'info',
                    'title': 'Margen Alto en Producto Usado',
                    'message': 'El margen es alto para un producto usado.',
                    'action': 'Verifica que el precio sea competitivo en el mercado.'
                })
            elif laptop.condition == 'refurbished':
                recommendations.append({
                    'level': 'info',
                    'title': 'Producto Refurbished',
                    'message': 'Destaca la garantía y proceso de renovación en marketing.',
                    'action': 'Comunica claramente el valor agregado del refurbishing.'
                })

        # Si no hay recomendaciones, agregar una genérica positiva
        if not recommendations:
            recommendations.append({
                'level': 'success',
                'title': 'Producto Bien Configurado',
                'message': 'El producto está correctamente configurado.',
                'action': 'Monitorea regularmente el rendimiento de ventas.'
            })

        return recommendations

    @staticmethod
    def format_recommendations_text(recommendations):
        """
        Convierte lista de recomendaciones a texto formateado

        Args:
            recommendations: Lista de dicts con recomendaciones

        Returns:
            str: Texto formateado para mostrar
        """
        if not recommendations:
            return "✅ Todo en orden. No hay recomendaciones en este momento."

        text_parts = []

        for rec in recommendations:
            # Emojis por nivel
            level_icons = {
                'danger': '🔴',
                'warning': '⚠️',
                'success': '✅',
                'info': 'ℹ️'
            }
            icon = level_icons.get(rec.get('level', 'info'), 'ℹ️')

            # Header
            header = f"{icon} {rec.get('title', 'Recomendación')}"
            message = rec.get('message', '')

            text_parts.append(f"{header}\n{message}")

            # Actions si existen
            if 'action' in rec and rec['action']:
                text_parts.append(f"→ {rec['action']}")

            text_parts.append("")  # Línea en blanco

        return "\n".join(text_parts)

    @staticmethod
    def analyze_pricing_strategy(laptop, similar_laptops=None):
        """
        Analiza la estrategia de precio comparando con laptops similares

        Args:
            laptop: Laptop a analizar
            similar_laptops: Lista de laptops similares (opcional)

        Returns:
            dict con análisis de precios
        """
        analysis = {
            'position': 'unknown',
            'recommendation': '',
            'competitive_score': 0
        }

        if not similar_laptops:
            return analysis

        # Calcular precio promedio de similares
        prices = [float(l.sale_price) for l in similar_laptops if l.sale_price]

        if not prices:
            return analysis

        avg_price = sum(prices) / len(prices)
        laptop_price = float(laptop.sale_price)

        # Determinar posición
        if laptop_price < avg_price * 0.9:
            analysis['position'] = 'below_market'
            analysis['recommendation'] = 'Precio por debajo del mercado. Podrías aumentar sin perder competitividad.'
            analysis['competitive_score'] = 85
        elif laptop_price > avg_price * 1.1:
            analysis['position'] = 'above_market'
            analysis[
                'recommendation'] = 'Precio por encima del mercado. Considera reducir o destacar valor diferencial.'
            analysis['competitive_score'] = 60
        else:
            analysis['position'] = 'competitive'
            analysis['recommendation'] = 'Precio competitivo dentro del rango de mercado.'
            analysis['competitive_score'] = 100

        analysis['market_average'] = round(avg_price, 2)
        analysis['price_difference'] = round(laptop_price - avg_price, 2)
        analysis['price_difference_percent'] = round(((laptop_price - avg_price) / avg_price) * 100, 2)

        return analysis

    @staticmethod
    def predict_best_category(laptop):
        """
        Predice la mejor categoría basándose en especificaciones

        Args:
            laptop: Objeto laptop con especificaciones

        Returns:
            str: 'gamer', 'working', o 'home'
        """
        score_gamer = 0
        score_working = 0
        score_home = 0

        # Analizar GPU
        if laptop.graphics_card:
            gpu_name = laptop.graphics_card.name.upper()
            if 'RTX' in gpu_name or 'RX 6' in gpu_name or 'RX 7' in gpu_name:
                score_gamer += 40
            elif 'GTX' in gpu_name or 'MX' in gpu_name:
                score_gamer += 20
                score_working += 10
            else:
                score_home += 20
                score_working += 10

        # Analizar CPU
        if laptop.processor:
            cpu_name = laptop.processor.name.upper()
            if 'I9' in cpu_name or 'RYZEN 9' in cpu_name:
                score_gamer += 30
                score_working += 30
            elif 'I7' in cpu_name or 'RYZEN 7' in cpu_name:
                score_gamer += 20
                score_working += 25
            elif 'I5' in cpu_name or 'RYZEN 5' in cpu_name:
                score_working += 20
                score_home += 15
            else:
                score_home += 25

        # Analizar RAM - CORREGIDO: usa laptop.ram_type consistentemente
        if laptop.ram_type:
            try:
                ram_name = laptop.ram_type.name.upper()
                if '32GB' in ram_name or '64GB' in ram_name:
                    score_gamer += 20
                    score_working += 25
                elif '16GB' in ram_name:
                    score_working += 15
                    score_gamer += 10
                else:
                    score_home += 20
            except AttributeError:
                pass  # Si no hay RAM, ignorar

        # Analizar precio
        if laptop.sale_price:
            price = float(laptop.sale_price)
            if price > 1200:
                score_gamer += 15
                score_working += 10
            elif price > 800:
                score_working += 15
                score_gamer += 5
            else:
                score_home += 20

        # Determinar categoría ganadora
        scores = {
            'gamer': score_gamer,
            'working': score_working,
            'home': score_home
        }

        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]

        return {
            'category': best_category,
            'confidence': confidence,
            'scores': scores
        }

    @staticmethod
    def suggest_marketing_points(laptop):
        """
        Sugiere puntos clave para marketing

        Args:
            laptop: Objeto laptop

        Returns:
            list: Lista de puntos de marketing
        """
        points = []

        # Especificaciones destacadas
        if laptop.processor:
            points.append(f"Procesador {laptop.processor.name}")

        # CORREGIDO: usa laptop.ram_type consistentemente
        if laptop.ram_type:
            points.append(f"Memoria {laptop.ram_type.name}")

        # CORREGIDO: usa laptop.storage_type consistentemente
        if laptop.storage_type:
            points.append(f"Almacenamiento {laptop.storage_type.name}")

        if laptop.graphics_card:
            points.append(f"Gráficos {laptop.graphics_card.name}")

        if laptop.screen:
            points.append(f"Pantalla {laptop.screen.name}")

        # Características especiales
        if laptop.npu:
            points.append(f"🤖 NPU: {laptop.npu}")

        if laptop.storage_upgradeable or laptop.ram_upgradeable:
            points.append("🔧 Ampliable")

        if laptop.condition == 'refurbished' and laptop.aesthetic_grade in ['A+', 'A']:
            points.append("♻️ Como nuevo - Refurbished")

        # Por categoría
        if laptop.category == 'gamer':
            points.append("🎮 Listo para gaming")
        elif laptop.category == 'working':
            points.append("💼 Productividad profesional")
        elif laptop.category == 'home':
            points.append("🏠 Perfecto para el hogar")

        return points[:5]  # Máximo 5 puntos
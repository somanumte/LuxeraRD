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
        Genera recomendaciones inteligentes basadas en múltiples factores

        Args:
            laptop: Objeto Laptop con todos sus datos

        Returns:
            str: Recomendaciones en formato texto
        """
        recommendations = []

        # === ANÁLISIS DE MARGEN ===
        if laptop.margin_percentage:
            margin = float(laptop.margin_percentage)

            if margin < 10:
                recommendations.append({
                    'level': 'danger',
                    'icon': '🔴',
                    'title': 'Margen crítico',
                    'message': f'Margen muy bajo ({margin:.1f}%). Considera aumentar precio o reducir costos.'
                })
            elif margin < 15:
                recommendations.append({
                    'level': 'warning',
                    'icon': '⚠️',
                    'title': 'Margen bajo',
                    'message': f'Margen de {margin:.1f}% es bajo. Objetivo recomendado: 20-30%.'
                })
            elif margin > 40:
                recommendations.append({
                    'level': 'success',
                    'icon': '💰',
                    'title': 'Excelente margen',
                    'message': f'Margen excepcional de {margin:.1f}%. Producto muy rentable.'
                })
            elif margin >= 20:
                recommendations.append({
                    'level': 'success',
                    'icon': '✅',
                    'title': 'Margen saludable',
                    'message': f'Margen de {margin:.1f}% está en rango óptimo.'
                })

        # === ANÁLISIS DE ROTACIÓN ===
        if laptop.rotation_status == 'slow' and laptop.days_in_inventory:
            days = laptop.days_in_inventory
            recommendations.append({
                'level': 'warning',
                'icon': '🐌',
                'title': 'Rotación lenta',
                'message': f'{days} días en inventario. Acciones sugeridas:',
                'actions': [
                    f'Reducir precio en 5-10% (aprox. ${float(laptop.sale_price) * 0.05:.2f})',
                    'Crear promoción o bundle',
                    'Destacar en redes sociales',
                    'Ofrecer financiamiento'
                ]
            })
        elif laptop.rotation_status == 'fast':
            recommendations.append({
                'level': 'success',
                'icon': '🚀',
                'title': 'Rotación rápida',
                'message': f'Producto con alta demanda. Considera:',
                'actions': [
                    'Reabastecer pronto',
                    'Aumentar stock de seguridad',
                    'Evaluar aumento de precio'
                ]
            })

        # === ANÁLISIS DE INVENTARIO ===
        if laptop.quantity <= 0:
            recommendations.append({
                'level': 'danger',
                'icon': '❌',
                'title': 'Sin stock',
                'message': 'Producto agotado. Reordenar urgentemente.'
            })
        elif laptop.quantity <= laptop.min_alert:
            recommendations.append({
                'level': 'warning',
                'icon': '📦',
                'title': 'Stock bajo',
                'message': f'Solo {laptop.quantity} unidades. Alerta mínima: {laptop.min_alert}.',
                'actions': ['Generar orden de compra', 'Contactar proveedor']
            })

        # === ANÁLISIS POR CATEGORÍA ===
        if laptop.category == 'gamer':
            if laptop.sale_price and float(laptop.sale_price) < 800:
                recommendations.append({
                    'level': 'info',
                    'icon': '🎮',
                    'title': 'Precio competitivo - Gamer',
                    'message': 'Laptop gamer con precio atractivo. Destaca en marketing.'
                })

            if laptop.graphics_card and 'RTX' in laptop.graphics_card.name.upper():
                recommendations.append({
                    'level': 'info',
                    'icon': '💎',
                    'title': 'GPU Premium',
                    'message': 'RTX detectada. Enfatiza rendimiento en gaming y streaming.'
                })

        elif laptop.category == 'working':
            if laptop.processor and 'i7' in laptop.processor.name or 'Ryzen 7' in laptop.processor.name:
                recommendations.append({
                    'level': 'info',
                    'icon': '💼',
                    'title': 'Ideal para profesionales',
                    'message': 'Procesador potente. Mercado objetivo: diseñadores, developers, editores.'
                })

        elif laptop.category == 'home':
            if laptop.sale_price and float(laptop.sale_price) < 500:
                recommendations.append({
                    'level': 'info',
                    'icon': '🏠',
                    'title': 'Precio accesible',
                    'message': 'Perfecto para estudiantes y uso básico. Destaca portabilidad y batería.'
                })

        # === ANÁLISIS DE CONDICIÓN ===
        if laptop.condition == 'refurbished':
            if laptop.aesthetic_grade in ['A+', 'A']:
                recommendations.append({
                    'level': 'success',
                    'icon': '♻️',
                    'title': 'Refurbished Premium',
                    'message': f'Grado estético {laptop.aesthetic_grade}. Destaca "como nuevo" y garantía.',
                    'actions': [
                        'Incluir fotos detalladas',
                        'Ofrecer garantía extendida',
                        'Destacar ahorro vs nuevo'
                    ]
                })
            else:
                recommendations.append({
                    'level': 'info',
                    'icon': '♻️',
                    'title': 'Refurbished - Transparencia',
                    'message': f'Grado {laptop.aesthetic_grade}. Ser transparente sobre condición cosmética.'
                })

        # === ANÁLISIS DE UPGRADABILIDAD ===
        upgrade_options = []
        if laptop.storage_upgradeable:
            upgrade_options.append('almacenamiento')
        if laptop.ram_upgradeable:
            upgrade_options.append('RAM')

        if upgrade_options:
            recommendations.append({
                'level': 'info',
                'icon': '🔧',
                'title': 'Ampliable',
                'message': f'Se puede ampliar: {", ".join(upgrade_options)}. Úsalo como argumento de venta.'
            })

        # === ANÁLISIS DE ESPECIFICACIONES ===
        if laptop.npu:
            recommendations.append({
                'level': 'info',
                'icon': '🤖',
                'title': 'NPU disponible',
                'message': 'Procesamiento AI integrado. Ideal para IA local y Copilot+.'
            })

        # === RECOMENDACIÓN DE PRECIO ===
        if laptop.margin_percentage and float(laptop.margin_percentage) < 20:
            from app.services.financial_service import FinancialService
            suggested = FinancialService.suggest_sale_price(laptop.purchase_cost, 25)
            recommendations.append({
                'level': 'info',
                'icon': '💡',
                'title': 'Sugerencia de precio',
                'message': f'Para margen 25%, considera precio: ${suggested}'
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
            # Header
            header = f"{rec['icon']} {rec['title']}"
            message = rec['message']

            text_parts.append(f"{header}\n{message}")

            # Actions si existen
            if 'actions' in rec and rec['actions']:
                text_parts.append("Acciones sugeridas:")
                for action in rec['actions']:
                    text_parts.append(f"  • {action}")

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

        # Analizar RAM
        if laptop.ram_type:
            ram_name = laptop.ram_type.name.upper()
            if '32GB' in ram_name or '64GB' in ram_name:
                score_gamer += 20
                score_working += 25
            elif '16GB' in ram_name:
                score_working += 15
                score_gamer += 10
            else:
                score_home += 20

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

        if laptop.ram_type:
            points.append(f"Memoria {laptop.ram_type.name}")

        if laptop.storage_type:
            points.append(f"Almacenamiento {laptop.storage_type.name}")

        if laptop.graphics_card:
            points.append(f"Gráficos {laptop.graphics_card.name}")

        if laptop.screen:
            points.append(f"Pantalla {laptop.screen.name}")

        # Características especiales
        if laptop.npu:
            points.append("🤖 NPU para IA")

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
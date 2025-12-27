/**
 * ============================================
 * PRICE RANGE SLIDER
 * ============================================
 * Double-handle slider para filtro de rango de precio
 * con valores dinámicos desde la base de datos
 */

class PriceSlider {
    constructor(options) {
        // Configuración
        this.dbMinPrice = options.dbMinPrice || 0;
        this.dbMaxPrice = options.dbMaxPrice || 10000;
        this.currentMinPrice = options.currentMinPrice || this.dbMinPrice;
        this.currentMaxPrice = options.currentMaxPrice || this.dbMaxPrice;

        // Elementos del DOM
        this.slider = document.getElementById('price-slider');
        this.minDisplay = document.getElementById('price-min-display');
        this.maxDisplay = document.getElementById('price-max-display');
        this.minInput = document.getElementById('min_price_input');
        this.maxInput = document.getElementById('max_price_input');

        // Verificar que existan los elementos
        if (!this.slider || !this.minDisplay || !this.maxDisplay || !this.minInput || !this.maxInput) {
            console.error('PriceSlider: Elementos requeridos no encontrados');
            return;
        }

        // Estado
        this.isDraggingMin = false;
        this.isDraggingMax = false;

        // Inicializar
        this.createSliderElements();
        this.attachEventListeners();
        this.updateSlider(this.currentMinPrice, this.currentMaxPrice);
    }

    /**
     * Crear los elementos visuales del slider
     */
    createSliderElements() {
        // Crear track (barra de rango seleccionado)
        this.track = document.createElement('div');
        this.track.className = 'slider-track';

        // Crear manija mínima
        this.handleMin = document.createElement('div');
        this.handleMin.className = 'slider-handle';
        this.handleMin.id = 'handle-min';
        this.handleMin.setAttribute('aria-label', 'Precio mínimo');

        // Crear manija máxima
        this.handleMax = document.createElement('div');
        this.handleMax.className = 'slider-handle';
        this.handleMax.id = 'handle-max';
        this.handleMax.setAttribute('aria-label', 'Precio máximo');

        // Agregar al slider
        this.slider.appendChild(this.track);
        this.slider.appendChild(this.handleMin);
        this.slider.appendChild(this.handleMax);
    }

    /**
     * Convertir precio a posición en el slider (0-100%)
     */
    priceToPosition(price) {
        return ((price - this.dbMinPrice) / (this.dbMaxPrice - this.dbMinPrice)) * 100;
    }

    /**
     * Convertir posición a precio
     */
    positionToPrice(position) {
        return this.dbMinPrice + (position / 100) * (this.dbMaxPrice - this.dbMinPrice);
    }

    /**
     * Actualizar la UI del slider
     */
    updateSlider(minPrice, maxPrice) {
        // Asegurar que los valores estén en rango
        minPrice = Math.max(this.dbMinPrice, Math.min(minPrice, this.dbMaxPrice));
        maxPrice = Math.max(this.dbMinPrice, Math.min(maxPrice, this.dbMaxPrice));

        // Asegurar que min < max
        if (minPrice >= maxPrice) {
            maxPrice = minPrice + 1;
        }

        const minPos = this.priceToPosition(minPrice);
        const maxPos = this.priceToPosition(maxPrice);

        // Actualizar posiciones de las manijas
        this.handleMin.style.left = minPos + '%';
        this.handleMax.style.left = maxPos + '%';

        // Actualizar track (barra de rango)
        this.track.style.left = minPos + '%';
        this.track.style.width = (maxPos - minPos) + '%';

        // Actualizar displays de texto
        this.minDisplay.textContent = '$' + this.formatPrice(minPrice);
        this.maxDisplay.textContent = '$' + this.formatPrice(maxPrice);

        // Actualizar inputs ocultos
        this.minInput.value = minPrice.toFixed(2);
        this.maxInput.value = maxPrice.toFixed(2);
    }

    /**
     * Formatear precio para display
     */
    formatPrice(price) {
        return price.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * Manejar el arrastre de las manijas
     */
    handleDrag(e, isMin) {
        const rect = this.slider.getBoundingClientRect();
        const x = (e.type.includes('mouse') ? e.clientX : e.touches[0].clientX) - rect.left;
        let position = (x / rect.width) * 100;

        // Limitar posición entre 0 y 100
        position = Math.max(0, Math.min(100, position));

        const price = this.positionToPrice(position);

        if (isMin) {
            const maxPrice = parseFloat(this.maxInput.value);
            const newMinPrice = Math.min(price, maxPrice - 1);
            this.updateSlider(newMinPrice, maxPrice);
        } else {
            const minPrice = parseFloat(this.minInput.value);
            const newMaxPrice = Math.max(price, minPrice + 1);
            this.updateSlider(minPrice, newMaxPrice);
        }
    }

    /**
     * Adjuntar event listeners
     */
    attachEventListeners() {
        // Event listeners para manija mínima
        this.handleMin.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.isDraggingMin = true;
        });
        this.handleMin.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.isDraggingMin = true;
        });

        // Event listeners para manija máxima
        this.handleMax.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this.isDraggingMax = true;
        });
        this.handleMax.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.isDraggingMax = true;
        });

        // Event listeners globales para movimiento
        document.addEventListener('mousemove', (e) => {
            if (this.isDraggingMin) {
                e.preventDefault();
                this.handleDrag(e, true);
            }
            if (this.isDraggingMax) {
                e.preventDefault();
                this.handleDrag(e, false);
            }
        });

        document.addEventListener('touchmove', (e) => {
            if (this.isDraggingMin || this.isDraggingMax) {
                e.preventDefault();
                this.handleDrag(e, this.isDraggingMin);
            }
        }, { passive: false });

        // Event listeners para soltar
        document.addEventListener('mouseup', () => {
            this.isDraggingMin = false;
            this.isDraggingMax = false;
        });

        document.addEventListener('touchend', () => {
            this.isDraggingMin = false;
            this.isDraggingMax = false;
        });

        // Click en el slider para mover la manija más cercana
        this.slider.addEventListener('click', (e) => {
            if (e.target === this.slider || e.target === this.track) {
                const rect = this.slider.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const position = (x / rect.width) * 100;
                const clickPrice = this.positionToPrice(position);

                const minPrice = parseFloat(this.minInput.value);
                const maxPrice = parseFloat(this.maxInput.value);

                // Determinar cuál manija está más cerca
                const distToMin = Math.abs(clickPrice - minPrice);
                const distToMax = Math.abs(clickPrice - maxPrice);

                if (distToMin < distToMax) {
                    this.updateSlider(clickPrice, maxPrice);
                } else {
                    this.updateSlider(minPrice, clickPrice);
                }
            }
        });
    }
}

// Exportar para uso global
window.PriceSlider = PriceSlider;
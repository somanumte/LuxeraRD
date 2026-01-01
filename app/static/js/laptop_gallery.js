// ============================================
// GALERÍA DE IMÁGENES PREMIUM CON DRAG & DROP
// ============================================

const LaptopGalleryPremium = {
    draggedCard: null,
    totalImages: 0,
    imageConfig: {
        maxSize: 5 * 1024 * 1024, // 5MB
        validTypes: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'],
        maxImages: 8
    },

    // Colores para los placeholders de imágenes
    placeholderColors: [
        'placeholder-color-1',
        'placeholder-color-2',
        'placeholder-color-3',
        'placeholder-color-4',
        'placeholder-color-5',
        'placeholder-color-6',
        'placeholder-color-7',
        'placeholder-color-8'
    ],

    // Inicializar galería
    init: function() {
        this.initDragDrop();
        this.initEventListeners();
        this.initTipsTooltip();
        this.initExistingImages();
        this.updateImageCounter();
    },

    // Inicializar drag & drop premium
    initDragDrop: function() {
        const uploadArea = document.getElementById('upload-area-premium');
        const dragOverlay = document.getElementById('drag-overlay-premium');

        if (!uploadArea || !dragOverlay) return;

        // Eventos para el área de drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Resaltar área de drop
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.highlightDropZone.bind(this), false);
            document.body.addEventListener(eventName, this.highlightBody.bind(this), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.unhighlightDropZone.bind(this), false);
            document.body.addEventListener(eventName, this.unhighlightBody.bind(this), false);
        });

        // Manejar drop
        uploadArea.addEventListener('drop', this.handleDrop.bind(this), false);
        document.body.addEventListener('drop', this.handleBodyDrop.bind(this), false);

        // Configurar click en área de drop
        const browseBtn = document.getElementById('browse-btn-premium');
        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                document.getElementById('bulk-upload-premium').click();
            });
        }

        // También permitir click en el área de carga
        uploadArea.addEventListener('click', (e) => {
            if (e.target === uploadArea || e.target.classList.contains('upload-icon-premium') ||
                e.target.classList.contains('upload-subtitle') || e.target.classList.contains('upload-title')) {
                document.getElementById('bulk-upload-premium').click();
            }
        });
    },

    // Inicializar event listeners
    initEventListeners: function() {
        const bulkUpload = document.getElementById('bulk-upload-premium');
        if (bulkUpload) {
            bulkUpload.addEventListener('change', this.handleBulkUpload.bind(this));
        }

        // Evento para el botón de eliminar todas las imágenes
        const clearAllBtn = document.getElementById('clear-all-images');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', this.clearAllImages.bind(this));
        }

        // Evento para el botón de guardar galería
        const saveBtn = document.getElementById('save-gallery-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', this.saveGallery.bind(this));
        }
    },

    // Inicializar tooltip de consejos
    initTipsTooltip: function() {
        const infoIcon = document.getElementById('info-icon-premium');
        const tipsTooltip = document.getElementById('tips-tooltip-premium');

        if (!infoIcon || !tipsTooltip) return;

        infoIcon.addEventListener('mouseenter', () => {
            tipsTooltip.classList.add('show');
        });

        infoIcon.addEventListener('mouseleave', () => {
            tipsTooltip.classList.remove('show');
        });

        // Cerrar tooltip al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!infoIcon.contains(e.target) && !tipsTooltip.contains(e.target)) {
                tipsTooltip.classList.remove('show');
            }
        });
    },

    // Inicializar imágenes existentes (modo edición)
    initExistingImages: function() {
        // Contar imágenes existentes
        let existingCount = 0;

        for (let i = 1; i <= 8; i++) {
            const input = document.getElementById(`image_${i}`);
            const preview = document.getElementById(`preview-${i}`);

            if (preview && preview.classList.contains('visible') && preview.src) {
                existingCount++;

                // Crear tarjeta para imagen existente
                this.createImageCardForExisting(i, preview.src);
            }
        }

        this.totalImages = existingCount;
        this.updateImageCounter();

        // Si hay imágenes, agregar clase has-images al área de carga
        const uploadArea = document.getElementById('upload-area-premium');
        if (existingCount > 0 && uploadArea) {
            uploadArea.classList.add('has-images');
        }
    },

    // Crear tarjeta para imagen existente
    createImageCardForExisting: function(slot, imageSrc) {
        const imagesContainer = document.getElementById('images-container-premium');
        if (!imagesContainer) return;

        const altInput = document.getElementById(`image_${slot}_alt`);
        const altText = altInput ? altInput.value : '';
        const fileName = `imagen-${slot}`;
        const isCover = slot === 1;

        const imageCard = this.createImageCardElement({
            id: slot,
            name: fileName,
            alt: altText,
            isCover: isCover,
            isExisting: true,
            src: imageSrc
        }, slot - 1);

        imagesContainer.appendChild(imageCard);
    },

    // Crear elemento de tarjeta de imagen
    createImageCardElement: function(imageData, index) {
        const card = document.createElement('div');
        card.className = `image-card-premium ${imageData.isCover ? 'cover' : ''}`;
        card.draggable = true;
        card.dataset.id = imageData.id;
        card.dataset.slot = imageData.id;

        // Guardar la URL del objeto para liberarla después si es necesario
        if (imageData.isExisting === false && imageData.src && imageData.src.startsWith('blob:')) {
            card.dataset.objectUrl = imageData.src;
        }

        // Obtener extensión del archivo
        const extension = imageData.name.split('.').pop().toUpperCase();

        card.innerHTML = `
            <div class="image-preview-premium">
                ${imageData.isCover ? `
                    <div class="cover-badge-premium">
                        <i class="fas fa-crown"></i> Portada
                    </div>
                ` : ''}
                
                <div class="image-actions-premium">
                    <button class="image-btn-premium set-cover" title="Establecer como portada">
                        <i class="fas fa-crown"></i>
                    </button>
                    <button class="image-btn-premium delete" title="Eliminar imagen">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
                
                <img src="${imageData.src}" alt="${imageData.alt}" class="w-full h-full object-cover">
            </div>
            <div class="image-info-premium">
                <div class="image-name-premium" title="${imageData.name}">${imageData.name}</div>
                <input type="text" 
                       class="alt-text-input-premium" 
                       value="${imageData.alt}" 
                       placeholder="Texto alternativo (SEO)"
                       data-id="${imageData.id}">
            </div>
        `;

        // Agregar event listeners
        this.addCardEventListeners(card, imageData.id);

        return card;
    },

    // Agregar event listeners a la tarjeta
    addCardEventListeners: function(card, slotId) {
        const setCoverBtn = card.querySelector('.set-cover');
        const deleteBtn = card.querySelector('.delete');
        const altInput = card.querySelector('.alt-text-input-premium');

        setCoverBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.setAsCover(slotId);
        });

        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteImage(slotId);
        });

        altInput.addEventListener('change', (e) => {
            this.updateAltText(slotId, e.target.value);
        });

        altInput.addEventListener('blur', (e) => {
            this.updateAltText(slotId, e.target.value);
        });

        // Eventos de drag & drop
        card.addEventListener('dragstart', (e) => this.dragStart(e, slotId));
        card.addEventListener('dragover', this.allowDrop);
        card.addEventListener('drop', (e) => this.drop(e, slotId));
        card.addEventListener('dragend', this.dragEnd);
    },

    // Manejar drop de imágenes
    handleDrop: function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    },

    handleBodyDrop: function(e) {
        if (!e.target.closest('#upload-area-premium')) {
            const dt = e.dataTransfer;
            const files = dt.files;
            this.handleFiles(files);
        }
    },

    // Manejar selección múltiple
    handleBulkUpload: function(e) {
        const files = e.target.files;
        this.handleFiles(files);
        e.target.value = ''; // Resetear input
    },

    // Procesar archivos
    handleFiles: function(files) {
        const fileArray = Array.from(files).slice(0, this.imageConfig.maxImages - this.totalImages);

        if (fileArray.length === 0) {
            if (files.length > (this.imageConfig.maxImages - this.totalImages)) {
                this.showNotification(`Solo puedes subir hasta ${this.imageConfig.maxImages} imágenes. Se seleccionarán las primeras ${this.imageConfig.maxImages - this.totalImages}.`, true);
            }
            return;
        }

        let processedCount = 0;
        fileArray.forEach((file) => {
            if (this.validateImageFile(file)) {
                this.uploadImage(file);
                processedCount++;
            }
        });

        if (processedCount > 0) {
            this.showNotification(`Se ${processedCount > 1 ? 'han añadido' : 'ha añadido'} ${processedCount} imagen${processedCount > 1 ? 'es' : ''} a la galería.`);
        }
    },

    // Subir imagen individual
    uploadImage: function(file) {
        // Encontrar el siguiente slot disponible
        let targetSlot = null;
        for (let i = 1; i <= this.imageConfig.maxImages; i++) {
            const input = document.getElementById(`image_${i}`);
            const preview = document.getElementById(`preview-${i}`);

            // Verificar si el slot está vacío (sin archivo ni imagen existente)
            if (input && (!input.files || !input.files[0])) {
                if (preview && !preview.classList.contains('visible')) {
                    targetSlot = i;
                    break;
                } else if (!preview) {
                    targetSlot = i;
                    break;
                }
            }
        }

        if (!targetSlot) {
            this.showNotification(`Ya has alcanzado el límite de ${this.imageConfig.maxImages} imágenes. Elimina algunas antes de añadir más.`, true);
            return;
        }

        // Asignar archivo al input
        const input = document.getElementById(`image_${targetSlot}`);
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        input.files = dataTransfer.files;

        // Actualizar texto alternativo si está vacío
        const altInput = document.getElementById(`image_${targetSlot}_alt`);
        if (altInput && !altInput.value) {
            const nameWithoutExt = file.name.replace(/\.[^/.]+$/, "");
            altInput.value = `Imagen de ${nameWithoutExt}`;
        }

        // Crear tarjeta de imagen
        const imagesContainer = document.getElementById('images-container-premium');
        if (imagesContainer) {
            // Remover empty state si existe
            const emptyState = imagesContainer.querySelector('.empty-state-premium');
            if (emptyState) {
                emptyState.remove();
            }

            const imageCard = this.createImageCardElement({
                id: targetSlot,
                name: file.name,
                alt: altInput ? altInput.value : '',
                isCover: this.totalImages === 0, // Primera imagen es portada
                isExisting: false,
                src: URL.createObjectURL(file)
            }, targetSlot - 1);

            imagesContainer.appendChild(imageCard);
        }

        this.totalImages++;
        this.updateImageCounter();

        // Actualizar área de carga
        const uploadArea = document.getElementById('upload-area-premium');
        if (uploadArea && !uploadArea.classList.contains('has-images')) {
            uploadArea.classList.add('has-images');
        }
    },

    // Establecer imagen como portada
    setAsCover: function(slotId) {
        // Remover clase cover de todas las imágenes
        document.querySelectorAll('.image-card-premium').forEach(card => {
            card.classList.remove('cover');
        });

        // Agregar clase cover a la imagen seleccionada
        const card = document.querySelector(`.image-card-premium[data-id="${slotId}"]`);
        if (card) {
            card.classList.add('cover');
        }

        // Mostrar notificación
        this.showNotification('Portada actualizada correctamente');
    },

    // Eliminar imagen
    deleteImage: function(slotId) {
        if (!confirm('¿Estás seguro de que quieres eliminar esta imagen?')) {
            return;
        }

        // Limpiar input file
        const input = document.getElementById(`image_${slotId}`);
        if (input) {
            input.value = '';
        }

        // Limpiar preview existente
        const preview = document.getElementById(`preview-${slotId}`);
        if (preview) {
            preview.src = '';
            preview.classList.remove('visible');
        }

        // Limpiar alt text
        const altInput = document.getElementById(`image_${slotId}_alt`);
        if (altInput) {
            altInput.value = '';
        }

        // Remover tarjeta de imagen y liberar URL del objeto si existe
        const card = document.querySelector(`.image-card-premium[data-id="${slotId}"]`);
        if (card) {
            // Liberar URL del objeto si fue creada para vista previa
            if (card.dataset.objectUrl) {
                URL.revokeObjectURL(card.dataset.objectUrl);
            }
            card.remove();
        }

        // Si eliminamos la imagen de portada y hay más imágenes, hacer la siguiente imagen la portada
        const wasCover = card && card.classList.contains('cover');
        if (wasCover && this.totalImages > 1) {
            // Buscar la primera imagen disponible
            const firstCard = document.querySelector('.image-card-premium');
            if (firstCard) {
                const firstSlotId = firstCard.dataset.id;
                this.setAsCover(firstSlotId);
            }
        }

        this.totalImages--;
        this.updateImageCounter();

        // Si no hay imágenes, mostrar empty state
        if (this.totalImages === 0) {
            this.showEmptyState();
            const uploadArea = document.getElementById('upload-area-premium');
            if (uploadArea) {
                uploadArea.classList.remove('has-images');
            }
        }

        this.showNotification('Imagen eliminada correctamente');
    },

    // Actualizar texto alternativo
    updateAltText: function(slotId, newAlt) {
        const altInput = document.getElementById(`image_${slotId}_alt`);
        if (altInput) {
            altInput.value = newAlt;
        }
    },

    // Mostrar estado vacío
    showEmptyState: function() {
        const imagesContainer = document.getElementById('images-container-premium');
        if (!imagesContainer) return;

        imagesContainer.innerHTML = `
            <div class="empty-state-premium">
                <div class="empty-icon-premium">
                    <i class="fas fa-images"></i>
                </div>
                <div class="empty-text-premium">
                    No hay imágenes cargadas. Arrastra y suelta imágenes aquí o haz clic en el botón de arriba.
                </div>
            </div>
        `;
    },

    // Actualizar contador de imágenes
    updateImageCounter: function() {
        const counter = document.getElementById('image-counter-premium');
        if (counter) {
            counter.textContent = this.totalImages;
        }
    },

    // Limpiar todas las imágenes
    clearAllImages: function() {
        if (this.totalImages === 0) {
            this.showNotification('No hay imágenes para eliminar', true);
            return;
        }

        if (!confirm('¿Estás seguro de que quieres eliminar todas las imágenes?')) {
            return;
        }

        // Liberar todas las URLs de objeto creadas
        document.querySelectorAll('.image-card-premium[data-object-url]').forEach(card => {
            if (card.dataset.objectUrl) {
                URL.revokeObjectURL(card.dataset.objectUrl);
            }
        });

        // Limpiar todos los inputs
        for (let i = 1; i <= this.imageConfig.maxImages; i++) {
            const input = document.getElementById(`image_${i}`);
            if (input) {
                input.value = '';
            }

            const altInput = document.getElementById(`image_${i}_alt`);
            if (altInput) {
                altInput.value = '';
            }

            const preview = document.getElementById(`preview-${i}`);
            if (preview) {
                preview.src = '';
                preview.classList.remove('visible');
            }
        }

        // Remover todas las tarjetas
        const imagesContainer = document.getElementById('images-container-premium');
        if (imagesContainer) {
            imagesContainer.innerHTML = '';
            this.showEmptyState();
        }

        this.totalImages = 0;
        this.updateImageCounter();

        // Actualizar área de carga
        const uploadArea = document.getElementById('upload-area-premium');
        if (uploadArea) {
            uploadArea.classList.remove('has-images');
        }

        this.showNotification('Todas las imágenes han sido eliminadas');
    },

    // Guardar galería (simulación)
    saveGallery: function() {
        const saveBtn = document.getElementById('save-gallery-btn');
        if (!saveBtn) return;

        // Simular guardado
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
        saveBtn.disabled = true;

        setTimeout(() => {
            this.showNotification('¡Galería guardada exitosamente!');
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Guardar galería';
            saveBtn.disabled = false;
        }, 1500);
    },

    // Funciones para drag & drop entre tarjetas (reordenar)
    dragStart: function(e, slotId) {
        this.draggedCard = e.currentTarget;
        e.dataTransfer.setData('text/plain', slotId);
        e.dataTransfer.effectAllowed = 'move';

        // Agregar clase dragging
        setTimeout(() => {
            if (this.draggedCard) {
                this.draggedCard.classList.add('dragging');
            }
        }, 0);
    },

    allowDrop: function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    },

    drop: function(e, targetSlotId) {
        e.preventDefault();

        if (this.draggedCard && this.draggedCard !== e.currentTarget) {
            const draggedSlotId = this.draggedCard.dataset.id;

            // Intercambiar posiciones en el DOM
            const imagesContainer = document.getElementById('images-container-premium');
            const targetCard = e.currentTarget;

            if (imagesContainer && draggedSlotId !== targetSlotId) {
                // Reinsertar el elemento arrastrado antes del objetivo
                imagesContainer.insertBefore(this.draggedCard, targetCard);

                // Notificar al usuario
                this.showNotification('Imágenes reordenadas. Nota: Para guardar el nuevo orden, debes guardar el formulario.');
            }
        }

        this.dragEnd();
    },

    dragEnd: function() {
        if (this.draggedCard) {
            this.draggedCard.classList.remove('dragging');
            this.draggedCard = null;
        }
    },

    // Validar archivo de imagen
    validateImageFile: function(file) {
        // Validar tipo
        if (!this.imageConfig.validTypes.includes(file.type)) {
            this.showImageError('Formato no válido. Usa: JPG, PNG, WebP o GIF');
            return false;
        }

        // Validar tamaño
        if (file.size > this.imageConfig.maxSize) {
            this.showImageError('Imagen muy grande. Máximo 5MB.');
            return false;
        }

        return true;
    },

    // Mostrar error de imagen
    showImageError: function(message) {
        this.showNotification(message, true);
    },

    // Mostrar notificación
    showNotification: function(message, isError = false) {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${isError ? '#fef2f2' : '#f0fdf4'};
            color: ${isError ? '#7f1d1d' : '#14532d'};
            padding: 16px 24px;
            border-radius: 10px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-weight: 500;
            display: flex;
            align-items: center;
            border-left: 4px solid ${isError ? '#ef4444' : '#10b981'};
            animation: slideIn 0.3s ease, fadeOut 0.3s ease 2.7s forwards;
        `;

        notification.innerHTML = `
            <i class="fas ${isError ? 'fa-exclamation-triangle' : 'fa-check-circle'}" style="margin-right: 12px;"></i>
            ${message}
        `;

        document.body.appendChild(notification);

        // Agregar estilos de animación si no existen
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes fadeOut {
                    from { opacity: 1; }
                    to { opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        // Eliminar notificación después de 3 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    },

    // Funciones auxiliares para eventos
    preventDefaults: function(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    highlightDropZone: function() {
        const uploadArea = document.getElementById('upload-area-premium');
        if (uploadArea) {
            uploadArea.classList.add('dragover');
        }
    },

    unhighlightDropZone: function() {
        const uploadArea = document.getElementById('upload-area-premium');
        if (uploadArea) {
            uploadArea.classList.remove('dragover');
        }
    },

    highlightBody: function() {
        const dragOverlay = document.getElementById('drag-overlay-premium');
        if (dragOverlay) {
            dragOverlay.classList.add('visible');
        }
    },

    unhighlightBody: function() {
        const dragOverlay = document.getElementById('drag-overlay-premium');
        if (dragOverlay) {
            dragOverlay.classList.remove('visible');
        }
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    LaptopGalleryPremium.init();
});

// Exponer para uso global
window.laptopGalleryPremium = LaptopGalleryPremium;
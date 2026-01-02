// ============================================
// GALERÍA DE IMÁGENES HÍBRIDA - VERSIÓN MEJORADA
// ============================================
// Maneja tanto imágenes existentes (BD) como nuevas (locales)

const LaptopGalleryHybrid = {
    // Estado del componente
    images: [],                    // Array unificado de todas las imágenes
    imagesToDelete: [],            // IDs de imágenes existentes a eliminar
    nextTempId: 1,                 // Contador para IDs temporales
    draggedCard: null,

    // Configuración
    imageConfig: {
        maxSize: 5 * 1024 * 1024,      // 5MB
        minWidth: 400,
        minHeight: 300,
        validTypes: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'],
        maxImages: 8
    },

    objectUrls: new Set(),

    // ===== INICIALIZACIÓN =====

    init: function() {
        console.log('🚀 Inicializando galería híbrida...');
        this.cacheElements();
        this.loadExistingImages();
        this.initDragDrop();
        this.initEventListeners();
        this.initTipsTooltip();
        this.render();
        window.addEventListener('beforeunload', this.cleanup.bind(this));
    },

    cacheElements: function() {
        this.elements = {
            uploadArea: document.getElementById('upload-area-premium'),
            dragOverlay: document.getElementById('drag-overlay-premium'),
            imagesContainer: document.getElementById('images-container-premium'),
            imageCounter: document.getElementById('image-counter-premium'),
            bulkUpload: document.getElementById('bulk-upload-premium'),
            browseBtn: document.getElementById('browse-btn-premium'),
            form: document.getElementById('laptop-form')
        };
    },

    // ===== CARGA DE IMÁGENES EXISTENTES =====

    loadExistingImages: function() {
        console.log('📂 Cargando imágenes existentes...');

        // Buscar todas las imágenes existentes en el formulario
        for (let i = 1; i <= this.imageConfig.maxImages; i++) {
            const input = document.getElementById(`image_${i}`);
            const altInput = document.getElementById(`image_${i}_alt`);

            if (!input) continue;

            let imageData = null;

            // CASO 1: Archivo nuevo ya seleccionado (en modo edición tras error de validación)
            if (input.files && input.files.length > 0) {
                const file = input.files[0];
                imageData = {
                    id: `temp-${this.nextTempId++}`,
                    type: 'new',
                    source: file,
                    url: URL.createObjectURL(file),
                    alt: altInput?.value || `Imagen ${i}`,
                    isCover: i === 1,
                    slot: i,
                    name: file.name
                };
                this.objectUrls.add(imageData.url);
            }
            // CASO 2: Imagen existente en la BD (el input tiene un value o data-image-url)
            else if (input.hasAttribute('data-image-url') && input.getAttribute('data-image-url').trim() !== '') {
                const imageUrl = input.getAttribute('data-image-url');
                const imageId = input.getAttribute('data-image-id') || i;

                imageData = {
                    id: imageId,
                    type: 'existing',
                    source: imageUrl,
                    url: imageUrl,
                    alt: altInput?.value || `Imagen ${i}`,
                    isCover: input.getAttribute('data-is-cover') === 'true',
                    slot: i,
                    name: `imagen-${i}.jpg`
                };
            }

            // Si encontramos datos, agregar a nuestro array
            if (imageData) {
                this.images.push(imageData);
                console.log(`✅ Imagen ${i} cargada:`, imageData.type, imageData.url.substring(0, 50));
            }
        }

        console.log(`📊 Total imágenes cargadas: ${this.images.length}`);

        // Asegurar que al menos una sea cover si hay imágenes
        if (this.images.length > 0) {
            const hasCover = this.images.some(img => img.isCover);
            if (!hasCover) {
                this.images[0].isCover = true;
            }
        }
    },

    // ===== RENDERIZADO =====

    render: function() {
        const { imagesContainer } = this.elements;
        if (!imagesContainer) return;

        // Limpiar contenedor
        imagesContainer.innerHTML = '';

        if (this.images.length === 0) {
            this.showEmptyState();
            this.elements.uploadArea?.classList.remove('has-images');
        } else {
            // Ordenar por slot
            this.images.sort((a, b) => a.slot - b.slot);

            // Crear cards para cada imagen
            const fragment = document.createDocumentFragment();
            this.images.forEach((imageData, index) => {
                const card = this.createImageCard(imageData, index);
                fragment.appendChild(card);
            });

            imagesContainer.appendChild(fragment);
            this.elements.uploadArea?.classList.add('has-images');
        }

        this.updateCounter();
        this.syncFormInputs();
    },

    createImageCard: function(imageData, index) {
        const card = document.createElement('div');
        card.className = `image-card-premium ${imageData.isCover ? 'cover' : ''}`;
        card.draggable = true;
        card.dataset.imageId = imageData.id;
        card.dataset.index = index;

        // Agregar indicador de tipo (opcional pero útil)
        const typeIndicator = imageData.type === 'existing'
            ? '<span class="type-badge existing"><i class="fas fa-cloud"></i></span>'
            : '<span class="type-badge new"><i class="fas fa-upload"></i></span>';

        card.innerHTML = `
            <div class="image-preview-premium">
                ${imageData.isCover ? `
                    <div class="cover-badge-premium">
                        <i class="fas fa-crown"></i> Portada
                    </div>
                ` : ''}
                
                ${typeIndicator}
                
                <div class="image-actions-premium">
                    <button type="button" class="image-btn-premium set-cover" title="Establecer como portada">
                        <i class="fas fa-crown"></i>
                    </button>
                    <button type="button" class="image-btn-premium delete" title="Eliminar imagen">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
                
                <img src="${imageData.url}" alt="${imageData.alt}" class="w-full h-full object-cover">
            </div>
            <div class="image-info-premium">
                <div class="image-name-premium" title="${imageData.name}">${imageData.name}</div>
                <input type="text" 
                       class="alt-text-input-premium" 
                       value="${imageData.alt}" 
                       placeholder="Texto alternativo (SEO)"
                       data-index="${index}">
            </div>
        `;

        this.addCardEventListeners(card, index);
        return card;
    },

    addCardEventListeners: function(card, index) {
        // Botón de portada
        card.querySelector('.set-cover')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.setAsCover(index);
        });

        // Botón de eliminar
        card.querySelector('.delete')?.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteImage(index);
        });

        // Input de texto alternativo
        const altInput = card.querySelector('.alt-text-input-premium');
        let altTimeout;
        altInput?.addEventListener('input', (e) => {
            clearTimeout(altTimeout);
            altTimeout = setTimeout(() => {
                this.updateAltText(index, e.target.value);
            }, 500);
        });

        // Drag and drop entre cards
        card.addEventListener('dragstart', (e) => this.dragStart(e, index));
        card.addEventListener('dragover', this.allowDrop);
        card.addEventListener('drop', (e) => this.drop(e, index));
        card.addEventListener('dragend', this.dragEnd.bind(this));
    },

    // ===== OPERACIONES SOBRE IMÁGENES =====

    setAsCover: function(index) {
        if (index < 0 || index >= this.images.length) return;

        // Remover cover de todas
        this.images.forEach(img => img.isCover = false);

        // Marcar la seleccionada
        this.images[index].isCover = true;

        this.render();
        this.showNotification('Portada actualizada', 'success');
    },

    deleteImage: function(index) {
        if (index < 0 || index >= this.images.length) return;

        if (!confirm('¿Estás seguro de que quieres eliminar esta imagen?')) {
            return;
        }

        const imageData = this.images[index];

        // Si es una imagen existente, agregar a la lista de eliminación
        if (imageData.type === 'existing') {
            this.imagesToDelete.push(imageData.id);
            console.log('🗑️ Marcada para eliminar:', imageData.id);
        }

        // Si es nueva, liberar el URL del objeto
        if (imageData.type === 'new' && imageData.url.startsWith('blob:')) {
            URL.revokeObjectURL(imageData.url);
            this.objectUrls.delete(imageData.url);
        }

        // Verificar si era la portada
        const wasCover = imageData.isCover;

        // Eliminar del array
        this.images.splice(index, 1);

        // Si era portada y aún hay imágenes, marcar la primera como portada
        if (wasCover && this.images.length > 0) {
            this.images[0].isCover = true;
        }

        this.render();
        this.showNotification('Imagen eliminada', 'success');
    },

    updateAltText: function(index, newAlt) {
        if (index >= 0 && index < this.images.length) {
            this.images[index].alt = newAlt;
            this.syncFormInputs();
        }
    },

    // ===== CARGA DE NUEVAS IMÁGENES =====

    async handleFiles(files) {
        const availableSlots = this.imageConfig.maxImages - this.images.length;

        if (availableSlots <= 0) {
            this.showNotification(
                `Ya tienes el máximo de ${this.imageConfig.maxImages} imágenes. Elimina algunas primero.`,
                'error'
            );
            return;
        }

        const fileArray = Array.from(files).slice(0, availableSlots);

        if (files.length > availableSlots) {
            this.showNotification(
                `Solo puedes agregar ${availableSlots} imagen${availableSlots !== 1 ? 'es' : ''} más.`,
                'warning'
            );
        }

        let successCount = 0;
        for (const file of fileArray) {
            try {
                await this.validateImageFile(file);
                this.addNewImage(file);
                successCount++;
            } catch (error) {
                this.showNotification(error.message, 'error');
            }
        }

        if (successCount > 0) {
            this.render();
            this.showNotification(
                `${successCount} imagen${successCount !== 1 ? 'es' : ''} agregada${successCount !== 1 ? 's' : ''}.`,
                'success'
            );
        }
    },

    addNewImage: function(file) {
        const url = URL.createObjectURL(file);
        this.objectUrls.add(url);

        const imageData = {
            id: `temp-${this.nextTempId++}`,
            type: 'new',
            source: file,
            url: url,
            alt: `Imagen de ${file.name.replace(/\.[^/.]+$/, "")}`,
            isCover: this.images.length === 0, // Primera imagen es portada
            slot: this.getNextSlot(),
            name: file.name
        };

        this.images.push(imageData);
        console.log('➕ Nueva imagen agregada:', imageData.name);
    },

    getNextSlot: function() {
        if (this.images.length === 0) return 1;
        const maxSlot = Math.max(...this.images.map(img => img.slot));
        return maxSlot + 1;
    },

    // ===== VALIDACIÓN =====

    async validateImageFile(file) {
        if (!this.imageConfig.validTypes.includes(file.type)) {
            throw new Error(`${file.name}: Formato no válido. Usa JPG, PNG, WebP o GIF`);
        }

        if (file.size > this.imageConfig.maxSize) {
            throw new Error(`${file.name}: Tamaño máximo 5MB`);
        }

        try {
            const dimensions = await this.getImageDimensions(file);
            if (dimensions.width < this.imageConfig.minWidth || dimensions.height < this.imageConfig.minHeight) {
                throw new Error(
                    `${file.name}: Dimensiones mínimas ${this.imageConfig.minWidth}x${this.imageConfig.minHeight}px`
                );
            }
        } catch (error) {
            if (error.message.includes('Dimensiones')) {
                throw error;
            }
            throw new Error(`${file.name}: No se pudo cargar la imagen`);
        }

        return true;
    },

    getImageDimensions: function(file) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const url = URL.createObjectURL(file);

            img.onload = () => {
                URL.revokeObjectURL(url);
                resolve({ width: img.naturalWidth, height: img.naturalHeight });
            };

            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Error cargando imagen'));
            };

            img.src = url;
        });
    },

    // ===== SINCRONIZACIÓN CON FORMULARIO =====

    syncFormInputs: function() {
        console.log('🔄 Sincronizando con formulario...');

        // Limpiar todos los inputs primero
        for (let i = 1; i <= this.imageConfig.maxImages; i++) {
            const input = document.getElementById(`image_${i}`);
            const altInput = document.getElementById(`image_${i}_alt`);

            if (input) {
                // No limpiar el value de inputs existentes, solo actualizar los nuevos
                if (!input.value || input.value === '') {
                    input.value = '';
                }
            }
            if (altInput) altInput.value = '';
        }

        // Sincronizar cada imagen con su slot correspondiente
        this.images.forEach((imageData, index) => {
            const slot = index + 1;
            const input = document.getElementById(`image_${slot}`);
            const altInput = document.getElementById(`image_${slot}_alt`);

            if (!input) return;

            // Actualizar slot
            imageData.slot = slot;

            // Para imágenes nuevas, actualizar el input file
            if (imageData.type === 'new' && imageData.source instanceof File) {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(imageData.source);
                input.files = dataTransfer.files;
            }
            // Para imágenes existentes, mantener el value/data attributes
            else if (imageData.type === 'existing') {
                // NO establecer input.value porque es tipo file
                input.setAttribute('data-image-id', imageData.id);
                input.setAttribute('data-image-url', imageData.url);
                input.setAttribute('data-is-cover', imageData.isCover);
            }

            // Actualizar alt text
            if (altInput) {
                altInput.value = imageData.alt;
            }
        });

        // Agregar campo oculto con IDs a eliminar
        this.syncDeletedImages();
    },

    syncDeletedImages: function() {
        // Buscar o crear input oculto para las imágenes a eliminar
        let deleteInput = document.getElementById('images_to_delete');

        if (!deleteInput) {
            deleteInput = document.createElement('input');
            deleteInput.type = 'hidden';
            deleteInput.id = 'images_to_delete';
            deleteInput.name = 'images_to_delete';
            this.elements.form.appendChild(deleteInput);
        }

        // Guardar los IDs como JSON
        deleteInput.value = JSON.stringify(this.imagesToDelete);

        console.log('🗑️ Imágenes marcadas para eliminar:', this.imagesToDelete);
    },

    // ===== DRAG & DROP =====

    initDragDrop: function() {
        const { uploadArea, dragOverlay } = this.elements;
        if (!uploadArea || !dragOverlay) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
            document.body.addEventListener(eventName, () => dragOverlay.classList.add('visible'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
            document.body.addEventListener(eventName, () => dragOverlay.classList.remove('visible'), false);
        });

        uploadArea.addEventListener('drop', this.handleDrop.bind(this), false);
        document.body.addEventListener('drop', this.handleBodyDrop.bind(this), false);
    },

    handleDrop: function(e) {
        const files = e.dataTransfer.files;
        this.handleFiles(files);
    },

    handleBodyDrop: function(e) {
        if (!e.target.closest('#upload-area-premium')) {
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        }
    },

    dragStart: function(e, index) {
        this.draggedCard = e.currentTarget;
        this.draggedIndex = index;
        e.dataTransfer.effectAllowed = 'move';
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

    drop: function(e, targetIndex) {
        e.preventDefault();

        if (this.draggedIndex !== undefined && this.draggedIndex !== targetIndex) {
            // Reordenar el array
            const [movedImage] = this.images.splice(this.draggedIndex, 1);
            this.images.splice(targetIndex, 0, movedImage);

            this.render();
            this.showNotification('Imágenes reordenadas', 'success');
        }

        this.dragEnd();
    },

    dragEnd: function() {
        if (this.draggedCard) {
            this.draggedCard.classList.remove('dragging');
            this.draggedCard = null;
            this.draggedIndex = undefined;
        }
    },

    // ===== EVENT LISTENERS =====

    initEventListeners: function() {
        const { bulkUpload, browseBtn } = this.elements;

        browseBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            bulkUpload.click();
        });

        bulkUpload?.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
            e.target.value = ''; // Limpiar para permitir subir el mismo archivo
        });

        // Click en el área de upload
        this.elements.uploadArea?.addEventListener('click', (e) => {
            if (e.target === this.elements.uploadArea ||
                e.target.closest('.upload-icon-premium, .upload-title, .upload-subtitle')) {
                bulkUpload.click();
            }
        });
    },

    initTipsTooltip: function() {
        const infoIcon = document.getElementById('info-icon-premium');
        const tipsTooltip = document.getElementById('tips-tooltip-premium');
        if (!infoIcon || !tipsTooltip) return;

        infoIcon.addEventListener('mouseenter', () => tipsTooltip.classList.add('show'));
        infoIcon.addEventListener('mouseleave', () => tipsTooltip.classList.remove('show'));

        document.addEventListener('click', (e) => {
            if (!infoIcon.contains(e.target) && !tipsTooltip.contains(e.target)) {
                tipsTooltip.classList.remove('show');
            }
        });
    },

    updateCounter: function() {
        if (this.elements.imageCounter) {
            this.elements.imageCounter.textContent = this.images.length;
        }
    },

    showNotification: function(message, type = 'success') {
        const notification = document.createElement('div');

        const colors = {
            success: { bg: '#f0fdf4', text: '#14532d', border: '#10b981' },
            error: { bg: '#fef2f2', text: '#7f1d1d', border: '#ef4444' },
            warning: { bg: '#fffbeb', text: '#78350f', border: '#f59e0b' },
            info: { bg: '#eff6ff', text: '#1e3a8a', border: '#3b82f6' }
        };

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-triangle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };

        const color = colors[type] || colors.info;
        const icon = icons[type] || icons.info;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${color.bg};
            color: ${color.text};
            padding: 16px 24px;
            border-radius: 10px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-weight: 500;
            display: flex;
            align-items: center;
            border-left: 4px solid ${color.border};
            animation: slideIn 0.3s ease, fadeOut 0.3s ease 2.7s forwards;
        `;

        notification.innerHTML = `
            <i class="fas ${icon}" style="margin-right: 12px;"></i>
            ${message}
        `;

        document.body.appendChild(notification);

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

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    },

    // ===== CLEANUP =====

    cleanup: function() {
        this.objectUrls.forEach(url => {
            try {
                URL.revokeObjectURL(url);
            } catch (e) {
                console.warn('Error liberando URL:', url);
            }
        });
        this.objectUrls.clear();
    },

    preventDefaults: function(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    // ===== API PÚBLICA =====

    getState: function() {
        return {
            images: this.images,
            imagesToDelete: this.imagesToDelete,
            totalCount: this.images.length,
            newCount: this.images.filter(img => img.type === 'new').length,
            existingCount: this.images.filter(img => img.type === 'existing').length
        };
    }
};

// ===== INICIALIZACIÓN =====

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎬 DOM listo, inicializando galería en 50ms...');

    setTimeout(() => {
        LaptopGalleryHybrid.init();

        // Debug: mostrar estado inicial
        console.log('📊 Estado inicial:', LaptopGalleryHybrid.getState());
    }, 50);
});

// Exponer globalmente para debugging
window.LaptopGalleryHybrid = LaptopGalleryHybrid;
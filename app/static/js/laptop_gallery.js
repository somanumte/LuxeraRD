// ============================================
// GALERÍA DE IMÁGENES HÍBRIDA - VERSIÓN MEJORADA
// ============================================
// Maneja tanto imágenes existentes (BD) como nuevas (locales)
// CON SOPORTE PARA ELIMINACIÓN DE FONDO Y SELECCIÓN DE PORTADA MEJORADA

const LaptopGalleryHybrid = {
    // Estado del componente
    images: [],                    // Array unificado de todas las imágenes
    imagesToDelete: [],            // IDs de imágenes existentes a eliminar
    nextTempId: 1,                 // Contador para IDs temporales
    draggedCard: null,
    currentCoverSlot: 1,           // Slot actual de la imagen de portada

    // Configuración
    imageConfig: {
        maxSize: 5 * 1024 * 1024,      // 5MB (límite de subida)
        bgMaxSize: 10 * 1024 * 1024,   // 10MB (límite para eliminación de fondo)
        minWidth: 400,
        minHeight: 300,
        validTypes: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'],
        maxImages: 8
    },

    objectUrls: new Set(),

    // ===== INICIALIZACIÓN =====

    init: function() {
        console.log('🚀 Inicializando galería híbrida con eliminación de fondo...');
        this.cacheElements();
        this.loadExistingImages();
        this.initDragDrop();
        this.initEventListeners();
        this.initTipsTooltip();
        this.initCoverSelector();
        this.render();
        this.updateCoverSelection();
        window.addEventListener('beforeunload', this.cleanup.bind(this));

        // Disparar evento para notificar que la galería está lista
        document.dispatchEvent(new CustomEvent('laptopGallery:initialized'));
    },

    cacheElements: function() {
        this.elements = {
            uploadArea: document.getElementById('upload-area-premium'),
            dragOverlay: document.getElementById('drag-overlay-premium'),
            imagesContainer: document.getElementById('images-container-premium'),
            imageCounter: document.getElementById('image-counter-premium'),
            bulkUpload: document.getElementById('bulk-upload-premium'),
            browseBtn: document.getElementById('browse-btn-premium'),
            form: document.getElementById('laptop-form'),
            coverSelector: document.getElementById('cover-selector'),
            removeBgCover: document.getElementById('remove_bg_cover'),
            removeBgAll: document.getElementById('remove_bg_all')
        };
    },

    // ===== CARGA DE IMÁGENES EXISTENTES =====

    loadExistingImages: function() {
        console.log('📂 Cargando imágenes existentes...');

        // Buscar todas las imágenes existentes en el formulario
        for (let i = 1; i <= this.imageConfig.maxImages; i++) {
            const input = document.getElementById(`image_${i}`);
            const altInput = document.getElementById(`image_${i}_alt`);
            const coverInput = document.getElementById(`image_${i}_is_cover`);

            if (!input) continue;

            let imageData = null;

            // CASO 1: Archivo nuevo ya seleccionado (en modo edición tras error de validación)
            if (input.files && input.files.length > 0) {
                const file = input.files[0];
                const isCover = coverInput ? coverInput.value === 'true' : i === 1;

                imageData = {
                    id: `temp-${this.nextTempId++}`,
                    type: 'new',
                    source: file,
                    url: URL.createObjectURL(file),
                    alt: altInput?.value || `Imagen ${i}`,
                    isCover: isCover,
                    slot: i,
                    name: file.name,
                    status: 'new' // nueva, no procesada
                };

                if (isCover) {
                    this.currentCoverSlot = i;
                }

                this.objectUrls.add(imageData.url);
            }
            // CASO 2: Imagen existente en la BD (el input tiene un value o data-image-url)
            else if (input.hasAttribute('data-image-url') && input.getAttribute('data-image-url').trim() !== '') {
                const imageUrl = input.getAttribute('data-image-url');
                const imageId = input.getAttribute('data-image-id') || i;
                const isCover = input.getAttribute('data-is-cover') === 'true';

                imageData = {
                    id: imageId,
                    type: 'existing',
                    source: imageUrl,
                    url: imageUrl,
                    alt: altInput?.value || `Imagen ${i}`,
                    isCover: isCover,
                    slot: i,
                    name: `imagen-${i}`,
                    status: 'existing' // ya guardada en BD
                };

                if (isCover) {
                    this.currentCoverSlot = i;
                }
            }

            // Si encontramos datos, agregar a nuestro array
            if (imageData) {
                this.images.push(imageData);
                console.log(`✅ Imagen ${i} cargada:`, imageData.type, imageData.status, imageData.url.substring(0, 50));
            }
        }

        console.log(`📊 Total imágenes cargadas: ${this.images.length}`);
        console.log(`👑 Portada actual: slot ${this.currentCoverSlot}`);

        // Asegurar que al menos una sea cover si hay imágenes
        if (this.images.length > 0) {
            const hasCover = this.images.some(img => img.isCover);
            if (!hasCover) {
                this.images[0].isCover = true;
                this.currentCoverSlot = this.images[0].slot;
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
        this.updateCoverSelection();

        // Disparar evento para notificar que las imágenes se actualizaron
        document.dispatchEvent(new CustomEvent('laptopGallery:imagesUpdated', {
            detail: { images: this.images }
        }));
    },

    createImageCard: function(imageData, index) {
        const card = document.createElement('div');
        card.className = `image-card-premium ${imageData.isCover ? 'cover' : ''}`;
        card.draggable = true;
        card.dataset.imageId = imageData.id;
        card.dataset.index = index;
        card.dataset.slot = imageData.slot;

        // Determinar badges según tipo y estado
        let typeBadge = '';
        if (imageData.type === 'existing') {
            typeBadge = '<span class="type-badge existing"><i class="fas fa-cloud"></i> Guardada</span>';
        } else if (imageData.type === 'new') {
            typeBadge = '<span class="type-badge new"><i class="fas fa-upload"></i> Nueva</span>';
        }

        // Badge para eliminación de fondo (si aplica)
        let bgBadge = '';
        if (imageData.hasBackgroundRemoved) {
            bgBadge = '<span class="type-badge bg-removed"><i class="fas fa-magic"></i> Sin fondo</span>';
        }

        card.innerHTML = `
            <div class="image-preview-premium">
                ${imageData.isCover ? `
                    <div class="cover-badge-premium">
                        <i class="fas fa-crown"></i> Portada
                    </div>
                ` : ''}
                
                ${typeBadge}
                ${bgBadge}
                
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
                <div class="image-name-premium" title="${imageData.name}">
                    ${imageData.name.length > 20 ? imageData.name.substring(0, 20) + '...' : imageData.name}
                </div>
                <input type="text" 
                       class="alt-text-input-premium" 
                       value="${imageData.alt}" 
                       placeholder="Texto alternativo (SEO)"
                       data-index="${index}">
                <div class="image-status-premium">
                    <small class="text-xs ${imageData.type === 'existing' ? 'text-green-600' : 'text-blue-600'}">
                        ${imageData.type === 'existing' ? '💾 Guardada' : '🆕 Nueva'}
                    </small>
                </div>
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

        const previousCoverSlot = this.currentCoverSlot;
        const newCoverImage = this.images[index];

        // Remover cover de todas
        this.images.forEach(img => img.isCover = false);

        // Marcar la seleccionada
        newCoverImage.isCover = true;
        this.currentCoverSlot = newCoverImage.slot;

        // Animación de feedback
        this.animateCoverChange(previousCoverSlot, newCoverImage.slot);

        this.render();
        this.showNotification('Portada actualizada correctamente', 'success');
    },

    animateCoverChange: function(previousSlot, newSlot) {
        // Encontrar elementos DOM
        const previousCard = document.querySelector(`[data-slot="${previousSlot}"]`);
        const newCard = document.querySelector(`[data-slot="${newSlot}"]`);

        if (previousCard) {
            previousCard.classList.add('cover-removed');
            setTimeout(() => previousCard.classList.remove('cover-removed'), 500);
        }

        if (newCard) {
            newCard.classList.add('cover-added');
            setTimeout(() => newCard.classList.remove('cover-added'), 500);
        }
    },

    deleteImage: function(index) {
        if (index < 0 || index >= this.images.length) return;

        const imageData = this.images[index];

        // Confirmar eliminación
        if (!confirm(`¿Estás seguro de que quieres eliminar "${imageData.name}"?`)) {
            return;
        }

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
            this.currentCoverSlot = this.images[0].slot;
        } else if (this.images.length === 0) {
            this.currentCoverSlot = 1;
        }

        this.render();
        this.showNotification('Imagen eliminada correctamente', 'success');
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
                `⚠️ Ya tienes el máximo de ${this.imageConfig.maxImages} imágenes. Elimina algunas primero.`,
                'error'
            );
            return;
        }

        const fileArray = Array.from(files).slice(0, availableSlots);

        if (files.length > availableSlots) {
            this.showNotification(
                `ℹ️ Solo puedes agregar ${availableSlots} imagen${availableSlots !== 1 ? 'es' : ''} más.`,
                'warning'
            );
        }

        let successCount = 0;
        let warningCount = 0;

        for (const file of fileArray) {
            try {
                await this.validateImageFile(file);
                this.addNewImage(file);
                successCount++;

                // Advertencia si la imagen es grande para eliminación de fondo
                if (file.size > this.imageConfig.bgMaxSize) {
                    warningCount++;
                }
            } catch (error) {
                this.showNotification(error.message, 'error');
            }
        }

        if (successCount > 0) {
            this.render();

            let message = `${successCount} imagen${successCount !== 1 ? 'es' : ''} agregada${successCount !== 1 ? 's' : ''} correctamente.`;
            if (warningCount > 0) {
                message += ` ${warningCount} imagen${warningCount !== 1 ? 'es' : ''} grande${warningCount !== 1 ? 's' : ''} (más de 10MB) puede fallar en eliminación de fondo.`;
            }

            this.showNotification(message, successCount > 0 ? 'success' : 'warning');
        }
    },

    addNewImage: function(file) {
        const url = URL.createObjectURL(file);
        this.objectUrls.add(url);

        // Determinar si será portada (primera imagen nueva si no hay imágenes, o si no hay portada)
        const willBeCover = this.images.length === 0 || !this.images.some(img => img.isCover);

        const imageData = {
            id: `temp-${this.nextTempId++}`,
            type: 'new',
            source: file,
            url: url,
            alt: `Imagen de ${file.name.replace(/\.[^/.]+$/, "")}`,
            isCover: willBeCover,
            slot: this.getNextSlot(),
            name: file.name,
            status: 'new',
            sizeMB: (file.size / (1024 * 1024)).toFixed(2)
        };

        if (willBeCover) {
            this.currentCoverSlot = imageData.slot;
        }

        this.images.push(imageData);
        console.log('➕ Nueva imagen agregada:', imageData.name, `(${imageData.sizeMB}MB)`);
    },

    getNextSlot: function() {
        if (this.images.length === 0) return 1;
        const usedSlots = this.images.map(img => img.slot);
        for (let i = 1; i <= this.imageConfig.maxImages; i++) {
            if (!usedSlots.includes(i)) {
                return i;
            }
        }
        return this.images.length + 1;
    },

    // ===== VALIDACIÓN =====

    async validateImageFile(file) {
        if (!this.imageConfig.validTypes.includes(file.type)) {
            throw new Error(`${file.name}: Formato no válido. Usa JPG, PNG, WebP o GIF`);
        }

        if (file.size > this.imageConfig.maxSize) {
            throw new Error(`${file.name}: Tamaño máximo 5MB para subida`);
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
            const coverInput = document.getElementById(`image_${i}_is_cover`);

            if (input) {
                // No limpiar el value de inputs existentes, solo actualizar los nuevos
                if (!input.value || input.value === '') {
                    input.value = '';
                }
            }
            if (altInput) altInput.value = '';
            if (coverInput) coverInput.value = 'false';
        }

        // Sincronizar cada imagen con su slot correspondiente
        this.images.forEach((imageData, index) => {
            const slot = imageData.slot;
            const input = document.getElementById(`image_${slot}`);
            const altInput = document.getElementById(`image_${slot}_alt`);
            const coverInput = document.getElementById(`image_${slot}_is_cover`);

            if (!input) return;

            // Para imágenes nuevas, actualizar el input file
            if (imageData.type === 'new' && imageData.source instanceof File) {
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(imageData.source);
                input.files = dataTransfer.files;
            }
            // Para imágenes existentes, mantener el value/data attributes
            else if (imageData.type === 'existing') {
                input.setAttribute('data-image-id', imageData.id);
                input.setAttribute('data-image-url', imageData.url);
                input.setAttribute('data-is-cover', imageData.isCover);
            }

            // Actualizar alt text
            if (altInput) {
                altInput.value = imageData.alt;
            }

            // Actualizar estado de portada
            if (coverInput) {
                coverInput.value = imageData.isCover ? 'true' : 'false';
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

    // ===== SELECTOR DE PORTADA =====

    initCoverSelector: function() {
        const { coverSelector } = this.elements;
        if (!coverSelector) return;

        // Actualizar selector cuando cambien las imágenes
        document.addEventListener('laptopGallery:imagesUpdated', () => {
            this.updateCoverSelection();
        });
    },

    updateCoverSelection: function() {
        const { coverSelector } = this.elements;
        if (!coverSelector) return;

        // Guardar selección actual
        const currentValue = coverSelector.value;

        // Limpiar selector
        coverSelector.innerHTML = '<option value="0">-- Seleccionar portada --</option>';

        // Agregar opciones para cada imagen
        this.images.forEach((img, index) => {
            const option = document.createElement('option');
            option.value = img.slot;

            let displayText = `Imagen ${img.slot}`;

            // Añadir indicadores
            if (img.type === 'existing') {
                displayText += ' 💾';
            } else {
                displayText += ' 🆕';
            }

            if (img.isCover) {
                displayText += ' 👑 PORTADA';
            }

            // Añadir nombre truncado
            if (img.name) {
                displayText += ` - ${img.name.substring(0, 20)}${img.name.length > 20 ? '...' : ''}`;
            }

            option.textContent = displayText;

            if (img.isCover) {
                option.selected = true;
            }

            coverSelector.appendChild(option);
        });

        // Si no hay imágenes, deshabilitar selector
        coverSelector.disabled = this.images.length === 0;

        // Si había una selección y aún existe, restaurarla
        if (currentValue && currentValue !== '0') {
            const optionExists = Array.from(coverSelector.options).some(opt => opt.value === currentValue);
            if (optionExists) {
                coverSelector.value = currentValue;
            }
        }
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
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
                dragOverlay.classList.add('visible');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
                dragOverlay.classList.remove('visible');
            }, false);
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

            // Actualizar slots basados en nueva posición
            this.images.forEach((img, idx) => {
                img.slot = idx + 1;
            });

            // Si la imagen movida era portada, actualizar el slot de portada
            if (movedImage.isCover) {
                this.currentCoverSlot = movedImage.slot;
            }

            this.render();
            this.showNotification('Imágenes reordenadas correctamente', 'success');
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
        const { bulkUpload, browseBtn, coverSelector } = this.elements;

        // Botón para buscar imágenes
        browseBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            bulkUpload.click();
        });

        // Input de carga múltiple
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

        // Selector de portada
        if (coverSelector) {
            coverSelector.addEventListener('change', (e) => {
                const selectedSlot = parseInt(e.target.value);
                if (selectedSlot > 0) {
                    const imageIndex = this.images.findIndex(img => img.slot === selectedSlot);
                    if (imageIndex !== -1) {
                        this.setAsCover(imageIndex);
                    }
                }
            });
        }
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
            this.elements.imageCounter.textContent = `${this.images.length}/${this.imageConfig.maxImages}`;
        }
    },

    showEmptyState: function() {
        const { imagesContainer } = this.elements;
        if (!imagesContainer) return;

        imagesContainer.innerHTML = `
            <div class="empty-state-premium">
                <div class="empty-icon-premium">
                    <i class="fas fa-images"></i>
                </div>
                <h3 class="empty-title-premium">Sin imágenes</h3>
                <p class="empty-description-premium">
                    Arrastra y suelta imágenes aquí o haz clic en el botón para subirlas.
                </p>
            </div>
        `;
    },

    showNotification: function(message, type = 'success') {
        // Usar Toastify si está disponible
        if (typeof Toastify !== 'undefined') {
            const colors = {
                success: 'linear-gradient(to right, #00b09b, #96c93d)',
                error: 'linear-gradient(to right, #ff5f6d, #ffc371)',
                warning: 'linear-gradient(to right, #f46b45, #eea849)',
                info: 'linear-gradient(to right, #4A00E0, #8E2DE2)'
            };

            Toastify({
                text: message,
                duration: 3000,
                gravity: "top",
                position: "right",
                backgroundColor: colors[type] || colors.info,
                stopOnFocus: true
            }).showToast();
        } else {
            // Fallback al sistema original
            console.log(`${type.toUpperCase()}: ${message}`);
        }
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
            existingCount: this.images.filter(img => img.type === 'existing').length,
            coverSlot: this.currentCoverSlot,
            hasCover: this.images.some(img => img.isCover)
        };
    },

    getCoverImage: function() {
        return this.images.find(img => img.isCover);
    },

    getNewImages: function() {
        return this.images.filter(img => img.type === 'new');
    },

    getExistingImages: function() {
        return this.images.filter(img => img.type === 'existing');
    }
};

// ===== INICIALIZACIÓN =====

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎬 DOM listo, inicializando galería en 100ms...');

    setTimeout(() => {
        try {
            LaptopGalleryHybrid.init();

            // Debug: mostrar estado inicial
            console.log('📊 Estado inicial de la galería:', LaptopGalleryHybrid.getState());

            // Verificar opciones de eliminación de fondo
            const removeBgCover = document.getElementById('remove_bg_cover');
            const removeBgAll = document.getElementById('remove_bg_all');

            if (removeBgCover && removeBgAll) {
                console.log('🎨 Opciones de eliminación de fondo disponibles');
            }
        } catch (error) {
            console.error('❌ Error al inicializar la galería:', error);
        }
    }, 100);
});

// Exponer globalmente para debugging e integración
window.LaptopGalleryHybrid = LaptopGalleryHybrid;
window.LaptopGallery = LaptopGalleryHybrid; // Alias para compatibilidad
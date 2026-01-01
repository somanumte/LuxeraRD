// ============================================
// GALERÍA DE IMÁGENES CON DRAG & DROP
// ============================================

const LaptopGallery = {
    draggedSlot: null,
    totalImages: 0,
    imageConfig: {
        maxSize: 5 * 1024 * 1024, // 5MB
        validTypes: ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif']
    },

    // Inicializar galería
    init: function() {
        this.initDragDrop();
        this.initEventListeners();
        this.updateImageCounter();
        this.initExistingImages();
    },

    // Inicializar drag & drop
    initDragDrop: function() {
        const dropZone = document.getElementById('drop-zone');
        const dragOverlay = document.getElementById('drag-overlay');

        if (!dropZone || !dragOverlay) return;

        // Eventos para el área de drop
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        // Resaltar área de drop
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.highlightDropZone.bind(this), false);
            document.body.addEventListener(eventName, this.highlightBody.bind(this), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.unhighlightDropZone.bind(this), false);
            document.body.addEventListener(eventName, this.unhighlightBody.bind(this), false);
        });

        // Manejar drop
        dropZone.addEventListener('drop', this.handleDrop.bind(this), false);
        document.body.addEventListener('drop', this.handleBodyDrop.bind(this), false);

        // Configurar click en área de drop
        dropZone.addEventListener('click', (e) => {
            if (e.target === dropZone || !e.target.closest('button')) {
                document.getElementById('bulk-upload').click();
            }
        });
    },

    // Inicializar event listeners
    initEventListeners: function() {
        const bulkUpload = document.getElementById('bulk-upload');
        if (bulkUpload) {
            bulkUpload.addEventListener('change', this.handleBulkUpload.bind(this));
        }

        // Inicializar eventos de drag & drop para cada slot
        for (let i = 1; i <= 8; i++) {
            const container = document.getElementById(`image-container-${i}`);
            if (container) {
                container.addEventListener('dragstart', (e) => this.dragStart(e, i));
                container.addEventListener('dragover', this.allowDrop);
                container.addEventListener('drop', (e) => this.drop(e, i));
                container.addEventListener('dragend', this.dragEnd.bind(this));

                // Botón eliminar
                const removeBtn = document.getElementById(`remove-btn-${i}`);
                if (removeBtn) {
                    removeBtn.addEventListener('click', () => this.removeImage(i));
                }

                // Input file individual
                const input = document.getElementById(`image_${i}`);
                if (input) {
                    input.addEventListener('change', (e) => this.handleSingleUpload(e, i));
                }
            }
        }
    },

    // Inicializar imágenes existentes
    initExistingImages: function() {
        for (let i = 1; i <= 8; i++) {
            const preview = document.getElementById(`preview-${i}`);
            const removeBtn = document.getElementById(`remove-btn-${i}`);
            if (preview && preview.classList.contains('visible') && removeBtn) {
                removeBtn.classList.add('visible');
            }
        }
    },

    // Manejar drop de imágenes
    handleDrop: function(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    },

    handleBodyDrop: function(e) {
        if (!e.target.closest('#drop-zone')) {
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

    // Manejar carga individual
    handleSingleUpload: function(e, slot) {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            if (this.validateImageFile(file)) {
                this.uploadToSlot(file, slot);
            } else {
                e.target.value = '';
            }
        }
    },

    // Procesar archivos
    handleFiles: function(files) {
        const fileArray = Array.from(files).slice(0, 8 - this.totalImages);
        let currentSlot = 1;

        fileArray.forEach((file) => {
            if (currentSlot <= 8 && this.validateImageFile(file)) {
                // Encontrar el siguiente slot vacío
                while (currentSlot <= 8) {
                    const preview = document.getElementById(`preview-${currentSlot}`);
                    if (!preview.classList.contains('visible')) {
                        this.uploadToSlot(file, currentSlot);
                        currentSlot++;
                        break;
                    }
                    currentSlot++;
                }
            }
        });

        this.updateImageCounter();
    },

    // Subir imagen a slot específico
    uploadToSlot: function(file, slot) {
        const input = document.getElementById(`image_${slot}`);
        const preview = document.getElementById(`preview-${slot}`);
        const placeholder = document.getElementById(`placeholder-${slot}`);
        const container = document.getElementById(`image-container-${slot}`);
        const removeBtn = document.getElementById(`remove-btn-${slot}`);

        if (!input || !preview || !placeholder || !container) return;

        // Asignar archivo al input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        input.files = dataTransfer.files;

        // Mostrar preview
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.src = e.target.result;
            preview.classList.add('visible');
            placeholder.classList.add('hidden');
            container.classList.add('has-image');
            if (removeBtn) {
                removeBtn.classList.add('visible');
            }
        };
        reader.readAsDataURL(file);
    },

    // Funciones para drag & drop entre slots
    dragStart: function(e, slot) {
        const container = document.getElementById(`image-container-${slot}`);
        const preview = document.getElementById(`preview-${slot}`);

        if (!preview.classList.contains('visible')) {
            e.preventDefault();
            return;
        }

        this.draggedSlot = slot;
        e.dataTransfer.setData('text/plain', slot);
        e.dataTransfer.effectAllowed = 'move';

        if (container) {
            container.classList.add('dragging');
        }
    },

    allowDrop: function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    },

    drop: function(e, targetSlot) {
        e.preventDefault();

        if (this.draggedSlot && this.draggedSlot !== targetSlot) {
            this.swapImages(this.draggedSlot, targetSlot);
            this.updateImageCounter();
        }

        this.dragEnd();
    },

    dragEnd: function() {
        if (this.draggedSlot) {
            const container = document.getElementById(`image-container-${this.draggedSlot}`);
            if (container) {
                container.classList.remove('dragging');
            }
            this.draggedSlot = null;
        }
    },

    // Intercambiar imágenes entre dos slots
    swapImages: function(slot1, slot2) {
        const input1 = document.getElementById(`image_${slot1}`);
        const input2 = document.getElementById(`image_${slot2}`);
        const preview1 = document.getElementById(`preview-${slot1}`);
        const preview2 = document.getElementById(`preview-${slot2}`);
        const placeholder1 = document.getElementById(`placeholder-${slot1}`);
        const placeholder2 = document.getElementById(`placeholder-${slot2}`);
        const container1 = document.getElementById(`image-container-${slot1}`);
        const container2 = document.getElementById(`image-container-${slot2}`);
        const removeBtn1 = document.getElementById(`remove-btn-${slot1}`);
        const removeBtn2 = document.getElementById(`remove-btn-${slot2}`);
        const alt1 = document.getElementById(`image_${slot1}_alt`);
        const alt2 = document.getElementById(`image_${slot2}_alt`);

        if (!input1 || !input2 || !preview1 || !preview2) return;

        // Guardar valores temporales
        const tempFiles = input1.files;
        const tempSrc = preview1.src;
        const tempAlt = alt1 ? alt1.value : '';
        const tempHasImage = preview1.classList.contains('visible');
        const tempHasImage2 = preview2.classList.contains('visible');

        // Mover slot1 a slot2
        input1.files = input2.files;
        preview1.src = preview2.src;
        if (alt1 && alt2) alt1.value = alt2.value;

        if (tempHasImage2) {
            preview1.classList.add('visible');
            placeholder1.classList.add('hidden');
            container1.classList.add('has-image');
            if (removeBtn1) removeBtn1.classList.add('visible');
        } else {
            preview1.classList.remove('visible');
            placeholder1.classList.remove('hidden');
            container1.classList.remove('has-image');
            if (removeBtn1) removeBtn1.classList.remove('visible');
        }

        // Mover temporales a slot2
        input2.files = tempFiles;
        preview2.src = tempSrc;
        if (alt2) alt2.value = tempAlt;

        if (tempHasImage) {
            preview2.classList.add('visible');
            placeholder2.classList.add('hidden');
            container2.classList.add('has-image');
            if (removeBtn2) removeBtn2.classList.add('visible');
        } else {
            preview2.classList.remove('visible');
            placeholder2.classList.remove('hidden');
            container2.classList.remove('has-image');
            if (removeBtn2) removeBtn2.classList.remove('visible');
        }
    },

    // Actualizar contador de imágenes
    updateImageCounter: function() {
        let count = 0;
        for (let i = 1; i <= 8; i++) {
            const preview = document.getElementById(`preview-${i}`);
            if (preview && preview.classList.contains('visible')) {
                count++;
            }
        }
        const counter = document.getElementById('image-counter');
        if (counter) {
            counter.textContent = count;
        }
        this.totalImages = count;
    },

    // Eliminar imagen específica
    removeImage: function(slot) {
        const input = document.getElementById(`image_${slot}`);
        const preview = document.getElementById(`preview-${slot}`);
        const placeholder = document.getElementById(`placeholder-${slot}`);
        const container = document.getElementById(`image-container-${slot}`);
        const removeBtn = document.getElementById(`remove-btn-${slot}`);
        const altInput = document.getElementById(`image_${slot}_alt`);

        // Resetear valores
        if (input) input.value = '';
        if (preview) {
            preview.src = '';
            preview.classList.remove('visible');
        }
        if (placeholder) placeholder.classList.remove('hidden');
        if (container) container.classList.remove('has-image');
        if (removeBtn) removeBtn.classList.remove('visible');
        if (altInput) altInput.value = '';

        this.updateImageCounter();
    },

    // Limpiar todas las imágenes
    clearAllImages: function() {
        if (confirm('¿Estás seguro de que quieres eliminar todas las imágenes?')) {
            for (let i = 1; i <= 8; i++) {
                this.removeImage(i);
            }
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

    // Mostrar error
    showImageError: function(message) {
        alert(message);
    },

    // Funciones auxiliares para eventos
    preventDefaults: function(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    highlightDropZone: function() {
        const dropZone = document.getElementById('drop-zone');
        if (dropZone) {
            dropZone.classList.add('dragover');
        }
    },

    unhighlightDropZone: function() {
        const dropZone = document.getElementById('drop-zone');
        if (dropZone) {
            dropZone.classList.remove('dragover');
        }
    },

    highlightBody: function() {
        const dragOverlay = document.getElementById('drag-overlay');
        if (dragOverlay) {
            dragOverlay.classList.add('visible');
        }
    },

    unhighlightBody: function() {
        const dragOverlay = document.getElementById('drag-overlay');
        if (dragOverlay) {
            dragOverlay.classList.remove('visible');
        }
    }
};

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    LaptopGallery.init();
});

// Exponer para uso global
window.laptopGallery = LaptopGallery;
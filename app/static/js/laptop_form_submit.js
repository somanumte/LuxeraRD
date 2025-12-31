// ============================================
// MANEJO DE ENVIO DE FORMULARIO DE LAPTOPS
// ============================================

$(document).ready(function() {
    var isSubmitting = false;

    $('#laptop-form').on('submit', function(e) {
        if (isSubmitting) {
            return true;
        }

        e.preventDefault();
        var form = $(this);
        var submitBtn = form.find('[type="submit"]');
        var originalText = submitBtn.val() || 'Guardar Laptop';

        // Validar que display_name no este vacio
        var displayNameVal = $('#display_name').val();
        if (!displayNameVal || displayNameVal.trim() === '') {
            alert('Por favor selecciona al menos Marca y Modelo para generar el nombre comercial.');
            return false;
        }

        submitBtn.prop('disabled', true).val('Guardando...');

        // Recolectar campos que necesitan crear nuevos items
        var fieldsToProcess = [
            { selector: '#brand_id', endpoint: '/api/catalog/brands' },
            { selector: '#model_id', endpoint: '/api/catalog/models', extraData: function() {
                var brandId = $('#brand_id').val();
                return brandId && !brandId.toString().startsWith('new:') ? { brand_id: brandId } : {};
            }},
            { selector: '#processor_id', endpoint: '/api/catalog/processors' },
            { selector: '#os_id', endpoint: '/api/catalog/operating-systems' },
            { selector: '#screen_id', endpoint: '/api/catalog/screens' },
            { selector: '#graphics_card_id', endpoint: '/api/catalog/graphics-cards' },
            { selector: '#storage_id', endpoint: '/api/catalog/storage' },
            { selector: '#ram_id', endpoint: '/api/catalog/ram' },
            { selector: '#store_id', endpoint: '/api/catalog/stores' },
            { selector: '#location_id', endpoint: '/api/catalog/locations' },
            { selector: '#supplier_id', endpoint: '/api/catalog/suppliers' }
        ];

        // Filtrar solo los que tienen valores nuevos
        var newItemsToCreate = [];
        for (var i = 0; i < fieldsToProcess.length; i++) {
            var field = fieldsToProcess[i];
            var value = $(field.selector).val();
            if (value && value.toString().startsWith('new:')) {
                newItemsToCreate.push(field);
            }
        }

        // Si no hay items nuevos, enviar directamente
        if (newItemsToCreate.length === 0) {
            isSubmitting = true;
            form[0].submit();
            return;
        }

        // Crear items nuevos secuencialmente
        var createNextItem = function(index) {
            if (index >= newItemsToCreate.length) {
                // Todos creados, enviar formulario
                isSubmitting = true;
                form[0].submit();
                return;
            }

            var field = newItemsToCreate[index];
            var value = $(field.selector).val();
            var newName = value.substring(4); // Quitar 'new:'
            var postData = { name: newName };

            if (field.extraData) {
                $.extend(postData, field.extraData());
            }

            $.ajax({
                url: field.endpoint,
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(postData),
                success: function(response) {
                    if (response && response.id) {
                        // Actualizar el campo con el nuevo ID
                        $(field.selector).val(response.id).trigger('change');
                    }
                    createNextItem(index + 1);
                },
                error: function(xhr, status, error) {
                    console.error('Error creando item:', error);
                    alert('Error al crear: ' + newName + '. Intente de nuevo.');
                    submitBtn.prop('disabled', false).val(originalText);
                    isSubmitting = false;
                }
            });
        };

        // Iniciar creacion de items
        createNextItem(0);
    });
});
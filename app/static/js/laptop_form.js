// ============================================
// FORMULARIO DE LAPTOPS - FUNCIONALIDAD
// ============================================

$(document).ready(function() {
    // ===== CONFIGURACION DE SELECT2 CON TAGS =====
    function initSelect2WithTags(selector, endpoint, placeholder) {
        $(selector).select2({
            tags: true,
            placeholder: placeholder || 'Selecciona o escribe para crear...',
            allowClear: true,
            width: '100%',
            ajax: {
                url: endpoint,
                dataType: 'json',
                delay: 250,
                data: function(params) {
                    return {
                        q: params.term || '',
                        page: params.page || 1
                    };
                },
                processResults: function(data, params) {
                    params.page = params.page || 1;
                    return {
                        results: data.results,
                        pagination: {
                            more: data.pagination && data.pagination.more
                        }
                    };
                },
                cache: true
            },
            createTag: function(params) {
                var term = $.trim(params.term);
                if (term === '') {
                    return null;
                }
                return {
                    id: 'new:' + term,
                    text: '+ Crear: "' + term + '"',
                    newTag: true
                };
            }
        });
    }

    // ===== INICIALIZAR CAMPOS SELECT2 =====
    initSelect2WithTags('#brand_id', '/api/catalog/brands', 'Selecciona o crea una marca...');

    $('#model_id').select2({
        tags: true,
        placeholder: 'Primero selecciona una marca...',
        allowClear: true,
        width: '100%',
        ajax: {
            url: '/api/catalog/models',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                var brandId = $('#brand_id').val();
                return {
                    q: params.term || '',
                    page: params.page || 1,
                    brand_id: brandId && !brandId.toString().startsWith('new:') ? brandId : ''
                };
            },
            processResults: function(data, params) {
                params.page = params.page || 1;
                return {
                    results: data.results,
                    pagination: {
                        more: data.pagination && data.pagination.more
                    }
                };
            },
            cache: true
        },
        createTag: function(params) {
            var term = $.trim(params.term);
            if (term === '') {
                return null;
            }
            return {
                id: 'new:' + term,
                text: '+ Crear: "' + term + '"',
                newTag: true
            };
        }
    });

    // Cuando cambia la marca, limpiar el modelo
    $('#brand_id').on('change', function() {
        var brandVal = $(this).val();
        $('#model_id').val(null).trigger('change');

        if (brandVal && !brandVal.toString().startsWith('new:')) {
            $('#model_id').data('select2').options.options.placeholder = 'Selecciona o crea un modelo...';
        } else {
            $('#model_id').data('select2').options.options.placeholder = 'Primero selecciona una marca...';
        }
    });

    // Otros campos de catalogo
    initSelect2WithTags('#processor_id', '/api/catalog/processors', 'Selecciona o crea un procesador...');
    initSelect2WithTags('#os_id', '/api/catalog/operating-systems', 'Selecciona o crea un SO...');
    initSelect2WithTags('#screen_id', '/api/catalog/screens', 'Selecciona o crea una pantalla...');
    initSelect2WithTags('#graphics_card_id', '/api/catalog/graphics-cards', 'Selecciona o crea una GPU...');
    initSelect2WithTags('#storage_id', '/api/catalog/storage', 'Selecciona o crea almacenamiento...');
    initSelect2WithTags('#ram_id', '/api/catalog/ram', 'Selecciona o crea RAM...');
    initSelect2WithTags('#store_id', '/api/catalog/stores', 'Selecciona o crea una tienda...');
    initSelect2WithTags('#location_id', '/api/catalog/locations', 'Selecciona o crea una ubicacion...');
    initSelect2WithTags('#supplier_id', '/api/catalog/suppliers', 'Selecciona o crea un proveedor...');

    // ===== GENERAR DISPLAY_NAME AUTOMATICAMENTE =====
    function generateDisplayName() {
        var parts = [];

        // Obtener texto de cada campo Select2
        var brand = $('#brand_id').select2('data')[0];
        var model = $('#model_id').select2('data')[0];
        var processor = $('#processor_id').select2('data')[0];
        var ram = $('#ram_id').select2('data')[0];
        var storage = $('#storage_id').select2('data')[0];
        var screen = $('#screen_id').select2('data')[0];
        var category = $('#category').val();

        // Agregar marca
        if (brand && brand.text && brand.id != 0) {
            var brandText = brand.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(brandText);
        }

        // Agregar modelo
        if (model && model.text && model.id != 0) {
            var modelText = model.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(modelText);
        }

        // Agregar procesador
        if (processor && processor.text && processor.id != 0) {
            var processorText = processor.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(processorText);
        }

        // Agregar RAM
        if (ram && ram.text && ram.id != 0) {
            var ramText = ram.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(ramText);
        }

        // Agregar almacenamiento
        if (storage && storage.text && storage.id != 0) {
            var storageText = storage.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(storageText);
        }

        // Agregar pantalla
        if (screen && screen.text && screen.id != 0) {
            var screenText = screen.text.replace('+ Crear: "', '').replace('"', '');
            parts.push(screenText);
        }

        // Agregar categoria
        if (category) {
            var categoryLabels = {
                'laptop': 'Laptop',
                'workstation': 'Workstation',
                'gaming': 'Gaming'
            };
            if (categoryLabels[category]) {
                parts.push(categoryLabels[category]);
            }
        }

        // Generar nombre
        var displayName = parts.join(' - ');
        $('#display_name').val(displayName);
    }

    // Escuchar cambios en los campos
    $('#brand_id, #model_id, #processor_id, #ram_id, #storage_id, #screen_id, #category').on('change', function() {
        generateDisplayName();
    });

    // Generar al cargar
    setTimeout(generateDisplayName, 100);

    // ===== CALCULAR MARGEN AUTOMATICAMENTE =====
    function calculateMargin() {
        var purchaseCost = parseFloat($('#purchase_cost').val()) || 0;
        var salePrice = parseFloat($('#sale_price').val()) || 0;

        if (salePrice > 0 && purchaseCost > 0) {
            var profit = salePrice - purchaseCost;
            var margin = (profit / salePrice) * 100;

            $('#margin-display').text(margin.toFixed(1) + '%');
            $('#profit-display').text('Ganancia: $' + profit.toFixed(2));

            // Cambiar color segun el margen
            $('#margin-display').removeClass('text-green-600 text-yellow-600 text-red-600 dark:text-green-400 dark:text-yellow-400 dark:text-red-400');
            if (margin < 15) {
                $('#margin-display').addClass('text-red-600 dark:text-red-400');
            } else if (margin < 25) {
                $('#margin-display').addClass('text-yellow-600 dark:text-yellow-400');
            } else {
                $('#margin-display').addClass('text-green-600 dark:text-green-400');
            }
        } else {
            $('#margin-display').text('0%').removeClass('text-yellow-600 text-red-600 dark:text-yellow-400 dark:text-red-400').addClass('text-green-600 dark:text-green-400');
            $('#profit-display').text('Ganancia: $0.00');
        }
    }

    $('#purchase_cost, #sale_price').on('input', calculateMargin);
    calculateMargin();
});
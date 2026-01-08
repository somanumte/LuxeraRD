// API Client para Gastos
class ExpensesAPI {
    constructor() {
        this.baseURL = '/expenses/api';
        this.cache = {
            expenses: null,
            categories: null,
            dashboard: null,
            notifications: null,
            lastUpdated: null
        };
    }

    // ========== Métodos Helper ==========
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    errorData = { error: `Error ${response.status}: ${response.statusText}` };
                }
                throw new Error(errorData.error || `Error ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // ========== Métodos para Gastos ==========

    // Obtener todos los gastos del usuario (con filtros opcionales)
    async getExpenses(filters = {}) {
        const params = new URLSearchParams();

        Object.keys(filters).forEach(key => {
            if (filters[key] !== undefined && filters[key] !== '') {
                params.append(key, filters[key]);
            }
        });

        const endpoint = `/expenses${params.toString() ? `?${params.toString()}` : ''}`;
        const data = await this.request(endpoint);

        // Cachear los resultados
        this.cache.expenses = data;
        this.cache.lastUpdated = new Date();

        return data;
    }

    // Obtener un gasto específico
    async getExpense(id) {
        return await this.request(`/expenses/${id}`);
    }

    // Crear un nuevo gasto
    async createExpense(expenseData) {
        // Si es un FormData, enviar como multipart/form-data
        if (expenseData instanceof FormData) {
            return await fetch('/expenses/create', {
                method: 'POST',
                body: expenseData,
                credentials: 'same-origin'
            });
        }

        // Si es un objeto JSON, enviar como JSON
        return await this.request('/expenses/create', {
            method: 'POST',
            body: JSON.stringify(expenseData)
        });
    }

    // Actualizar un gasto existente
    async updateExpense(id, expenseData) {
        return await this.request(`/expenses/${id}`, {
            method: 'PUT',
            body: JSON.stringify(expenseData)
        });
    }

    // Eliminar un gasto
    async deleteExpense(id) {
        return await this.request(`/expenses/${id}`, {
            method: 'DELETE'
        });
    }

    // Marcar gasto como pagado
    async markAsPaid(id) {
        return await this.request(`/expenses/${id}/paid`, {
            method: 'POST'
        });
    }

    // Marcar gasto como pendiente
    async markAsPending(id) {
        return await this.request(`/expenses/${id}/pending`, {
            method: 'POST'
        });
    }

    // Acciones en lote
    async bulkAction(action, expenseIds) {
        return await this.request('/expenses/bulk', {
            method: 'POST',
            body: JSON.stringify({
                action: action,
                expense_ids: expenseIds
            })
        });
    }

    // ========== Métodos para Categorías ==========

    // Obtener todas las categorías
    async getCategories() {
        // Usar cache si los datos son recientes
        const now = new Date();
        if (this.cache.categories && this.cache.lastUpdated &&
            (now - this.cache.lastUpdated) < 5 * 60 * 1000) {
            return this.cache.categories;
        }

        const data = await this.request('/categories');
        this.cache.categories = data;
        this.cache.lastUpdated = now;
        return data;
    }

    // Obtener una categoría específica
    async getCategory(id) {
        return await this.request(`/categories/${id}`);
    }

    // Crear una nueva categoría
    async createCategory(categoryData) {
        return await this.request('/categories', {
            method: 'POST',
            body: JSON.stringify(categoryData)
        });
    }

    // ========== Métodos para Dashboard y Analíticas ==========

    // Datos del dashboard con gráficos
    async getDashboardData() {
        // Usar cache si los datos son recientes (menos de 5 minutos)
        const now = new Date();
        if (this.cache.dashboard && this.cache.lastUpdated &&
            (now - this.cache.lastUpdated) < 5 * 60 * 1000) {
            return this.cache.dashboard;
        }

        const data = await this.request('/dashboard');
        this.cache.dashboard = data;
        this.cache.lastUpdated = now;
        return data;
    }

    // Resumen para tarjetas
    async getSummary() {
        return await this.request('/expenses/summary');
    }

    // Notificaciones
    async getNotifications() {
        const data = await this.request('/notifications');
        this.cache.notifications = data;
        return data;
    }

    // Búsqueda
    async search(query, filters = {}) {
        const params = new URLSearchParams({ q: query, ...filters });
        return await this.request(`/search?${params.toString()}`);
    }

    // Análisis mensual
    async getMonthlyAnalytics(year = null) {
        const params = new URLSearchParams();
        if (year) params.append('year', year);
        return await this.request(`/analytics/monthly?${params.toString()}`);
    }

    // Estadísticas por categoría
    async getCategoriesStats(startDate = null, endDate = null) {
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        return await this.request(`/categories/stats?${params.toString()}`);
    }

    // ========== Métodos Específicos ==========

    // Marcar múltiples gastos como pagados
    async markAsPaidBulk(expenseIds) {
        return await this.bulkAction('mark_paid', expenseIds);
    }

    // Marcar múltiples gastos como pendientes
    async markAsPendingBulk(expenseIds) {
        return await this.bulkAction('mark_pending', expenseIds);
    }

    // Eliminar múltiples gastos
    async deleteBulk(expenseIds) {
        return await this.bulkAction('delete', expenseIds);
    }

    // Obtener próximos vencimientos
    async getUpcomingExpenses(days = 7) {
        const notifications = await this.getNotifications();
        return notifications.upcoming || [];
    }

    // Obtener gastos vencidos
    async getOverdueExpenses() {
        const notifications = await this.getNotifications();
        return notifications.overdue || [];
    }

    // Exportar gastos a CSV
    async exportExpenses() {
        try {
            const response = await fetch('/expenses/export', {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }

            // Crear un blob con la respuesta y descargar
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `gastos_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            return { success: true, message: 'Exportación completada' };
        } catch (error) {
            console.error('Error en exportación:', error);
            throw error;
        }
    }

    // ========== Métodos de Utilidad ==========

    // Formatear moneda
    formatCurrency(amount) {
        return new Intl.NumberFormat('es-DO', {
            style: 'currency',
            currency: 'DOP',
            minimumFractionDigits: 2
        }).format(amount);
    }

    // Formatear fecha
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-DO', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    // Formatear fecha completa
    formatDateTime(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('es-DO', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Calcular días hasta/hasta que
    calculateDays(dateString) {
        if (!dateString) return 0;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const targetDate = new Date(dateString);
        targetDate.setHours(0, 0, 0, 0);

        const diffTime = targetDate - today;
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    // Obtener estado del gasto
    getExpenseStatus(expense) {
        if (expense.is_paid) {
            return { status: 'paid', label: 'Pagado', color: 'green', class: 'success' };
        }

        const days = this.calculateDays(expense.due_date);
        if (days < 0) {
            return { status: 'overdue', label: 'Vencido', color: 'red', class: 'danger' };
        } else if (days <= 7) {
            return { status: 'urgent', label: 'Próximo', color: 'orange', class: 'warning' };
        } else {
            return { status: 'pending', label: 'Pendiente', color: 'blue', class: 'info' };
        }
    }

    // Generar colores para gráficos
    generateChartColors(count) {
        const baseColors = [
            '#2D64B3', '#4CAF50', '#FF6B35', '#9C27B0', '#FF9800',
            '#2196F3', '#F44336', '#009688', '#673AB7', '#FF5722',
            '#795548', '#607D8B', '#00BCD4', '#CDDC39', '#E91E63'
        ];

        if (count <= baseColors.length) {
            return baseColors.slice(0, count);
        }

        // Generar colores adicionales si es necesario
        const additionalColors = [];
        for (let i = baseColors.length; i < count; i++) {
            const hue = (i * 137.508) % 360; // Usar ángulo dorado
            additionalColors.push(`hsl(${hue}, 70%, 65%)`);
        }

        return [...baseColors, ...additionalColors];
    }

    // Crear gradiente para gráficos
    createGradient(ctx, color1, color2) {
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        return gradient;
    }

    // Validar datos de gasto
    validateExpenseData(data) {
        const errors = [];

        if (!data.description || data.description.trim().length < 3) {
            errors.push('La descripción debe tener al menos 3 caracteres');
        }

        if (!data.amount || data.amount <= 0) {
            errors.push('El monto debe ser mayor a 0');
        }

        if (!data.category_id) {
            errors.push('La categoría es requerida');
        }

        if (!data.due_date) {
            errors.push('La fecha de vencimiento es requerida');
        } else {
            const dueDate = new Date(data.due_date);
            const today = new Date();
            today.setHours(0, 0, 0, 0);

            if (dueDate < today && !data.is_paid) {
                errors.push('La fecha de vencimiento no puede ser en el pasado para gastos pendientes');
            }
        }

        if (data.is_recurring && !data.frequency) {
            errors.push('La frecuencia es requerida para gastos recurrentes');
        }

        return errors;
    }

    // Refrescar cache
    refreshCache() {
        this.cache = {
            expenses: null,
            categories: null,
            dashboard: null,
            notifications: null,
            lastUpdated: null
        };
    }

    // Manejar errores de API
    handleApiError(error, defaultMessage = 'Error en la solicitud') {
        console.error('API Error Details:', error);

        let userMessage = defaultMessage;

        if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
            userMessage = 'Error de conexión. Verifica tu conexión a internet.';
        } else if (error.message.includes('403')) {
            userMessage = 'No tienes permiso para realizar esta acción.';
        } else if (error.message.includes('404')) {
            userMessage = 'Recurso no encontrado.';
        } else if (error.message.includes('500')) {
            userMessage = 'Error interno del servidor. Intenta nuevamente más tarde.';
        }

        return {
            success: false,
            error: error.message,
            userMessage: userMessage
        };
    }

    // Retry con backoff exponencial
    async retryRequest(endpoint, options, maxRetries = 3, baseDelay = 1000) {
        let lastError;

        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await this.request(endpoint, options);
            } catch (error) {
                lastError = error;

                // No reintentar si es un error 4xx (excepto 429 - Too Many Requests)
                if (error.message.includes('4') && !error.message.includes('429')) {
                    throw error;
                }

                // Calcular delay exponencial con jitter
                const delay = baseDelay * Math.pow(2, attempt - 1) + Math.random() * 1000;

                if (attempt < maxRetries) {
                    console.warn(`Intento ${attempt} fallido, reintentando en ${delay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
            }
        }

        throw lastError;
    }

    // ========== Métodos de Cache ==========

    // Verificar si los datos en cache son válidos
    isCacheValid(cacheKey, maxAgeMinutes = 5) {
        if (!this.cache[cacheKey] || !this.cache.lastUpdated) {
            return false;
        }

        const now = new Date();
        const cacheAge = now - this.cache.lastUpdated;
        return cacheAge < maxAgeMinutes * 60 * 1000;
    }

    // Actualizar cache específico
    updateCache(cacheKey, data) {
        this.cache[cacheKey] = data;
        this.cache.lastUpdated = new Date();
    }

    // Limpiar cache específico
    clearCache(cacheKey) {
        this.cache[cacheKey] = null;
    }

    // ========== Métodos de UI Helper ==========

    // Crear badge de estado
    createStatusBadge(status) {
        const statusConfig = {
            paid: { text: 'Pagado', class: 'bg-green-100 text-green-800', icon: '✓' },
            pending: { text: 'Pendiente', class: 'bg-yellow-100 text-yellow-800', icon: '⏱' },
            overdue: { text: 'Vencido', class: 'bg-red-100 text-red-800', icon: '⚠' },
            urgent: { text: 'Urgente', class: 'bg-orange-100 text-orange-800', icon: '🚨' }
        };

        const config = statusConfig[status] || statusConfig.pending;
        return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.class}">
            ${config.icon ? `<span class="mr-1">${config.icon}</span>` : ''}
            ${config.text}
        </span>`;
    }

    // Crear chip de categoría
    createCategoryChip(category) {
        const color = category.color || '#6B7280';
        return `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" style="background-color: ${color}20; color: ${color}; border: 1px solid ${color}40;">
            ${category.name}
        </span>`;
    }

    // Formatear fecha relativa
    formatRelativeDate(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));

        if (diffDays === 0) {
            return 'Hoy';
        } else if (diffDays === 1) {
            return 'Ayer';
        } else if (diffDays < 7) {
            return `Hace ${diffDays} días`;
        } else if (diffDays < 30) {
            const weeks = Math.floor(diffDays / 7);
            return `Hace ${weeks} semana${weeks > 1 ? 's' : ''}`;
        } else if (diffDays < 365) {
            const months = Math.floor(diffDays / 30);
            return `Hace ${months} mes${months > 1 ? 'es' : ''}`;
        } else {
            const years = Math.floor(diffDays / 365);
            return `Hace ${years} año${years > 1 ? 's' : ''}`;
        }
    }
}

// Singleton instance
const expensesAPI = new ExpensesAPI();

// Exportar para uso global en el navegador
window.expensesAPI = expensesAPI;

// Configurar para módulos ES6
if (typeof module !== 'undefined' && module.exports) {
    module.exports = expensesAPI;
}

// Extender el prototype de Date para utilidades adicionales
if (!Date.prototype.addDays) {
    Date.prototype.addDays = function(days) {
        const date = new Date(this.valueOf());
        date.setDate(date.getDate() + days);
        return date;
    };
}

if (!Date.prototype.isToday) {
    Date.prototype.isToday = function() {
        const today = new Date();
        return this.getDate() === today.getDate() &&
               this.getMonth() === today.getMonth() &&
               this.getFullYear() === today.getFullYear();
    };
}

// Helper para formatear números con separadores de miles
if (!Number.prototype.formatNumber) {
    Number.prototype.formatNumber = function(decimals = 2) {
        return this.toLocaleString('es-DO', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    };
}

// Helper para formatear porcentaje
if (!Number.prototype.formatPercent) {
    Number.prototype.formatPercent = function(decimals = 1) {
        return `${this.toFixed(decimals)}%`;
    };
}

// Polyfill para Promise.allSettled (si no está disponible)
if (!Promise.allSettled) {
    Promise.allSettled = function(promises) {
        return Promise.all(promises.map(p => Promise.resolve(p).then(
            value => ({ status: 'fulfilled', value }),
            reason => ({ status: 'rejected', reason })
        )));
    };
}

// Configurar interceptores globales para fetch
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    // Agregar timestamp para evitar cache del navegador
    if (args[0].includes('/expenses/api/')) {
        const url = new URL(args[0], window.location.origin);
        url.searchParams.set('_t', Date.now());
        args[0] = url.toString();
    }

    try {
        const response = await originalFetch.apply(this, args);

        // Verificar si hay errores de autenticación
        if (response.status === 401) {
            window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
            return Promise.reject(new Error('No autenticado'));
        }

        // Verificar si hay errores de permisos
        if (response.status === 403) {
            console.warn('Acceso denegado:', args[0]);
            // Mostrar notificación al usuario
            if (window.showNotification) {
                window.showNotification('No tienes permiso para realizar esta acción', 'error');
            }
        }

        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
};

// Inicializar event listeners para errores de red
window.addEventListener('offline', () => {
    console.warn('La aplicación está offline');
    if (window.showNotification) {
        window.showNotification('Estás offline. Algunas funciones pueden no estar disponibles.', 'warning');
    }
});

window.addEventListener('online', () => {
    console.info('La aplicación está online nuevamente');
    if (window.showNotification) {
        window.showNotification('Conexión restablecida. Sincronizando datos...', 'success');
    }
    // Refrescar datos cuando se recupera la conexión
    if (expensesAPI) {
        expensesAPI.refreshCache();
    }
});

// Configurar para modo desarrollo
if (process.env.NODE_ENV === 'development') {
    // Habilitar logging detallado
    expensesAPI.debug = true;

    // Mock para pruebas (solo en desarrollo)
    expensesAPI.mock = {
        getExpenses: async () => {
            console.log('[MOCK] getExpenses');
            return {
                expenses: [],
                summary: { total_amount: 0, total_count: 0 }
            };
        }
    };
}

// Exportar funciones de ayuda para uso global
window.expensesHelper = {
    formatCurrency: expensesAPI.formatCurrency.bind(expensesAPI),
    formatDate: expensesAPI.formatDate.bind(expensesAPI),
    createStatusBadge: expensesAPI.createStatusBadge.bind(expensesAPI),
    createCategoryChip: expensesAPI.createCategoryChip.bind(expensesAPI)
};
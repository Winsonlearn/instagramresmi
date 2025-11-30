/**
 * Instagram Clone - Client-side Utilities
 * State management, caching, error handling, and UI helpers
 */

// ============================================================================
// STATE MANAGEMENT & CACHING
// ============================================================================

const AppState = {
    cache: new Map(),
    cacheTimeout: 5 * 60 * 1000, // 5 minutes
    
    /**
     * Set item in cache with expiration
     */
    setCache(key, value, timeout = null) {
        const expiry = timeout || this.cacheTimeout;
        this.cache.set(key, {
            value,
            expiry: Date.now() + expiry
        });
    },
    
    /**
     * Get item from cache if not expired
     */
    getCache(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        
        if (Date.now() > item.expiry) {
            this.cache.delete(key);
            return null;
        }
        
        return item.value;
    },
    
    /**
     * Clear expired cache entries
     */
    clearExpired() {
        const now = Date.now();
        for (const [key, item] of this.cache.entries()) {
            if (now > item.expiry) {
                this.cache.delete(key);
            }
        }
    },
    
    /**
     * Clear all cache
     */
    clearAll() {
        this.cache.clear();
    }
};

// Clean up expired cache every minute
setInterval(() => AppState.clearExpired(), 60 * 1000);

// ============================================================================
// ERROR HANDLING & RETRY MECHANISMS
// ============================================================================

const ErrorHandler = {
    /**
     * Retry a fetch request with exponential backoff
     */
    async retryFetch(url, options = {}, maxRetries = 3, delay = 1000) {
        for (let i = 0; i < maxRetries; i++) {
            try {
                const response = await fetch(url, options);
                if (response.ok) {
                    return response;
                }
                // Don't retry on client errors (4xx)
                if (response.status >= 400 && response.status < 500) {
                    throw new Error(`Client error: ${response.status}`);
                }
            } catch (error) {
                if (i === maxRetries - 1) throw error;
                // Exponential backoff
                await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
            }
        }
    },
    
    /**
     * Handle API errors gracefully
     */
    handleError(error, userMessage = 'An error occurred. Please try again.') {
        console.error('Error:', error);
        Toast.show(userMessage, 'error');
        return { error: userMessage };
    }
};

// ============================================================================
// TOAST NOTIFICATIONS
// ============================================================================

const Toast = {
    container: null,
    
    /**
     * Initialize toast container
     */
    init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(this.container);
        }
    },
    
    /**
     * Show toast notification
     */
    show(message, type = 'info', duration = 3000) {
        this.init();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        
        toast.style.cssText = `
            background: ${colors[type] || colors.info};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease-out;
            max-width: 350px;
            word-wrap: break-word;
        `;
        
        toast.textContent = message;
        this.container.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, duration);
        
        return toast;
    },
    
    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    },
    
    error(message, duration = 4000) {
        return this.show(message, 'error', duration);
    },
    
    warning(message, duration = 3000) {
        return this.show(message, 'warning', duration);
    },
    
    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }
};

// Add toast animations to head
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// LOADING STATES
// ============================================================================

const LoadingManager = {
    /**
     * Show loading overlay
     */
    show(target = document.body) {
        const loader = document.createElement('div');
        loader.className = 'loading-overlay';
        loader.id = 'app-loader';
        loader.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
            </div>
        `;
        loader.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        
        // Add spinner styles if not already present
        if (!document.getElementById('spinner-styles')) {
            const style = document.createElement('style');
            style.id = 'spinner-styles';
            style.textContent = `
                .loading-spinner .spinner {
                    width: 40px;
                    height: 40px;
                    border: 4px solid rgba(255, 255, 255, 0.3);
                    border-top-color: white;
                    border-radius: 50%;
                    animation: spin 0.8s linear infinite;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
        
        if (target === document.body) {
            target.style.position = 'relative';
        }
        target.appendChild(loader);
    },
    
    /**
     * Hide loading overlay
     */
    hide() {
        const loader = document.getElementById('app-loader');
        if (loader) {
            loader.remove();
        }
    }
};

// ============================================================================
// MODAL SYSTEM
// ============================================================================

const Modal = {
    /**
     * Show confirmation modal
     */
    confirm(title, message, onConfirm, onCancel) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>${title}</h3>
                <p>${message}</p>
                <div class="modal-actions">
                    <button class="modal-btn modal-btn-cancel">Cancel</button>
                    <button class="modal-btn modal-btn-confirm">Confirm</button>
                </div>
            </div>
        `;
        
        // Add modal styles if not already present
        if (!document.getElementById('modal-styles')) {
            const style = document.createElement('style');
            style.id = 'modal-styles';
            style.textContent = `
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 10000;
                    animation: fadeIn 0.2s ease-out;
                }
                .modal-content {
                    background: white;
                    padding: 24px;
                    border-radius: 12px;
                    max-width: 400px;
                    width: 90%;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    animation: slideUp 0.3s ease-out;
                }
                .modal-content h3 {
                    margin: 0 0 12px 0;
                    color: #1f2937;
                }
                .modal-content p {
                    margin: 0 0 20px 0;
                    color: #6b7280;
                }
                .modal-actions {
                    display: flex;
                    gap: 12px;
                    justify-content: flex-end;
                }
                .modal-btn {
                    padding: 8px 16px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-weight: 500;
                    transition: all 0.2s;
                }
                .modal-btn-cancel {
                    background: #f3f4f6;
                    color: #374151;
                }
                .modal-btn-cancel:hover {
                    background: #e5e7eb;
                }
                .modal-btn-confirm {
                    background: #ef4444;
                    color: white;
                }
                .modal-btn-confirm:hover {
                    background: #dc2626;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slideUp {
                    from {
                        transform: translateY(20px);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        const close = () => {
            modal.style.animation = 'fadeOut 0.2s ease-out';
            setTimeout(() => modal.remove(), 200);
        };
        
        modal.querySelector('.modal-btn-confirm').addEventListener('click', () => {
            if (onConfirm) onConfirm();
            close();
        });
        
        modal.querySelector('.modal-btn-cancel').addEventListener('click', () => {
            if (onCancel) onCancel();
            close();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                if (onCancel) onCancel();
                close();
            }
        });
        
        document.body.appendChild(modal);
    }
};

// ============================================================================
// IMAGE LAZY LOADING
// ============================================================================

const LazyLoader = {
    /**
     * Initialize lazy loading for images
     */
    init() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.classList.add('loaded');
                            img.removeAttribute('data-src');
                        }
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px'
            });
            
            // Observe all images with data-src
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        } else {
            // Fallback for older browsers
            document.querySelectorAll('img[data-src]').forEach(img => {
                img.src = img.dataset.src;
                img.classList.add('loaded');
            });
        }
    },
    
    /**
     * Create lazy-loaded image element
     */
    createImage(src, alt = '', className = '') {
        const img = document.createElement('img');
        img.className = className;
        img.alt = alt;
        img.dataset.src = src;
        img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E'; // Placeholder
        img.style.cssText = `
            background: #f3f4f6;
            transition: opacity 0.3s;
        `;
        img.classList.add('lazy-image');
        return img;
    }
};

// Initialize lazy loading when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => LazyLoader.init());
} else {
    LazyLoader.init();
}

// ============================================================================
// API HELPERS WITH CACHING
// ============================================================================

const API = {
    /**
     * Fetch with caching
     */
    async fetch(url, options = {}, useCache = true) {
        const cacheKey = `api_${url}_${JSON.stringify(options)}`;
        
        // Check cache first
        if (useCache) {
            const cached = AppState.getCache(cacheKey);
            if (cached) return cached;
        }
        
        try {
            const response = await ErrorHandler.retryFetch(url, options);
            const data = await response.json();
            
            // Cache successful responses
            if (useCache && response.ok) {
                AppState.setCache(cacheKey, data);
            }
            
            return data;
        } catch (error) {
            return ErrorHandler.handleError(error);
        }
    },
    
    /**
     * POST request with loading state
     */
    async post(url, data = {}, showLoading = true) {
        if (showLoading) LoadingManager.show();
        
        try {
            const formData = new FormData();
            for (const key in data) {
                formData.append(key, data[key]);
            }
            
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const result = await response.json();
            
            // Clear relevant cache
            AppState.clearExpired();
            
            return result;
        } catch (error) {
            return ErrorHandler.handleError(error);
        } finally {
            if (showLoading) LoadingManager.hide();
        }
    }
};

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================

const KeyboardShortcuts = {
    shortcuts: new Map(),
    
    /**
     * Register a keyboard shortcut
     */
    register(key, handler, preventDefault = true) {
        this.shortcuts.set(key.toLowerCase(), { handler, preventDefault });
    },
    
    /**
     * Initialize keyboard shortcuts
     */
    init() {
        document.addEventListener('keydown', (e) => {
            const key = `${e.ctrlKey || e.metaKey ? 'ctrl+' : ''}${e.shiftKey ? 'shift+' : ''}${e.key.toLowerCase()}`;
            const shortcut = this.shortcuts.get(key);
            
            if (shortcut) {
                if (shortcut.preventDefault) {
                    e.preventDefault();
                }
                shortcut.handler(e);
            }
        });
    },
    
    /**
     * Register default shortcuts
     */
    registerDefaults() {
        // Escape key closes modals
        this.register('Escape', () => {
            const modal = document.querySelector('.modal-overlay');
            if (modal) modal.remove();
        });
        
        // Ctrl/Cmd + K for search
        this.register('ctrl+k', () => {
            const searchLink = document.querySelector('a[href*="search"]');
            if (searchLink) searchLink.click();
        });
        
        // Ctrl/Cmd + N for new post
        this.register('ctrl+n', () => {
            const createLink = document.querySelector('a[href*="create"]');
            if (createLink) createLink.click();
        });
    }
};

// Initialize keyboard shortcuts
KeyboardShortcuts.init();
KeyboardShortcuts.registerDefaults();

// ============================================================================
// OFFLINE DETECTION
// ============================================================================

const OfflineManager = {
    init() {
        window.addEventListener('online', () => {
            Toast.success('You are back online!');
            // Sync any pending actions if needed
        });
        
        window.addEventListener('offline', () => {
            Toast.warning('You are offline. Some features may not work.');
        });
    }
};

OfflineManager.init();

// ============================================================================
// EXPORT FOR USE IN OTHER SCRIPTS
// ============================================================================

// Make utilities available globally
window.AppUtils = {
    AppState,
    ErrorHandler,
    Toast,
    LoadingManager,
    Modal,
    LazyLoader,
    API,
    KeyboardShortcuts,
    OfflineManager
};



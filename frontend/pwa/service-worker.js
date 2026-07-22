// ==========================================
// service-worker.js - Didasko AI
// Permite que la app funcione offline
// ==========================================

const CACHE_NAME = 'didasko-ai-v1.0.0';

// Archivos a guardar en caché
const ARCHIVOS_CACHE = [
    '/',
    '/index.html',
    '/css/style.css',
    '/css/bienvenida.css',
    '/css/secciones.css',
    '/css/responsive.css',
    '/css/animations.css',
    '/js/config.js',
    '/js/main.js',
    '/js/navegacion.js',
    '/js/chat.js',
    '/js/imagen.js',
    '/js/vision.js',
    '/js/video.js',
    '/js/publicidad.js',
    '/js/apoyar.js',
    '/assets/logo/buho-columna.png',
    '/assets/logo/buho-mascota.png',
    '/assets/logo/favicon/favicon.ico',
    '/assets/logo/favicon/favicon-16x16.png',
    '/assets/logo/favicon/favicon-32x32.png',
    '/assets/logo/favicon/apple-touch-icon.png',
    '/assets/logo/favicon/android-chrome-192x192.png',
    '/assets/logo/favicon/android-chrome-512x512.png',
    '/assets/fondos/fondo-circuito-web.png',
    '/assets/fondos/fondo-circuito-app.png',
    '/assets/pagos/paypal.png',
    '/assets/pagos/nequi.png',
    '/assets/iconos-app/icono-chat.png',
    '/assets/iconos-app/icono-imagen.png',
    '/assets/iconos-app/icono-vision.png',
    '/assets/iconos-app/icono-video.png',
    '/assets/iconos-app/icono-apoyar.png',
    '/pwa/manifest.json'
];

// ===================================
// INSTALACIÓN: Guardar archivos en caché
// ===================================
self.addEventListener('install', event => {
    console.log('🦉 Service Worker: Instalando...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Guardando archivos en caché...');
                return cache.addAll(ARCHIVOS_CACHE);
            })
            .then(() => {
                console.log('✅ Todos los archivos guardados en caché');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('❌ Error al guardar caché:', error);
            })
    );
});

// ===================================
// ACTIVACIÓN: Limpiar cachés viejos
// ===================================
self.addEventListener('activate', event => {
    console.log('🦉 Service Worker: Activando...');
    
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️ Eliminando caché viejo:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('✅ Service Worker activado');
            return self.clients.claim();
        })
    );
});

// ===================================
// FETCH: Interceptar peticiones
// ===================================
self.addEventListener('fetch', event => {
    // No interceptar peticiones al backend (API)
    if (event.request.url.includes('/api/')) {
        return;
    }
    
    // No interceptar peticiones que no sean GET
    if (event.request.method !== 'GET') {
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Si está en caché, devolverlo
                if (response) {
                    return response;
                }
                
                // Si no, hacer petición a la red
                return fetch(event.request)
                    .then(response => {
                        // Si la respuesta es válida, guardarla en caché
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        const responseClone = response.clone();
                        
                        caches.open(CACHE_NAME).then(cache => {
                            cache.put(event.request, responseClone);
                        });
                        
                        return response;
                    })
                    .catch(() => {
                        // Si falla y es una página HTML, devolver index
                        if (event.request.destination === 'document') {
                            return caches.match('/index.html');
                        }
                    });
            })
    );
});

// ===================================
// MENSAJES: Comunicación con la app
// ===================================
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CLEAR_CACHE') {
        caches.delete(CACHE_NAME).then(() => {
            console.log('🗑️ Caché limpiada');
        });
    }
});

console.log('🦉 Service Worker: Cargado');

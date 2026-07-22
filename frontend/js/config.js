// ==========================================
// config.js - Didasko AI
// Configuración global del frontend
// ==========================================

const CONFIG = {

    // 🌐 URL del backend
    // - Cuando pruebas local: 'http://localhost:5000'
    // - Cuando esté en Render: 'https://tu-app.onrender.com'
    // - Si el backend sirve el frontend: dejar vacío ''
    BACKEND_URL: '',

    // 📢 Configuración de publicidad
    AD_FREQUENCY: 3, // Cada 3 tareas muestra publicidad
    AD_WHATSAPP: '573171547065',
    AD_TEXT: '📢 ¿Quieres publicidad aquí? Contáctanos: +57 317 154 7065',

    // 🎯 Sesión del usuario (para memoria del chat)
    SESSION_ID: 'user_' + Math.random().toString(36).substr(2, 9),

    // ⏱️ Tiempo entre consultas de video (ms)
    VIDEO_POLL_INTERVAL: 10000, // 10 segundos

    // 🎨 Modo debug (muestra logs en consola)
    DEBUG: true
};

// Función auxiliar para construir URLs del backend
function apiUrl(endpoint) {
    return CONFIG.BACKEND_URL + endpoint;
}

// Log inicial
if (CONFIG.DEBUG) {
    console.log('🦉 Didasko AI - Configuración cargada');
    console.log('📍 Backend URL:', CONFIG.BACKEND_URL || '(mismo servidor)');
    console.log('🎫 Session ID:', CONFIG.SESSION_ID);
}
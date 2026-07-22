# ===================================
# app.py - Didasko AI
# Servidor principal Flask
# ===================================

import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

# ===================================
# Configuración de la app
# ===================================

# Ruta a la carpeta frontend (para servir HTML, CSS, JS)
FRONTEND_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'frontend')

# Crear la app Flask
app = Flask(
    __name__,
    static_folder=FRONTEND_FOLDER,
    static_url_path=''
)

# Configurar CORS (permite conexión frontend-backend)
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# ===================================
# Importar y registrar rutas (endpoints)
# ===================================

from routes.chat import chat_bp
from routes.imagen import imagen_bp
from routes.vision import vision_bp
from routes.video import video_bp

app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(imagen_bp, url_prefix='/api/imagen')
app.register_blueprint(vision_bp, url_prefix='/api/vision')
app.register_blueprint(video_bp, url_prefix='/api/video')

# ===================================
# Rutas para servir el frontend
# ===================================

@app.route('/')
def index():
    """Sirve la página principal (index.html)"""
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """Sirve archivos estáticos (CSS, JS, imágenes)"""
    return send_from_directory(FRONTEND_FOLDER, path)

# ===================================
# Endpoint de estado (health check)
# ===================================

@app.route('/api/status')
def status():
    """Verifica que el servidor esté funcionando"""
    return jsonify({
        'status': 'ok',
        'app': 'Didasko AI',
        'version': '1.0.0',
        'message': '🦉 Servidor funcionando correctamente'
    })

# ===================================
# Endpoint de configuración pública
# ===================================

@app.route('/api/config')
def config():
    """Devuelve configuración pública para el frontend (publicidad, etc)"""
    return jsonify({
        'ad_whatsapp': os.getenv('AD_WHATSAPP', '573171547065'),
        'ad_text': os.getenv('AD_TEXT', '📢 ¿Quieres publicidad aquí? Contáctanos: +57 317 154 7065'),
        'ad_frequency': 3  # Cada 3 tareas muestra publicidad
    })

# ===================================
# Manejo de errores
# ===================================

@app.errorhandler(404)
def not_found(e):
    """Si no encuentra la ruta, devuelve el index (para SPA)"""
    return send_from_directory(FRONTEND_FOLDER, 'index.html')

@app.errorhandler(500)
def server_error(e):
    return jsonify({
        'error': 'Error interno del servidor',
        'message': str(e)
    }), 500

# ===================================
# Iniciar servidor
# ===================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print("=" * 50)
    print("🦉 DIDASKO AI - Servidor iniciado")
    print(f"📍 Puerto: {port}")
    print(f"🔧 Modo: {'Desarrollo' if debug else 'Producción'}")
    print(f"🌐 URL local: http://localhost:{port}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
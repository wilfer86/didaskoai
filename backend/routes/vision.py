# ===================================
# vision.py - Endpoint de Análisis de Fotos
# ===================================
# Usa Gemini Vision para analizar imágenes
# Resuelve tareas fotografiadas
# ===================================

import os
import base64
from io import BytesIO
from flask import Blueprint, request, jsonify
import google.generativeai as genai
from PIL import Image

# Crear Blueprint para las rutas de visión
vision_bp = Blueprint('vision', __name__)

# ===================================
# Configurar Gemini
# ===================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ===================================
# Instrucción del sistema para análisis
# ===================================

VISION_INSTRUCTION = """
Eres Didasko AI 🦉, un tutor educativo que analiza imágenes académicas.

TU TAREA:
Analizar la imagen que te envía el estudiante y ayudarle según lo que pida.

TIPOS DE IMÁGENES QUE PUEDES ANALIZAR:
📐 Ejercicios de matemáticas (ecuaciones, geometría, cálculos)
📝 Textos, párrafos, preguntas
🧪 Diagramas científicos, fórmulas químicas
🗺️ Mapas, gráficos, tablas
🎨 Dibujos, diagramas
📚 Páginas de libros, hojas de tareas
📊 Ejercicios de cualquier materia

CÓMO RESPONDER:
1. Primero describe brevemente qué ves en la imagen
2. Luego resuelve o explica lo que el usuario pidió
3. Muestra el PROCESO paso a paso (no solo la respuesta)
4. Adapta el nivel según lo que veas (primaria/secundaria/universidad)
5. Usa formato claro con emojis, listas y subtítulos

SI EL USUARIO NO ESPECIFICA QUÉ QUIERE:
Ofrece opciones: "Puedo ayudarte a: resolver el ejercicio, explicar el tema, corregir errores..."

REGLAS:
- SIEMPRE muestra el proceso educativo
- Si la imagen es de un examen, guía SIN dar respuestas directas
- Si la imagen no es clara, pide una foto mejor
- Responde en español
- Sé motivador al final
"""

# ===================================
# Endpoint principal de análisis
# ===================================

@vision_bp.route('/analizar', methods=['POST'])
def analizar_imagen():
    """
    Recibe una imagen y una descripción de qué hacer con ella.
    
    Body form-data esperado:
    - imagen: archivo de imagen (JPG, PNG, etc.)
    - prompt: texto describiendo qué extraer/resolver (opcional)
    
    O body JSON con imagen en base64:
    {
        "imagen_base64": "data:image/png;base64,iVBORw0...",
        "prompt": "Resuelve este ejercicio"
    }
    """
    try:
        # Validar clave API
        if not GEMINI_API_KEY:
            return jsonify({
                'error': 'GEMINI_API_KEY no configurada',
                'message': 'Configura tu clave de Gemini en el archivo .env'
            }), 500
        
        imagen_pil = None
        prompt = ""
        
        # OPCIÓN 1: Recibe archivo directo (form-data)
        if 'imagen' in request.files:
            archivo = request.files['imagen']
            
            if archivo.filename == '':
                return jsonify({
                    'error': 'No se seleccionó archivo',
                    'message': 'Selecciona una imagen para analizar'
                }), 400
            
            # Convertir a PIL Image
            imagen_pil = Image.open(archivo.stream)
            prompt = request.form.get('prompt', '').strip()
        
        # OPCIÓN 2: Recibe imagen en base64 (JSON)
        elif request.is_json:
            data = request.get_json()
            imagen_base64 = data.get('imagen_base64', '')
            prompt = data.get('prompt', '').strip()
            
            if not imagen_base64:
                return jsonify({
                    'error': 'Falta imagen',
                    'message': 'Envía una imagen para analizar'
                }), 400
            
            # Limpiar prefijo base64 si existe
            if ',' in imagen_base64:
                imagen_base64 = imagen_base64.split(',')[1]
            
            # Decodificar base64 a imagen
            imagen_bytes = base64.b64decode(imagen_base64)
            imagen_pil = Image.open(BytesIO(imagen_bytes))
        
        else:
            return jsonify({
                'error': 'Formato inválido',
                'message': 'Envía la imagen como archivo o base64'
            }), 400
        
        # Si no hay prompt, usar uno por defecto
        if not prompt:
            prompt = "Analiza esta imagen y ayúdame con lo que ves. Explica paso a paso."
        
        # Convertir a RGB si es necesario (por si es PNG con transparencia)
        if imagen_pil.mode != 'RGB':
            imagen_pil = imagen_pil.convert('RGB')
        
        # Configurar el modelo Gemini con capacidad de visión
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=VISION_INSTRUCTION
        )
        
        # Enviar imagen + prompt a Gemini
        response = model.generate_content([prompt, imagen_pil])
        respuesta_texto = response.text
        
        return jsonify({
            'respuesta': respuesta_texto,
            'prompt_usado': prompt,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': 'Error al analizar imagen',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint de prueba
# ===================================

@vision_bp.route('/test', methods=['GET'])
def test():
    """Verifica que el endpoint de visión está funcionando"""
    return jsonify({
        'status': 'ok',
        'endpoint': 'vision',
        'gemini_configured': bool(GEMINI_API_KEY),
        'message': '🔍 Vision endpoint funcionando'
    })
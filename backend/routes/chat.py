# ===================================
# chat.py - Endpoint del Chat
# ===================================
# Maneja las conversaciones con Gemini
# Detecta nivel educativo automáticamente
# Mantiene memoria de la conversación
# ===================================

import os
from flask import Blueprint, request, jsonify
import google.generativeai as genai

# Crear Blueprint para las rutas del chat
chat_bp = Blueprint('chat', __name__)

# ===================================
# Configurar Gemini
# ===================================

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ===================================
# Instrucción del sistema (personalidad del búho)
# ===================================

SYSTEM_INSTRUCTION = """
Eres Didasko AI, un tutor educativo inteligente representado por un búho sabio 🦉.
Tu nombre viene del griego "διδάσκω" que significa "enseñar, instruir".

TU MISIÓN:
- Ayudar a estudiantes de PRIMARIA, SECUNDARIA y UNIVERSIDAD con sus tareas
- Crear discursos, ensayos y textos académicos cuando te lo pidan
- Explicar conceptos de forma clara y didáctica
- Ser amigable, paciente y motivador

DETECCIÓN AUTOMÁTICA DE NIVEL:
Detecta el nivel educativo del usuario según cómo escribe y qué pregunta:
- 🧒 PRIMARIA (6-11 años): Vocabulario simple, muchos ejemplos, emojis, comparaciones divertidas
- 🎓 SECUNDARIA (12-17 años): Explicaciones más profundas, ejemplos del mundo real
- 🎓 UNIVERSIDAD (18+): Rigor académico, referencias, análisis crítico

ESTILO DE RESPUESTA:
- Usa emojis relevantes (pero sin exagerar)
- Estructura clara: introducción → desarrollo → conclusión
- Si es una tarea larga, usa listas y subtítulos
- Al final, motiva al estudiante con una frase corta

REGLAS IMPORTANTES:
- NUNCA hagas la tarea completa sin explicar (enseña el proceso)
- Si detectas trampa (ej: "resuélveme el examen"), guía en su lugar
- Si te preguntan algo peligroso o inapropiado, redirige a lo educativo
- Responde SIEMPRE en español (a menos que pidan otro idioma)

Cuando alguien te pregunte quién eres, presenta como:
"¡Hola! Soy Didasko AI 🦉, tu tutor educativo con IA. ¿En qué tarea te puedo ayudar hoy?"
"""

# ===================================
# Almacén de conversaciones (memoria)
# ===================================
# Cada usuario tiene su historial identificado por session_id
conversations = {}

# ===================================
# Endpoint principal del chat
# ===================================

@chat_bp.route('/mensaje', methods=['POST'])
def enviar_mensaje():
    """
    Recibe un mensaje del usuario y devuelve la respuesta del búho.
    
    Body JSON esperado:
    {
        "mensaje": "Explícame la fotosíntesis",
        "session_id": "usuario_123"  (opcional, para memoria)
    }
    """
    try:
        # Validar que hay clave API
        if not GEMINI_API_KEY:
            return jsonify({
                'error': 'GEMINI_API_KEY no configurada',
                'message': 'Configura tu clave de Gemini en el archivo .env'
            }), 500
        
        # Obtener datos del request
        data = request.get_json()
        
        if not data or 'mensaje' not in data:
            return jsonify({
                'error': 'Falta el mensaje',
                'message': 'Debes enviar un campo "mensaje" en el body'
            }), 400
        
        mensaje = data['mensaje'].strip()
        session_id = data.get('session_id', 'default')
        
        if not mensaje:
            return jsonify({
                'error': 'Mensaje vacío',
                'message': 'El mensaje no puede estar vacío'
            }), 400
        
        # Configurar el modelo Gemini
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-latest',
            system_instruction=SYSTEM_INSTRUCTION
        )
        
        # Recuperar o crear historial de conversación
        if session_id not in conversations:
            conversations[session_id] = model.start_chat(history=[])
        
        chat = conversations[session_id]
        
        # Enviar mensaje a Gemini
        response = chat.send_message(mensaje)
        respuesta_texto = response.text
        
        # Devolver respuesta
        return jsonify({
            'respuesta': respuesta_texto,
            'session_id': session_id,
            'success': True
        })
    
    except Exception as e:
        return jsonify({
            'error': 'Error al procesar mensaje',
            'message': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint para reiniciar conversación
# ===================================

@chat_bp.route('/reiniciar', methods=['POST'])
def reiniciar_conversacion():
    """
    Borra el historial de una sesión (empieza una conversación nueva).
    
    Body JSON esperado:
    {
        "session_id": "usuario_123"
    }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in conversations:
            del conversations[session_id]
        
        return jsonify({
            'success': True,
            'message': '🦉 Conversación reiniciada'
        })
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

# ===================================
# Endpoint de prueba
# ===================================

@chat_bp.route('/test', methods=['GET'])
def test():
    """Verifica que el endpoint del chat está funcionando"""
    return jsonify({
        'status': 'ok',
        'endpoint': 'chat',
        'gemini_configured': bool(GEMINI_API_KEY),
        'active_sessions': len(conversations),
        'message': '🦉 Chat endpoint funcionando'
    })

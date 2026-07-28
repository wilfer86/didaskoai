# ===================================
# chat.py - Endpoint del Chat
# ===================================
# Maneja las conversaciones con NVIDIA (principal) y Gemini (respaldo)
# Detecta nivel educativo automáticamente
# Mantiene memoria de la conversación
# ===================================

import os
from flask import Blueprint, request, jsonify
from openai import OpenAI
import google.generativeai as genai

# Crear Blueprint para las rutas del chat
chat_bp = Blueprint('chat', __name__)

# ===================================
# Configurar NVIDIA (principal)
# ===================================

NVIDIA_API_KEY = os.getenv('NVIDIA_API_KEY')

nvidia_client = None
if NVIDIA_API_KEY:
    nvidia_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY
    )

# ===================================
# Configurar Gemini (respaldo)
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
conversations = {}

# ===================================
# Función principal: NVIDIA con respaldo Gemini
# ===================================

def generar_respuesta(mensaje, historial):
    """
    Intenta con NVIDIA primero.
    Si falla, usa Gemini como respaldo.
    """

    # --- NVIDIA (principal) ---
    if nvidia_client:
        try:
            # Construir mensajes con historial
            messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
            for item in historial:
                messages.append(item)
            messages.append({"role": "user", "content": mensaje})

            response = nvidia_client.chat.completions.create(
                model="nvidia/nemotron-ultra-253b-v1",
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            return response.choices[0].message.content, "nvidia"

        except Exception as e:
            print(f"⚠️ NVIDIA falló: {e} — usando Gemini como respaldo")

    # --- Gemini (respaldo) ---
    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(
                model_name='gemini-flash-latest',
                system_instruction=SYSTEM_INSTRUCTION
            )
            chat = model.start_chat(history=[])
            response = chat.send_message(mensaje)
            return response.text, "gemini"

        except Exception as e:
            print(f"❌ Gemini también falló: {e}")

    return "🦉 No hay servicio disponible en este momento. Intenta más tarde.", "none"

# ===================================
# Endpoint principal del chat
# ===================================

@chat_bp.route('/mensaje', methods=['POST'])
def enviar_mensaje():
    try:
        if not NVIDIA_API_KEY and not GEMINI_API_KEY:
            return jsonify({
                'error': 'Sin API configurada',
                'message': 'Configura NVIDIA_API_KEY o GEMINI_API_KEY'
            }), 500

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

        # Recuperar historial de conversación
        if session_id not in conversations:
            conversations[session_id] = []

        historial = conversations[session_id]

        # Generar respuesta
        respuesta_texto, modelo_usado = generar_respuesta(mensaje, historial)

        # Guardar en historial
        conversations[session_id].append({"role": "user", "content": mensaje})
        conversations[session_id].append({"role": "assistant", "content": respuesta_texto})

        # Limitar historial a últimos 20 mensajes (10 intercambios)
        if len(conversations[session_id]) > 20:
            conversations[session_id] = conversations[session_id][-20:]

        return jsonify({
            'respuesta': respuesta_texto,
            'session_id': session_id,
            'modelo': modelo_usado,
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
    return jsonify({
        'status': 'ok',
        'endpoint': 'chat',
        'nvidia_configurado': bool(NVIDIA_API_KEY),
        'gemini_configurado': bool(GEMINI_API_KEY),
        'sesiones_activas': len(conversations),
        'message': '🦉 Chat endpoint funcionando'
    })

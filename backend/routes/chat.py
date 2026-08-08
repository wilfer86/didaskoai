# ===================================
# chat.py - Endpoint del Chat V3.0
# ===================================
# Maneja las conversaciones con NVIDIA (principal) y Gemini (respaldo)
# 🆕 Guarda historial en Supabase por usuario
# ===================================

import os
from flask import Blueprint, request, jsonify, session
from openai import OpenAI
import google.generativeai as genai
from supabase_client import guardar_chat, obtener_historial, eliminar_chat

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
# Almacén de conversaciones en memoria (para sesión activa)
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
# 🆕 Cargar historial desde Supabase al iniciar sesión
# ===================================
def cargar_historial_supabase(usuario_id, session_id):
    """Carga los últimos 10 mensajes de Supabase a memoria."""
    if session_id in conversations and len(conversations[session_id]) > 0:
        return  # Ya tiene historial en memoria
    
    try:
        chats_previos = obtener_historial(usuario_id, limite=10)
        # Ordenar de más antiguo a más reciente
        chats_previos = list(reversed(chats_previos))
        
        historial_memoria = []
        for chat in chats_previos:
            if chat.get('seccion') == 'chat':
                historial_memoria.append({"role": "user", "content": chat['mensaje_usuario']})
                historial_memoria.append({"role": "assistant", "content": chat['respuesta_ia']})
        
        conversations[session_id] = historial_memoria
        print(f"✅ Historial cargado: {len(historial_memoria)} mensajes")
    except Exception as e:
        print(f"⚠️ Error cargando historial: {e}")
        conversations[session_id] = []

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

        # 🆕 Obtener usuario logueado
        usuario_id = session.get('usuario_id')
        
        # 🆕 Cargar historial desde Supabase (primera vez)
        if usuario_id:
            cargar_historial_supabase(usuario_id, session_id)

        # Recuperar historial de conversación
        if session_id not in conversations:
            conversations[session_id] = []

        historial = conversations[session_id]

        # Generar respuesta
        respuesta_texto, modelo_usado = generar_respuesta(mensaje, historial)

        # Guardar en historial (memoria)
        conversations[session_id].append({"role": "user", "content": mensaje})
        conversations[session_id].append({"role": "assistant", "content": respuesta_texto})

        # Limitar historial a últimos 20 mensajes (10 intercambios)
        if len(conversations[session_id]) > 20:
            conversations[session_id] = conversations[session_id][-20:]

        # 🆕 Guardar en Supabase (persistente)
        if usuario_id:
            try:
                guardar_chat(
                    usuario_id=usuario_id,
                    seccion='chat',
                    mensaje=mensaje,
                    respuesta=respuesta_texto,
                    modelo=modelo_usado
                )
            except Exception as e:
                print(f"⚠️ No se pudo guardar en Supabase: {e}")

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
# 🆕 Endpoint para obtener historial del usuario
# ===================================

@chat_bp.route('/historial', methods=['GET'])
def obtener_historial_usuario():
    """Devuelve el historial de chats del usuario logueado."""
    try:
        usuario_id = session.get('usuario_id')
        
        if not usuario_id:
            return jsonify({
                'success': False,
                'error': 'No hay sesión activa'
            }), 401
        
        limite = int(request.args.get('limite', 50))
        historial = obtener_historial(usuario_id, limite=limite)
        
        return jsonify({
            'success': True,
            'total': len(historial),
            'historial': historial
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===================================
# 🆕 Endpoint para eliminar un chat del historial
# ===================================

@chat_bp.route('/eliminar/<chat_id>', methods=['DELETE'])
def eliminar_chat_historial(chat_id):
    """Elimina un chat específico del historial del usuario."""
    try:
        usuario_id = session.get('usuario_id')
        
        if not usuario_id:
            return jsonify({
                'success': False,
                'error': 'No hay sesión activa'
            }), 401
        
        resultado = eliminar_chat(chat_id, usuario_id)
        return jsonify(resultado)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
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
        'usuario_logueado': session.get('usuario_id') is not None,
        'message': '🦉 Chat endpoint V3.0 funcionando'
    })

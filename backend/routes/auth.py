"""
═══════════════════════════════════════════════
DIDASKO AI - Blueprint de Autenticación
═══════════════════════════════════════════════
Endpoints: registro, login, logout, sesión
"""

from flask import Blueprint, request, jsonify, session
from supabase_client import (
    registrar_usuario,
    login_usuario,
    obtener_usuario,
    verificar_conexion
)

# Crear el Blueprint
auth_bp = Blueprint('auth', __name__)


# ═══════════════════════════════════════════════
# 📝 REGISTRO DE USUARIO
# ═══════════════════════════════════════════════
@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registra un nuevo usuario.
    Body JSON: { email, password, nombre (opcional) }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos"
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        nombre = data.get('nombre', '').strip()
        
        # Validaciones básicas
        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Email y contraseña son obligatorios"
            }), 400
        
        if '@' not in email or '.' not in email:
            return jsonify({
                "success": False,
                "error": "Email inválido"
            }), 400
        
        if len(password) < 6:
            return jsonify({
                "success": False,
                "error": "La contraseña debe tener al menos 6 caracteres"
            }), 400
        
        # Registrar en Supabase
        resultado = registrar_usuario(email, password, nombre)
        
        if resultado["success"]:
            # Crear sesión automáticamente
            session['usuario_id'] = resultado["usuario"]["id"]
            session['usuario_email'] = resultado["usuario"]["email"]
            session['usuario_nombre'] = resultado["usuario"]["nombre"]
            
            return jsonify({
                "success": True,
                "message": "✅ Usuario registrado exitosamente",
                "usuario": resultado["usuario"]
            }), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════
# 🔐 LOGIN
# ═══════════════════════════════════════════════
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Inicia sesión de un usuario.
    Body JSON: { email, password }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No se recibieron datos"
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "error": "Email y contraseña son obligatorios"
            }), 400
        
        # Validar en Supabase
        resultado = login_usuario(email, password)
        
        if resultado["success"]:
            # Crear sesión
            session['usuario_id'] = resultado["usuario"]["id"]
            session['usuario_email'] = resultado["usuario"]["email"]
            session['usuario_nombre'] = resultado["usuario"]["nombre"]
            
            return jsonify({
                "success": True,
                "message": "✅ Sesión iniciada",
                "usuario": resultado["usuario"]
            }), 200
        else:
            return jsonify(resultado), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}"
        }), 500


# ═══════════════════════════════════════════════
# 🚪 LOGOUT
# ═══════════════════════════════════════════════
@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Cierra la sesión del usuario."""
    try:
        session.clear()
        return jsonify({
            "success": True,
            "message": "👋 Sesión cerrada correctamente"
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ═══════════════════════════════════════════════
# 👤 OBTENER USUARIO ACTUAL
# ═══════════════════════════════════════════════
@auth_bp.route('/me', methods=['GET'])
def me():
    """
    Devuelve los datos del usuario actualmente logueado.
    """
    try:
        usuario_id = session.get('usuario_id')
        
        if not usuario_id:
            return jsonify({
                "success": False,
                "logueado": False,
                "error": "No hay sesión activa"
            }), 401
        
        usuario = obtener_usuario(usuario_id)
        
        if not usuario:
            session.clear()
            return jsonify({
                "success": False,
                "logueado": False,
                "error": "Usuario no encontrado"
            }), 404
        
        return jsonify({
            "success": True,
            "logueado": True,
            "usuario": {
                "id": usuario["id"],
                "email": usuario["email"],
                "nombre": usuario["nombre"],
                "avatar": usuario.get("avatar"),
                "plan": usuario["plan"],
                "tareas_completadas": usuario.get("tareas_completadas", 0)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ═══════════════════════════════════════════════
# 🔍 STATUS DE SUPABASE
# ═══════════════════════════════════════════════
@auth_bp.route('/status', methods=['GET'])
def status():
    """Verifica si Supabase está conectado."""
    conectado = verificar_conexion()
    return jsonify({
        "supabase_conectado": conectado,
        "mensaje": "✅ Supabase OK" if conectado else "❌ Supabase no responde"
    }), 200

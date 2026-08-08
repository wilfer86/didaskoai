"""
═══════════════════════════════════════════════
DIDASKO AI - Cliente Supabase
═══════════════════════════════════════════════
Gestiona: usuarios, chats, historial, sesiones
"""

import os
import hashlib
from datetime import datetime
from supabase import create_client, Client

# ═══════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Cliente global de Supabase
supabase: Client = None


def init_supabase():
    """Inicializa el cliente de Supabase al arrancar el servidor."""
    global supabase
    try:
        if SUPABASE_URL and SUPABASE_SERVICE_KEY:
            supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
            print("✅ Supabase conectado correctamente")
            return True
        else:
            print("⚠️ Faltan variables SUPABASE_URL o SUPABASE_SERVICE_KEY")
            return False
    except Exception as e:
        print(f"❌ Error conectando Supabase: {e}")
        return False


def get_client() -> Client:
    """Devuelve el cliente de Supabase (para usar en otros módulos)."""
    global supabase
    if supabase is None:
        init_supabase()
    return supabase


# ═══════════════════════════════════════════════
# UTILIDADES DE SEGURIDAD
# ═══════════════════════════════════════════════
def hash_password(password: str) -> str:
    """Hashea una contraseña con SHA-256 + salt."""
    salt = "didasko_ai_2026_secure"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verifica si una contraseña coincide con su hash."""
    return hash_password(password) == hashed


# ═══════════════════════════════════════════════
# GESTIÓN DE USUARIOS
# ═══════════════════════════════════════════════
def registrar_usuario(email: str, password: str, nombre: str = None):
    """Registra un nuevo usuario en Didasko."""
    try:
        client = get_client()
        if not client:
            return {"success": False, "error": "Supabase no conectado"}
        
        # Verificar si el email ya existe
        existente = client.table("usuarios").select("id").eq("email", email).execute()
        if existente.data:
            return {"success": False, "error": "Este email ya está registrado"}
        
        # Crear usuario
        nuevo_usuario = {
            "email": email,
            "password_hash": hash_password(password),
            "nombre": nombre or email.split("@")[0],
            "proveedor": "email",
            "plan": "free"
        }
        
        resultado = client.table("usuarios").insert(nuevo_usuario).execute()
        
        if resultado.data:
            usuario = resultado.data[0]
            return {
                "success": True,
                "usuario": {
                    "id": usuario["id"],
                    "email": usuario["email"],
                    "nombre": usuario["nombre"],
                    "plan": usuario["plan"]
                }
            }
        return {"success": False, "error": "Error al crear usuario"}
        
    except Exception as e:
        print(f"❌ Error registrar_usuario: {e}")
        return {"success": False, "error": str(e)}


def login_usuario(email: str, password: str):
    """Valida credenciales y devuelve datos del usuario."""
    try:
        client = get_client()
        if not client:
            return {"success": False, "error": "Supabase no conectado"}
        
        resultado = client.table("usuarios").select("*").eq("email", email).execute()
        
        if not resultado.data:
            return {"success": False, "error": "Email no registrado"}
        
        usuario = resultado.data[0]
        
        if not verify_password(password, usuario["password_hash"]):
            return {"success": False, "error": "Contraseña incorrecta"}
        
        # Actualizar último acceso
        client.table("usuarios").update({
            "ultimo_acceso": datetime.now().isoformat()
        }).eq("id", usuario["id"]).execute()
        
        return {
            "success": True,
            "usuario": {
                "id": usuario["id"],
                "email": usuario["email"],
                "nombre": usuario["nombre"],
                "avatar": usuario.get("avatar"),
                "plan": usuario["plan"]
            }
        }
        
    except Exception as e:
        print(f"❌ Error login_usuario: {e}")
        return {"success": False, "error": str(e)}


def obtener_usuario(usuario_id: str):
    """Obtiene datos de un usuario por su ID."""
    try:
        client = get_client()
        resultado = client.table("usuarios").select("*").eq("id", usuario_id).execute()
        if resultado.data:
            return resultado.data[0]
        return None
    except Exception as e:
        print(f"Error obteniendo usuario: {e}")
        return None


# ═══════════════════════════════════════════════
# GESTIÓN DE CHATS (HISTORIAL)
# ═══════════════════════════════════════════════
def guardar_chat(usuario_id: str, seccion: str, mensaje: str, respuesta: str, modelo: str = "nemotron"):
    """Guarda una conversación en el historial."""
    try:
        client = get_client()
        chat = {
            "usuario_id": usuario_id,
            "seccion": seccion,
            "mensaje_usuario": mensaje,
            "respuesta_ia": respuesta,
            "modelo_usado": modelo
        }
        resultado = client.table("chats").insert(chat).execute()
        return {"success": True, "id": resultado.data[0]["id"]} if resultado.data else {"success": False}
    except Exception as e:
        print(f"Error guardando chat: {e}")
        return {"success": False, "error": str(e)}


def obtener_historial(usuario_id: str, limite: int = 50):
    """Obtiene el historial de chats de un usuario."""
    try:
        client = get_client()
        resultado = client.table("chats").select("*").eq("usuario_id", usuario_id).order("fecha", desc=True).limit(limite).execute()
        return resultado.data if resultado.data else []
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return []


def eliminar_chat(chat_id: str, usuario_id: str):
    """Elimina un chat del historial."""
    try:
        client = get_client()
        resultado = client.table("chats").delete().eq("id", chat_id).eq("usuario_id", usuario_id).execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════
# VERIFICAR ESTADO
# ═══════════════════════════════════════════════
def verificar_conexion():
    """Verifica si Supabase está conectado y responde."""
    try:
        client = get_client()
        if client is None:
            return False
        client.table("usuarios").select("id").limit(1).execute()
        return True
    except:
        return False

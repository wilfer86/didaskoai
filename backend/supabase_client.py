"""
═══════════════════════════════════════════════
DIDASKO AI - Cliente Supabase V3.1
═══════════════════════════════════════════════
Gestiona: usuarios, chats, historial, sesiones, imágenes
"""

import os
import hashlib
import base64
import uuid
from datetime import datetime
from supabase import create_client, Client

# ═══════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
BUCKET_IMAGENES = "imagenes-didasko"

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
    """Devuelve el cliente de Supabase."""
    global supabase
    if supabase is None:
        init_supabase()
    return supabase


# ═══════════════════════════════════════════════
# UTILIDADES DE SEGURIDAD
# ═══════════════════════════════════════════════
def hash_password(password: str) -> str:
    salt = "didasko_ai_2026_secure"
    return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ═══════════════════════════════════════════════
# 🆕 SUBIR IMAGEN A SUPABASE STORAGE
# ═══════════════════════════════════════════════
def subir_imagen_storage(imagen_base64_o_url: str, usuario_id: str, tipo: str = "creada") -> str:
    """
    Sube una imagen a Supabase Storage y devuelve la URL pública.
    Acepta base64 o URL externa.
    """
    try:
        client = get_client()
        if not client:
            return imagen_base64_o_url  # Devolver original si no hay cliente
        
        imagen_bytes = None
        
        # Caso 1: base64
        if imagen_base64_o_url.startswith('data:image'):
            # Extraer bytes del base64
            base64_str = imagen_base64_o_url.split(',')[1] if ',' in imagen_base64_o_url else imagen_base64_o_url
            imagen_bytes = base64.b64decode(base64_str)
        
        # Caso 2: URL externa (Pollinations)
        elif imagen_base64_o_url.startswith('http'):
            import requests
            response = requests.get(imagen_base64_o_url, timeout=30)
            if response.status_code == 200:
                imagen_bytes = response.content
            else:
                return imagen_base64_o_url  # No se pudo descargar, devolver original
        
        if not imagen_bytes:
            return imagen_base64_o_url
        
        # Generar nombre único
        nombre_archivo = f"{usuario_id}/{tipo}_{uuid.uuid4().hex}.png"
        
        # Subir a Supabase Storage
        client.storage.from_(BUCKET_IMAGENES).upload(
            path=nombre_archivo,
            file=imagen_bytes,
            file_options={"content-type": "image/png", "upsert": "true"}
        )
        
        # Obtener URL pública
        url_publica = client.storage.from_(BUCKET_IMAGENES).get_public_url(nombre_archivo)
        
        print(f"✅ Imagen subida a Storage: {nombre_archivo}")
        return url_publica
        
    except Exception as e:
        print(f"⚠️ Error subiendo a Storage: {e}")
        return imagen_base64_o_url  # Fallback: devolver original


# ═══════════════════════════════════════════════
# GESTIÓN DE USUARIOS
# ═══════════════════════════════════════════════
def registrar_usuario(email: str, password: str, nombre: str = None):
    try:
        client = get_client()
        if not client:
            return {"success": False, "error": "Supabase no conectado"}
        
        existente = client.table("usuarios").select("id").eq("email", email).execute()
        if existente.data:
            return {"success": False, "error": "Este email ya está registrado"}
        
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
# GESTIÓN DE CHATS
# ═══════════════════════════════════════════════
def guardar_chat(usuario_id: str, seccion: str, mensaje: str, respuesta: str, modelo: str = "nemotron"):
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
    try:
        client = get_client()
        resultado = client.table("chats").select("*").eq("usuario_id", usuario_id).order("fecha", desc=True).limit(limite).execute()
        return resultado.data if resultado.data else []
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return []


def eliminar_chat(chat_id: str, usuario_id: str):
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
    try:
        client = get_client()
        if client is None:
            return False
        client.table("usuarios").select("id").limit(1).execute()
        return True
    except:
        return False

# 🦉 Didasko AI

**Tu tutor educativo con Inteligencia Artificial**

Del griego διδάσκω ("enseñar, instruir"), Didasko AI es una plataforma educativa gratuita que ayuda a estudiantes de primaria, secundaria y universidad con sus tareas, discursos y proyectos escolares.

![Didasko AI](frontend/assets/logo/buho-columna.png)

---

## ✨ Características

- 💬 **Chat inteligente** — Resuelve dudas, crea discursos, explica conceptos
- 🔍 **Análisis de fotos** — Sube foto de tu tarea y recibe explicación paso a paso
- 🌌 **Creación de imágenes** — Genera imágenes con IA (formatos 1:1, 16:9, 9:16)
- 🎬 **Creación de videos** — Genera videos cortos verticales (9:16)
- 📱 **PWA instalable** — Funciona como app en tu celular
- 🎓 **Adaptación automática** — Detecta el nivel educativo (primaria/secundaria/universidad)
- 💾 **Memoria conversacional** — Recuerda todo el chat para continuidad

---

## 🚀 Tecnologías

### Backend
- **Python** con Flask
- **Google Gemini 1.5 Flash** → Chat + Vision
- **SiliconFlow (Flux)** → Generación de imágenes
- **SiliconFlow (CogVideoX)** → Generación de videos

### Frontend
- HTML5 + CSS3 + JavaScript vanilla
- Diseño responsive (móvil y escritorio)
- PWA (Progressive Web App)

### Deploy
- **GitHub** (código fuente)
- **Render** (hosting gratuito)
- **PWABuilder** (conversión a APK para Play Store)

---

## 📱 Cómo usar

### En navegador (Web)
Visita: [https://didasko-ai.onrender.com](https://didasko-ai.onrender.com)

### En celular (App)
1. Abre el sitio en Chrome/Safari
2. Menú → "Instalar app"
3. ¡Listo! Tienes Didasko AI en tu pantalla de inicio

---

## 🛠️ Instalación local (Desarrolladores)

### Requisitos
- Python 3.11+
- API Key de [Google Gemini](https://aistudio.google.com/app/apikey)
- API Key de [SiliconFlow](https://cloud.siliconflow.cn)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/wilfer86/didasko-ai.git
cd didasko-ai/backend

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus claves API

# 4. Iniciar servidor
python app.py

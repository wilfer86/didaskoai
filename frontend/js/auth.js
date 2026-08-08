/* ═══════════════════════════════════════════════
   DIDASKO AI - Lógica de Login/Registro
   Conecta con /api/auth/* del backend
═══════════════════════════════════════════════ */

// ═══════════════ TOGGLE FORMULARIOS ═══════════════
function mostrarFormulario(tipo) {
    const formLogin = document.getElementById('form-login');
    const formRegistro = document.getElementById('form-registro');
    const btnLogin = document.getElementById('btn-login');
    const btnRegistro = document.getElementById('btn-registro');

    // Limpiar mensajes
    limpiarMensajes();

    if (tipo === 'login') {
        formLogin.classList.add('active');
        formRegistro.classList.remove('active');
        btnLogin.classList.add('active');
        btnRegistro.classList.remove('active');
    } else {
        formRegistro.classList.add('active');
        formLogin.classList.remove('active');
        btnRegistro.classList.add('active');
        btnLogin.classList.remove('active');
    }
}

// ═══════════════ MOSTRAR MENSAJE ═══════════════
function mostrarMensaje(elementId, texto, tipo = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.className = 'login-mensaje ' + tipo;
    el.textContent = texto;
}

function limpiarMensajes() {
    ['mensaje-login', 'mensaje-registro'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.className = 'login-mensaje';
            el.textContent = '';
        }
    });
}

// ═══════════════ REGISTRAR NUEVO USUARIO ═══════════════
async function hacerRegistro(event) {
    event.preventDefault();

    const nombre = document.getElementById('registro-nombre').value.trim();
    const email = document.getElementById('registro-email').value.trim().toLowerCase();
    const password = document.getElementById('registro-password').value;
    const btn = document.getElementById('btn-hacer-registro');

    // Validaciones
    if (!nombre || !email || !password) {
        mostrarMensaje('mensaje-registro', '⚠️ Completa todos los campos', 'error');
        return;
    }

    if (password.length < 6) {
        mostrarMensaje('mensaje-registro', '⚠️ La contraseña debe tener mínimo 6 caracteres', 'error');
        return;
    }

    // Estado cargando
    btn.disabled = true;
    btn.textContent = '⏳ Creando cuenta...';
    mostrarMensaje('mensaje-registro', '🔄 Registrando usuario...', 'info');

    try {
        const respuesta = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ nombre, email, password })
        });

        const data = await respuesta.json();

        if (data.success) {
            mostrarMensaje('mensaje-registro', '✅ ¡Cuenta creada! Redirigiendo...', 'exito');
            
            // Guardar datos localmente
            localStorage.setItem('didasko_usuario', JSON.stringify(data.usuario));
            
            // Redirigir al home después de 1 segundo
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            mostrarMensaje('mensaje-registro', '❌ ' + (data.error || 'Error al registrar'), 'error');
            btn.disabled = false;
            btn.textContent = '✨ Crear mi cuenta';
        }
    } catch (error) {
        mostrarMensaje('mensaje-registro', '❌ Error de conexión: ' + error.message, 'error');
        btn.disabled = false;
        btn.textContent = '✨ Crear mi cuenta';
    }
}

// ═══════════════ INICIAR SESIÓN ═══════════════
async function hacerLogin(event) {
    event.preventDefault();

    const email = document.getElementById('login-email').value.trim().toLowerCase();
    const password = document.getElementById('login-password').value;
    const btn = document.getElementById('btn-hacer-login');

    if (!email || !password) {
        mostrarMensaje('mensaje-login', '⚠️ Completa email y contraseña', 'error');
        return;
    }

    btn.disabled = true;
    btn.textContent = '⏳ Entrando...';
    mostrarMensaje('mensaje-login', '🔄 Verificando credenciales...', 'info');

    try {
        const respuesta = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password })
        });

        const data = await respuesta.json();

        if (data.success) {
            mostrarMensaje('mensaje-login', '✅ ¡Bienvenido ' + data.usuario.nombre + '!', 'exito');
            
            localStorage.setItem('didasko_usuario', JSON.stringify(data.usuario));
            
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            mostrarMensaje('mensaje-login', '❌ ' + (data.error || 'Credenciales inválidas'), 'error');
            btn.disabled = false;
            btn.textContent = '🚀 Entrar';
        }
    } catch (error) {
        mostrarMensaje('mensaje-login', '❌ Error de conexión: ' + error.message, 'error');
        btn.disabled = false;
        btn.textContent = '🚀 Entrar';
    }
}

// ═══════════════ CERRAR SESIÓN (usado desde index) ═══════════════
async function cerrarSesion() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
    } catch (e) {
        console.warn('Error cerrando sesión:', e);
    }
    localStorage.removeItem('didasko_usuario');
    window.location.href = '/login.html';
}

// ═══════════════ VERIFICAR SESIÓN AL CARGAR ═══════════════
async function verificarSesion() {
    try {
        const respuesta = await fetch('/api/auth/me', {
            credentials: 'include'
        });
        const data = await respuesta.json();

        if (data.success && data.logueado) {
            // Si ya está logueado y está en login.html, redirigir al home
            if (window.location.pathname.includes('login.html')) {
                window.location.href = '/';
            }
            return data.usuario;
        }
        return null;
    } catch (error) {
        console.warn('Error verificando sesión:', error);
        return null;
    }
}

// ═══════════════ AL CARGAR LA PÁGINA ═══════════════
document.addEventListener('DOMContentLoaded', () => {
    // Si está en login.html, verificar si ya está logueado
    if (window.location.pathname.includes('login.html') || 
        window.location.pathname === '/login.html') {
        verificarSesion();
    }
});

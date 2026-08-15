// ==========================================
// apoyar.js - Didasko AI V2.0
// Función copiarDato() para métodos de pago
// ==========================================

// 🔥 FUNCIÓN GLOBAL: Se llama desde onclick en HTML
function copiarDato(dato, metodo) {
    console.log(`📋 Copiando ${metodo}: ${dato}`);
    
    // Intentar copiar con método moderno
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(dato)
            .then(() => {
                mostrarToast(`✅ ${metodo} copiado: ${dato}`, 'exito');
                animarTarjeta(metodo);
            })
            .catch(err => {
                console.warn('Error clipboard API:', err);
                copiarAlternativo(dato, metodo);
            });
    } else {
        // Método alternativo (fallback)
        copiarAlternativo(dato, metodo);
    }
}

// Método alternativo para navegadores viejos o sin HTTPS
function copiarAlternativo(dato, metodo) {
    try {
        const textArea = document.createElement('textarea');
        textArea.value = dato;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.top = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        const exitoso = document.execCommand('copy');
        document.body.removeChild(textArea);
        
        if (exitoso) {
            mostrarToast(`✅ ${metodo} copiado: ${dato}`, 'exito');
            animarTarjeta(metodo);
        } else {
            mostrarToast(`❌ Copia manualmente: ${dato}`, 'error');
        }
    } catch (err) {
        console.error('Error al copiar:', err);
        mostrarToast(`❌ Copia manualmente: ${dato}`, 'error');
    }
}

// Mostrar notificación tipo toast
function mostrarToast(mensaje, tipo = 'exito') {
    // Eliminar toast anterior si existe
    const toastExistente = document.getElementById('didasko-toast');
    if (toastExistente) toastExistente.remove();
    
    // Crear nuevo toast
    const toast = document.createElement('div');
    toast.id = 'didasko-toast';
    toast.className = `didasko-toast toast-${tipo}`;
    toast.innerHTML = mensaje;
    
    // Estilos inline (por si falta el CSS)
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        left: 50%;
        transform: translateX(-50%);
        background: ${tipo === 'exito' ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #ef4444, #dc2626)'};
        color: white;
        padding: 15px 25px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        z-index: 99999;
        animation: toastSlideUp 0.3s ease-out;
        max-width: 90%;
        text-align: center;
    `;
    
    document.body.appendChild(toast);
    
    // Quitar después de 2.5 segundos
    setTimeout(() => {
        toast.style.animation = 'toastFadeOut 0.3s ease-in';
        setTimeout(() => toast.remove(), 300);
    }, 2500);
}

// Animar la tarjeta cuando se copia
function animarTarjeta(metodo) {
    const tarjetas = document.querySelectorAll('.metodo-card');
    tarjetas.forEach(tarjeta => {
        const h3 = tarjeta.querySelector('h3');
        if (h3 && h3.textContent.trim().toLowerCase() === metodo.toLowerCase()) {
            tarjeta.style.transform = 'scale(1.05)';
            tarjeta.style.boxShadow = '0 0 30px rgba(16, 185, 129, 0.6)';
            
            setTimeout(() => {
                tarjeta.style.transform = '';
                tarjeta.style.boxShadow = '';
            }, 300);
        }
    });
}

// Inyectar CSS de animaciones
(function inyectarCSS() {
    if (document.getElementById('didasko-toast-css')) return;
    
    const style = document.createElement('style');
    style.id = 'didasko-toast-css';
    style.innerHTML = `
        @keyframes toastSlideUp {
            from {
                opacity: 0;
                transform: translateX(-50%) translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
        }
        
        @keyframes toastFadeOut {
            from {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }
            to {
                opacity: 0;
                transform: translateX(-50%) translateY(-30px);
            }
        }
        
        .metodo-card {
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
    `;
    document.head.appendChild(style);
})();

console.log('💰 apoyar.js V2.0 cargado - copiarDato() disponible');

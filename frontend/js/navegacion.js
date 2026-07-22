// Selección de formato de imagen (temporal para diseño)
function seleccionarFormato(formato) {
    const botones = document.querySelectorAll('.btn-formato');
    botones.forEach(btn => btn.classList.remove('active'));
    
    const btnSeleccionado = document.querySelector(`.btn-formato[data-formato="${formato}"]`);
    if (btnSeleccionado) {
        btnSeleccionado.classList.add('active');
    }
    
    if (CONFIG.DEBUG) console.log('🖼️ Formato seleccionado:', formato);
}
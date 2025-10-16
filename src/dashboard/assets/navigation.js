// Script para manejar la navegación del sidebar
// Este archivo se carga automáticamente por Dash desde la carpeta assets/

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 Inicializando sistema de navegación...');
    
    // Función para toggle del sidebar
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const page = document.querySelector('.page');
        
        if (!sidebar || !overlay) {
            console.warn('⚠️ Elementos de navegación no encontrados');
            return;
        }
        
        if (sidebar.classList.contains('sidebar-collapsed')) {
            // Abrir sidebar
            sidebar.classList.remove('sidebar-collapsed');
            overlay.classList.add('active');
            if (page && window.innerWidth > 768) {
                page.classList.add('sidebar-open');
            }
            console.log('📂 Sidebar abierto');
        } else {
            // Cerrar sidebar
            sidebar.classList.add('sidebar-collapsed');
            overlay.classList.remove('active');
            if (page) {
                page.classList.remove('sidebar-open');
            }
            console.log('📁 Sidebar cerrado');
        }
    }
    
    // Función para cerrar sidebar
    function closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const page = document.querySelector('.page');
        
        if (sidebar && overlay) {
            sidebar.classList.add('sidebar-collapsed');
            overlay.classList.remove('active');
            if (page) {
                page.classList.remove('sidebar-open');
            }
        }
    }
    
    // Configurar eventos con delegation para manejar re-renders de Dash
    document.body.addEventListener('click', function(e) {
        // Toggle button
        if (e.target.closest('#sidebar-toggle')) {
            e.preventDefault();
            toggleSidebar();
        }
        
        // Overlay
        if (e.target.id === 'sidebar-overlay') {
            e.preventDefault();
            closeSidebar();
        }
        
        // Links de navegación (cerrar en móvil)
        if (e.target.closest('.nav-item:not(.nav-item-disabled)')) {
            if (window.innerWidth <= 768) {
                setTimeout(closeSidebar, 300); // Delay para animación
            }
        }
    });
    
    // Cerrar sidebar al cambiar tamaño de ventana (de móvil a desktop)
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth > 768) {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebar-overlay');
                if (sidebar && !sidebar.classList.contains('sidebar-collapsed')) {
                    const page = document.querySelector('.page');
                    if (page) {
                        page.classList.add('sidebar-open');
                    }
                }
            }
        }, 250);
    });
    
    console.log('✅ Sistema de navegación inicializado');
});

"""
Callbacks para la navegación lateral.
La lógica del sidebar se maneja con JavaScript puro en assets/navigation.js
para evitar conflictos con los re-renders de Dash.
"""


def register_navigation_callbacks(app):
    """
    Los callbacks de navegación se manejan con JavaScript del lado del cliente.
    Ver: src/dashboard/assets/navigation.js
    
    Esta función se mantiene para consistencia pero no registra callbacks.
    """
    # La navegación se maneja completamente con JavaScript en assets/navigation.js
    # Esto evita conflictos con los callbacks de Dash y proporciona mejor rendimiento
    pass

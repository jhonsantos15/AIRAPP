"""
Componente de navegación lateral para dashboards.
Sistema moderno con sidebar colapsable y mejor UX.
"""
from dash import html, dcc


def create_navigation_sidebar(current_page="principal"):
    """
    Crea un sidebar de navegación moderno y colapsable.
    
    Args:
        current_page: Identificador de la página actual ('principal', 'viento-gases', etc.)
    """
    
    # Definición de las secciones del dashboard
    nav_items = [
        {
            "id": "principal",
            "icon": "💨",
            "title": "Material Particulado",
            "description": "PM2.5, PM10, Temperatura y Humedad",
            "path": "/dash/",
        },
        {
            "id": "viento-gases",
            "icon": "🌬️",
            "title": "Viento y Gases",
            "description": "NO2, CO2, Rosa de Vientos",
            "path": "/dash/viento-gases",
        },
        {
            "id": "reportes",
            "icon": "📊",
            "title": "Reportes y Análisis",
            "description": "Exportar datos, estadísticas",
            "path": "#reportes",
            "disabled": True,  # Próximamente
        },
        {
            "id": "configuracion",
            "icon": "⚙️",
            "title": "Configuración",
            "description": "Alertas, umbrales, dispositivos",
            "path": "#config",
            "disabled": True,  # Próximamente
        },
    ]
    
    # Construir items del menú
    menu_items = []
    for item in nav_items:
        is_active = item["id"] == current_page
        is_disabled = item.get("disabled", False)
        
        # Clases CSS dinámicas
        item_class = "nav-item"
        if is_active:
            item_class += " nav-item-active"
        if is_disabled:
            item_class += " nav-item-disabled"
        
        # Crear el link o div
        if is_disabled:
            nav_element = html.Div(
                className=item_class,
                children=[
                    html.Div(className="nav-icon", children=item["icon"]),
                    html.Div(
                        className="nav-content",
                        children=[
                            html.Div(className="nav-title", children=item["title"]),
                            html.Div(className="nav-desc", children=item["description"]),
                            html.Span(className="nav-badge", children="Próximamente"),
                        ],
                    ),
                ],
            )
        else:
            nav_element = dcc.Link(
                href=item["path"],
                className=item_class,
                children=[
                    html.Div(className="nav-icon", children=item["icon"]),
                    html.Div(
                        className="nav-content",
                        children=[
                            html.Div(className="nav-title", children=item["title"]),
                            html.Div(className="nav-desc", children=item["description"]),
                        ],
                    ),
                    html.Div(className="nav-arrow", children="›") if not is_disabled else None,
                ],
            )
        
        menu_items.append(nav_element)
    
    # Toggle button (FUERA del sidebar para que siempre sea visible)
    toggle_button = html.Button(
        id="sidebar-toggle",
        className="sidebar-toggle",
        children=[
            html.Span(className="hamburger-line"),
            html.Span(className="hamburger-line"),
            html.Span(className="hamburger-line"),
        ],
        n_clicks=0,
    )
    
    # Estructura del sidebar
    sidebar = html.Div(
        id="sidebar",
        className="sidebar sidebar-collapsed",  # Inicia colapsado
        children=[
            # Header del sidebar
            html.Div(
                className="sidebar-header",
                children=[
                    html.Div(className="sidebar-logo", children="🌡️"),
                    html.H3(className="sidebar-brand", children="AireApp"),
                    html.Div(className="sidebar-subtitle", children="Monitoreo de Calidad del Aire"),
                ],
            ),
            
            # Navegación principal
            html.Div(
                className="sidebar-nav",
                children=[
                    html.Div(className="nav-section-title", children="DASHBOARDS"),
                    *menu_items[:2],  # Principal y Viento-Gases
                    
                    html.Div(className="nav-divider"),
                    
                    html.Div(className="nav-section-title", children="HERRAMIENTAS"),
                    *menu_items[2:],  # Reportes y Configuración
                ],
            ),
            
            # Footer con info
            html.Div(
                className="sidebar-footer",
                children=[
                    html.Div(
                        className="footer-stat",
                        children=[
                            html.Span("📡", className="footer-icon"),
                            html.Div([
                                html.Div("6 Sensores", className="footer-stat-value"),
                                html.Div("Activos", className="footer-stat-label"),
                            ]),
                        ],
                    ),
                    html.Div(
                        className="footer-info",
                        children="© 2025 AireApp v1.0",
                    ),
                ],
            ),
        ],
    )
    
    # Overlay para cerrar sidebar en móvil
    overlay = html.Div(
        id="sidebar-overlay",
        className="sidebar-overlay",
    )
    
    # Retornar solo sidebar y overlay (el botón se integrará en el topbar)
    return html.Div(
        className="navigation-wrapper",
        children=[overlay, sidebar],
    )


def create_sidebar_toggle_button():
    """
    Crea el botón hamburger para toggle del sidebar.
    Este botón se integra dentro del topbar para mejor ubicación estratégica.
    """
    return html.Button(
        id="sidebar-toggle",
        className="sidebar-toggle",
        children=[
            html.Span(className="hamburger-line"),
            html.Span(className="hamburger-line"),
            html.Span(className="hamburger-line"),
        ],
        n_clicks=0,
    )


def create_breadcrumbs(path_items):
    """
    Crea breadcrumbs para orientación del usuario.
    
    Args:
        path_items: Lista de tuplas (nombre, url) o strings
        Ejemplo: [("Inicio", "/"), "Material Particulado"]
    """
    breadcrumb_items = []
    
    for i, item in enumerate(path_items):
        is_last = i == len(path_items) - 1
        
        if isinstance(item, tuple):
            name, url = item
            if is_last:
                breadcrumb_items.append(
                    html.Span(className="breadcrumb-current", children=name)
                )
            else:
                breadcrumb_items.append(
                    dcc.Link(href=url, className="breadcrumb-link", children=name)
                )
        else:
            breadcrumb_items.append(
                html.Span(className="breadcrumb-current", children=item)
            )
        
        # Separador
        if not is_last:
            breadcrumb_items.append(
                html.Span(className="breadcrumb-separator", children="/")
            )
    
    return html.Nav(
        className="breadcrumbs",
        children=breadcrumb_items,
    )


def create_quick_actions():
    """
    Crea un panel de acciones rápidas (shortcuts).
    """
    actions = [
        {
            "icon": "📥",
            "label": "Exportar Excel",
            "href": "/api/reports/excel?period=24hours",
            "color": "green",
        },
        {
            "icon": "🔄",
            "label": "Actualizar",
            "id": "quick-refresh",
            "color": "blue",
        },
        {
            "icon": "📧",
            "label": "Reportar Problema",
            "href": "mailto:soporte@aireapp.com",
            "color": "orange",
        },
    ]
    
    action_buttons = []
    for action in actions:
        if "href" in action:
            button = html.A(
                href=action["href"],
                target="_blank" if action["href"].startswith("http") or action["href"].startswith("/api") else None,
                className=f"quick-action quick-action-{action['color']}",
                children=[
                    html.Span(className="quick-action-icon", children=action["icon"]),
                    html.Span(className="quick-action-label", children=action["label"]),
                ],
            )
        else:
            button = html.Button(
                id=action.get("id", "quick-action-btn"),
                className=f"quick-action quick-action-{action['color']}",
                children=[
                    html.Span(className="quick-action-icon", children=action["icon"]),
                    html.Span(className="quick-action-label", children=action["label"]),
                ],
            )
        action_buttons.append(button)
    
    return html.Div(
        className="quick-actions-bar",
        children=action_buttons,
    )

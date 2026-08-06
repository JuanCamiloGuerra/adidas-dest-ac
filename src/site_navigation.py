"""Navegación global compartida por todos los HTML publicados.

Entradas: identificador de la sección activa y modo fijo o sticky.
Salidas: HTML y CSS consistentes para GitHub Pages.
Dependencias: biblioteca estándar.
"""

from __future__ import annotations

from html import escape


NAV_ITEMS = [
    ("presentation", "Presentación ejecutiva", "presentacion-ejecutiva.html", None),
    ("phase1", "Fase 1", "fase-1-api-tabla-maestra.html", None),
    ("markdown", "Markdown", "markdown.html", None),
    ("dashboard", "Dashboard", "index.html#overview", "overview"),
    ("scenarios", "Escenarios", "index.html#scenarios", "scenarios"),
    ("decisions", "Decisiones y ML", "index.html#decisions", "decisions"),
    ("summary", "Resumen", "executive_summary.html", None),
]


def navigation_html(active: str, fixed: bool = False) -> str:
    """Devuelve el menú en el orden aprobado para todas las páginas."""

    links = []
    for key, label, href, dashboard_page in NAV_ITEMS:
        classes = "global-nav__link" + (" active" if key == active else "")
        page_attribute = f' data-dashboard-page="{dashboard_page}"' if dashboard_page else ""
        links.append(
            f'<a class="{classes}" href="{escape(href)}"{page_attribute}>{escape(label)}</a>'
        )
    mode = " global-nav--fixed" if fixed else ""
    return (
        f'<header class="global-nav{mode}"><a class="global-nav__brand" href="index.html#overview">'
        'SPORTRETAIL <small>LAM</small></a><nav class="global-nav__links" '
        f'aria-label="Navegación principal">{"".join(links)}</nav></header>'
    )


def navigation_css() -> str:
    """CSS con contraste AA y desplazamiento horizontal controlado en móvil."""

    return """
.global-nav{height:58px;background:#000;color:#fff;display:flex;align-items:center;
justify-content:space-between;position:sticky;top:0;z-index:1000;border-bottom:1px solid #3b3b3b}
.global-nav--fixed{position:fixed;left:0;right:0;top:0}
.global-nav__brand{color:#fff;text-decoration:none;font-size:17px;font-weight:900;
letter-spacing:-.04em;padding:0 24px;white-space:nowrap}
.global-nav__brand small{color:#bdbdbd;font-size:9px;letter-spacing:.16em;margin-left:8px}
.global-nav__links{display:flex;height:100%;overflow-x:auto;scrollbar-width:thin}
.global-nav__link{display:flex;align-items:center;justify-content:center;padding:0 15px;
border-left:1px solid #383838;background:#000;color:#d0d0d0;text-decoration:none;
font-size:9px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;white-space:nowrap}
.global-nav__link:hover,.global-nav__link:focus-visible,.global-nav__link.active{
background:#fff;color:#000;outline-offset:-3px}
@media(max-width:1050px){.global-nav__brand{display:none}.global-nav__links{width:100%}
.global-nav__link{flex:1;padding:0 10px}}
@media(max-width:680px){.global-nav__link{flex:0 0 auto;padding:0 13px}.global-nav__links{justify-content:flex-start}}
@media print{.global-nav{display:none}}
"""

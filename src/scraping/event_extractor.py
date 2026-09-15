"""Detecta una estrategia y busca eventos en la página y sus iframes."""

import logging

from .strategy_registry import EVENT_STRATEGIES
from .iframe_wait import wait_for_iframes


LOGGER = logging.getLogger(__name__)


def _clave_evento(evento):
    opciones = tuple(opcion.get("url", "") for opcion in evento.get("opciones", []))
    return evento.get("nombre", ""), evento.get("hora", ""), opciones


def extraer_eventos(driver, iframe_timeout=10):
    """Busca eventos en todos los contextos y combina las estrategias válidas."""
    wait_for_iframes(driver, timeout=iframe_timeout)
    encontrados = []
    estrategia_usada = None

    def recorrer_contexto():
        nonlocal estrategia_usada

        diagnostico = driver.execute_script(
            """
            return {
                frames: document.querySelectorAll('iframe').length,
                menus: document.querySelectorAll('#menu').length,
                eventosMenu: document.querySelectorAll('#menu > li.toggle-submenu').length,
                opcionesMenu: document.querySelectorAll('#menu a.submenu-item[href]').length,
                url: location.href
            };
            """
        )
        LOGGER.debug("Contexto de eventos: %s", diagnostico)

        for estrategia in EVENT_STRATEGIES:
            eventos = estrategia.extraer(driver)
            if eventos:
                if estrategia_usada:
                    estrategia_usada += f", {estrategia.nombre}"
                else:
                    estrategia_usada = estrategia.nombre
                encontrados.extend(eventos)

        iframes = driver.find_elements("tag name", "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                recorrer_contexto()
                driver.switch_to.parent_frame()
            except Exception:
                driver.switch_to.default_content()

    recorrer_contexto()

    unicos = []
    vistos = set()
    for evento in encontrados:
        clave = _clave_evento(evento)
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(evento)

    return unicos, estrategia_usada

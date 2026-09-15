"""Espera de contenido dinámico y iframes antes de extraer eventos."""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def _context_signature(driver):
    """Devuelve una firma del DOM actual y de todos sus iframes."""
    body_length = driver.execute_script(
        "return document.body ? document.body.innerHTML.length : 0"
    )
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    children = []
    for frame in frames:
        try:
            driver.switch_to.frame(frame)
            if driver.execute_script("return document.readyState") != "complete":
                return None
            child_signature = _context_signature(driver)
            if child_signature is None:
                return None
            children.append(child_signature)
            driver.switch_to.parent_frame()
        except Exception:
            try:
                driver.switch_to.default_content()
            except Exception:
                pass
            return None
    frame_signature = tuple(
        frame.get_attribute("src") or frame.get_attribute("id") or ""
        for frame in frames
    )
    return body_length, frame_signature, tuple(children)


def wait_for_iframes(driver, timeout=10, settle=0.75):
    """Espera DOM listo, iframes cargados y una breve estabilidad del DOM."""
    state = {"signature": None, "since": None}

    def ready(current_driver):
        current_driver.switch_to.default_content()
        if current_driver.execute_script("return document.readyState") != "complete":
            state["since"] = None
            return False

        signature = _context_signature(current_driver)
        if signature is None:
            state["since"] = None
            return False
        if signature != state["signature"]:
            state["signature"] = signature
            state["since"] = time.monotonic()
            return False
        return time.monotonic() - state["since"] >= settle

    WebDriverWait(driver, timeout, poll_frequency=0.25).until(ready)
    driver.switch_to.default_content()

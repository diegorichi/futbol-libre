"""Persistencia y notificación de cambios en dominios."""
import requests
from dotenv import set_key


class SiteChangeNotifier:
    def __init__(self, urls_file, ntfy_url): self.urls_file, self.ntfy_url = urls_file, ntfy_url

    def notify(self, valid_urls, invalid_urls):
        if not invalid_urls and not valid_urls: return
        if invalid_urls and not valid_urls:
            print("No se eliminan URLs: no quedó ningún sitio válido."); return
        if invalid_urls:
            self.urls_file.parent.mkdir(parents=True, exist_ok=True)
            set_key(str(self.urls_file), "FUTBOL_LIBRE_URL", ",".join(valid_urls))
            print(f"URLs eliminadas del .env: {len(invalid_urls)}")
        else: return
        if not self.ntfy_url:
            print("NTFY_URL no configurada; no se envió aviso."); return
        message = f"Actualización de sitios FUTBOL_LIBRE_URL\nSitios válidos: {len(valid_urls)}\nSitios borrados: {len(invalid_urls)}\nURLs detectadas como inválidas:\n" + "\n".join(invalid_urls)
        try:
            response = requests.post(self.ntfy_url, data=message.encode("utf-8"), headers={"Title": "Actualizar URLs de Fútbol Libre"}, timeout=30)
            response.raise_for_status(); print("Aviso de URLs enviado a NTFY")
        except requests.RequestException as error: print(f"No se pudo enviar el aviso a NTFY: {error}")

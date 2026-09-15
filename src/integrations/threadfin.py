"""Adaptador de actualización del catálogo en Threadfin."""

import logging
import time

import requests


LOGGER = logging.getLogger(__name__)


class ThreadfinRefresher:
    COMMANDS = ("update.m3u", "update.xmltv", "update.xepg")

    def __init__(self, endpoint, pause_seconds=2):
        self.endpoint = endpoint
        self.pause_seconds = pause_seconds

    def refresh(self):
        for command in self.COMMANDS:
            try:
                response = requests.post(self.endpoint, json={"cmd": command}, timeout=30)
                if response.status_code == 200:
                    LOGGER.info("Threadfin actualizado: comando=%s", command)
                elif response.status_code == 423:
                    LOGGER.warning("Threadfin bloqueado: comando=%s", command)
                else:
                    LOGGER.error("Threadfin rechazó comando=%s status=%s respuesta=%s", command, response.status_code, response.text)
            except requests.RequestException as error:
                LOGGER.error("No se pudo actualizar Threadfin: %s", error)
            time.sleep(self.pause_seconds)


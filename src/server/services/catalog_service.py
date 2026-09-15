"""Fachada de lectura del catálogo canónico para las interfaces del servidor."""

from .channel_service import ChannelService


class CatalogService:
    def __init__(self, xml_path, m3u_path, events_path):
        self._channels = ChannelService(xml_path, m3u_path, events_path)

    def groups(self):
        return self._channels.list_event_groups()

    def channels(self):
        return self._channels.list_channels()

    def events(self):
        return self._channels.list_events()

    def source_update_dates(self):
        return self._channels.source_update_dates()


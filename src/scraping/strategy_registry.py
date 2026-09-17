"""Registro explícito de estrategias de detección de eventos."""

from .agenda_php_strategy import AgendaPhpStrategy
from .agenda_time_strategy import AgendaTimeStrategy
from .direct_channel_strategy import DirectChannelStrategy
from .event_link_time_strategy import EventLinkTimeStrategy
from .eventos_html_strategy import EventosHtmlStrategy
from .fl_event_strategy import FlEventStrategy
from .menu_strategy import MenuStrategy
from .structured_time_strategy import StructuredTimeStrategy


EVENT_STRATEGIES = (
    FlEventStrategy(),
    EventLinkTimeStrategy(),
    EventosHtmlStrategy(),
    AgendaPhpStrategy(),
    DirectChannelStrategy(),
    StructuredTimeStrategy(),
    AgendaTimeStrategy(),
    MenuStrategy(),
)

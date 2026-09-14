"""Reloj de dominio para resolver horas de eventos."""
from datetime import datetime, timedelta


class EventClock:
    def nearest(self, value, now=None):
        now = now or datetime.now()
        event_time = datetime.strptime(value, "%H:%M").time()
        candidate = datetime.combine(now.date(), event_time)
        if candidate - now > timedelta(hours=12): candidate -= timedelta(days=1)
        elif now - candidate > timedelta(hours=12): candidate += timedelta(days=1)
        return candidate

    def is_upcoming(self, value, now=None):
        try:
            now = now or datetime.now(); event = self.nearest(value, now)
            return now + timedelta(minutes=30) <= event or value == "23:59"
        except (TypeError, ValueError): return False

    def is_active(self, value, now=None):
        try:
            now = now or datetime.now(); event = self.nearest(value, now)
            return now - timedelta(hours=2, minutes=30) <= event <= now + timedelta(minutes=30)
        except (TypeError, ValueError): return False

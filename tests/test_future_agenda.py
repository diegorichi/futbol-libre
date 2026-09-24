import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path


class FutureAgendaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root / "src"))

    @staticmethod
    def fixture():
        data = {
            "today": "2026-09-23",
            "dates": [
                {"fecha": "2026-09-23", "torneos": [{"nombre": "Liga", "deporte": {"nombre": "Fútbol"}, "eventos": [{"fecha": "2026-09-23 21:00:00", "nombre": "Hoy A vs B", "canales": []}]}]},
                {"fecha": "2026-09-24", "torneos": [{"nombre": "Reserva", "deporte": {"nombre": "Fútbol"}, "eventos": [{"fecha": "2026-09-24 15:00:00", "nombre": "River vs Boca", "canales": [{"nombre": "LPF Play"}, {"nombre": "LPF Play"}]}]}]},
                {"fecha": "2026-09-25", "torneos": [{"nombre": "Fórmula 1", "deporte": {"nombre": "Automovilismo"}, "eventos": [{"fecha": "2026-09-25 09:00:00", "nombre": "Clasificación", "canales": [{"nombre": "Disney+"}]}]}]},
            ],
        }
        payload = {"props": {"pageProps": {"matchConfig": {"properties": {"service": {"data": data}}}}}}
        return f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script></html>'

    def test_scraper_excludes_source_today_and_preserves_explicit_future_dates(self):
        from scraping.future_agenda_scraper import FutureAgendaScraper

        events = FutureAgendaScraper.parse(self.fixture(), today=date(2026, 9, 23))

        self.assertEqual([event["date"] for event in events], ["2026-09-24", "2026-09-25"])
        self.assertEqual(events[0]["match"], "River vs Boca")
        self.assertEqual(events[0]["channel"], "LPF Play")
        self.assertEqual(events[1]["sport"], "Automovilismo")

    def test_tyc_scraper_reads_future_date_tournament_match_and_channels(self):
        from scraping.tyc_future_agenda_scraper import TycFutureAgendaScraper

        html = """
        <div class="agenda_results" data-selectDia="manana">
          <h2 class="border-bottom">PARTIDOS DE Mañana 24 de Septiembre del 2026</h2>
          <div class="agenda_comp_results" data-selectCompetencia="amistoso" data-selectDeporte="futbol">
            <div class="header_comp_agenda"><h2>Amistosos</h2></div>
            <div class="agenda_items_group">
              <div class="item_agenda" data-selectHorario="manana">
                <div class="hs-item-agenda">07:05</div>
                <div class="text-item-agenda">
                  <div class="text-teams-agenda"><h3>Japón VS Uruguay</h3></div>
                  <div class="text-channels-agenda"><span>TyC Sports</span><span>TyC Sports</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        """

        events = TycFutureAgendaScraper.parse(html, today=date(2026, 9, 23))

        self.assertEqual(events, [{
            "starts_at": "2026-09-24T07:05:00",
            "date": "2026-09-24",
            "time": "07:05",
            "sport": "Fútbol",
            "tournament": "Amistosos",
            "match": "Japón VS Uruguay",
            "channel": "TyC Sports",
        }])

    def test_merge_deduplicates_source_variants_and_combines_channels(self):
        from scraping.future_agenda_merge import merge_future_agendas

        tyc = [{
            "starts_at": "2026-09-24T08:00:00", "date": "2026-09-24", "time": "08:00",
            "sport": "Fútbol", "tournament": "Amistosos", "match": "Rep. de Corea VS Ecuador",
            "channel": "TyC Sports",
        }]
        clarin = [{
            "starts_at": "2026-09-24T08:00:00", "date": "2026-09-24", "time": "08:00",
            "sport": "Fútbol", "tournament": "Amistoso Internacional", "match": "Corea del Sur vs. Ecuador",
            "channel": "Disney + Premium",
        }]

        events = merge_future_agendas(tyc, clarin)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["match"], "Rep. de Corea VS Ecuador")
        self.assertEqual(events[0]["channel"], "TyC Sports, Disney + Premium")

    def test_merge_keeps_same_teams_when_tournaments_are_different(self):
        from scraping.future_agenda_merge import merge_future_agendas

        base = {
            "starts_at": "2026-09-24T15:00:00", "date": "2026-09-24", "time": "15:00",
            "sport": "Fútbol", "match": "River vs Boca", "channel": "",
        }
        events = merge_future_agendas(
            [{**base, "tournament": "Reserva"}],
            [{**base, "tournament": "Primera División Femenina"}],
        )

        self.assertEqual(len(events), 2)

    def test_merge_deduplicates_channel_spelling_variants(self):
        from scraping.future_agenda_merge import merge_future_agendas

        base = {
            "starts_at": "2026-09-26T15:00:00", "date": "2026-09-26", "time": "15:00",
            "sport": "Fútbol", "tournament": "Primera B", "match": "Arsenal vs Liniers",
        }
        events = merge_future_agendas(
            [{**base, "channel": "LPF Play, Disney+ Premium, Win Sports, Win Sports +"}],
            [{**base, "channel": "LPF PLAY, Disney + Premium"}],
        )

        self.assertEqual(events[0]["channel"], "LPF Play, Disney+ Premium, Win Sports, Win Sports +")

    def test_empty_source_keeps_previous_file(self):
        from application.update_future_agenda import FutureAgendaUpdater

        class EmptyScraper:
            url = "https://agenda.test"

            @staticmethod
            def fetch():
                return []

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.json"
            path.write_text('{"events":[{"match":"existente"}]}', encoding="utf-8")
            updater = FutureAgendaUpdater(scraper=EmptyScraper(), output_path=path)

            with self.assertRaises(RuntimeError):
                updater.run()

            self.assertIn("existente", path.read_text(encoding="utf-8"))

    def test_future_service_never_returns_today(self):
        from server.services.future_agenda_service import FutureAgendaService

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.json"
            path.write_text(json.dumps({"events": [
                {"starts_at": "2026-09-23T23:00:00", "date": "2026-09-23", "match": "Hoy"},
                {"starts_at": "2026-09-24T15:00:00", "date": "2026-09-24", "match": "Mañana"},
            ]}), encoding="utf-8")

            events = FutureAgendaService(path, datetime(2026, 9, 23, 10, 0)).events()

        self.assertEqual([event["match"] for event in events], ["Mañana"])

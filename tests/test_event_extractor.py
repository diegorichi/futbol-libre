from selenium.common.exceptions import TimeoutException

from scraping import event_extractor


class _SwitchTo:
    def __init__(self):
        self.default_content_calls = 0

    def default_content(self):
        self.default_content_calls += 1


class _Driver:
    def __init__(self):
        self.switch_to = _SwitchTo()

    def execute_script(self, _script):
        return {
            "frames": 0,
            "menus": 1,
            "eventosMenu": 1,
            "opcionesMenu": 1,
            "url": "https://pelotalibre.watch/",
        }

    def find_elements(self, _by, _value):
        return []


class _Strategy:
    nombre = "test-menu"

    @staticmethod
    def extraer(_driver):
        return [{"nombre": "Partido", "hora": "20:00", "opciones": []}]


def test_iframe_settle_timeout_still_extracts_available_dom(monkeypatch):
    driver = _Driver()
    monkeypatch.setattr(
        event_extractor,
        "wait_for_iframes",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(TimeoutException()),
    )
    monkeypatch.setattr(event_extractor, "EVENT_STRATEGIES", (_Strategy(),))

    events, strategy = event_extractor.extraer_eventos(driver, iframe_timeout=10)

    assert [event["nombre"] for event in events] == ["Partido"]
    assert strategy == "test-menu"
    assert driver.switch_to.default_content_calls == 1

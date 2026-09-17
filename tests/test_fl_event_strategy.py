from scraping.fl_event_strategy import FlEventStrategy


class _Driver:
    def __init__(self, result):
        self.result = result
        self.script = ""

    def execute_script(self, script):
        self.script = script
        return self.result


def test_fl_event_strategy_preserves_event_contract_and_channels():
    driver = _Driver([
        {
            "nombre": "Copa Mundial Sub-20 (F): Inglaterra vs Nigeria",
            "hora": "10:00",
            "logo": "https://futbollibre.love/assets/soccer.png",
            "opciones": [
                {"url": "https://futbollibre.love/ver/dsports2", "canal": "DSports 2"},
                {"url": "https://futbollibre.love/ver/tudn", "canal": "TUDN MX"},
            ],
        }
    ])

    events = FlEventStrategy().extraer(driver)

    assert events[0]["nombre"] == "Copa Mundial Sub-20 (F): Inglaterra vs Nigeria"
    assert events[0]["hora"] == "10:00"
    assert [option["canal"] for option in events[0]["opciones"]] == ["DSports 2", "TUDN MX"]
    assert "article.fl-event" in driver.script
    assert ".fl-event-channel[href]" in driver.script

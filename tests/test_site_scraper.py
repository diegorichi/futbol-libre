from scraping.site_scraper import SiteScraper


class _Driver:
    def __init__(self):
        self.current_url = None
        self.opened = []
        self.switch_to = self

    def default_content(self):
        pass

    def get(self, url):
        self.current_url = url
        self.opened.append(url)


def test_validation_and_scraping_open_each_site_once():
    driver = _Driver()
    progress = []

    def extractor(current_driver):
        return ([{"title": current_driver.current_url, "opciones": []}], "test")

    scraper = SiteScraper(extractor=extractor, matcher=lambda events: events)
    raw, sites, errors = scraper.scrape(
        driver,
        ["https://one.test", "https://two.test"],
        validation_callback=lambda current_driver: False,
        progress_callback=lambda done, total, url: progress.append((done, total, url)),
    )

    assert driver.opened == ["https://one.test", "https://two.test"]
    assert [site["url"] for site in sites] == driver.opened
    assert errors == []
    assert len(raw) == 2
    assert progress == [
        (1, 2, "https://one.test"),
        (2, 2, "https://two.test"),
    ]


def test_validation_failure_does_not_run_extractor():
    driver = _Driver()
    extracted = []

    def extractor(_):
        extracted.append(True)
        return ([], "test")

    scraper = SiteScraper(extractor=extractor, matcher=lambda events: events)
    raw, sites, errors = scraper.scrape(
        driver,
        ["https://invalid.test"],
        validation_callback=lambda current_driver: current_driver.current_url.endswith("invalid.test"),
    )

    assert raw == []
    assert sites == []
    assert extracted == []
    assert errors[0]["url"] == "https://invalid.test"
    assert errors[0]["phase"] == "validation"

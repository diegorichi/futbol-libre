from selenium.common.exceptions import TimeoutException

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

    def quit(self):
        pass


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


def test_isolated_driver_failure_does_not_break_following_site():
    class IsolatedDriver(_Driver):
        def __init__(self, fails=False):
            super().__init__()
            self.fails = fails
            self.closed = False

        def get(self, url):
            super().get(url)
            if self.fails:
                raise TimeoutError("site timed out")

        def quit(self):
            self.closed = True

    drivers = [IsolatedDriver(fails=True), IsolatedDriver()]
    created = []

    def driver_factory():
        driver = drivers[len(created)]
        created.append(driver)
        return driver

    scraper = SiteScraper(
        extractor=lambda current_driver: (
            [{"title": current_driver.current_url, "opciones": []}],
            "test",
        ),
        matcher=lambda events: events,
    )
    raw, sites, errors = scraper.scrape(
        None,
        ["https://broken.test", "https://healthy.test"],
        driver_factory=driver_factory,
    )

    assert [event["title"] for event in raw] == ["https://healthy.test"]
    assert [site["url"] for site in sites] == ["https://healthy.test"]
    assert [error["url"] for error in errors] == ["https://broken.test"]
    assert all(driver.closed for driver in drivers)


def test_page_load_timeout_uses_partial_dom_when_browser_is_responsive():
    class PartialDriver(_Driver):
        def __init__(self):
            super().__init__()
            self.stopped = False

        def get(self, url):
            super().get(url)
            raise TimeoutException("secondary resource did not finish")

        def execute_script(self, script):
            if script == "window.stop();":
                self.stopped = True
                return None
            return 1024

    driver = PartialDriver()
    scraper = SiteScraper(
        extractor=lambda current_driver: (
            [{"title": current_driver.current_url, "opciones": []}],
            "test",
        ),
        matcher=lambda events: events,
    )

    raw, sites, errors = scraper.scrape(driver, ["https://slow.test"])

    assert driver.stopped is True
    assert [event["title"] for event in raw] == ["https://slow.test"]
    assert [site["url"] for site in sites] == ["https://slow.test"]
    assert errors == []

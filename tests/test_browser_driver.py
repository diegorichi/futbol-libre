from pathlib import Path

from scraping import browser_driver


class _Options:
    def __init__(self):
        self.arguments = []

    def add_argument(self, _argument):
        self.arguments.append(_argument)


class _Driver:
    def __init__(self):
        self.page_load_timeout = None
        self.closed = False

    def set_page_load_timeout(self, timeout):
        self.page_load_timeout = timeout

    def quit(self):
        self.closed = True


def test_driver_factory_sets_timeout_and_removes_profile(monkeypatch, tmp_path):
    driver = _Driver()
    profile_dir = tmp_path / "profile"
    profile_dir.mkdir()
    monkeypatch.setattr(browser_driver.webdriver, "ChromeOptions", _Options)
    monkeypatch.setattr(browser_driver.webdriver, "Chrome", lambda **_kwargs: driver)
    monkeypatch.setattr(browser_driver.tempfile, "mkdtemp", lambda **_kwargs: str(profile_dir))

    created = browser_driver.BrowserDriverFactory(
        headless=False,
        page_load_timeout=17,
    ).create()

    assert created is driver
    assert driver.page_load_timeout == 17
    assert Path(driver._futbol_profile_dir) == profile_dir

    browser_driver.close_browser(driver)

    assert driver.closed is True
    assert not profile_dir.exists()

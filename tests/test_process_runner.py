import os
import signal

from server.services.process_runner import ProcessRunner


class _Status:
    def append(self, _message):
        pass

    def finish(self, _success, _message):
        pass


def test_signal_session_targets_every_process(monkeypatch, tmp_path):
    runner = ProcessRunner(str(tmp_path), _Status())
    sent = []
    monkeypatch.setattr(
        ProcessRunner,
        "_session_pids",
        staticmethod(lambda _session_id: [101, 102, 103]),
    )
    monkeypatch.setattr(os, "kill", lambda pid, signal_number: sent.append((pid, signal_number)))

    runner._signal_session(77, signal.SIGTERM)

    assert sent == [
        (103, signal.SIGTERM),
        (102, signal.SIGTERM),
        (101, signal.SIGTERM),
    ]


def test_stop_terminates_complete_scraper_session(monkeypatch, tmp_path):
    runner = ProcessRunner(str(tmp_path), _Status())
    terminated = []
    monkeypatch.setattr(runner, "_find_process_pids", lambda: [200])
    monkeypatch.setattr(runner, "_read_pid", lambda: None)
    monkeypatch.setattr(runner, "_is_update_process", lambda _pid: True)
    monkeypatch.setattr(runner, "_session_id", lambda pid: 900 if pid == 200 else None)
    monkeypatch.setattr(runner, "_terminate_session", terminated.append)
    monkeypatch.setattr(runner, "_pid_exists", lambda _pid: False)
    monkeypatch.setattr(runner, "_remove_pid", lambda _pid: None)

    assert runner.stop() is True
    assert terminated == [900]


def test_cleanup_browser_profiles_only_removes_matching_session(monkeypatch, tmp_path):
    matching = tmp_path / "futbol-chrome-900-one"
    unrelated = tmp_path / "futbol-chrome-901-two"
    matching.mkdir()
    unrelated.mkdir()
    monkeypatch.setattr("server.services.process_runner.tempfile.gettempdir", lambda: str(tmp_path))

    ProcessRunner._cleanup_browser_profiles(900)

    assert not matching.exists()
    assert unrelated.exists()

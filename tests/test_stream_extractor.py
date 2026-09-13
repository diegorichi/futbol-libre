import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class RuntimeDriver:
    def __init__(self, value):
        self.value = value

    def execute_script(self, script):
        self.script = script
        return self.value


class StreamExtractorTest(unittest.TestCase):
    def test_extracts_runtime_playback_url(self):
        from scraping.stream_extractor import StreamExtractionPool

        driver = RuntimeDriver("https://stream.example/live/index.m3u8?token=x")

        self.assertEqual(
            StreamExtractionPool.extract_runtime_url(driver),
            ("https://stream.example/live/index.m3u8?token=x", "playbackURL-runtime"),
        )
        self.assertIn("window.playbackURL", driver.script)

    def test_runtime_empty_value_falls_back(self):
        from scraping.stream_extractor import StreamExtractionPool

        self.assertEqual(StreamExtractionPool.extract_runtime_url(RuntimeDriver("")), (None, None))
        self.assertEqual(StreamExtractionPool.extract_runtime_url(RuntimeDriver(None)), (None, None))


if __name__ == "__main__":
    unittest.main()

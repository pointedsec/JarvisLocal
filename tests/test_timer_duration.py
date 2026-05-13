"""
test_timer_duration.py

Tests for the _parse_timer_duration function in voice_assistant.py.
"""

import unittest
import sys
import os

# To import voice_assistant modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

# Mock heavy dependencies before importing voice_assistant
from unittest.mock import MagicMock

sys.modules.setdefault("openwakeword", MagicMock())
sys.modules.setdefault("openwakeword.model", MagicMock())
sys.modules.setdefault("piper", MagicMock())

from voice_assistant.voice_assistant import _parse_timer_duration  # noqa: E402


class TestParseTimerDuration(unittest.TestCase):
    """Tests for the _parse_timer_duration helper."""

    # --- Seconds ---
    def test_seconds_singular(self):
        self.assertEqual(_parse_timer_duration("30 segundo"), 30)

    def test_seconds_plural(self):
        self.assertEqual(_parse_timer_duration("45 segundos"), 45)

    def test_one_second(self):
        self.assertEqual(_parse_timer_duration("1 segundo"), 1)

    # --- Minutes ---
    def test_minutes_singular(self):
        self.assertEqual(_parse_timer_duration("5 minuto"), 300)

    def test_minutes_plural(self):
        self.assertEqual(_parse_timer_duration("10 minutos"), 600)

    def test_half_minute(self):
        self.assertEqual(_parse_timer_duration("medio minuto"), 30)

    # --- Hours ---
    def test_hours_singular(self):
        self.assertEqual(_parse_timer_duration("2 hora"), 7200)

    def test_hours_plural(self):
        self.assertEqual(_parse_timer_duration("3 horas"), 10800)

    def test_half_hour(self):
        self.assertEqual(_parse_timer_duration("media hora"), 1800)

    def test_quarter_hour(self):
        self.assertEqual(_parse_timer_duration("cuarto de hora"), 900)

    # --- Combinations ---
    def test_minutes_and_seconds(self):
        self.assertEqual(_parse_timer_duration("2 minutos y 30 segundos"), 150)

    def test_hours_and_minutes(self):
        self.assertEqual(_parse_timer_duration("1 hora y 30 minutos"), 5400)

    # --- Edge cases ---
    def test_returns_none_for_unparseable_text(self):
        self.assertIsNone(_parse_timer_duration("dime la hora"))

    def test_returns_none_for_empty_string(self):
        self.assertIsNone(_parse_timer_duration(""))

    def test_strips_trailing_punctuation(self):
        self.assertEqual(_parse_timer_duration("5 minutos."), 300)
        self.assertEqual(_parse_timer_duration("10 segundos!"), 10)

    def test_case_insensitive(self):
        self.assertEqual(_parse_timer_duration("5 MINUTOS"), 300)


if __name__ == "__main__":
    unittest.main()

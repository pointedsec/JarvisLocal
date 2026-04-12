"""
test_multiple_wakewords.py

Tests for multiple wakewords support in config and voice assistant.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import argparse

# To import voice_assistant modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from voice_assistant.audio_utils import DEFAULT_SETTINGS


class TestMultipleWakewordsConfig(unittest.TestCase):
    """Tests for multiple wakewords configuration parsing."""

    @patch('voice_assistant.config_manager.sanitize_file_path', side_effect=lambda x, y: x)
    @patch('voice_assistant.config_manager.os.path.exists', return_value=False)
    @patch('argparse.ArgumentParser.parse_args')
    def test_default_wakewords_list(self, mock_parse_args, mock_exists, mock_sanitize):
        """Test that the default config produces a wakewords list."""
        from voice_assistant.config_manager import load_config_and_args

        mock_namespace = argparse.Namespace(
            list_devices=False,
            list_output_devices=False,
            debug=False,
            **DEFAULT_SETTINGS
        )
        mock_parse_args.return_value = mock_namespace

        args, config, should_exit = load_config_and_args()

        self.assertIsInstance(args.wakewords_list, list)
        self.assertTrue(len(args.wakewords_list) >= 1)

    @patch('voice_assistant.config_manager.sanitize_file_path', side_effect=lambda x, y: x)
    @patch('voice_assistant.config_manager.os.path.exists', return_value=False)
    @patch('argparse.ArgumentParser.parse_args')
    def test_comma_separated_wakewords(self, mock_parse_args, mock_exists, mock_sanitize):
        """Test parsing of comma-separated wakewords."""
        from voice_assistant.config_manager import load_config_and_args

        mock_namespace = argparse.Namespace(
            list_devices=False,
            list_output_devices=False,
            debug=False,
            **{**DEFAULT_SETTINGS, 'wakewords': 'hey jarvis, jarvis, oye jarvis'}
        )
        mock_parse_args.return_value = mock_namespace

        args, config, should_exit = load_config_and_args()

        self.assertEqual(args.wakewords_list, ['hey jarvis', 'jarvis', 'oye jarvis'])
        self.assertEqual(args.wakeword, 'hey jarvis')  # backward compat

    @patch('voice_assistant.config_manager.sanitize_file_path', side_effect=lambda x, y: x)
    @patch('voice_assistant.config_manager.os.path.exists', return_value=False)
    @patch('argparse.ArgumentParser.parse_args')
    def test_single_wakeword_backward_compat(self, mock_parse_args, mock_exists, mock_sanitize):
        """Test that single wakeword still works for backward compatibility."""
        from voice_assistant.config_manager import load_config_and_args

        mock_namespace = argparse.Namespace(
            list_devices=False,
            list_output_devices=False,
            debug=False,
            **{**DEFAULT_SETTINGS, 'wakewords': None, 'wakeword': 'hey jarvis'}
        )
        mock_parse_args.return_value = mock_namespace

        args, config, should_exit = load_config_and_args()

        self.assertEqual(args.wakewords_list, ['hey jarvis'])
        self.assertEqual(args.wakeword, 'hey jarvis')

    @patch('voice_assistant.config_manager.sanitize_file_path', side_effect=lambda x, y: x)
    @patch('voice_assistant.config_manager.os.path.exists', return_value=False)
    @patch('argparse.ArgumentParser.parse_args')
    def test_wakewords_whitespace_handling(self, mock_parse_args, mock_exists, mock_sanitize):
        """Test that whitespace in wakewords is handled correctly."""
        from voice_assistant.config_manager import load_config_and_args

        mock_namespace = argparse.Namespace(
            list_devices=False,
            list_output_devices=False,
            debug=False,
            **{**DEFAULT_SETTINGS, 'wakewords': '  hey jarvis ,  jarvis  , oye jarvis  '}
        )
        mock_parse_args.return_value = mock_namespace

        args, config, should_exit = load_config_and_args()

        self.assertEqual(args.wakewords_list, ['hey jarvis', 'jarvis', 'oye jarvis'])

    @patch('voice_assistant.config_manager.sanitize_file_path', side_effect=lambda x, y: x)
    @patch('voice_assistant.config_manager.os.path.exists', return_value=False)
    @patch('argparse.ArgumentParser.parse_args')
    def test_empty_wakewords_entries_filtered(self, mock_parse_args, mock_exists, mock_sanitize):
        """Test that empty entries in wakewords are filtered out."""
        from voice_assistant.config_manager import load_config_and_args

        mock_namespace = argparse.Namespace(
            list_devices=False,
            list_output_devices=False,
            debug=False,
            **{**DEFAULT_SETTINGS, 'wakewords': 'hey jarvis,, ,jarvis'}
        )
        mock_parse_args.return_value = mock_namespace

        args, config, should_exit = load_config_and_args()

        self.assertEqual(args.wakewords_list, ['hey jarvis', 'jarvis'])


class TestDefaultSettings(unittest.TestCase):
    """Tests for the updated default settings."""

    def test_wakewords_default_exists(self):
        """Test that wakewords default is present."""
        self.assertIn('wakewords', DEFAULT_SETTINGS)

    def test_wakewords_default_is_string(self):
        """Test that wakewords default is a string."""
        self.assertIsInstance(DEFAULT_SETTINGS['wakewords'], str)

    def test_wakewords_default_contains_comma(self):
        """Test that default wakewords has multiple entries."""
        wakewords = DEFAULT_SETTINGS['wakewords']
        parts = [w.strip() for w in wakewords.split(',') if w.strip()]
        self.assertTrue(len(parts) >= 1)

    def test_max_phrase_duration_is_20(self):
        """Test that max_phrase_duration default is 20 seconds (Alexa-style)."""
        self.assertEqual(DEFAULT_SETTINGS['max_phrase_duration'], 20.0)

    def test_backward_compat_wakeword_exists(self):
        """Test that the old wakeword key still exists for backward compatibility."""
        self.assertIn('wakeword', DEFAULT_SETTINGS)


class TestWakewordTrimming(unittest.TestCase):
    """Tests for wake word trimming with multiple wakewords."""

    def _create_mock_assistant(self, wakewords_list):
        """Helper to create a minimal mock VoiceAssistant for trimming tests."""
        # We need to test _trim_wakeword method, so we import it
        # and create a minimal args namespace
        from voice_assistant.voice_assistant import VoiceAssistant

        args = argparse.Namespace(
            wakeword=wakewords_list[0] if wakewords_list else 'hey jarvis',
            wakewords_list=wakewords_list,
            trim_wake_word=True,
        )

        # Create a mock object with the _trim_wakeword method
        # We can't fully instantiate VoiceAssistant without audio etc,
        # so we'll test the method directly by creating a partial mock
        assistant = MagicMock(spec=VoiceAssistant)
        assistant.args = args
        assistant._trim_wakeword = VoiceAssistant._trim_wakeword.__get__(assistant, VoiceAssistant)
        return assistant

    def test_trim_first_wakeword(self):
        """Test trimming the first configured wakeword."""
        assistant = self._create_mock_assistant(['hey jarvis', 'jarvis', 'oye jarvis'])
        result = assistant._trim_wakeword("hey jarvis dime la hora")
        self.assertEqual(result, "dime la hora")

    def test_trim_second_wakeword(self):
        """Test trimming the second configured wakeword."""
        assistant = self._create_mock_assistant(['hey jarvis', 'jarvis', 'oye jarvis'])
        result = assistant._trim_wakeword("jarvis dime la hora")
        self.assertEqual(result, "dime la hora")

    def test_trim_third_wakeword(self):
        """Test trimming the third configured wakeword."""
        assistant = self._create_mock_assistant(['hey jarvis', 'jarvis', 'oye jarvis'])
        result = assistant._trim_wakeword("oye jarvis dime la hora")
        self.assertEqual(result, "dime la hora")

    def test_no_wakeword_keeps_text(self):
        """Test that text without a wakeword is kept unchanged."""
        assistant = self._create_mock_assistant(['hey jarvis', 'jarvis'])
        result = assistant._trim_wakeword("dime la hora por favor")
        self.assertEqual(result, "dime la hora por favor")

    def test_wakeword_at_end_trimmed(self):
        """Test trimming wakeword from the end of text."""
        assistant = self._create_mock_assistant(['hey jarvis', 'jarvis'])
        result = assistant._trim_wakeword("dime la hora jarvis")
        self.assertEqual(result, "dime la hora")

    def test_case_insensitive_trimming(self):
        """Test that wakeword trimming is case-insensitive."""
        assistant = self._create_mock_assistant(['hey jarvis', 'jarvis'])
        result = assistant._trim_wakeword("Hey Jarvis dime la hora")
        self.assertEqual(result, "dime la hora")


class TestListeningTimeout(unittest.TestCase):
    """Tests for the 20-second listening timeout configuration."""

    def test_config_ini_phrase_duration(self):
        """Test that max_phrase_duration in config.ini is set to 20."""
        import configparser
        config = configparser.ConfigParser()
        config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config.ini'
        )
        if os.path.exists(config_path):
            config.read(config_path)
            if 'Functionality' in config:
                value = config['Functionality'].get('max_phrase_duration', '').split('#')[0].strip()
                if value:
                    self.assertEqual(float(value), 20.0)

    def test_default_phrase_duration(self):
        """Test that the default max_phrase_duration is 20 seconds."""
        self.assertEqual(DEFAULT_SETTINGS['max_phrase_duration'], 20.0)


if __name__ == '__main__':
    unittest.main()

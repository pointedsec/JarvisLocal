"""
test_config_manager_helpers.py

Tests for config_manager helper functions: sanitize_file_path,
device_index_type, check_internet_connectivity, and get_groq_client.
"""

import unittest
from unittest.mock import patch, MagicMock
import argparse
import sys
import os

# To import voice_assistant modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from voice_assistant.config_manager import (
    sanitize_file_path,
    device_index_type,
    check_internet_connectivity,
    get_groq_client,
    PROJECT_ROOT,
)


class TestSanitizeFilePath(unittest.TestCase):
    """Tests for the sanitize_file_path function."""

    def test_absolute_path_returned_unchanged_structure(self):
        """Test that an absolute path is returned as an absolute path."""
        abs_path = os.path.join(PROJECT_ROOT, "models", "test.onnx")
        result = sanitize_file_path(abs_path, "test model")
        self.assertTrue(os.path.isabs(result))

    def test_relative_path_resolved_to_project_root(self):
        """Test that a relative path is resolved relative to the project root."""
        result = sanitize_file_path("models/test.onnx", "wakeword model")
        self.assertTrue(os.path.isabs(result))
        self.assertTrue(result.startswith(PROJECT_ROOT))

    def test_empty_path_raises_value_error(self):
        """Test that an empty path raises ValueError."""
        with self.assertRaises(ValueError):
            sanitize_file_path("", "test file")

    def test_path_traversal_raises_value_error(self):
        """Test that path traversal attempts are rejected."""
        with self.assertRaises(ValueError):
            sanitize_file_path("../../etc/passwd", "test file")

    def test_model_path_outside_models_dir_raises(self):
        """Test that model paths outside models/ directory are rejected."""
        with self.assertRaises(ValueError):
            sanitize_file_path("configs/model.onnx", "wakeword model")

    def test_model_path_in_models_dir_accepted(self):
        """Test that model paths inside models/ directory are accepted."""
        result = sanitize_file_path("models/jarvis.onnx", "wakeword model")
        self.assertIn("models", result)

    def test_absolute_path_outside_project_root_allowed(self):
        """Test that absolute paths outside the project root are allowed."""
        abs_path = "/tmp/some_model.onnx"
        result = sanitize_file_path(abs_path, "test file")
        self.assertEqual(result, abs_path)


class TestDeviceIndexType(unittest.TestCase):
    """Tests for the device_index_type argument converter."""

    def test_integer_string_converted(self):
        """Test that an integer string is converted to int."""
        self.assertEqual(device_index_type("0"), 0)
        self.assertEqual(device_index_type("2"), 2)
        self.assertEqual(device_index_type("10"), 10)

    def test_none_string_returns_none(self):
        """Test that 'none' (case-insensitive) returns None."""
        self.assertIsNone(device_index_type("none"))
        self.assertIsNone(device_index_type("None"))
        self.assertIsNone(device_index_type("NONE"))

    def test_invalid_string_raises_argument_type_error(self):
        """Test that a non-integer string raises ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            device_index_type("abc")

    def test_float_string_rejected(self):
        """Test that float strings raise ArgumentTypeError."""
        with self.assertRaises(argparse.ArgumentTypeError):
            device_index_type("1.5")


class TestCheckInternetConnectivity(unittest.TestCase):
    """Tests for check_internet_connectivity."""

    @patch("voice_assistant.config_manager.socket.create_connection")
    @patch("voice_assistant.config_manager.socket.setdefaulttimeout")
    def test_returns_true_when_connected(self, mock_timeout, mock_connect):
        """Test returns True when TCP connection succeeds."""
        mock_connect.return_value.__enter__ = MagicMock(return_value=None)
        mock_connect.return_value.__exit__ = MagicMock(return_value=False)
        result = check_internet_connectivity()
        self.assertTrue(result)

    @patch(
        "voice_assistant.config_manager.socket.create_connection",
        side_effect=OSError("Connection refused"),
    )
    @patch("voice_assistant.config_manager.socket.setdefaulttimeout")
    def test_returns_false_when_disconnected(self, mock_timeout, mock_connect):
        """Test returns False when TCP connection fails."""
        result = check_internet_connectivity()
        self.assertFalse(result)


class TestGetGroqClient(unittest.TestCase):
    """Tests for get_groq_client."""

    def test_returns_none_when_api_key_missing(self):
        """Test returns None when the API key is empty."""
        result = get_groq_client("")
        self.assertIsNone(result)

    def test_returns_client_with_valid_api_key(self):
        """Test that a client is created when a valid API key is provided."""
        mock_client = MagicMock()
        mock_groq_class = MagicMock(return_value=mock_client)
        mock_groq_module = MagicMock()
        mock_groq_module.Groq = mock_groq_class

        with patch.dict(sys.modules, {"groq": mock_groq_module}):
            result = get_groq_client("valid-api-key")

        self.assertIsNotNone(result)
        mock_groq_class.assert_called_once_with(api_key="valid-api-key")

    def test_returns_none_on_client_creation_error(self):
        """Test returns None when Groq client creation raises an exception."""
        mock_groq_module = MagicMock()
        mock_groq_module.Groq.side_effect = Exception("Auth error")

        with patch.dict(sys.modules, {"groq": mock_groq_module}):
            result = get_groq_client("bad-key")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()

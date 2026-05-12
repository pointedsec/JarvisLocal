"""
test_groq_handler.py

Tests for the GroqHandler class, covering initialization, history management,
prompt augmentation, streaming, and error handling.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import argparse

# To import voice_assistant modules
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from voice_assistant.groq_handler import GroqHandler
from voice_assistant.audio_utils import MAX_HISTORY_MESSAGES


class TestGroqHandlerInit(unittest.TestCase):
    """Tests for GroqHandler initialization."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.args = argparse.Namespace(
            system_prompt="You are a helpful assistant.",
            groq_model="llama-3.3-70b-versatile",
        )

    def test_initialization(self):
        """Test that the handler initializes with the system prompt."""
        handler = GroqHandler(self.mock_client, self.args)
        self.assertEqual(len(handler.messages), 1)
        self.assertEqual(handler.messages[0]["role"], "system")
        self.assertEqual(handler.messages[0]["content"], self.args.system_prompt)

    def test_initial_token_counts_zero(self):
        """Test that token counters start at zero."""
        handler = GroqHandler(self.mock_client, self.args)
        self.assertEqual(handler.total_prompt_tokens, 0)
        self.assertEqual(handler.total_completion_tokens, 0)


class TestGroqHandlerResetHistory(unittest.TestCase):
    """Tests for reset_history method."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.args = argparse.Namespace(
            system_prompt="You are a helpful assistant.",
            groq_model="llama-3.3-70b-versatile",
        )
        self.handler = GroqHandler(self.mock_client, self.args)

    def test_reset_history_clears_messages(self):
        """Test that reset_history clears all messages except system prompt."""
        self.handler.messages.append({"role": "user", "content": "Hello"})
        self.handler.messages.append({"role": "assistant", "content": "Hi!"})
        self.assertEqual(len(self.handler.messages), 3)

        self.handler.reset_history()

        self.assertEqual(len(self.handler.messages), 1)
        self.assertEqual(self.handler.messages[0]["role"], "system")
        self.assertEqual(self.handler.messages[0]["content"], self.args.system_prompt)


class TestGroqHandlerBuildAugmentedPrompt(unittest.TestCase):
    """Tests for _build_augmented_prompt method."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.args = argparse.Namespace(
            system_prompt="You are a helpful assistant.",
            groq_model="llama-3.3-70b-versatile",
        )
        self.handler = GroqHandler(self.mock_client, self.args)

    @patch("voice_assistant.groq_handler.is_football_query", return_value=False)
    @patch("voice_assistant.groq_handler.needs_web_search", return_value=False)
    def test_no_augmentation_for_normal_query(
        self, mock_needs_search, mock_is_football
    ):
        """Test that normal queries pass through unchanged."""
        user_text = "¿Cuánto es 2 + 2?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertEqual(result, user_text)

    @patch("voice_assistant.groq_handler.is_football_query", return_value=True)
    @patch("voice_assistant.groq_handler.needs_web_search", return_value=False)
    def test_football_query_adds_manolo_lama_style(
        self, mock_needs_search, mock_is_football
    ):
        """Test that football queries add Manolo Lama style."""
        user_text = "¿Cómo quedó el Atleti?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertIn("Manolo Lama", result)
        self.assertIn(user_text, result)

    @patch("voice_assistant.groq_handler.web_search")
    @patch("voice_assistant.groq_handler.is_football_query", return_value=False)
    @patch("voice_assistant.groq_handler.needs_web_search", return_value=True)
    def test_web_search_results_added(
        self, mock_needs_search, mock_is_football, mock_web_search
    ):
        """Test that web search results are prepended to the prompt."""
        mock_web_search.return_value = [
            {"title": "Result", "body": "Info", "href": "https://example.com"}
        ]
        user_text = "¿Qué pasó ayer?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertIn("[Resultados de búsqueda en internet]:", result)
        self.assertIn(user_text, result)

    @patch("voice_assistant.groq_handler.web_search")
    @patch("voice_assistant.groq_handler.is_football_query", return_value=False)
    @patch("voice_assistant.groq_handler.needs_web_search", return_value=True)
    def test_no_augmentation_when_search_returns_nothing(
        self, mock_needs_search, mock_is_football, mock_web_search
    ):
        """Test that no augmentation happens when search returns None."""
        mock_web_search.return_value = None
        user_text = "¿Qué pasó ayer?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertEqual(result, user_text)


class TestGroqHandlerChatStream(unittest.TestCase):
    """Tests for chat_stream method."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.args = argparse.Namespace(
            system_prompt="You are a helpful assistant.",
            groq_model="llama-3.3-70b-versatile",
        )
        self.handler = GroqHandler(self.mock_client, self.args)

    @patch("voice_assistant.groq_handler.is_football_query", return_value=False)
    @patch("voice_assistant.groq_handler.needs_web_search", return_value=False)
    def test_chat_stream_success(self, mock_needs_search, mock_is_football):
        """Test a successful streaming chat response."""
        chunk1 = MagicMock()
        chunk1.choices[0].delta.content = "Hello"
        chunk2 = MagicMock()
        chunk2.choices[0].delta.content = " world"
        self.mock_client.chat.completions.create.return_value = [chunk1, chunk2]

        user_text = "Say hello"
        tokens = list(self.handler.chat_stream(user_text))

        self.assertEqual(tokens, ["Hello", " world"])
        self.assertEqual(len(self.handler.messages), 3)
        self.assertEqual(self.handler.messages[1]["role"], "user")
        self.assertEqual(self.handler.messages[2]["role"], "assistant")
        self.assertEqual(self.handler.messages[2]["content"], "Hello world")

    @patch("voice_assistant.groq_handler.is_football_query", return_value=False)
    @patch("voice_assistant.groq_handler.needs_web_search", return_value=False)
    def test_chat_stream_error_yields_none(self, mock_needs_search, mock_is_football):
        """Test that errors yield None and roll back user message."""
        self.mock_client.chat.completions.create.side_effect = Exception("API error")

        tokens = list(self.handler.chat_stream("Hello"))

        self.assertEqual(tokens, [None])
        # User message should be rolled back
        self.assertEqual(len(self.handler.messages), 1)
        self.assertEqual(self.handler.messages[0]["role"], "system")

    @patch("voice_assistant.groq_handler.is_football_query", return_value=False)
    @patch("voice_assistant.groq_handler.needs_web_search", return_value=False)
    def test_token_counts_accumulate(self, mock_needs_search, mock_is_football):
        """Test that token counts accumulate across calls."""
        chunk = MagicMock()
        chunk.choices[
            0
        ].delta.content = "This is a longer response to ensure token count"
        self.mock_client.chat.completions.create.return_value = [chunk]

        list(self.handler.chat_stream("Hello, how are you doing today?"))
        self.assertGreater(self.handler.total_prompt_tokens, 0)
        self.assertGreater(self.handler.total_completion_tokens, 0)


class TestGroqHandlerPruneHistory(unittest.TestCase):
    """Tests for _prune_history method."""

    def setUp(self):
        self.mock_client = MagicMock()
        self.args = argparse.Namespace(
            system_prompt="You are a helpful assistant.",
            groq_model="llama-3.3-70b-versatile",
        )
        self.handler = GroqHandler(self.mock_client, self.args)

    @patch("voice_assistant.groq_handler.gc.collect")
    def test_prune_history_trims_excess_messages(self, mock_gc):
        """Test that history is pruned to MAX_HISTORY_MESSAGES pairs."""
        for i in range(MAX_HISTORY_MESSAGES + 5):
            self.handler.messages.append({"role": "user", "content": f"User {i}"})
            self.handler.messages.append({"role": "assistant", "content": f"Bot {i}"})

        self.handler._prune_history()

        expected = MAX_HISTORY_MESSAGES * 2 + 1
        self.assertEqual(len(self.handler.messages), expected)
        self.assertEqual(self.handler.messages[0]["role"], "system")
        mock_gc.assert_called_once()

    def test_prune_history_no_op_when_within_limit(self):
        """Test that no pruning happens when within message limit."""
        self.handler.messages.append({"role": "user", "content": "Hi"})
        self.handler.messages.append({"role": "assistant", "content": "Hello"})

        self.handler._prune_history()

        self.assertEqual(len(self.handler.messages), 3)


if __name__ == "__main__":
    unittest.main()

"""
test_llm_handler_search.py

Tests for the LLM handler's web search and football detection integration.
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import argparse

# To import voice_assistant modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from voice_assistant.llm_handler import LLMHandler


class TestLLMHandlerAugmentedPrompt(unittest.TestCase):
    """Tests for the _build_augmented_prompt method."""

    def setUp(self):
        """Set up a mock client and args for each test."""
        self.mock_client = MagicMock()
        self.args = argparse.Namespace(
            system_prompt="You are a helpful assistant.",
            ollama_model="test_model"
        )
        self.handler = LLMHandler(self.mock_client, self.args)

    @patch('voice_assistant.llm_handler.is_football_query', return_value=False)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=False)
    def test_no_augmentation_for_normal_query(self, mock_needs_search, mock_is_football):
        """Test that normal queries are not augmented."""
        user_text = "¿Cuánto es 2 + 2?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertEqual(result, user_text)

    @patch('voice_assistant.llm_handler.is_football_query', return_value=True)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=False)
    def test_football_query_adds_manolo_lama_style(self, mock_needs_search, mock_is_football):
        """Test that football queries add Manolo Lama style."""
        user_text = "¿Cómo quedó el partido del Atleti?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertIn("Manolo Lama", result)
        self.assertIn(user_text, result)

    @patch('voice_assistant.llm_handler.web_search')
    @patch('voice_assistant.llm_handler.is_football_query', return_value=False)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=True)
    def test_current_info_query_adds_search_results(self, mock_needs_search, mock_is_football, mock_web_search):
        """Test that current-info queries add web search results."""
        mock_web_search.return_value = [
            {"title": "Result", "body": "Some info", "href": "https://example.com"}
        ]
        user_text = "¿Qué pasó ayer en las noticias?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertIn("[Resultados de búsqueda en internet]:", result)
        self.assertIn("Result", result)
        self.assertIn(user_text, result)
        mock_web_search.assert_called_once_with(user_text)

    @patch('voice_assistant.llm_handler.web_search')
    @patch('voice_assistant.llm_handler.is_football_query', return_value=True)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=True)
    def test_football_and_search_combined(self, mock_needs_search, mock_is_football, mock_web_search):
        """Test that football queries with search needs get both augmentations."""
        mock_web_search.return_value = [
            {"title": "Atlético 2-1 Real Madrid", "body": "Victoria colchonera", "href": "https://example.com"}
        ]
        user_text = "¿Cómo quedó ayer el Atleti?"
        result = self.handler._build_augmented_prompt(user_text)
        self.assertIn("Manolo Lama", result)
        self.assertIn("[Resultados de búsqueda en internet]:", result)
        self.assertIn(user_text, result)

    @patch('voice_assistant.llm_handler.web_search')
    @patch('voice_assistant.llm_handler.is_football_query', return_value=False)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=True)
    def test_search_with_no_results(self, mock_needs_search, mock_is_football, mock_web_search):
        """Test handling of web search that returns no results."""
        mock_web_search.return_value = None
        user_text = "¿Qué pasó ayer?"
        result = self.handler._build_augmented_prompt(user_text)
        # Should just return the original text since no results were found
        self.assertEqual(result, user_text)

    @patch('voice_assistant.llm_handler.web_search')
    @patch('voice_assistant.llm_handler.is_football_query', return_value=False)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=True)
    def test_search_results_prepended_to_user_text(self, mock_needs_search, mock_is_football, mock_web_search):
        """Test that search results are prepended before the user text."""
        mock_web_search.return_value = [
            {"title": "Info", "body": "Details", "href": "https://example.com"}
        ]
        user_text = "Pregunta del usuario"
        result = self.handler._build_augmented_prompt(user_text)
        # Search context should come before the user text
        search_idx = result.index("[Resultados de búsqueda en internet]:")
        user_idx = result.index(user_text)
        self.assertLess(search_idx, user_idx)

    @patch('voice_assistant.llm_handler.is_football_query', return_value=True)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=False)
    def test_manolo_lama_style_prepended_to_user_text(self, mock_needs_search, mock_is_football):
        """Test that Manolo Lama style is prepended before the user text."""
        user_text = "¿Cómo va la liga?"
        result = self.handler._build_augmented_prompt(user_text)
        manolo_idx = result.index("Manolo Lama")
        user_idx = result.index(user_text)
        self.assertLess(manolo_idx, user_idx)


class TestLLMHandlerChatStreamWithSearch(unittest.TestCase):
    """Tests that chat_stream correctly uses augmented prompts."""

    def setUp(self):
        """Set up a mock client and args for each test."""
        self.mock_client = MagicMock()
        self.args = argparse.Namespace(
            system_prompt="You are a helpful assistant.",
            ollama_model="test_model"
        )
        self.handler = LLMHandler(self.mock_client, self.args)

    @patch('voice_assistant.llm_handler.is_football_query', return_value=True)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=False)
    def test_chat_stream_uses_augmented_prompt(self, mock_needs_search, mock_is_football):
        """Test that chat_stream sends the augmented prompt to the LLM."""
        mock_response_chunks = [
            {'message': {'content': '¡GOOOL!'}},
        ]
        self.mock_client.chat.return_value = mock_response_chunks

        user_text = "¿Cómo va la liga?"
        result = list(self.handler.chat_stream(user_text))

        # After streaming, messages list has: system, user, assistant
        # The user message (index 1) should contain the augmented prompt
        user_message = self.handler.messages[1]
        self.assertEqual(user_message['role'], 'user')
        self.assertIn("Manolo Lama", user_message['content'])
        self.assertIn(user_text, user_message['content'])

    @patch('voice_assistant.llm_handler.is_football_query', return_value=False)
    @patch('voice_assistant.llm_handler.needs_web_search', return_value=False)
    def test_chat_stream_normal_query_unchanged(self, mock_needs_search, mock_is_football):
        """Test that normal queries are sent unchanged to the LLM."""
        mock_response_chunks = [
            {'message': {'content': '4'}},
        ]
        self.mock_client.chat.return_value = mock_response_chunks

        user_text = "¿Cuánto es 2 + 2?"
        result = list(self.handler.chat_stream(user_text))

        # After streaming, messages list has: system, user, assistant
        user_message = self.handler.messages[1]
        self.assertEqual(user_message['content'], user_text)


if __name__ == '__main__':
    unittest.main()

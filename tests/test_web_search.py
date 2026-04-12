"""
test_web_search.py

Tests for the web search module including football detection,
current-info detection, search formatting, and search execution.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# To import voice_assistant modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from voice_assistant.web_search import (
    is_football_query,
    needs_web_search,
    web_search,
    format_search_results,
    MANOLO_LAMA_STYLE,
    FOOTBALL_KEYWORDS,
    CURRENT_INFO_KEYWORDS,
)


class TestIsFootballQuery(unittest.TestCase):
    """Tests for the is_football_query function."""

    def test_detects_spanish_football_terms(self):
        """Test detection of common Spanish football terms."""
        self.assertTrue(is_football_query("¿Cómo quedó el partido de ayer?"))
        self.assertTrue(is_football_query("¿Quién metió el gol?"))
        self.assertTrue(is_football_query("Resultados de la liga"))
        self.assertTrue(is_football_query("Dime sobre la Champions League"))

    def test_detects_team_names(self):
        """Test detection of football team names."""
        self.assertTrue(is_football_query("¿Cómo quedó el Atleti?"))
        self.assertTrue(is_football_query("¿Ganó el Real Madrid?"))
        self.assertTrue(is_football_query("El Barça jugó bien"))
        self.assertTrue(is_football_query("Resultados del Barcelona"))
        self.assertTrue(is_football_query("¿Cómo va el Sevilla?"))
        self.assertTrue(is_football_query("El Betis perdió"))

    def test_detects_player_names(self):
        """Test detection of famous footballer names."""
        self.assertTrue(is_football_query("¿Cuántos goles lleva Messi?"))
        self.assertTrue(is_football_query("Cristiano Ronaldo marcó"))
        self.assertTrue(is_football_query("Mbappé fichó por el Madrid"))
        self.assertTrue(is_football_query("Bellingham está en forma"))

    def test_detects_english_football_terms(self):
        """Test detection of English football terms."""
        self.assertTrue(is_football_query("What was the football score?"))
        self.assertTrue(is_football_query("Premier League results"))
        self.assertTrue(is_football_query("Liverpool won the match"))

    def test_non_football_queries(self):
        """Test that non-football queries are not detected."""
        self.assertFalse(is_football_query("¿Qué tiempo hace hoy?"))
        self.assertFalse(is_football_query("¿Cuál es la capital de Francia?"))
        self.assertFalse(is_football_query("Cuéntame un chiste"))
        self.assertFalse(is_football_query("¿Cómo se cocina una tortilla?"))

    def test_case_insensitive(self):
        """Test that detection is case-insensitive."""
        self.assertTrue(is_football_query("FÚTBOL"))
        self.assertTrue(is_football_query("Real MADRID"))
        self.assertTrue(is_football_query("champions LEAGUE"))

    def test_empty_string(self):
        """Test with empty string."""
        self.assertFalse(is_football_query(""))

    def test_football_positions(self):
        """Test detection of football position terms."""
        self.assertTrue(is_football_query("El portero paró un penalti"))
        self.assertTrue(is_football_query("El delantero metió un golazo"))
        self.assertTrue(is_football_query("El centrocampista distribuyó bien"))

    def test_football_events(self):
        """Test detection of football events."""
        self.assertTrue(is_football_query("Le sacaron tarjeta roja"))
        self.assertTrue(is_football_query("Hubo un penalti claro"))
        self.assertTrue(is_football_query("Estaba fuera de juego"))


class TestNeedsWebSearch(unittest.TestCase):
    """Tests for the needs_web_search function."""

    def test_time_sensitive_queries(self):
        """Test detection of time-sensitive queries."""
        self.assertTrue(needs_web_search("¿Qué pasó ayer?"))
        self.assertTrue(needs_web_search("Noticias de hoy"))
        self.assertTrue(needs_web_search("¿Cómo quedó el partido de anoche?"))
        self.assertTrue(needs_web_search("Resultados de esta semana"))

    def test_sports_results_queries(self):
        """Test detection of sports result queries."""
        self.assertTrue(needs_web_search("¿Cuál fue el resultado?"))
        self.assertTrue(needs_web_search("¿Quién ganó el partido?"))
        self.assertTrue(needs_web_search("Clasificación de la liga"))
        self.assertTrue(needs_web_search("Marcador del partido"))

    def test_news_queries(self):
        """Test detection of news queries."""
        self.assertTrue(needs_web_search("Últimas noticias"))
        self.assertTrue(needs_web_search("¿Qué ha pasado?"))
        self.assertTrue(needs_web_search("Última hora"))

    def test_price_weather_queries(self):
        """Test detection of price/weather queries."""
        self.assertTrue(needs_web_search("¿Cuál es el precio del Bitcoin?"))
        self.assertTrue(needs_web_search("¿Qué tiempo hace?"))
        self.assertTrue(needs_web_search("Cotización de las acciones"))

    def test_non_current_info_queries(self):
        """Test that general knowledge queries don't trigger search."""
        self.assertFalse(needs_web_search("¿Cuál es la raíz cuadrada de 144?"))
        self.assertFalse(needs_web_search("Cuéntame un chiste"))
        self.assertFalse(needs_web_search("¿Cómo se dice hola en inglés?"))

    def test_empty_string(self):
        """Test with empty string."""
        self.assertFalse(needs_web_search(""))


class TestFormatSearchResults(unittest.TestCase):
    """Tests for the format_search_results function."""

    def test_formats_multiple_results(self):
        """Test formatting of multiple search results."""
        results = [
            {"title": "Result 1", "body": "Description 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Description 2", "href": "https://example.com/2"},
        ]
        formatted = format_search_results(results)
        self.assertIn("[Resultados de búsqueda en internet]:", formatted)
        self.assertIn("1. Result 1: Description 1", formatted)
        self.assertIn("2. Result 2: Description 2", formatted)

    def test_formats_single_result(self):
        """Test formatting of a single search result."""
        results = [
            {"title": "Only Result", "body": "Only Description", "href": "https://example.com"},
        ]
        formatted = format_search_results(results)
        self.assertIn("1. Only Result: Only Description", formatted)

    def test_empty_results(self):
        """Test formatting with empty results."""
        self.assertEqual(format_search_results([]), "")

    def test_none_results(self):
        """Test formatting with None."""
        self.assertEqual(format_search_results(None), "")

    def test_missing_fields(self):
        """Test formatting when result fields are missing."""
        results = [{"title": "Test"}]
        formatted = format_search_results(results)
        self.assertIn("Sin descripción", formatted)

    def test_missing_title(self):
        """Test formatting when title is missing."""
        results = [{"body": "A description"}]
        formatted = format_search_results(results)
        self.assertIn("Sin título", formatted)


class TestWebSearch(unittest.TestCase):
    """Tests for the web_search function."""

    @patch('voice_assistant.web_search.DDGS_AVAILABLE', True)
    @patch('voice_assistant.web_search.DDGS')
    def test_successful_search(self, mock_ddgs_class):
        """Test a successful web search."""
        mock_results = [
            {"title": "Result 1", "body": "Desc 1", "href": "https://example.com/1"},
            {"title": "Result 2", "body": "Desc 2", "href": "https://example.com/2"},
        ]
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = mock_results
        mock_ddgs_class.return_value.__enter__ = MagicMock(return_value=mock_ddgs_instance)
        mock_ddgs_class.return_value.__exit__ = MagicMock(return_value=False)

        results = web_search("test query", max_results=2)

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Result 1")
        mock_ddgs_instance.text.assert_called_once_with(
            "test query", max_results=2, region="es-es"
        )

    @patch('voice_assistant.web_search.DDGS_AVAILABLE', True)
    @patch('voice_assistant.web_search.DDGS')
    def test_empty_results(self, mock_ddgs_class):
        """Test web search with no results."""
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = []
        mock_ddgs_class.return_value.__enter__ = MagicMock(return_value=mock_ddgs_instance)
        mock_ddgs_class.return_value.__exit__ = MagicMock(return_value=False)

        results = web_search("nonexistent query xyz")
        self.assertIsNone(results)

    @patch('voice_assistant.web_search.DDGS_AVAILABLE', True)
    @patch('voice_assistant.web_search.DDGS')
    def test_search_exception(self, mock_ddgs_class):
        """Test web search when an exception occurs."""
        mock_ddgs_class.return_value.__enter__ = MagicMock(
            side_effect=Exception("Network error")
        )
        mock_ddgs_class.return_value.__exit__ = MagicMock(return_value=False)

        results = web_search("test query")
        self.assertIsNone(results)

    @patch('voice_assistant.web_search.DDGS_AVAILABLE', False)
    def test_search_unavailable(self):
        """Test web search when duckduckgo-search is not installed."""
        results = web_search("test query")
        self.assertIsNone(results)


class TestManoloLamaStyle(unittest.TestCase):
    """Tests for the Manolo Lama style constant."""

    def test_style_contains_key_phrases(self):
        """Test that the Manolo Lama style prompt contains key phrases."""
        self.assertIn("Manolo Lama", MANOLO_LAMA_STYLE)
        self.assertIn("GOOOOL", MANOLO_LAMA_STYLE)
        self.assertIn("fútbol", MANOLO_LAMA_STYLE)

    def test_style_is_non_empty(self):
        """Test that the style prompt is non-empty."""
        self.assertTrue(len(MANOLO_LAMA_STYLE) > 0)


class TestKeywordLists(unittest.TestCase):
    """Tests for the keyword lists."""

    def test_football_keywords_non_empty(self):
        """Test that football keywords list is non-empty."""
        self.assertTrue(len(FOOTBALL_KEYWORDS) > 0)

    def test_current_info_keywords_non_empty(self):
        """Test that current info keywords list is non-empty."""
        self.assertTrue(len(CURRENT_INFO_KEYWORDS) > 0)

    def test_football_keywords_are_lowercase(self):
        """Test that all football keywords are lowercase."""
        for keyword in FOOTBALL_KEYWORDS:
            self.assertEqual(keyword, keyword.lower(),
                             f"Keyword '{keyword}' is not lowercase")

    def test_current_info_keywords_are_lowercase(self):
        """Test that all current info keywords are lowercase."""
        for keyword in CURRENT_INFO_KEYWORDS:
            self.assertEqual(keyword, keyword.lower(),
                             f"Keyword '{keyword}' is not lowercase")


if __name__ == '__main__':
    unittest.main()

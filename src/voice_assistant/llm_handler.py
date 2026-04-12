import logging
import ollama
import gc
from .audio_utils import MAX_HISTORY_MESSAGES, SENTENCE_END_PUNCTUATION
from .web_search import (
    is_football_query,
    needs_web_search,
    web_search,
    format_search_results,
    MANOLO_LAMA_STYLE,
)

class LLMHandler:
    def __init__(self, client: ollama.Client, args):
        self.client = client
        self.args = args
        self.messages = []
        self.reset_history()

    def reset_history(self):
        self.messages = [{'role': 'system', 'content': self.args.system_prompt}]

    def _build_augmented_prompt(self, user_text: str) -> str:
        """
        Augments the user prompt with web search results and/or football style
        instructions when needed.

        Returns the (possibly augmented) user text to send to the LLM.
        """
        parts = []

        # Check if the query is football-related
        is_football = is_football_query(user_text)
        if is_football:
            logging.info("Football query detected — activating Manolo Lama mode")
            parts.append(MANOLO_LAMA_STYLE)

        # Check if the query needs current information from the internet
        if needs_web_search(user_text):
            logging.info("Query may need current info — performing web search")
            results = web_search(user_text)
            if results:
                context = format_search_results(results)
                parts.append(context)
                logging.debug(f"Web search context added ({len(results)} results)")
            else:
                logging.debug("No web search results found")

        if parts:
            # Prepend the augmented context to the user text
            augmented = "\n\n".join(parts) + "\n\n" + user_text
            return augmented

        return user_text

    def chat_stream(self, user_text: str):
        """Yields tokens from the LLM response."""
        augmented_text = self._build_augmented_prompt(user_text)
        self.messages.append({'role': 'user', 'content': augmented_text})
        self._prune_history()
        
        full_response = ""
        try:
            stream = self.client.chat(
                model=self.args.ollama_model,
                messages=self.messages,
                stream=True
            )
            for chunk in stream:
                token = chunk.get('message', {}).get('content', '')
                full_response += token
                yield token
                
            self.messages.append({'role': 'assistant', 'content': full_response})
            
        except Exception as e:
            logging.error(f"Ollama Error: {e}")
            # Rollback user message on failure
            if self.messages and self.messages[-1]['role'] == 'user':
                self.messages.pop()
            yield None

    def _prune_history(self):
        """More aggressive history management"""
        # Keep system prompt + recent exchanges
        max_pairs = MAX_HISTORY_MESSAGES
        
        if len(self.messages) > (max_pairs * 2 + 1):
            # Keep system prompt (index 0)
            system_prompt = self.messages[0]
            # Keep only recent messages
            recent = self.messages[-(max_pairs * 2):]
            self.messages = [system_prompt] + recent
            
            # Force garbage collection after major prune
            gc.collect()
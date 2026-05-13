import logging
import gc
from .audio_utils import MAX_HISTORY_MESSAGES
from .web_search import (
    is_football_query,
    needs_web_search,
    web_search,
    format_search_results,
    MANOLO_LAMA_STYLE,
)


class GroqHandler:
    """LLM handler that uses the Groq API for fast cloud inference."""

    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.messages = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.reset_history()

    def reset_history(self):
        self.messages = [{"role": "system", "content": self.args.system_prompt}]

    def _build_augmented_prompt(self, user_text: str) -> str:
        """
        Augments the user prompt with web search results and/or football style
        instructions when needed.
        """
        parts = []

        is_football = is_football_query(user_text)
        if is_football:
            logging.info("Football query detected — activating Manolo Lama mode")
            parts.append(MANOLO_LAMA_STYLE)

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
            augmented = "\n\n".join(parts) + "\n\n" + user_text
            return augmented

        return user_text

    def chat_stream(self, user_text: str):
        """Yields tokens from the Groq API response."""
        augmented_text = self._build_augmented_prompt(user_text)
        self.messages.append({"role": "user", "content": augmented_text})
        self._prune_history()

        full_response = ""
        try:
            prompt_tokens = sum(len(m["content"]) // 4 for m in self.messages)
            stream = self.client.chat.completions.create(
                model=self.args.groq_model,
                messages=self.messages,
                stream=True,
            )
            for chunk in stream:
                token = chunk.choices[0].delta.content or ""
                full_response += token
                yield token

            completion_tokens = len(full_response) // 4
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
            logging.info(
                f"[Groq tokens] prompt≈{prompt_tokens} completion≈{completion_tokens} "
                f"total≈{prompt_tokens + completion_tokens} | "
                f"acumulado≈{self.total_prompt_tokens + self.total_completion_tokens}"
            )

            self.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            logging.error(f"Groq Error: {e}")
            if self.messages and self.messages[-1]["role"] == "user":
                self.messages.pop()
            yield None

    def _prune_history(self):
        """
        Prunes the conversation history to keep memory usage bounded.
        Retains the system prompt (index 0) plus the most recent
        MAX_HISTORY_MESSAGES user/assistant pairs and forces garbage
        collection after any prune.
        """
        max_pairs = MAX_HISTORY_MESSAGES

        if len(self.messages) > (max_pairs * 2 + 1):
            system_prompt = self.messages[0]
            recent = self.messages[-(max_pairs * 2) :]
            self.messages = [system_prompt] + recent
            gc.collect()

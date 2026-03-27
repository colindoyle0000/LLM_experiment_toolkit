"""
models.py — Handles the actual communication with each AI provider's API.

This file wraps three different APIs (Anthropic, OpenAI, Google) behind
one shared interface. No matter which provider you use, the rest of the
toolkit just calls client.call(system_prompt, user_prompt) and gets back
a ModelResponse with the text, token counts, and timing.

If an API call fails (network error, rate limit, etc.), the error is
caught here and recorded in the response rather than crashing the experiment.

YOU PROBABLY DON'T NEED TO EDIT THIS FILE.
If a provider changes their API or you need to pass additional parameters
(like response format or stop sequences), this is where to make that change.
"""

import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelResponse:
    """The result of a single API call."""
    content: str
    provider: str
    model_name: str
    temperature: float
    max_tokens: int
    input_tokens: int
    output_tokens: int
    duration_seconds: float
    error: str | None = None


class AnthropicClient:
    def __init__(self, model_name: str, temperature: float, max_tokens: int):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not found. "
                "Check that your .env file contains ANTHROPIC_API_KEY=your_key_here"
            )
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def call(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start = time.time()
        try:
            response = self._client.messages.create(
                model=self.model_name,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            content = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            error = None
        except Exception as e:
            content = ""
            input_tokens = 0
            output_tokens = 0
            error = f"{type(e).__name__}: {e}"

        return ModelResponse(
            content=content,
            provider="anthropic",
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=round(time.time() - start, 2),
            error=error,
        )


class OpenAIClient:
    def __init__(self, model_name: str, temperature: float, max_tokens: int):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found. "
                "Check that your .env file contains OPENAI_API_KEY=your_key_here"
            )
        import openai
        self._client = openai.OpenAI(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _uses_max_completion_tokens(self) -> bool:
        """Newer OpenAI models (o1, o3, o4-mini, gpt-5, etc.) use max_completion_tokens."""
        name = self.model_name.lower()
        import re
        return bool(re.match(r"o\d", name)) or name.startswith("gpt-5")

    def call(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start = time.time()
        try:
            is_new_model = self._uses_max_completion_tokens()
            token_param = "max_completion_tokens" if is_new_model else "max_tokens"
            params = {
                "model": self.model_name,
                token_param: self.max_tokens,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            }
            if not is_new_model:
                params["temperature"] = self.temperature
            response = self._client.chat.completions.create(**params)
            content = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            error = None
        except Exception as e:
            content = ""
            input_tokens = 0
            output_tokens = 0
            error = f"{type(e).__name__}: {e}"

        return ModelResponse(
            content=content,
            provider="openai",
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=round(time.time() - start, 2),
            error=error,
        )


class GeminiClient:
    def __init__(self, model_name: str, temperature: float, max_tokens: int):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY not found. "
                "Check that your .env file contains GEMINI_API_KEY=your_key_here"
            )
        from google import genai
        self._client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def call(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        from google.genai import types

        start = time.time()
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                ),
            )
            content = response.text or ""
            # Gemini token counts come from usage_metadata
            meta = response.usage_metadata
            input_tokens = getattr(meta, "prompt_token_count", 0) or 0
            output_tokens = getattr(meta, "candidates_token_count", 0) or 0
            # Detect safety blocks: Gemini returns empty text instead of raising
            if not content:
                finish_reason = None
                safety_info = ""
                candidates = getattr(response, "candidates", None)
                if candidates:
                    finish_reason = getattr(candidates[0], "finish_reason", None)
                    ratings = getattr(candidates[0], "safety_ratings", []) or []
                    blocked = [r for r in ratings if getattr(r, "blocked", False)]
                    if blocked:
                        safety_info = "; ".join(str(r.category) for r in blocked)
                prompt_feedback = getattr(response, "prompt_feedback", None)
                block_reason = getattr(prompt_feedback, "block_reason", None)
                if block_reason:
                    error = f"Blocked by Gemini (prompt): {block_reason}"
                elif safety_info:
                    error = f"Blocked by Gemini (safety): {safety_info}"
                elif finish_reason and str(finish_reason) not in ("FinishReason.STOP", "STOP", "1"):
                    error = f"Gemini finish_reason: {finish_reason}"
                else:
                    error = "Gemini returned empty response (unknown reason)"
            else:
                error = None
        except Exception as e:
            content = ""
            input_tokens = 0
            output_tokens = 0
            error = f"{type(e).__name__}: {e}"

        return ModelResponse(
            content=content,
            provider="google",
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_seconds=round(time.time() - start, 2),
            error=error,
        )


def create_client(model_config) -> "AnthropicClient | OpenAIClient | GeminiClient":
    """Return the appropriate API client for the given model configuration."""
    if model_config.provider == "anthropic":
        return AnthropicClient(model_config.name, model_config.temperature, model_config.max_tokens)
    elif model_config.provider == "openai":
        return OpenAIClient(model_config.name, model_config.temperature, model_config.max_tokens)
    elif model_config.provider == "google":
        return GeminiClient(model_config.name, model_config.temperature, model_config.max_tokens)
    else:
        raise ValueError(f"Unknown provider: '{model_config.provider}'. Must be 'anthropic', 'openai', or 'google'.")

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

    def _uses_responses_api(self) -> bool:
        """Reasoning-era OpenAI models work more reliably with the Responses API."""
        name = self.model_name.lower()
        import re
        return bool(re.match(r"o\d", name)) or name.startswith("gpt-5")

    def _default_reasoning(self) -> dict[str, str] | None:
        """
        GPT-5 spends from the same output-token budget on hidden reasoning.
        A minimal default avoids blank responses at modest max_tokens values.
        """
        name = self.model_name.lower()
        if name.startswith("gpt-5") and "pro" not in name:
            return {"effort": "minimal"}
        return None

    @staticmethod
    def _extract_response_text(response) -> str:
        """
        Prefer the SDK's flattened text helper, then fall back to the raw
        output structure if needed.
        """
        text = getattr(response, "output_text", None)
        if text:
            return text

        pieces: list[str] = []
        for item in getattr(response, "output", []) or []:
            if getattr(item, "type", None) != "message":
                continue
            for content in getattr(item, "content", []) or []:
                content_type = getattr(content, "type", None)
                if content_type in ("output_text", "text"):
                    piece = getattr(content, "text", "") or ""
                    if piece:
                        pieces.append(piece)
        return "".join(pieces)

    @staticmethod
    def _extract_usage_tokens(response) -> tuple[int, int]:
        """Handle usage objects from both chat completions and responses."""
        usage = getattr(response, "usage", None)
        if usage is None:
            return 0, 0

        input_tokens = (
            getattr(usage, "input_tokens", None)
            or getattr(usage, "prompt_tokens", None)
            or 0
        )
        output_tokens = (
            getattr(usage, "output_tokens", None)
            or getattr(usage, "completion_tokens", None)
            or 0
        )
        return int(input_tokens), int(output_tokens)

    @staticmethod
    def _extract_api_error(response) -> str | None:
        """Surface non-exception OpenAI failures instead of writing a blank file."""
        error = getattr(response, "error", None)
        if error:
            message = getattr(error, "message", None)
            return str(message or error)

        status = getattr(response, "status", None)
        if status and status != "completed":
            details = getattr(response, "incomplete_details", None)
            if details:
                reason = getattr(details, "reason", None)
                if reason == "max_output_tokens":
                    return (
                        "OpenAI hit max_output_tokens before producing visible text. "
                        "Increase max_tokens for this model."
                    )
                return f"OpenAI response status '{status}': {details}"
            return f"OpenAI response status '{status}'"

        return None

    def call(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        start = time.time()
        try:
            if self._uses_responses_api():
                params = {
                    "model": self.model_name,
                    "instructions": system_prompt,
                    "input": user_prompt,
                    "max_output_tokens": self.max_tokens,
                }
                reasoning = self._default_reasoning()
                if reasoning:
                    params["reasoning"] = reasoning
                response = self._client.responses.create(**params)
                content = self._extract_response_text(response)
                input_tokens, output_tokens = self._extract_usage_tokens(response)
                error = self._extract_api_error(response)
                if content:
                    error = None
                elif not error:
                    error = "OpenAI returned an empty response"
            else:
                response = self._client.chat.completions.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                content = response.choices[0].message.content or ""
                input_tokens, output_tokens = self._extract_usage_tokens(response)
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

    def _default_thinking_config(self, types_module):
        """
        Gemini 2.5 Pro can return empty text under dynamic thinking even when
        Flash succeeds on the same prompt. Pinning the minimum valid thinking
        budget makes Pro's behavior much more stable for this toolkit.
        """
        if self.model_name.lower().startswith("gemini-2.5-pro"):
            return types_module.ThinkingConfig(thinking_budget=128)
        return None

    def call(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        from google.genai import types

        start = time.time()
        try:
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            thinking_config = self._default_thinking_config(types)
            if thinking_config is not None:
                config.thinking_config = thinking_config

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config,
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
                elif finish_reason and str(finish_reason) in ("FinishReason.MAX_TOKENS", "MAX_TOKENS"):
                    error = (
                        "Gemini hit max_output_tokens before producing visible text. "
                        "Increase max_tokens for this model."
                    )
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

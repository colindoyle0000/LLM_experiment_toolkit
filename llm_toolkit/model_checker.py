"""
model_checker.py — Check which AI models are available under each API key.

Called from check_models.py. Connects to each provider's API, fetches the
list of available models, and prints them in a clean table.

Models marked with [*] have a cost estimate entry in estimator.py, so the
toolkit will show you a cost estimate before running an experiment with them.
Models without [*] will still work — you just won't see a cost estimate.

YOU PROBABLY DON'T NEED TO EDIT THIS FILE.
"""

import os

from dotenv import load_dotenv

from llm_toolkit.estimator import PRICING

load_dotenv()

# Prefixes used to filter OpenAI's model list down to chat/reasoning models.
# OpenAI's API returns every model type (embeddings, image, audio, etc.).
_OPENAI_CHAT_PREFIXES = ("gpt-", "o1", "o2", "o3", "o4", "chatgpt")

# Gemini model name segments that indicate non-text-generation models.
_GEMINI_EXCLUDE_TERMS = ("tts", "embedding", "aqa", "vision")


def check_all() -> None:
    """Check all three providers and print available models."""
    print()
    _check_anthropic()
    _check_openai()
    _check_google()
    print(
        "  [*] = cost estimate available in estimator.py\n"
        "  Use the model id shown in the left column in your config.yaml.\n"
    )


# ---------------------------------------------------------------------------
# Per-provider checks
# ---------------------------------------------------------------------------

def _check_anthropic() -> None:
    _print_header("ANTHROPIC (Claude)", "anthropic")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        _print_missing_key("ANTHROPIC_API_KEY")
        return
    try:
        import anthropic  # pylint: disable=import-outside-toplevel
        client = anthropic.Anthropic(api_key=api_key)
        response = client.models.list()
        rows = [(m.id, m.display_name) for m in response.data]
        _print_models(rows, provider="anthropic")
    except Exception as e:  # pylint: disable=broad-except
        _print_api_error(e)


def _check_openai() -> None:
    _print_header("OPENAI (GPT / o-series)", "openai")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        _print_missing_key("OPENAI_API_KEY")
        return
    try:
        import openai  # pylint: disable=import-outside-toplevel
        client = openai.OpenAI(api_key=api_key)
        all_models = client.models.list()
        # Filter to chat/reasoning models; rely on prefix, not owned_by,
        # because newer models may show owned_by == "openai-internal"
        chat_models = [
            m for m in all_models.data
            if any(m.id.startswith(p) for p in _OPENAI_CHAT_PREFIXES)
        ]
        chat_models.sort(key=lambda m: m.created, reverse=True)
        rows = [(m.id, "") for m in chat_models]
        _print_models(rows, provider="openai")
    except Exception as e:  # pylint: disable=broad-except
        _print_api_error(e)


def _check_google() -> None:
    _print_header("GOOGLE (Gemini)", "google")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        _print_missing_key("GEMINI_API_KEY")
        return
    try:
        from google import genai  # pylint: disable=import-outside-toplevel
        client = genai.Client(api_key=api_key)
        all_models = list(client.models.list())
        # Only show text-generation models; exclude TTS, embedding, etc.
        text_models = [
            m for m in all_models
            if "generateContent" in (m.supported_actions or [])
            and not any(t in m.name.lower() for t in _GEMINI_EXCLUDE_TERMS)
        ]
        # Strip the "models/" prefix — that prefix is not used in config.yaml
        rows = [
            (m.name.removeprefix("models/"), m.display_name or "")
            for m in text_models
        ]
        _print_models(rows, provider="google")
    except Exception as e:  # pylint: disable=broad-except
        _print_api_error(e)


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _print_header(label: str, provider: str) -> None:
    W = 66
    print("=" * W)
    priced_count = len(PRICING.get(provider, {}))
    print(f"  {label}  ({priced_count} models with cost estimates)")
    print("=" * W)


def _print_missing_key(env_var: str) -> None:
    print(f"  Key not found — add {env_var} to your .env file.\n")


def _print_api_error(error: Exception) -> None:
    print(f"  Could not connect: {type(error).__name__}: {error}\n")


def _print_models(rows: list[tuple[str, str]], provider: str) -> None:
    if not rows:
        print("  No models found.\n")
        return

    priced = PRICING.get(provider, {})
    col_w = max(len(model_id) for model_id, _ in rows) + 2

    for model_id, display_name in rows:
        star = "[*]" if model_id in priced else "   "
        name_part = f"  {display_name}" if display_name else ""
        print(f"  {star} {model_id:<{col_w}}{name_part}")

    print()

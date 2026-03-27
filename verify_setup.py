"""
VERIFY SETUP

Run this script to confirm that your API keys are working and the toolkit
is installed correctly before running a real experiment.

Usage:
    python verify_setup.py

This sends one short, inexpensive test message to each provider whose API
key is present in your .env file, then prints the response. A passing check
looks like:

    Anthropic ... OK (claude-opus-4-6, 0.8s)
    OpenAI    ... OK (gpt-4o, 1.2s)
    Google    ... OK (gemini-2.0-flash, 0.6s)

If a provider shows FAILED or SKIPPED, see the message for what to fix
before running experiments that cost money.
"""

import os
import time

from dotenv import load_dotenv

load_dotenv()

TEST_PROMPT = "Reply with exactly the words: Setup successful."

W = 60


def main():
    print()
    print("=" * W)
    print("  VERIFYING SETUP")
    print("=" * W)
    print()

    _check_anthropic()
    _check_openai()
    _check_google()

    print()
    print("=" * W)
    print("  If all providers you need show OK, you are ready to run")
    print("  experiments. If a provider shows FAILED, check your .env")
    print("  file and try running: python check_models.py")
    print("=" * W)
    print()


def _check_anthropic():
    label = "Anthropic"
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        _print_skipped(label, "ANTHROPIC_API_KEY not found in .env")
        return
    try:
        import anthropic  # pylint: disable=import-outside-toplevel
        client = anthropic.Anthropic(api_key=api_key)
        model = "claude-opus-4-6"
        start = time.time()
        response = client.messages.create(
            model=model,
            max_tokens=20,
            temperature=0.0,
            messages=[{"role": "user", "content": TEST_PROMPT}],
        )
        elapsed = round(time.time() - start, 1)
        reply = response.content[0].text.strip()
        _print_ok(label, model, elapsed, reply)
    except Exception as e:  # pylint: disable=broad-except
        _print_failed(label, e)


def _check_openai():
    label = "OpenAI   "
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        _print_skipped(label, "OPENAI_API_KEY not found in .env")
        return
    try:
        import openai  # pylint: disable=import-outside-toplevel
        client = openai.OpenAI(api_key=api_key)
        model = "gpt-4o"
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            max_tokens=20,
            temperature=0.0,
            messages=[{"role": "user", "content": TEST_PROMPT}],
        )
        elapsed = round(time.time() - start, 1)
        reply = response.choices[0].message.content.strip()
        _print_ok(label, model, elapsed, reply)
    except Exception as e:  # pylint: disable=broad-except
        _print_failed(label, e)


def _check_google():
    label = "Google   "
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        _print_skipped(label, "GEMINI_API_KEY not found in .env")
        return
    try:
        from google import genai  # pylint: disable=import-outside-toplevel
        from google.genai import types  # pylint: disable=import-outside-toplevel
        client = genai.Client(api_key=api_key)
        model_name = "gemini-2.5-flash"
        start = time.time()
        response = client.models.generate_content(
            model=model_name,
            contents=TEST_PROMPT,
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=20),
        )
        elapsed = round(time.time() - start, 1)
        reply = response.text.strip()
        _print_ok(label, model_name, elapsed, reply)
    except Exception as e:  # pylint: disable=broad-except
        _print_failed(label, e)


def _print_ok(label: str, model: str, elapsed: float, reply: str) -> None:
    print(f"  {label} ... OK ({model}, {elapsed}s)")
    print(f"           Response: \"{reply}\"")
    print()


def _print_failed(label: str, error: Exception) -> None:
    print(f"  {label} ... FAILED")
    print(f"           {type(error).__name__}: {error}")
    print()


def _print_skipped(label: str, reason: str) -> None:
    print(f"  {label} ... SKIPPED — {reason}")
    print()


if __name__ == "__main__":
    main()

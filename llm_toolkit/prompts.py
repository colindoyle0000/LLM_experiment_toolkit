"""
prompts.py — Loads your prompt .txt files and fills in {{variables}}.

Your prompt files can contain placeholders written in double curly braces,
like {{user_persona}}. Before each API call, this module reads the prompt
file and replaces every {{placeholder}} with the actual value for that run.

Example:
  Prompt file contains:  "You are advising {{user_persona}}."
  Value for this run:    "a pro se litigant with no legal training"
  Final prompt sent:     "You are advising a pro se litigant with no legal training."

If a {{placeholder}} appears in your prompt but has no matching value
defined in config.yaml, you will get a clear error telling you what to fix.

YOU PROBABLY DON'T NEED TO EDIT THIS FILE.
"""

import re


def load_system(path: str) -> str:
    """Read and return the system prompt from a .txt file."""
    return _read(path)


def load_user(path: str, variables: dict) -> str:
    """
    Read the user prompt from a .txt file and substitute {{variable}} placeholders.

    All keys in `variables` must appear in the prompt file as {{key}}.
    Raises ValueError if any {{placeholder}} in the file has no matching variable.
    """
    text = _read(path)
    text = _substitute(text, variables, path)
    return text


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def _substitute(text: str, variables: dict, path: str) -> str:
    # Replace each {{key}} with its value.
    for key, value in variables.items():
        placeholder = "{{" + key + "}}"
        text = text.replace(placeholder, str(value))

    # Check if any unreplaced {{placeholders}} remain.
    remaining = re.findall(r"\{\{(\w+)\}\}", text)
    if remaining:
        raise ValueError(
            f"The following variable(s) are used in '{path}' but were not provided:\n"
            + "".join(f"  - {{{{  {v}  }}}}\n" for v in remaining)
            + "\nMake sure every {{variable}} in your prompt file matches a variable "
            "defined in your config.yaml."
        )

    return text

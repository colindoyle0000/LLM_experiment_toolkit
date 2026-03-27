"""
CHECK AVAILABLE MODELS

Run this script to see which AI models your API keys give you access to.

Usage:
    python check_models.py

This will connect to each provider (Anthropic, OpenAI, Google) and print
the full list of models available under your API keys.

Models marked with [*] have a cost estimate entry in the toolkit, so you
will see a cost estimate before running an experiment with them.

Use the model id shown in the output as the 'name' field in your config.yaml.
"""

from llm_toolkit.model_checker import check_all

if __name__ == "__main__":
    check_all()

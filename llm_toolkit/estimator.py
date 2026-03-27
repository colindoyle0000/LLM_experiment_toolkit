"""
estimator.py — Shows a cost estimate before every experiment run.

Before the first API call, this module builds all the prompts, counts their
tokens, looks up the current price for each model, and prints a table like:

    Model                    Runs   Input tok   Output tok (max)   Cost range
    claude-opus-4-6             3         858        up to 3,000   $0.01-$0.24

You are then asked to press Enter to proceed, or Ctrl+C to cancel.

HOW TOKEN COUNTING WORKS:
  Input tokens are estimated from your actual prompt text using the rule of
  thumb that one token ≈ 4 characters. This is accurate to within ~15%.

  Output tokens cannot be known in advance, so the table shows a range:
  the low end assumes a very short response; the high end assumes the model
  uses the full max_tokens you configured. Real cost is almost always closer
  to the low end.

YOU MAY WANT TO EDIT THE PRICING TABLE IN THIS FILE if prices have changed
or if you are using a model that is not listed. The PRICING dict near the
top of this file maps model names to their cost per million tokens.
Check current rates at:
  Anthropic: https://www.anthropic.com/pricing
  OpenAI:    https://openai.com/api/pricing
  Google:    https://ai.google.dev/pricing
"""

import sys

import pandas as pd

import llm_toolkit.prompts as prompts
from llm_toolkit.config import ExperimentConfig, ModelConfig


# ---------------------------------------------------------------------------
# Pricing table
# Format: provider -> model_name -> (input_cost_per_1M, output_cost_per_1M)
# Prices in USD. Approximate as of late March 2026.
# ---------------------------------------------------------------------------

PRICING: dict[str, dict[str, tuple[float, float]]] = {
    "anthropic": {
        # Claude 4.x Opus series
        "claude-opus-4-6":      ( 5.00,  25.00),
        "claude-opus-4-5":      ( 5.00,  25.00),
        "claude-opus-4-1":      (15.00,  75.00),
        "claude-opus-4-0":      (15.00,  75.00),
        # Claude 4.x Sonnet series
        "claude-sonnet-4-6":    ( 3.00,  15.00),
        "claude-sonnet-4-5":    ( 3.00,  15.00),
        "claude-sonnet-4-0":    ( 3.00,  15.00),
        # Claude 3.x Sonnet (deprecated)
        "claude-3-7-sonnet-20250219": (3.00, 15.00),
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        # Claude 4.x Haiku series
        "claude-haiku-4-5-20251001": (1.00,  5.00),
        "claude-haiku-4-5":          (1.00,  5.00),
        # Claude 3.x Haiku
        "claude-3-5-haiku-20241022": (0.80,  4.00),
        "claude-3-haiku-20240307":   (0.25,  1.25),
        # Claude 3 Opus (deprecated)
        "claude-3-opus-20240229":   (15.00, 75.00),
    },
    "openai": {
        # GPT-5 series
        "gpt-5":                 (1.25,  10.00),
        "gpt-5-mini":            (0.25,   2.00),
        "gpt-5-nano":            (0.05,   0.40),
        "gpt-5-pro":            (15.00, 120.00),
        # GPT-4.1 series
        "gpt-4.1":               (2.00,   8.00),
        "gpt-4.1-mini":          (0.40,   1.60),
        "gpt-4.1-nano":          (0.10,   0.40),
        # GPT-4o series
        "gpt-4o":                (2.50,  10.00),
        "gpt-4o-mini":           (0.15,   0.60),
        # o-series reasoning models
        "o4-mini":               (1.10,   4.40),
        "o3":                    (2.00,   8.00),
        "o3-mini":               (1.10,   4.40),
        "o3-pro":               (20.00,  80.00),
        "o1":                   (15.00,  60.00),
        "o1-mini":               (1.10,   4.40),
        "o1-pro":              (150.00, 600.00),
        # Legacy models
        "gpt-4-turbo-2024-04-09":(10.00,  30.00),
        "gpt-3.5-turbo":         (0.50,   1.50),
    },
    "google": {
        # Gemini 3.x series
        "gemini-3.1-pro-preview":       ( 2.00,  12.00),
        "gemini-3.1-flash-lite-preview": ( 0.25,   1.50),
        "gemini-3-flash-preview":       ( 0.50,   3.00),
        # Gemini 2.5 series
        "gemini-2.5-pro":               ( 1.25,  10.00),
        "gemini-2.5-flash":             ( 0.30,   2.50),
        "gemini-2.5-flash-lite":        ( 0.10,   0.40),
        "gemini-2.5-flash-lite-preview-09-2025": (0.10, 0.40),
        # Gemini 2.0 series (deprecated June 2026)
        "gemini-2.0-flash":             ( 0.10,   0.40),
        "gemini-2.0-flash-lite":        ( 0.075,  0.30),
    },
}


def estimate_tokens(text: str) -> int:
    """Approximate token count. Rule of thumb: ~4 characters per token."""
    return max(1, len(text) // 4)


def show_estimate(cfg: ExperimentConfig) -> None:
    """
    Print a cost estimate table and ask the user to confirm before proceeding.

    Builds all prompts, counts input tokens, looks up pricing, and displays
    a per-model summary table. Raises SystemExit if the user presses Ctrl+C.
    """
    # Build the full list of (model_config, system_str, user_str) for every planned run.
    # We build each unique (model, condition) prompt pair once — repetitions use
    # the same prompts, so we multiply by repetitions for the token total.
    system_str = prompts.load_system(cfg.system_prompt_path)

    if cfg.pattern == "variable_groups":
        prompt_pairs = _build_variable_group_pairs(cfg, system_str)
    else:
        prompt_pairs = _build_data_iteration_pairs(cfg, system_str)

    # Aggregate per model
    model_stats = _aggregate_by_model(cfg, prompt_pairs)

    _print_table(cfg, model_stats)
    _confirm()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_variable_group_pairs(
    cfg: ExperimentConfig, system_str: str
) -> list[tuple[ModelConfig, str, str]]:
    """Return one (model, system, user) tuple per unique model+group combination."""
    pairs = []
    for model_cfg in cfg.models:
        for group in cfg.groups:
            variables = {cfg.variable: group.value}
            user_str = prompts.load_user(cfg.user_prompt_path, variables)
            pairs.append((model_cfg, system_str, user_str))
    return pairs


def _build_data_iteration_pairs(
    cfg: ExperimentConfig, system_str: str
) -> list[tuple[ModelConfig, str, str]]:
    """Return one (model, system, user) tuple per unique model+row combination."""
    df = pd.read_csv(cfg.data_file_path)
    pairs = []
    for model_cfg in cfg.models:
        for _, row in df.iterrows():
            variables = {col: str(val) for col, val in row.items()}
            user_str = prompts.load_user(cfg.user_prompt_path, variables)
            pairs.append((model_cfg, system_str, user_str))
    return pairs


def _aggregate_by_model(
    cfg: ExperimentConfig,
    pairs: list[tuple[ModelConfig, str, str]],
) -> list[dict]:
    """
    For each model, sum up input tokens across all its conditions,
    multiply by repetitions, and look up pricing.
    """
    # Group by model
    model_data: dict[str, dict] = {}
    for model_cfg, system_str, user_str in pairs:
        key = f"{model_cfg.provider}:{model_cfg.name}"
        if key not in model_data:
            model_data[key] = {
                "model_cfg": model_cfg,
                "total_input_tokens": 0,
                "n_conditions": 0,
            }
        tokens = estimate_tokens(system_str) + estimate_tokens(user_str)
        model_data[key]["total_input_tokens"] += tokens
        model_data[key]["n_conditions"] += 1

    stats = []
    for key, data in model_data.items():
        model_cfg: ModelConfig = data["model_cfg"]
        n_conditions = data["n_conditions"]
        n_runs = n_conditions * cfg.repetitions

        # Input tokens: multiply unique-pair count by repetitions
        input_tokens = data["total_input_tokens"] * cfg.repetitions

        # Output tokens: range from 0 to max_tokens per run
        max_output_tokens = model_cfg.max_tokens * n_runs

        # Look up pricing
        price = PRICING.get(model_cfg.provider, {}).get(model_cfg.name)
        if price:
            input_rate, output_rate = price   # per 1M tokens
            cost_input = input_tokens * input_rate / 1_000_000
            cost_max = cost_input + max_output_tokens * output_rate / 1_000_000
            cost_str = f"${cost_input:.4f} – ${cost_max:.4f}"
        else:
            cost_input = None
            cost_max = None
            cost_str = "(price unknown)"

        stats.append({
            "provider": model_cfg.provider,
            "model_name": model_cfg.name,
            "n_runs": n_runs,
            "input_tokens": input_tokens,
            "max_output_tokens": max_output_tokens,
            "cost_input": cost_input,
            "cost_max": cost_max,
            "cost_str": cost_str,
        })

    return stats


def _print_table(cfg: ExperimentConfig, model_stats: list[dict]) -> None:
    W = 72

    print()
    print("=" * W)
    print("  COST ESTIMATE")
    print("=" * W)
    print(f"  {'Model':<30} {'Runs':>5}  {'Input tok':>10}  {'Output tok (max)':>16}  {'Cost range':>20}")
    print("  " + "-" * (W - 2))

    total_cost_min = 0.0
    total_cost_max = 0.0
    all_priced = True

    for s in model_stats:
        label = f"{s['model_name']} ({s['provider']})"
        input_fmt = f"{s['input_tokens']:,}"
        output_fmt = f"up to {s['max_output_tokens']:,}"
        print(f"  {label:<30} {s['n_runs']:>5}  {input_fmt:>10}  {output_fmt:>16}  {s['cost_str']:>20}")
        if s["cost_input"] is not None:
            total_cost_min += s["cost_input"]
            total_cost_max += s["cost_max"]
        else:
            all_priced = False

    print("  " + "-" * (W - 2))
    total_runs = sum(s["n_runs"] for s in model_stats)
    total_input = sum(s["input_tokens"] for s in model_stats)
    total_output = sum(s["max_output_tokens"] for s in model_stats)

    if all_priced and model_stats:
        total_str = f"${total_cost_min:.4f} – ${total_cost_max:.4f}"
    elif model_stats:
        total_str = "(some prices unknown)"
    else:
        total_str = "—"

    print(f"  {'TOTAL':<30} {total_runs:>5}  {total_input:>10,}  {f'up to {total_output:,}':>16}  {total_str:>20}")
    print("=" * W)
    print()
    print("  Token counts are approximate (±15%). Output cost assumes model uses")
    print("  up to max_tokens per response; actual cost is likely lower.")
    if not all_priced:
        print("  Some models are not in the pricing table. Edit PRICING in estimator.py")
        print("  to add them.")
    print("  For current rates: anthropic.com/pricing  |  openai.com/api/pricing")
    print("                     ai.google.dev/pricing")
    print()


def _confirm() -> None:
    try:
        input("  Press Enter to start the experiment, or Ctrl+C to cancel... ")
    except KeyboardInterrupt:
        print("\n\n  Experiment cancelled.")
        sys.exit(0)
    print()

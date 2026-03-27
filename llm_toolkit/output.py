"""
output.py — Saves experiment results to your output/ folder.

After each API call, this module writes two files:
  - A .txt file you can open in any text editor to read the result
  - A .json file for loading into data analysis tools (pandas, Excel)

At the end of the experiment it also writes summary.json, which combines
every run into one file — this is the easiest file to use for analysis.

YOU PROBABLY DON'T NEED TO EDIT THIS FILE.
If you want to change the format of the .txt output (e.g. add new fields
or change the layout), look at the _write_txt method in OutputWriter.
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime

from llm_toolkit.models import ModelResponse


# ---------------------------------------------------------------------------
# RunResult — a simple container for everything about one API call
# ---------------------------------------------------------------------------

@dataclass  # pylint: disable=too-many-instance-attributes
class RunResult:
    """Everything about one API call: config, prompts sent, and response received."""

    experiment_name: str
    run_index: int          # sequential counter across the whole experiment
    condition_label: str    # human-readable label, e.g. "pro_se_litigant" or "case_042"
    repetition: int
    total_repetitions: int
    timestamp: str
    system_prompt: str
    user_prompt: str
    response: ModelResponse


# ---------------------------------------------------------------------------
# OutputWriter — creates the output folder and writes files after each run
# ---------------------------------------------------------------------------

class OutputWriter:
    """Creates the output folder and writes .txt, .json, and summary files."""

    def __init__(self, experiment_name: str, output_root: str = "output"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{experiment_name}__{timestamp}"
        self.output_dir = os.path.join(output_root, folder_name)
        os.makedirs(self.output_dir, exist_ok=True)
        self._all_results: list[dict] = []
        print(f"\nOutput folder: {self.output_dir}\n")

    def write(self, run_result: RunResult) -> None:
        """Write a single run result to .txt and .json files."""
        base_name = _make_filename(run_result)
        self._write_txt(run_result, os.path.join(self.output_dir, base_name + ".txt"))
        self._write_json(run_result, os.path.join(self.output_dir, base_name + ".json"))
        self._all_results.append(_run_to_dict(run_result))

    def write_summary(self) -> None:
        """Write all results to a single summary.json file."""
        summary_path = os.path.join(self.output_dir, "summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(self._all_results, f, indent=2, ensure_ascii=False)
        print(f"\nSummary written to: {summary_path}")

    def _write_txt(self, r: RunResult, path: str) -> None:
        status = "FAILED" if r.response.error else "OK"
        lines = [
            "=" * 70,
            f"EXPERIMENT:  {r.experiment_name}",
            f"CONDITION:   {r.condition_label}",
            f"MODEL:       {r.response.model_name} ({r.response.provider})",
            f"REPETITION:  {r.repetition} of {r.total_repetitions}",
            f"TIMESTAMP:   {r.timestamp}",
            f"STATUS:      {status}",
        ]
        if not r.response.error:
            lines += [
                f"TOKENS:      {r.response.input_tokens} in / {r.response.output_tokens} out",
                f"DURATION:    {r.response.duration_seconds}s",
            ]
        lines += [
            "=" * 70,
            "",
            "SYSTEM PROMPT",
            "-" * 70,
            r.system_prompt,
            "",
            "USER PROMPT",
            "-" * 70,
            r.user_prompt,
            "",
            "RESPONSE",
            "-" * 70,
        ]
        if r.response.error:
            lines.append(f"[ERROR] {r.response.error}")
        else:
            lines.append(r.response.content)
        lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _write_json(self, r: RunResult, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_run_to_dict(r), f, indent=2, ensure_ascii=False)


def _make_filename(r: RunResult) -> str:
    """
    Build a filename like: run_003__pro_se_litigant__gpt-4o__rep-2
    Sanitize the condition label so it's safe for file systems.
    """
    safe_condition = _sanitize(r.condition_label)
    safe_model = _sanitize(r.response.model_name)
    return f"run_{r.run_index:03d}__{safe_condition}__{safe_model}__rep-{r.repetition}"


def _sanitize(s: str) -> str:
    """Replace characters that are problematic in file names."""
    return "".join(c if c.isalnum() or c in "-_." else "-" for c in s)


def _run_to_dict(r: RunResult) -> dict:
    return {
        "experiment_name": r.experiment_name,
        "run_index": r.run_index,
        "condition_label": r.condition_label,
        "repetition": r.repetition,
        "total_repetitions": r.total_repetitions,
        "timestamp": r.timestamp,
        "system_prompt": r.system_prompt,
        "user_prompt": r.user_prompt,
        "provider": r.response.provider,
        "model_name": r.response.model_name,
        "temperature": r.response.temperature,
        "max_tokens": r.response.max_tokens,
        "input_tokens": r.response.input_tokens,
        "output_tokens": r.response.output_tokens,
        "duration_seconds": r.response.duration_seconds,
        "response_content": r.response.content,
        "error": r.response.error,
    }

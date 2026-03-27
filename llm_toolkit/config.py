"""
config.py — Reads and validates your config.yaml experiment file.

When you run an experiment, this is the first thing that runs. It opens
your config.yaml file, checks that all the required fields are present,
and converts the settings into a form the rest of the toolkit can use.
If something is missing or misspelled in your config.yaml, this module
will catch it and print a clear error message telling you what to fix.

YOU PROBABLY DON'T NEED TO EDIT THIS FILE.
If you want to add new configuration options to the toolkit, start here.
"""

import os
from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class ModelConfig:
    """Settings for one AI model: which provider, which model, and parameters."""

    provider: str       # "anthropic", "openai", or "google"
    name: str           # model name, e.g. "claude-opus-4-6"
    temperature: float = 0.0
    max_tokens: int = 1000


@dataclass
class GroupConfig:
    """One condition in a variable_groups experiment."""

    name: str           # used in output file names, e.g. "pro_se_litigant"
    value: str          # the actual value substituted into the prompt


@dataclass  # pylint: disable=too-many-instance-attributes
class ExperimentConfig:
    """All settings for one experiment, loaded from a config.yaml file."""

    experiment_name: str
    pattern: str                        # "variable_groups" or "data_iteration"
    models: list[ModelConfig]
    system_prompt_path: str             # absolute path
    user_prompt_path: str               # absolute path
    repetitions: int = 1

    # variable_groups fields
    variable: str = ""
    groups: list[GroupConfig] = field(default_factory=list)

    # data_iteration fields
    data_file_path: str = ""            # absolute path
    row_id_column: str = ""

    @classmethod
    def load(cls, config_path: str) -> "ExperimentConfig":  # pylint: disable=too-many-locals
        """Load and validate a config.yaml file."""
        config_path = os.path.abspath(config_path)
        config_dir = os.path.dirname(config_path)

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Config file not found: {config_path}\n"
                "Check that CONFIG_PATH in run_experiment.py points to "
                "an existing config.yaml file."
            )

        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if raw is None:
            raise ValueError(f"Config file is empty: {config_path}")

        # Required top-level fields
        _require(raw, "experiment_name", config_path)
        _require(raw, "pattern", config_path)
        _require(raw, "model", config_path)
        _require(raw, "prompts", config_path)

        pattern = raw["pattern"]
        if pattern not in ("variable_groups", "data_iteration"):
            raise ValueError(
                f"'pattern' must be 'variable_groups' or 'data_iteration', "
                f"got '{pattern}' in {config_path}"
            )

        # Parse models (accept a single dict or a list of dicts)
        model_raw = raw["model"]
        if isinstance(model_raw, dict):
            model_raw = [model_raw]
        models = [_parse_model(m, config_path) for m in model_raw]

        # Resolve prompt paths relative to the config file
        prompts_cfg = raw["prompts"]
        _require(prompts_cfg, "system", config_path, parent_key="prompts")
        _require(prompts_cfg, "user", config_path, parent_key="prompts")
        system_path = _resolve(prompts_cfg["system"], config_dir, config_path)
        user_path = _resolve(prompts_cfg["user"], config_dir, config_path)

        repetitions = int(raw.get("repetitions", 1))
        if repetitions < 1:
            raise ValueError(
                f"'repetitions' must be at least 1, got {repetitions} in {config_path}"
            )

        # Pattern-specific fields
        variable = ""
        groups: list[GroupConfig] = []
        data_file_path = ""
        row_id_column = ""

        if pattern == "variable_groups":
            _require(raw, "variable", config_path)
            _require(raw, "groups", config_path)
            variable = raw["variable"]
            for g in raw["groups"]:
                if "name" not in g or "value" not in g:
                    raise ValueError(
                        "Each entry under 'groups' must have a 'name' and a 'value'. "
                        f"Found: {g} in {config_path}"
                    )
                groups.append(GroupConfig(name=str(g["name"]), value=str(g["value"])))
            if len(groups) == 0:
                raise ValueError(f"'groups' list is empty in {config_path}")

        elif pattern == "data_iteration":
            _require(raw, "data_file", config_path)
            _require(raw, "row_id_column", config_path)
            data_file_path = _resolve(raw["data_file"], config_dir, config_path)
            row_id_column = raw["row_id_column"]

        return cls(
            experiment_name=raw["experiment_name"],
            pattern=pattern,
            models=models,
            system_prompt_path=system_path,
            user_prompt_path=user_path,
            repetitions=repetitions,
            variable=variable,
            groups=groups,
            data_file_path=data_file_path,
            row_id_column=row_id_column,
        )


def _require(d: dict, key: str, config_path: str, parent_key: str = "") -> None:
    if key not in d:
        location = f"'{parent_key}.{key}'" if parent_key else f"'{key}'"
        raise ValueError(
            f"Missing required field {location} in {config_path}.\n"
            "Check the example configs in experiments/ for the correct format."
        )


def _resolve(relative_path: str, base_dir: str, config_path: str) -> str:
    abs_path = os.path.join(base_dir, relative_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(
            f"File not found: {abs_path}\n"
            f"Referenced in {config_path} as '{relative_path}'.\n"
            "Paths in config.yaml are relative to the config file's location."
        )
    return abs_path


def _parse_model(m: Any, config_path: str) -> ModelConfig:
    if not isinstance(m, dict):
        raise ValueError(
            "Each entry under 'model' must be a mapping with 'provider' and 'name'. "
            f"Got: {m} in {config_path}"
        )
    if "provider" not in m:
        raise ValueError(f"Model entry is missing 'provider' in {config_path}: {m}")
    if "name" not in m:
        raise ValueError(f"Model entry is missing 'name' in {config_path}: {m}")

    provider = m["provider"].lower()
    if provider not in ("anthropic", "openai", "google"):
        raise ValueError(
            f"'provider' must be 'anthropic', 'openai', or 'google'. "
            f"Got '{m['provider']}' in {config_path}"
        )

    return ModelConfig(
        provider=provider,
        name=m["name"],
        temperature=float(m.get("temperature", 0.0)),
        max_tokens=int(m.get("max_tokens", 1000)),
    )

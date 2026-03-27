# LLM Experiment Toolkit — Claude Code Context

This project is a Python toolkit for Loyola Law and AI Lab students to run
structured experiments with large language models. Students have little or no
programming background and use Claude Code to extend and modify the project.

## Who the users are

Law students running empirical research on LLM behavior. They are not
programmers. They edit config files and prompt files; they rarely need to
touch the Python code directly. When they do modify Python, they do it with
AI coding assistant help.

## Project structure

```
run_experiment.py       Entry point. Students change CONFIG_PATH, run this.
check_models.py         Lists available models under each API key.
verify_setup.py         Confirms API keys and dependencies work before experiments.

experiments/            Each subfolder is one experiment.
  my_experiment/
    config.yaml         All experiment settings (model, params, pattern, prompts).
    system_prompt.txt   Instructions to the model (its role/persona).
    user_prompt.txt     The actual question or task. May contain {{variables}}.
    cases.csv           Data file for data_iteration experiments (optional).

llm_toolkit/            Core package. Students rarely edit these directly.
  config.py             Loads and validates config.yaml files.
  prompts.py            Reads .txt prompt files; substitutes {{variables}}.
  models.py             API clients for Anthropic, OpenAI, Google Gemini.
  runner.py             Orchestrates the full experiment loop.
  output.py             Writes .txt and .json result files; summary.json.
  estimator.py          Shows cost estimate before each run; holds PRICING table.
  model_checker.py      Fetches available model lists from each provider's API.

output/                 Auto-created. One timestamped subfolder per run.
```

## Two experiment patterns

**variable_groups** — vary one variable across conditions.
Config defines `variable: some_name` and a list of `groups`, each with a
`name` and `value`. The prompt file uses `{{some_name}}` as a placeholder.
The runner substitutes the value before each API call.

**data_iteration** — iterate through rows of a CSV file.
Config defines `data_file` and `row_id_column`. Every column header in the
CSV becomes a `{{variable}}` available in the prompt file.

## Prompt variable syntax

Double curly braces: `{{variable_name}}`. Substitution is done with
`str.replace()` in `llm_toolkit/prompts.py` — no Jinja2, no regex needed.
Variable names must match exactly (case-sensitive) between the prompt file
and `config.yaml`.

## Multi-model support

`model:` in config.yaml accepts a single dict or a list of dicts. The runner
loops `model × condition × repetition`, producing separate output files for
each combination.

## Output files

Each run produces:
- `run_NNN__condition__model__rep-N.txt` — human-readable, all metadata + prompts + response
- `run_NNN__condition__model__rep-N.json` — same data, machine-readable
- `summary.json` — all runs combined; this is what students load for analysis

## API keys

Loaded from `.env` via `python-dotenv` in `llm_toolkit/models.py`.
Variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`.

## Conventions

- Temperature defaults to `0.0` for reproducibility in empirical research.
- API errors are caught per-call; the experiment continues, error saved in output.
- All file paths in config.yaml are relative to the config file's location.
- Output folder names are `experiment_name__YYYY-MM-DD_HH-MM-SS`.
- Cost estimates use ~4 chars/token approximation; pricing table is in `estimator.py`.

## What students commonly want to change

- Add a new experiment: copy an example folder, edit config.yaml and prompt files.
- Add a model to the cost estimate: edit `PRICING` dict in `llm_toolkit/estimator.py`.
- Change the .txt output format: edit `_write_txt` in `llm_toolkit/output.py`.
- Add a new experiment pattern: add a branch in `llm_toolkit/runner.py` and
  corresponding fields to `ExperimentConfig` in `llm_toolkit/config.py`.
- Add a delay between API calls (to avoid rate limits): edit the loop in
  `runner.py` to call `time.sleep(seconds)` between iterations.

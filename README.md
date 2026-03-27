# LLM Experiment Toolkit

A toolkit for law students to run structured experiments with AI language models — Claude (Anthropic), GPT (OpenAI), and Gemini (Google).

You describe your experiment in a simple configuration file, write your prompts in plain text files, and run one command. The toolkit handles all the API calls and saves every result automatically.

---

## Table of Contents

1. [Before You Start — Key Concepts](#before-you-start--key-concepts)
2. [One-Time Setup](#one-time-setup)
3. [Running Your First Experiment](#running-your-first-experiment)
4. [Understanding the Project Folder](#understanding-the-project-folder)
5. [Creating Your Own Experiment](#creating-your-own-experiment)
6. [Experiment Pattern A: Variable Groups](#experiment-pattern-a-variable-groups)
7. [Experiment Pattern B: Data Iteration](#experiment-pattern-b-data-iteration)
8. [Running Multiple Models at Once](#running-multiple-models-at-once)
9. [Config File Reference](#config-file-reference)
10. [Understanding the Cost Estimate](#understanding-the-cost-estimate)
11. [Your Output Files](#your-output-files)
12. [Checking Available Models](#checking-available-models)
13. [Troubleshooting](#troubleshooting)

---

## Before You Start — Key Concepts

### What is a terminal?

The terminal (also called the command line, shell, or console) is a text-based way to interact with your computer. Instead of clicking icons, you type short commands and press Enter.

- **On Mac:** Open Spotlight (Cmd + Space), type "Terminal", and press Enter. Or find Terminal in Applications → Utilities. Macs default to **zsh** (Z shell) — all commands in this guide work in zsh.
- **On Windows:** Search for "Command Prompt" or "PowerShell" in the Start menu.

When instructions say to "run a command," they mean: type the command into the terminal and press Enter.

### What is Python?

Python is the programming language this toolkit is written in. You don't need to know how to write Python — but you do need it installed on your computer so it can run the toolkit.

### What is a .env file?

The `.env` file is a private file that stores your API keys. API keys are like passwords that let you access the AI models. This file is already set up with your keys. Never share it with anyone.

### What is a token?

AI models don't process words — they process chunks of text called tokens. One token is roughly four characters of English text, or about ¾ of a word. When you send a prompt to an AI model, you're charged based on the number of tokens sent (input) and received (output).

### What is YAML?

YAML (the `.yaml` files in this project) is a simple format for writing configuration settings. It looks like a plain-English list. You don't need to know YAML — just copy an example file and change the values. The most important rule: **indentation matters**. Use spaces, not tabs, and keep the spacing consistent.

---

## One-Time Setup

Do these steps once when you first get the project. You won't need to repeat them.

### Step 1: Open your terminal and navigate to the project folder

In your terminal, type `cd` followed by the path to this project folder, then press Enter.

For example, if your project is in Documents:

```sh
cd Documents/LLM_experiment_toolkit
```

You should now see the project folder name in your terminal prompt. If you're not sure of the path, you can drag the folder into the terminal window after typing `cd` and a space, and it will fill in the path automatically (Mac only).

### Step 2: Check that Python is installed

```sh
python --version
```

You should see something like `Python 3.11.2`. If you see an error, try `python3 --version`. If neither works, download Python from [python.org/downloads](https://www.python.org/downloads/) and install it.

If `python3` works but `python` does not, use `python3` everywhere in these instructions instead of `python`.

### Step 3: Install the required libraries

This command downloads all the additional code the toolkit needs:

```sh
pip install -r requirements.txt
```

You should see a list of packages being downloaded. This only needs to happen once. If you see an error about `pip`, try `pip3 install -r requirements.txt`.

### Step 4: Confirm your API keys are in place

Open the `.env` file in a text editor (Notepad, TextEdit, VS Code, etc.). It should contain three lines like these, each with a real key after the equals sign:

```text
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AI...
```

If a key is missing, check the `.env.example` file (also in the project folder) to see what the format should look like, then ask your instructor for the missing key.

### Step 5: Verify everything works

Run this script to confirm your API keys are valid and the toolkit is installed correctly:

```sh
python verify_setup.py
```

It sends one short test message to each provider and prints whether it succeeded:

```text
  Anthropic ... OK (claude-opus-4-6, 0.8s)
             Response: "Setup successful."

  OpenAI    ... OK (gpt-4o, 1.2s)
             Response: "Setup successful."

  Google    ... OK (gemini-2.5-flash, 0.6s)
             Response: "Setup successful."
```

If a provider shows **SKIPPED**, that key is missing from `.env`. If it shows **FAILED**, the key is present but not working — check for typos or contact your instructor.

---

## Running Your First Experiment

The project comes with two example experiments. Here's how to run one.

### Step 1: Open `run_experiment.py`

This file is in the main project folder. Open it in VS Code, Codex, Antigravity, Claude Code or any other text editor.

You will see something like this near the top:

```python
CONFIG_PATH = "experiments/example_variable_groups/config.yaml"
```

This line tells the toolkit which experiment to run. The path points to a `config.yaml` file inside one of the example experiment folders.

### Step 2: Run the experiment

Back in your terminal (make sure you're still in the project folder), type:

```sh
python run_experiment.py
```

Press Enter. The toolkit will:

1. Load your experiment configuration
2. Show you a cost estimate
3. Wait for you to press Enter to confirm
4. Make the API calls one by one, printing progress
5. Save all results to the `output/` folder

### Step 3: Find your results

Open the `output/` folder. You'll see a new folder named after your experiment with a timestamp, like:

```text
output/contract_advice_by_persona__2026-03-27_14-23-11/
```

Inside it, you'll find `.txt` files (human-readable results) and a `summary.json` file.

---

## Understanding the Project Folder

Here is what everything in this project does:

```text
LLM_experiment_toolkit/
│
├── run_experiment.py          ← THE FILE YOU EDIT. Change one line to run your experiment.
├── check_models.py            ← Run this to see which models your API keys can access.
├── verify_setup.py            ← Run this first to confirm everything is installed correctly.
├── requirements.txt           ← List of libraries the toolkit needs (don't edit)
├── README.md                  ← This file
├── .env                       ← Your private API keys (don't share this file)
├── .env.example               ← Template showing what .env should look like (safe to share)
│
├── experiments/               ← YOUR EXPERIMENTS LIVE HERE
│   ├── example_variable_groups/      ← Example: comparing responses across conditions
│   │   ├── config.yaml               ← Experiment settings
│   │   ├── system_prompt.txt         ← Instructions for the model
│   │   └── user_prompt.txt           ← The question or task
│   │
│   └── example_data_iteration/       ← Example: running the same prompt on many inputs
│       ├── config.yaml
│       ├── system_prompt.txt
│       ├── user_prompt.txt
│       └── cases.csv                 ← Data file (one row per case)
│
├── output/                    ← RESULTS APPEAR HERE (created automatically)
│   └── experiment_name__date/
│       ├── run_001__condition__model__rep-1.txt    ← Human-readable result
│       ├── run_001__condition__model__rep-1.json   ← Machine-readable result
│       └── summary.json                            ← All results combined
│
└── llm_toolkit/               ← The toolkit's internal code (you probably won't edit this)
    ├── config.py              ← Reads and validates config.yaml files
    ├── prompts.py             ← Loads prompt files and fills in variables
    ├── models.py              ← Handles communication with AI APIs
    ├── runner.py              ← Runs the experiment from start to finish
    ├── output.py              ← Saves results to disk
    └── estimator.py           ← Calculates the cost estimate
```

---

## Creating Your Own Experiment

### Step 1: Copy an example experiment folder

Copy either `experiments/example_variable_groups/` or `experiments/example_data_iteration/` — whichever matches your research design — and give the copy a descriptive name.

For example: `experiments/persona_effect_on_advice/`

### Step 2: Edit the config.yaml file

Open `config.yaml` in your new folder. Change:

- `experiment_name` — a short label for your experiment (no spaces; use underscores)
- The model settings — which AI model(s) to use
- The prompts settings — your prompt file names (leave these as-is if you keep the same file names)
- `repetitions` — how many times to run each condition
- The variable groups or data file settings specific to your experiment pattern

See the [Config File Reference](#config-file-reference) section for a full explanation of every field.

### Step 3: Write your prompts

Edit `system_prompt.txt` and `user_prompt.txt` in your experiment folder. These are plain text files — open them in any text editor.

### Step 4: Point `run_experiment.py` at your experiment

Open `run_experiment.py` and change the `CONFIG_PATH` line:

```python
CONFIG_PATH = "experiments/persona_effect_on_advice/config.yaml"
```

Make sure the path matches the exact name of your experiment folder and ends with `/config.yaml`.

### Step 5: Run it

```sh
python run_experiment.py
```

---

## Experiment Pattern A: Variable Groups

**Use this when:** You want to compare how the model responds differently across a set of defined conditions.

**Example research question:** "Does the AI give different legal advice depending on whether it's told the user is a pro se litigant, a solo practitioner, or a BigLaw partner?"

In this pattern, you define a **variable** — a piece of text that changes across conditions — and write `{{variable_name}}` in your prompt wherever you want that text to be inserted. The toolkit runs the prompt once for each group (condition), substituting the group's value each time.

### Pattern A: Example prompt file (`user_prompt.txt`)

```text
You are advising {{user_persona}}.

Please review the following force majeure clause and explain what it means
for your client, whether it is favorable or unfavorable, and one specific
concern or recommendation.

Clause: "Neither party shall be liable..."
```

### Pattern A: Example config.yaml

```yaml
experiment_name: persona_effect_on_advice
pattern: variable_groups

model:
  - provider: anthropic
    name: claude-sonnet-4-6
    temperature: 0.0
    max_tokens: 1000

prompts:
  system: system_prompt.txt
  user: user_prompt.txt

repetitions: 1

# The variable name must exactly match what you wrote in {{double curly braces}}
# in your prompt file.
variable: user_persona

groups:
  - name: pro_se_litigant
    value: "a pro se litigant with no legal training"
  - name: solo_practitioner
    value: "a solo practitioner attorney with five years of experience"
  - name: biglaw_partner
    value: "a senior partner at a large law firm"
```

The toolkit will make three API calls — one for each group — substituting `{{user_persona}}` with the group's `value` each time.

---

## Experiment Pattern B: Data Iteration

**Use this when:** You want to run the same prompt on many different inputs (cases, statutes, contract clauses, etc.) stored in a spreadsheet.

**Example research question:** "Can the model correctly identify the holding of each of these forty cases?"

In this pattern, you prepare a CSV file (a spreadsheet saved as a `.csv` file — Excel and Google Sheets can export to this format). Each row is one input. Each column becomes a variable you can use in your prompt.

### How to prepare your CSV file

Open Excel or Google Sheets. Create a table with one row per case (or document). The first row should be column headers — short names with no spaces.

Example:

| case_name | court | year | opinion_excerpt |
| --- | --- | --- | --- |
| Palsgraf v. Long Island RR | NY Court of Appeals | 1928 | The conduct of... |
| Hadley v. Baxendale | Court of Exchequer | 1854 | Where two parties... |

Save it as a `.csv` file (File → Download → CSV, or File → Save As → CSV) and put it in your experiment folder.

### Pattern B: Example prompt file (`user_prompt.txt`)

```text
Case: {{case_name}}
Court: {{court}}
Year: {{year}}

Excerpt:
{{opinion_excerpt}}

Please identify the holding of this case in one or two sentences.
```

Every column header from your CSV becomes a `{{variable}}` you can use.

### Pattern B: Example config.yaml

```yaml
experiment_name: holding_identification
pattern: data_iteration

model:
  - provider: anthropic
    name: claude-sonnet-4-6
    temperature: 0.0
    max_tokens: 500

prompts:
  system: system_prompt.txt
  user: user_prompt.txt

repetitions: 1

# The CSV file with your data. Must be in the same folder as this config.yaml.
data_file: cases.csv

# The column whose value will be used to name your output files.
# Use a column that uniquely identifies each row, like a case name.
row_id_column: case_name
```

---

## Running Multiple Models at Once

You can run the same experiment on multiple AI models simultaneously by listing them under `model:`. The toolkit will run every condition for every model and save separate results for each.

```yaml
model:
  - provider: anthropic
    name: claude-opus-4-6
    temperature: 0.0
    max_tokens: 1000
  - provider: openai
    name: gpt-4o
    temperature: 0.0
    max_tokens: 1000
  - provider: google
    name: gemini-2.5-flash
    temperature: 0.0
    max_tokens: 1000
```

---

## Config File Reference

This section explains every field you can use in a `config.yaml` file.

---

### `experiment_name`

A short label for your experiment. Used in the output folder name. Use underscores instead of spaces.

```yaml
experiment_name: persona_effect_on_contract_advice
```

---

### `pattern`

Which experiment design to use. Must be exactly one of these two values:

```yaml
pattern: variable_groups    # compare responses across defined conditions
pattern: data_iteration     # run the same prompt on many rows of a spreadsheet
```

---

### `model`

Which AI model(s) to use. You can list one or several. Each entry needs:

| Field | What it means |
| --- | --- |
| `provider` | Who makes the model: `anthropic`, `openai`, or `google` |
| `name` | The exact model name (see [Checking Available Models](#checking-available-models)) |
| `temperature` | How random the responses are (see below) |
| `max_tokens` | Maximum response length (see below) |

**Temperature** controls how consistent or varied the model's responses are:

- `0.0` — The model gives its single most likely response every time. Use this for empirical research so your results are reproducible and comparable.
- `0.5` — Some variation between runs.
- `1.0` — Noticeably different responses each time.

**Max tokens** is a hard cap on response length. One token ≈ ¾ of a word.

- `500` tokens ≈ about 375 words — good for short answers
- `1000` tokens ≈ about 750 words — good for a paragraph or two
- `2000` tokens ≈ about 1500 words — good for longer analysis

Setting `max_tokens` higher does not make responses longer — it just allows them to be longer if the model needs the space. You are charged for actual tokens used, not the maximum.

---

### `prompts`

Points to your prompt files. Paths are relative to the location of `config.yaml` (so if both files are in the same folder, just use the file name):

```yaml
prompts:
  system: system_prompt.txt
  user: user_prompt.txt
```

**system_prompt.txt** — Instructions to the model about its role. This is sent before every question and is not visible to the "user" in the conversation. Use it to set the model's persona, tone, and task framing.

**user_prompt.txt** — The actual question or task. This is what the model responds to. If you're using variables, place `{{variable_name}}` wherever you want a value substituted.

---

### `repetitions`

How many times to run each condition. With `temperature: 0.0`, repetitions will produce identical results — useful to confirm the model is deterministic. With a higher temperature, repetitions let you measure variation.

```yaml
repetitions: 1    # run each condition once
repetitions: 5    # run each condition five times to study variation
```

---

### `variable` and `groups` (variable_groups pattern only)

`variable` is the name of the placeholder in your prompt (without the curly braces). It must exactly match what you wrote in `{{double_curly_braces}}` in your prompt file, including capitalization.

`groups` is the list of conditions. Each group has:

- `name` — a short label used in output file names (no spaces; use underscores)
- `value` — the text that replaces `{{variable}}` in the prompt

```yaml
variable: user_persona

groups:
  - name: pro_se_litigant
    value: "a pro se litigant with no legal training"
  - name: solo_practitioner
    value: "a solo practitioner attorney"
```

---

### `data_file` and `row_id_column` (data_iteration pattern only)

`data_file` is the name of your CSV file. It must be in the same folder as `config.yaml`.

`row_id_column` is the name of the column whose values will be used to name your output files. Choose a column that uniquely identifies each row (like `case_name`).

```yaml
data_file: cases.csv
row_id_column: case_name
```

---

## Understanding the Cost Estimate

Before every experiment, the toolkit shows a cost estimate and asks you to confirm:

```text
========================================================================
  COST ESTIMATE
========================================================================
  Model                           Runs   Input tok  Output tok (max)   Cost range
  ----------------------------------------------------------------------
  claude-opus-4-6 (anthropic)        3         858       up to 3,000   $0.01 – $0.24
  gpt-4o (openai)                    3         858       up to 3,000   $0.00 – $0.03
  ----------------------------------------------------------------------
  TOTAL                              6       1,716       up to 6,000   $0.02 – $0.27
========================================================================
  Press Enter to start the experiment, or Ctrl+C to cancel...
```

**Input tokens** — how many tokens are in the prompts you're sending. This is calculated exactly from your prompt files.

**Output tokens (max)** — how many tokens the model's responses could use. We can't know in advance how long responses will be, so this shows the maximum based on your `max_tokens` setting. Real responses are almost always shorter.

**Cost range** — the low end assumes very short responses; the high end assumes maximum-length responses. Your actual cost will almost always fall somewhere in between, and is typically much closer to the low end.

Press Enter to proceed, or press **Ctrl+C** (hold the Control key and press C) to cancel without spending anything.

---

## Your Output Files

After an experiment runs, you'll find a new folder in `output/` named after your experiment and the time it ran:

```text
output/persona_effect__2026-03-27_14-23-11/
```

Inside it:

### Individual run files (`.txt`)

One `.txt` file per API call. Open these in any text editor to read the results. Each file shows:

- Which experiment, condition, model, and repetition this was
- The exact timestamp of the call
- How many tokens were used and how long it took
- The complete system prompt that was sent
- The complete user prompt that was sent (with variables already substituted)
- The model's complete response

### Individual run files (`.json`)

One `.json` file per API call. These contain the same information as the `.txt` files but in a structured format suitable for data analysis. You can open them in a text editor to read them, but they're designed to be loaded into analysis tools.

### `summary.json`

A single file containing all runs from the experiment combined. This is the file to use for analysis.

**Opening summary.json in Excel:**

1. Open Excel
2. Go to **Data → Get Data → From File → From JSON**
3. Navigate to your `summary.json` file and click Import
4. In the Power Query window that opens, click the **Convert** button or **To Table** button (top left)
5. Click **OK** on the dialog that appears, then click **Close & Load**

You now have a spreadsheet with one row per API call. Useful things to do from here:

- **Filter by condition:** Click the dropdown arrow on the `condition_label` column header to show only one group at a time.
- **Compare models:** Add a filter on `model_name` to see responses side by side.
- **Spot failures:** Filter `error` to non-blank values to find any calls that failed.
- **Pivot table for comparison:** Select the data, go to Insert → PivotTable. Drag `condition_label` to Rows, `model_name` to Columns, and `response_content` to Values (set to "Count") to see how many responses you have per condition per model.

If the JSON import steps above don't match your version of Excel, try saving the file as `summary.json`, then search online for "import JSON into Excel" with your Excel version — the steps vary slightly between Excel for Mac and Excel for Windows.

**Loading summary.json in Python (for more advanced analysis):**

```python
import pandas as pd
df = pd.read_json("output/persona_effect__2026-03-27_14-23-11/summary.json")
```

The most useful columns in the data:

| Column | What it contains |
| --- | --- |
| `condition_label` | Which group or row this was (e.g., `pro_se_litigant`) |
| `model_name` | Which model was used (e.g., `claude-opus-4-6`) |
| `repetition` | Which repetition this was |
| `response_content` | The model's response |
| `input_tokens` | Tokens sent |
| `output_tokens` | Tokens received |
| `duration_seconds` | How long the API call took |
| `error` | Error message if the call failed, otherwise empty |

---

## Checking Available Models

To see the exact models your API keys give you access to, run:

```sh
python check_models.py
```

This connects to each provider and prints a list like this:

```text
==================================================================
  ANTHROPIC (Claude)  (6 models with cost estimates)
==================================================================
  [*] claude-sonnet-4-6          Claude Sonnet 4.6
  [*] claude-opus-4-6            Claude Opus 4.6
      claude-haiku-4-5-20251001  Claude Haiku 4.5
      ...

==================================================================
  OPENAI (GPT / o-series)  (5 models with cost estimates)
==================================================================
  [*] gpt-4o
  [*] gpt-4o-mini
      ...

==================================================================
  GOOGLE (Gemini)  (4 models with cost estimates)
==================================================================
  [*] gemini-2.0-flash           Gemini 2.0 Flash
      gemini-2.5-pro             Gemini 2.5 Pro
      ...
```

**Reading the output:**

- The value in the **left column** is the model id — copy this exactly into the `name` field in your `config.yaml`.
- **`[*]`** means the toolkit has a cost estimate for that model, so you'll see a dollar-range before the experiment runs. Models without `[*]` will still work; they just won't show a cost estimate. You can add pricing for any model by editing the `PRICING` table in `llm_toolkit/estimator.py`.
- If a provider section says **"Key not found"**, that API key is missing from your `.env` file.
- If it says **"Could not connect"**, the key may be expired or invalid.

The cost estimate shown before each experiment run will give you exact numbers for your specific prompts and settings.

---

## Troubleshooting

### "error: externally-managed-environment" when running pip install

Your Python installation restricts global package installs (common on Macs
that use Homebrew). The fix is to use a **virtual environment** — an isolated
space for this project's packages that won't interfere with anything else on
your computer.

Run these two commands once from the project folder:

```sh
python -m venv .venv
source .venv/bin/activate
```

Then install the packages as normal:

```sh
pip install -r requirements.txt
```

**Important:** every time you open a new terminal window to run experiments,
you need to activate the environment first:

```sh
source .venv/bin/activate
```

You'll know it's active when you see `(.venv)` at the start of your terminal
prompt. Once active, `python run_experiment.py` and `python check_models.py`
work exactly as described in this guide.

---

### "python: command not found" or "python3: command not found"

Python is not installed. Download and install it from [python.org/downloads](https://www.python.org/downloads/). After installing, close and reopen your terminal, then try again.

### "No module named llm_toolkit" or import errors

You're running the command from the wrong folder. Make sure your terminal is in the project folder. Type `pwd` (Mac) or `cd` (Windows) to see where you are, then use `cd` to navigate to the right place.

### "Config file not found"

The `CONFIG_PATH` in `run_experiment.py` doesn't match an actual file. Check that:

- The path is spelled correctly
- The experiment folder exists inside the `experiments/` folder
- The path ends with `/config.yaml`

### "API key not found"

The `.env` file is missing a key for the provider you're trying to use. Open `.env` and check that the relevant line exists and has a real key after the equals sign.

### "Variable '{{xyz}}' not found"

The `{{variable_name}}` in your prompt file doesn't match the `variable:` field in `config.yaml`. They must be identical, including capitalization. For example, if your prompt has `{{user_Persona}}` but your config says `variable: user_persona`, it will fail.

### "File not found: system_prompt.txt" (or user_prompt.txt)

The prompt file name listed in `config.yaml` doesn't match the actual file name. Check the spelling and capitalization. File names are case-sensitive on Mac.

### Some runs show "RateLimitError" or "429" errors

You have sent too many requests too quickly and the provider has temporarily
blocked further calls. This is common when running large experiments (many
conditions, many rows, or multiple models at once).

What to do:

- Wait a few minutes, then re-run the experiment. Failed runs will be recorded
  in a new output folder alongside any successful ones.
- Reduce the size of your experiment — try a smaller subset of rows or fewer
  models first to confirm it works, then run the full set.
- Check your API account's rate limit tier. Free or trial accounts have much
  lower limits than paid accounts. Contact your instructor if you need a
  higher-tier key.

The toolkit records which runs failed (with the error message) in both the
individual `.json` files and `summary.json`, so you can identify exactly
which calls need to be re-run.

### One run shows "FAILED" in the terminal, others continue

An individual API call failed (perhaps a temporary network issue or rate limit). The experiment keeps going — the failed run is saved with an `error` description in its output file. You can re-run the experiment and compare, or simply note the failed run in your analysis.

### The experiment ran but I can't find the output

Look inside the `output/` folder in the project directory. Each run creates a new subfolder with a timestamp. If you've run the experiment multiple times, you'll have multiple subfolders — the most recent one will have the latest timestamp.

---

## Getting Help

This toolkit is a foundation for you to build on. If you want to modify how it works, extend it with new features, or adapt it to a research design it doesn't currently support, the best approach is to open the relevant file in your AI coding assistant (Claude Code, Copilot, etc.) and describe what you want to change.

The Python files in `llm_toolkit/` each begin with a comment explaining what they do and whether you're likely to want to edit them.

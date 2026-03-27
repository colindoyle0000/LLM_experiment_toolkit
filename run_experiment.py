"""
LLM EXPERIMENT RUNNER

This is the only file you need to edit to run an experiment.

INSTRUCTIONS:
  1. Change CONFIG_PATH below to point to your experiment folder.
     It should end with /config.yaml

  2. Save this file.

  3. In your terminal, run:
        python run_experiment.py

EXAMPLE CONFIG_PATH values:
  "experiments/example_variable_groups/config.yaml"
  "experiments/example_data_iteration/config.yaml"
  "experiments/my_experiment/config.yaml"

The path goes: experiments/ → your experiment folder → config.yaml
Use forward slashes ( / ), not backslashes ( \\ ).
"""

from llm_toolkit.runner import ExperimentRunner

CONFIG_PATH = "experiments/example_variable_groups/config.yaml"

# =============================================================================
# Do not edit below this line.
# =============================================================================

if __name__ == "__main__":
    runner = ExperimentRunner(CONFIG_PATH)
    runner.run()

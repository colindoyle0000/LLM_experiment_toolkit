"""
runner.py — Runs an experiment from start to finish.

This is the "conductor" of the toolkit. It reads the config, shows you the
cost estimate, then loops through every combination of model × condition ×
repetition, sends each prompt to the API, and saves the result.

Progress is printed to the terminal as each call completes, so you can
watch the experiment run in real time.

Usage (from run_experiment.py):
    runner = ExperimentRunner("experiments/my_study/config.yaml")
    runner.run()

YOU PROBABLY DON'T NEED TO EDIT THIS FILE.
If you want to change how the experiment loops (e.g. randomize run order,
add a delay between calls, or skip certain conditions), this is the place.
"""

from datetime import datetime

import pandas as pd

from llm_toolkit.config import ExperimentConfig
from llm_toolkit.estimator import show_estimate
from llm_toolkit.models import create_client
from llm_toolkit.output import OutputWriter, RunResult
import llm_toolkit.prompts as prompts


class ExperimentRunner:
    def __init__(self, config_path: str):
        self.config = ExperimentConfig.load(config_path)

    def run(self) -> None:
        cfg = self.config
        print(f"Experiment: {cfg.experiment_name}")
        print(f"Pattern:    {cfg.pattern}")
        print(f"Models:     {', '.join(m.name for m in cfg.models)}")
        if cfg.pattern == "variable_groups":
            print(f"Groups:     {', '.join(g.name for g in cfg.groups)}")
            n_conditions = len(cfg.groups)
        else:
            df = pd.read_csv(cfg.data_file_path)
            print(f"Data rows:  {len(df)}")
            n_conditions = len(df)
        print(f"Models x Conditions x Reps = {len(cfg.models)} x {n_conditions} x {cfg.repetitions} = "
              f"{len(cfg.models) * n_conditions * cfg.repetitions} total API calls")

        show_estimate(cfg)

        writer = OutputWriter(cfg.experiment_name)

        if cfg.pattern == "variable_groups":
            self._run_variable_groups(writer)
        else:
            self._run_data_iteration(writer)

        writer.write_summary()
        print("\nDone.")

    def _run_variable_groups(self, writer: OutputWriter) -> None:
        cfg = self.config
        total = len(cfg.models) * len(cfg.groups) * cfg.repetitions
        run_index = 1

        system_str = prompts.load_system(cfg.system_prompt_path)

        for model_cfg in cfg.models:
            client = create_client(model_cfg)
            for group in cfg.groups:
                variables = {cfg.variable: group.value}
                user_str = prompts.load_user(cfg.user_prompt_path, variables)

                for rep in range(1, cfg.repetitions + 1):
                    label = f"{group.name} | {model_cfg.name}"
                    print(f"[{run_index}/{total}] {label} | rep {rep}...", end=" ", flush=True)

                    response = client.call(system_str, user_str)

                    if response.error:
                        print(f"FAILED ({response.error})")
                    else:
                        print(f"done ({response.duration_seconds}s, "
                              f"{response.input_tokens}+{response.output_tokens} tokens)")

                    result = RunResult(
                        experiment_name=cfg.experiment_name,
                        run_index=run_index,
                        condition_label=group.name,
                        repetition=rep,
                        total_repetitions=cfg.repetitions,
                        timestamp=datetime.now().isoformat(timespec="seconds"),
                        system_prompt=system_str,
                        user_prompt=user_str,
                        response=response,
                    )
                    writer.write(result)
                    run_index += 1

    def _run_data_iteration(self, writer: OutputWriter) -> None:
        cfg = self.config
        df = pd.read_csv(cfg.data_file_path)

        if cfg.row_id_column not in df.columns:
            raise ValueError(
                f"'row_id_column' is set to '{cfg.row_id_column}' in config.yaml, "
                f"but that column was not found in {cfg.data_file_path}.\n"
                f"Available columns: {list(df.columns)}"
            )

        total = len(cfg.models) * len(df) * cfg.repetitions
        run_index = 1

        system_str = prompts.load_system(cfg.system_prompt_path)

        for model_cfg in cfg.models:
            client = create_client(model_cfg)

            for _, row in df.iterrows():
                variables = {col: str(val) for col, val in row.items()}
                user_str = prompts.load_user(cfg.user_prompt_path, variables)
                row_id = str(row[cfg.row_id_column])

                for rep in range(1, cfg.repetitions + 1):
                    label = f"{row_id} | {model_cfg.name}"
                    print(f"[{run_index}/{total}] {label} | rep {rep}...", end=" ", flush=True)

                    response = client.call(system_str, user_str)

                    if response.error:
                        print(f"FAILED ({response.error})")
                    else:
                        print(f"done ({response.duration_seconds}s, "
                              f"{response.input_tokens}+{response.output_tokens} tokens)")

                    result = RunResult(
                        experiment_name=cfg.experiment_name,
                        run_index=run_index,
                        condition_label=row_id,
                        repetition=rep,
                        total_repetitions=cfg.repetitions,
                        timestamp=datetime.now().isoformat(timespec="seconds"),
                        system_prompt=system_str,
                        user_prompt=user_str,
                        response=response,
                    )
                    writer.write(result)
                    run_index += 1

#!/usr/bin/env python3
import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = ROOT / "workloads" / "bin"


def build_command(task: dict) -> list[str]:
    task_type = task["type"]
    if task_type == "cpu":
        return [str(BIN_DIR / "cpu_bound"), str(task["duration_ms"])]
    if task_type == "sleep_burst":
        return [
            str(BIN_DIR / "sleep_burst"),
            str(task["burst_ms"]),
            str(task["sleep_ms"]),
            str(task["cycles"]),
        ]
    raise ValueError(f"unsupported task type: {task_type}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Launch workload tasks from JSON config")
    parser.add_argument("config", help="Path to workload JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without launching")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    data = json.loads(config_path.read_text())
    tasks = sorted(data.get("tasks", []), key=lambda item: item.get("start_delay_ms", 0))

    if not tasks:
        print("No tasks defined in config", file=sys.stderr)
        return 1

    processes: list[subprocess.Popen] = []
    start_time = time.monotonic()

    try:
        for task in tasks:
            delay_ms = int(task.get("start_delay_ms", 0))
            now_ms = int((time.monotonic() - start_time) * 1000)
            remaining_ms = delay_ms - now_ms
            if remaining_ms > 0:
                time.sleep(remaining_ms / 1000.0)

            cmd = build_command(task)
            task_name = task.get("name", task["type"])
            task_nice = int(task.get("nice", 0))

            if args.dry_run:
                print(f"{task_name}: nice={task_nice} cmd={' '.join(cmd)}")
                continue

            process = subprocess.Popen(
                cmd,
                preexec_fn=lambda nice=task_nice: os.nice(nice),
            )
            print(f"started {task_name} pid={process.pid} nice={task_nice}")
            processes.append(process)

        if args.dry_run:
            return 0

        exit_code = 0
        for process in processes:
            result = process.wait()
            if result != 0:
                exit_code = result
        return exit_code
    except KeyboardInterrupt:
        for process in processes:
            if process.poll() is None:
                process.send_signal(signal.SIGTERM)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())

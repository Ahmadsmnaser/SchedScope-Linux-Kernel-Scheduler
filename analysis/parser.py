from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Iterable


TRACE_PREFIX_RE = re.compile(
    r"^\s*(?P<comm>.+)-(?P<trace_pid>\d+)\s+\[(?P<cpu>\d+)\].*?:\s+"
    r"(?P<trace_func>[A-Za-z0-9_]+):\s+(?P<payload>\[SCHED_TRACE\].*)$"
)

KV_RE = re.compile(r"([A-Za-z_]+)=(-?\d+|[A-Za-z0-9_./:-]+)")

INT_FIELDS = {
    "ts",
    "cpu",
    "pid",
    "prev",
    "next",
    "curr",
    "cand",
    "vruntime",
    "nice",
}

CSV_FIELDS = [
    "line_number",
    "comm",
    "trace_pid",
    "trace_cpu",
    "trace_func",
    "ev",
    "ts",
    "cpu",
    "pid",
    "prev",
    "next",
    "curr",
    "cand",
    "vruntime",
    "nice",
    "raw_line",
]


def parse_trace_line(line: str, line_number: int) -> dict | None:
    match = TRACE_PREFIX_RE.match(line.rstrip("\n"))
    if not match:
        return None

    data = {
        "line_number": line_number,
        "comm": match.group("comm").strip(),
        "trace_pid": int(match.group("trace_pid")),
        "trace_cpu": int(match.group("cpu")),
        "trace_func": match.group("trace_func"),
        "raw_line": line.rstrip("\n"),
    }

    payload = match.group("payload")
    for key, value in KV_RE.findall(payload):
        if key in INT_FIELDS:
            data[key] = int(value)
        else:
            data[key] = value

    if "ev" not in data or "ts" not in data:
        return None

    for field in CSV_FIELDS:
        data.setdefault(field, None)

    return data


def parse_trace_file(path: str | Path) -> list[dict]:
    events: list[dict] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            event = parse_trace_line(line, line_number)
            if event is not None:
                events.append(event)
    return events


def write_jsonl(events: Iterable[dict], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True))
            handle.write("\n")


def write_csv(events: Iterable[dict], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for event in events:
            writer.writerow({field: event.get(field) for field in CSV_FIELDS})

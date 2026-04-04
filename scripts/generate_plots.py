#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import struct
import zlib
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLOT_COLORS = [
    (11, 110, 79),
    (200, 76, 9),
    (53, 101, 169),
    (156, 47, 47),
    (106, 76, 147),
    (42, 157, 143),
    (188, 108, 37),
    (95, 15, 64),
]
WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
GRAY = (210, 210, 210)
LIGHT_GRAY = (236, 236, 236)
BLUE = (53, 101, 169)
ORANGE = (200, 76, 9)
GREEN = (11, 110, 79)
TEAL = (42, 157, 143)


class Canvas:
    def __init__(self, width: int, height: int, background: tuple[int, int, int] = WHITE) -> None:
        self.width = width
        self.height = height
        self.pixels = bytearray(background * width * height)

    def _offset(self, x: int, y: int) -> int:
        return (y * self.width + x) * 3

    def set_pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            idx = self._offset(x, y)
            self.pixels[idx : idx + 3] = bytes(color)

    def fill_rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int]) -> None:
        if w <= 0 or h <= 0:
            return
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            idx = self._offset(x0, yy)
            self.pixels[idx : idx + len(row)] = row

    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int]) -> None:
        dx = abs(x2 - x1)
        sx = 1 if x1 < x2 else -1
        dy = -abs(y2 - y1)
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        while True:
            self.set_pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    def save_png(self, path: Path) -> None:
        def chunk(tag: bytes, data: bytes) -> bytes:
            return (
                struct.pack("!I", len(data))
                + tag
                + data
                + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
            )

        raw = bytearray()
        stride = self.width * 3
        for y in range(self.height):
            raw.append(0)
            start = y * stride
            raw.extend(self.pixels[start : start + stride])

        png = bytearray(b"\x89PNG\r\n\x1a\n")
        png.extend(
            chunk(
                b"IHDR",
                struct.pack("!IIBBBBB", self.width, self.height, 8, 2, 0, 0, 0),
            )
        )
        png.extend(chunk(b"IDAT", zlib.compress(bytes(raw), level=9)))
        png.extend(chunk(b"IEND", b""))
        path.write_bytes(bytes(png))


def load_metrics(run_dir: Path) -> dict:
    return json.loads((run_dir / "metrics_summary.json").read_text(encoding="utf-8"))


def load_pick_intervals(run_dir: Path, pid_to_comm: dict[int, str]) -> list[dict]:
    picks: list[dict] = []
    with (run_dir / "normalized_events.csv").open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("ev") != "pick":
                continue
            next_pid = row.get("next")
            ts = row.get("ts")
            if not next_pid or not ts:
                continue
            pid = int(next_pid)
            if pid < 0:
                continue
            picks.append({"ts": int(ts), "pid": pid})

    intervals: list[dict] = []
    for current, following in zip(picks, picks[1:]):
        if following["ts"] <= current["ts"]:
            continue
        pid = current["pid"]
        intervals.append(
            {
                "pid": pid,
                "comm": pid_to_comm.get(pid, f"pid_{pid}"),
                "start_ts": current["ts"],
                "end_ts": following["ts"],
                "duration_ns": following["ts"] - current["ts"],
            }
        )
    return intervals


def write_timeline_csv(intervals: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["pid", "comm", "start_ts", "end_ts", "duration_ns"])
        writer.writeheader()
        for row in intervals:
            writer.writerow(row)


def write_per_task_csv(per_task: list[dict], path: Path) -> None:
    fields = [
        "pid",
        "comm",
        "runtime_ns",
        "wait_time_ns",
        "response_time_ns",
        "turnaround_time_ns_inferred",
        "pick_count",
        "enqueue_count",
        "dequeue_count",
        "preempted_count",
        "preempt_candidate_count",
        "completed_in_trace_inferred",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in per_task:
            writer.writerow({field: row.get(field) for field in fields})


def draw_axes(canvas: Canvas, left: int, top: int, right: int, bottom: int) -> None:
    canvas.line(left, top, left, bottom, BLACK)
    canvas.line(left, bottom, right, bottom, BLACK)
    for idx in range(1, 5):
        y = top + ((bottom - top) * idx) // 5
        canvas.line(left, y, right, y, LIGHT_GRAY)


def plot_timeline(intervals: list[dict], path: Path) -> None:
    canvas = Canvas(1200, 520)
    left, top, right, bottom = 80, 40, 1160, 470
    draw_axes(canvas, left, top, right, bottom)

    if intervals:
        totals = defaultdict(int)
        for item in intervals:
            totals[item["pid"]] += item["duration_ns"]
        selected = [pid for pid, _ in sorted(totals.items(), key=lambda item: item[1], reverse=True)[:8]]
        filtered = [item for item in intervals if item["pid"] in selected]
        if filtered:
            min_ts = min(item["start_ts"] for item in filtered)
            max_ts = max(item["end_ts"] for item in filtered)
            span = max(max_ts - min_ts, 1)
            pid_order = sorted(selected)
            band_h = max((bottom - top) // max(len(pid_order), 1), 1)
            for band, pid in enumerate(pid_order):
                y = top + band * band_h
                canvas.fill_rect(left, y, right - left, max(band_h - 1, 1), (250, 250, 250) if band % 2 == 0 else WHITE)
                color = PLOT_COLORS[band % len(PLOT_COLORS)]
                for item in filtered:
                    if item["pid"] != pid:
                        continue
                    x1 = left + int((item["start_ts"] - min_ts) * (right - left) / span)
                    x2 = left + int((item["end_ts"] - min_ts) * (right - left) / span)
                    canvas.fill_rect(x1, y + 4, max(x2 - x1, 1), max(band_h - 8, 1), color)

    canvas.save_png(path)


def _histogram(values: list[float], bins: int) -> tuple[list[int], float, float]:
    if not values:
        return [0] * bins, 0.0, 1.0
    low = min(values)
    high = max(values)
    if high <= low:
        high = low + 1.0
    width = (high - low) / bins
    counts = [0] * bins
    for value in values:
        index = int((value - low) / width)
        if index >= bins:
            index = bins - 1
        counts[index] += 1
    return counts, low, high


def plot_latency(per_task: list[dict], path: Path) -> None:
    canvas = Canvas(1000, 520)
    left, top, right, bottom = 70, 40, 960, 470
    draw_axes(canvas, left, top, right, bottom)

    wait_ms = [task["wait_time_ns"] / 1_000_000 for task in per_task if task.get("wait_time_ns")]
    response_ms = [task["response_time_ns"] / 1_000_000 for task in per_task if task.get("response_time_ns") is not None]
    bins = 12
    wait_hist, _, _ = _histogram(wait_ms, bins)
    resp_hist, _, _ = _histogram(response_ms, bins)
    max_count = max(wait_hist + resp_hist + [1])
    slot_w = max((right - left) // bins, 1)

    for idx in range(bins):
        x = left + idx * slot_w + 4
        wait_h = int(wait_hist[idx] * (bottom - top - 20) / max_count)
        resp_h = int(resp_hist[idx] * (bottom - top - 20) / max_count)
        canvas.fill_rect(x, bottom - wait_h, max(slot_w // 2 - 6, 1), wait_h, BLUE)
        canvas.fill_rect(x + slot_w // 2, bottom - resp_h, max(slot_w // 2 - 6, 1), resp_h, ORANGE)

    canvas.save_png(path)


def plot_fairness(run_dir: Path, per_task: list[dict], path: Path, summary_csv: Path | None) -> None:
    canvas = Canvas(1000, 520)
    left, top, right, bottom = 70, 40, 960, 470
    draw_axes(canvas, left, top, right, bottom)

    labels: list[str] = []
    values: list[float] = []
    color = GREEN

    if summary_csv and summary_csv.exists():
        with summary_csv.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                fairness = row.get("fairness_jain_runtime_user_tasks")
                if not fairness:
                    continue
                labels.append(row.get("run_name") or row.get("experiment") or "run")
                values.append(float(fairness))

    if not values:
        selected = sorted(per_task, key=lambda task: task.get("runtime_ns", 0), reverse=True)[:8]
        labels = [str(task["pid"]) for task in selected]
        values = [task.get("runtime_ns", 0) / 1_000_000 for task in selected]
        color = TEAL

    max_value = max(values + [1.0])
    slot_w = max((right - left) // max(len(values), 1), 1)
    for idx, value in enumerate(values):
        x = left + idx * slot_w + 8
        bar_h = int(value * (bottom - top - 20) / max_value)
        canvas.fill_rect(x, bottom - bar_h, max(slot_w - 16, 1), bar_h, color)

    canvas.save_png(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate SchedScope CSV exports and plots")
    parser.add_argument("run_dir", help="Run directory containing normalized events and metrics summary")
    parser.add_argument("--summary-csv", help="Optional benchmark summary.csv for fairness comparison")
    parser.add_argument("--output-dir", help="Directory for plot images; defaults to plots/<run_name>")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    metrics = load_metrics(run_dir)
    per_task = metrics.get("per_task", [])
    pid_to_comm = {int(task["pid"]): task.get("comm") or f"pid_{task['pid']}" for task in per_task}
    intervals = load_pick_intervals(run_dir, pid_to_comm)

    timeline_csv = run_dir / "timeline_data.csv"
    per_task_csv = run_dir / "per_task_metrics.csv"
    write_timeline_csv(intervals, timeline_csv)
    write_per_task_csv(per_task, per_task_csv)

    output_dir = Path(args.output_dir).resolve() if args.output_dir else (ROOT / "plots" / run_dir.name)
    output_dir.mkdir(parents=True, exist_ok=True)

    plot_timeline(intervals, output_dir / "timeline.png")
    plot_latency(per_task, output_dir / "latency.png")
    summary_csv = Path(args.summary_csv).resolve() if args.summary_csv else None
    plot_fairness(run_dir, per_task, output_dir / "fairness.png", summary_csv)

    print(f"Wrote {timeline_csv}")
    print(f"Wrote {per_task_csv}")
    print(f"Wrote {output_dir / 'timeline.png'}")
    print(f"Wrote {output_dir / 'latency.png'}")
    print(f"Wrote {output_dir / 'fairness.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

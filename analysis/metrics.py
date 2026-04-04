from __future__ import annotations

from collections import Counter
from math import fsum


HELPER_COMMS = {
    "cat",
    "exe",
    "renice",
    "rcu_preempt",
    "sh",
    "sleep",
}


def _make_task(pid: int, comm: str | None) -> dict:
    return {
        "pid": pid,
        "comm": comm,
        "first_seen_ts": None,
        "last_seen_ts": None,
        "first_enqueue_ts": None,
        "first_run_ts": None,
        "last_dequeue_ts": None,
        "last_event": None,
        "enqueue_count": 0,
        "dequeue_count": 0,
        "pick_count": 0,
        "preempted_count": 0,
        "preempt_candidate_count": 0,
        "runtime_ns": 0,
        "wait_time_ns": 0,
        "response_time_ns": None,
        "turnaround_time_ns_inferred": None,
        "completed_in_trace_inferred": False,
    }


def _prefer_comm(existing: str | None, new: str | None) -> str | None:
    if not new:
        return existing
    if not existing:
        return new
    if existing == new:
        return existing
    if existing in HELPER_COMMS and new not in HELPER_COMMS:
        return new
    if existing == "sh" and new != "sh":
        return new
    return existing


def _is_user_workload_task(task: dict) -> bool:
    comm = task.get("comm")
    if not comm:
        return False
    if comm in HELPER_COMMS:
        return False
    if comm.startswith("kworker") or comm.startswith("ksoftirqd") or comm.startswith("kcompactd"):
        return False
    return True


def _jain_index(values: list[int]) -> float | None:
    positive = [float(value) for value in values if value > 0]
    if not positive:
        return None
    numerator = fsum(positive) ** 2
    denominator = len(positive) * fsum(value * value for value in positive)
    if denominator == 0:
        return None
    return numerator / denominator


def compute_metrics(events: list[dict]) -> dict:
    if not events:
        return {
            "trace_summary": {
                "event_count": 0,
                "trace_start_ns": None,
                "trace_end_ns": None,
                "trace_duration_ns": 0,
            },
            "aggregate_metrics": {},
            "per_task": [],
        }

    tasks: dict[int, dict] = {}
    event_counts = Counter()
    current_pid: int | None = None
    last_pick_ts: int | None = None
    runnable_since: dict[int, int] = {}

    def ensure_task(pid: int | None, comm: str | None = None) -> dict | None:
        if pid is None or pid < 0:
            return None
        task = tasks.get(pid)
        if task is None:
            task = _make_task(pid, comm)
            tasks[pid] = task
        else:
            task["comm"] = _prefer_comm(task.get("comm"), comm)
        return task

    def mark_task_seen(pid: int | None, comm: str | None, ts: int, event_name: str) -> None:
        task = ensure_task(pid, comm)
        if task is None:
            return
        if task["first_seen_ts"] is None:
            task["first_seen_ts"] = ts
        task["last_seen_ts"] = ts
        task["last_event"] = event_name

    def close_runtime(ts: int) -> None:
        nonlocal last_pick_ts
        if current_pid is None or last_pick_ts is None or ts < last_pick_ts:
            return
        task = ensure_task(current_pid)
        if task is not None:
            task["runtime_ns"] += ts - last_pick_ts
            task["last_seen_ts"] = ts

    for event in events:
        ts = event["ts"]
        ev = event["ev"]
        comm = event.get("comm")
        event_counts[ev] += 1

        mark_task_seen(event.get("trace_pid"), comm, ts, ev)

        for field in ("pid", "prev", "next", "curr", "cand"):
            if field in event:
                known_comm = comm if event.get(field) == event.get("trace_pid") else None
                mark_task_seen(event[field], known_comm, ts, ev)

        if ev == "enqueue":
            pid = event.get("pid")
            task = ensure_task(pid, comm)
            if task is None:
                continue
            task["enqueue_count"] += 1
            if task["first_enqueue_ts"] is None:
                task["first_enqueue_ts"] = ts
            if pid != current_pid:
                runnable_since.setdefault(pid, ts)

        elif ev == "dequeue":
            pid = event.get("pid")
            task = ensure_task(pid, comm)
            if task is None:
                continue
            task["dequeue_count"] += 1
            task["last_dequeue_ts"] = ts
            if pid in runnable_since:
                task["wait_time_ns"] += ts - runnable_since.pop(pid)

        elif ev == "preempt":
            curr = event.get("curr")
            cand = event.get("cand")
            curr_task = ensure_task(curr)
            cand_task = ensure_task(cand)
            if curr_task is not None:
                curr_task["preempted_count"] += 1
            if cand_task is not None:
                cand_task["preempt_candidate_count"] += 1

        elif ev == "pick":
            prev_pid = event.get("prev")
            next_pid = event.get("next")

            close_runtime(ts)

            next_task = ensure_task(next_pid, comm)
            if next_task is not None:
                next_task["pick_count"] += 1
                if next_task["first_run_ts"] is None:
                    next_task["first_run_ts"] = ts
                    if next_task["first_enqueue_ts"] is not None:
                        next_task["response_time_ns"] = ts - next_task["first_enqueue_ts"]
                if next_pid in runnable_since:
                    next_task["wait_time_ns"] += ts - runnable_since.pop(next_pid)

            if prev_pid is not None and next_pid is not None and prev_pid >= 0 and prev_pid != next_pid:
                runnable_since[prev_pid] = ts

            current_pid = next_pid if next_pid is not None and next_pid >= 0 else None
            last_pick_ts = ts

    trace_end_ns = events[-1]["ts"]
    close_runtime(trace_end_ns)

    per_task: list[dict] = []
    inferred_completed = 0
    for pid in sorted(tasks):
        task = tasks[pid]
        last_dequeue_ts = task["last_dequeue_ts"]
        first_enqueue_ts = task["first_enqueue_ts"]
        completed_inferred = (
            last_dequeue_ts is not None
            and task["last_event"] == "dequeue"
            and task["enqueue_count"] >= 1
            and task["pick_count"] >= 1
        )
        if completed_inferred and first_enqueue_ts is not None:
            task["completed_in_trace_inferred"] = True
            task["turnaround_time_ns_inferred"] = last_dequeue_ts - first_enqueue_ts
            inferred_completed += 1
        per_task.append(task)

    trace_start_ns = events[0]["ts"]
    trace_duration_ns = max(trace_end_ns - trace_start_ns, 0)
    total_runtime_ns = sum(task["runtime_ns"] for task in per_task)
    runtime_values = [task["runtime_ns"] for task in per_task]
    workload_tasks = [task for task in per_task if _is_user_workload_task(task)]
    workload_runtime_values = [task["runtime_ns"] for task in workload_tasks]
    turnaround_samples = [
        task["turnaround_time_ns_inferred"]
        for task in per_task
        if task["turnaround_time_ns_inferred"] is not None
    ]
    response_samples = [
        task["response_time_ns"] for task in per_task if task["response_time_ns"] is not None
    ]
    wait_samples = [task["wait_time_ns"] for task in per_task if task["wait_time_ns"] > 0]

    return {
        "trace_summary": {
            "event_count": len(events),
            "event_counts": dict(event_counts),
            "trace_start_ns": trace_start_ns,
            "trace_end_ns": trace_end_ns,
            "trace_duration_ns": trace_duration_ns,
        },
        "aggregate_metrics": {
            "context_switches": sum(
                1
                for event in events
                if event.get("ev") == "pick"
                and event.get("prev", -1) >= 0
                and event.get("next", -1) >= 0
                and event.get("prev") != event.get("next")
            ),
            "preemptions": event_counts.get("preempt", 0),
            "cpu_utilization_estimate": (
                total_runtime_ns / trace_duration_ns if trace_duration_ns > 0 else None
            ),
            "throughput_tasks_per_sec_inferred": (
                inferred_completed / (trace_duration_ns / 1_000_000_000)
                if trace_duration_ns > 0
                else None
            ),
            "completed_tasks_inferred": inferred_completed,
            "average_wait_time_ns": (
                sum(wait_samples) / len(wait_samples) if wait_samples else None
            ),
            "average_response_time_ns": (
                sum(response_samples) / len(response_samples) if response_samples else None
            ),
            "average_turnaround_time_ns_inferred": (
                sum(turnaround_samples) / len(turnaround_samples) if turnaround_samples else None
            ),
            "fairness_jain_runtime_all_tasks": _jain_index(runtime_values),
            "fairness_jain_runtime_user_tasks": _jain_index(workload_runtime_values),
            "tracked_task_count": len(per_task),
            "tracked_user_task_count": len(workload_tasks),
        },
        "per_task": per_task,
    }

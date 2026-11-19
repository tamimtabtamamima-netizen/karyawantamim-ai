"""Memori persistent sebagai JSON file. Bounded size, atomic write."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import config
from log import warn, info


def _empty_state() -> dict:
    return {
        "tasks_done": [],
        "context": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def load() -> dict:
    """Muat memori. Return state kosong kalau file hilang atau corrupt (dengan log)."""
    if not config.MEMORY_PATH.exists():
        return _empty_state()
    try:
        data = json.loads(config.MEMORY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("root must be JSON object")
        if "tasks_done" not in data:
            data["tasks_done"] = []
        if "context" not in data:
            data["context"] = ""
        return data
    except (json.JSONDecodeError, ValueError) as e:
        warn("memory corrupt, resetting", reason=str(e))
        return _empty_state()


def save(state: dict) -> None:
    """Atomic write: tulis ke .tmp lalu os.replace. Cap history supaya tidak tumbuh."""
    state["tasks_done"] = state["tasks_done"][-config.MEMORY_MAX_TASKS:]
    state["context"] = (state.get("context") or "")[-config.MEMORY_MAX_CONTEXT_CHARS:]
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    tmp = config.MEMORY_PATH.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(tmp, config.MEMORY_PATH)
    info("memory saved", tasks=len(state["tasks_done"]))


def append_task(state: dict, task: str, result: str) -> None:
    """Tambah entry task ke state (belum save)."""
    state["tasks_done"].append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "task": task,
        "result": result[:500],
    })
    state["context"] = (
        f"[{datetime.now(timezone.utc).isoformat()}] {task}: {result[:200]}"
    )

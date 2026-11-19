"""Structured JSON logging. Satu event = satu baris JSON ke stdout."""
import json
import sys
from datetime import datetime, timezone


def log(level: str, msg: str, **fields) -> None:
    """Emit satu baris JSON. Flush supaya realtime di CI log."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "msg": msg,
    }
    entry.update(fields)
    sys.stdout.write(json.dumps(entry, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def info(msg: str, **f) -> None:
    log("INFO", msg, **f)


def warn(msg: str, **f) -> None:
    log("WARN", msg, **f)


def error(msg: str, **f) -> None:
    log("ERROR", msg, **f)

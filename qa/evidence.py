"""Per-test evidence folder: reports/artifacts/<test id>/ - screenshots and JSON a test wants to keep."""

from __future__ import annotations

import json
import re
from pathlib import Path

from qa.config import ROOT

ARTIFACTS = ROOT / "reports" / "artifacts"
_SECRET_KEYS = re.compile(r"pass(word)?|token|secret|authorization|cookie", re.I)


def folder_for(nodeid: str) -> Path:
    path = ARTIFACTS / re.sub(r"[^\w.-]+", "_", nodeid).strip("_")
    path.mkdir(parents=True, exist_ok=True)
    return path


def mask(data):
    """A copy with password / token values masked - evidence is committed and shared, secrets never are."""
    if isinstance(data, dict):
        return {k: "***" if _SECRET_KEYS.search(str(k)) else mask(v) for k, v in data.items()}
    if isinstance(data, list):
        return [mask(v) for v in data]
    return data


class Evidence:
    def __init__(self, nodeid: str):
        self.dir = folder_for(nodeid)
        self.files: list[Path] = []

    def path(self, label: str, suffix: str = ".png") -> Path:
        name = re.sub(r"[^\w.-]+", "_", label)
        path = self.dir / f"{name}{suffix}"
        n = 2
        while path.exists():
            path = self.dir / f"{name}_{n:02d}{suffix}"
            n += 1
        self.files.append(path)
        return path

    def app(self, device, label: str) -> Path:
        return device.screenshot(self.path(label))

    def json(self, label: str, data) -> Path:
        path = self.path(label, ".json")
        path.write_text(json.dumps(mask(data), indent=1, default=str), encoding="utf-8")
        return path

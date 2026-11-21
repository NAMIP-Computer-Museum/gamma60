"""Access to the data tables in ``data/*.yaml``.

Every uncertain value lives in these tables, never in the code (CLAUDE.md rule 2). An
uncertain value is written ``{value: ..., status: hypothesis, unknown: U-xx}``; ``resolve``
returns the bare value, ``hypotheses`` lists them for validation.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

#: Sections of directives.yaml that hold cut and directive tables.
ELEMENT_KINDS = (
    "arithmetic",
    "logical",
    "transcoder",
    "comparator",
    "drum",
    "card_reader",
    "card_reader_punch",
    "printer",
    "uniselector",
    "paper_tape_reader",
    "paper_tape_punch",
    "desk",
)

_UNKNOWN_ID = re.compile(r"^U-\d{2}$")


@cache
def load(name: str) -> dict[str, Any]:
    """Load ``data/<name>.yaml`` (``name`` may contain a sub-directory, e.g. ``configs/max``)."""
    path = DATA_DIR / f"{name}.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_hypothesis(node: Any) -> bool:
    return isinstance(node, dict) and node.get("status") == "hypothesis"


def resolve(node: Any) -> Any:
    """Return the value of a node, unwrapping ``{value, status: hypothesis, unknown}``."""
    if isinstance(node, dict) and "value" in node and "status" in node:
        return node["value"]
    return node


def hypotheses(node: Any, path: str = "") -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield ``(path, node)`` for every node marked ``status: hypothesis``."""
    if isinstance(node, dict):
        if is_hypothesis(node):
            yield path, node
        for key, child in node.items():
            yield from hypotheses(child, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for i, child in enumerate(node):
            yield from hypotheses(child, f"{path}[{i}]")


def unknown_ids(node: Any) -> Iterator[str]:
    """Yield every ``unknown:`` reference found in a tree."""
    if isinstance(node, dict):
        if "unknown" in node:
            yield node["unknown"]
        for child in node.values():
            yield from unknown_ids(child)
    elif isinstance(node, list):
        for child in node:
            yield from unknown_ids(child)


def is_unknown_id(text: Any) -> bool:
    return isinstance(text, str) and bool(_UNKNOWN_ID.match(text))


# --- machine profiles -------------------------------------------------------------------


@dataclass(frozen=True)
class Profile:
    name: str
    memory_cycle_us: int
    check_key: str
    join_count_in: str
    memory_blocks_min: int
    memory_blocks_max: int
    mic_entries: int
    times_us: dict[str, int] = field(default_factory=dict)


def profile_names() -> list[str]:
    return list(load("profiles")["profiles"])


def get_profile(name: str | None = None) -> Profile:
    table = load("profiles")
    name = name or table["default"]
    p = table["profiles"][name]
    return Profile(
        name=name,
        memory_cycle_us=resolve(p["memory_cycle_us"]),
        check_key=resolve(p["check_key"]),
        join_count_in=resolve(p["join_count_in"]),
        memory_blocks_min=p["memory_blocks"]["min"],
        memory_blocks_max=p["memory_blocks"]["max"],
        mic_entries=resolve(p["mic"])["entries"],
        times_us=dict(p["times_us"]),
    )


# --- installation configurations ---------------------------------------------------------


@dataclass(frozen=True)
class Config:
    name: str
    memory_blocks: int
    elements: dict[str, int]
    classes: dict[str, int]
    behavior: dict[str, Any]


def config_names() -> list[str]:
    return sorted(p.stem for p in (DATA_DIR / "configs").glob("*.yaml"))


def get_config(name: str) -> Config:
    """Load a configuration, merging class and behaviour overrides onto the defaults."""
    cfg = load(f"configs/{name}")
    classes = {k: resolve(v) for k, v in load("topology")["classes"].items()}
    classes.update({k: resolve(v) for k, v in (cfg.get("classes") or {}).items()})
    behavior = {k: resolve(v) for k, v in load("behavior").items()}
    behavior.update({k: resolve(v) for k, v in (cfg.get("behavior") or {}).items()})
    return Config(
        name=cfg["name"],
        memory_blocks=resolve(cfg["memory_blocks"]),
        elements={k: resolve(v) for k, v in cfg["elements"].items()},
        classes=classes,
        behavior=behavior,
    )


# --- code B languages ---------------------------------------------------------------------


def languages() -> list[str]:
    table = load("directives")["languages"]
    return [k for k in table if k != "default"]


def default_language() -> str:
    return load("directives")["languages"]["default"]


def spelling(mnemonic: dict[str, Any], language: str) -> str | None:
    """Spelling of a ``mnemonic: {fr, en}`` field in a language, or None if not recorded."""
    value = mnemonic.get(language)
    return None if value is None else str(resolve(value))


def _index(entries: dict[str, Any], language: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for ident, entry in entries.items():
        if isinstance(entry, dict) and "mnemonic" in entry:
            word = spelling(entry["mnemonic"], language)
            if word is not None:
                out[word] = ident
    return out


def cut_index(language: str) -> dict[str, str]:
    """Mnemonic → cut identifier (``arithmetic``, ``fork``…)."""
    return _index(load("directives")["cuts"], language)


def address_index(language: str) -> dict[str, str]:
    return _index(load("directives")["address_instructions"], language)


def central_index(language: str) -> dict[str, str]:
    return _index(load("directives")["central_directives"], language)


def element_index(kind: str, language: str) -> dict[str, str]:
    """Mnemonic → directive identifier for one element kind (empty if it has none)."""
    element = load("directives")["elements"].get(kind) or {}
    return _index(element.get("directives") or {}, language)

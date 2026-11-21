"""data/registers.yaml: structure, consistency with directives.yaml, configs and MACHINE.md."""

from __future__ import annotations

from pathlib import Path

import pytest

from gamma60 import data

ROOT = Path(__file__).resolve().parents[1]
REGS = data.load("registers")
REGISTERS = REGS["registers"]
ELEMENT_KINDS = set(data.load("topology")["classes"])  # includes desk (U-27, U-29)
OWNERS = {"central_unit", "program_distributor", "every_element"} | ELEMENT_KINDS
LOCATIONS = {"central_unit", "map", "maq", "central_memory", "element"}


def by_id(ident: str) -> dict:
    return next(r for r in REGISTERS if r["id"] == ident)


def test_ids_are_unique():
    ids = [r["id"] for r in REGISTERS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("reg", REGISTERS, ids=lambda r: r["id"])
def test_register_fields(reg):
    assert reg["owner"] in OWNERS
    assert reg["location"] in LOCATIONS
    assert set(reg["name"]) == {"en", "fr"}
    assert set(reg["long"]) == {"en", "fr"} and all(reg["long"].values())
    assert set(reg["display"]) == {"en", "fr"}
    assert isinstance(data.resolve(reg["bits"]), int) and data.resolve(reg["bits"]) > 0
    assert isinstance(reg.get("count", 1), int) and reg.get("count", 1) >= 1
    assert reg["role"] and reg["source"]


def test_every_element_kind_has_a_rac_count():
    assert set(REGS["rac_per_element"]) == ELEMENT_KINDS


def test_rac_counts_match_directives():
    elements = data.load("directives")["elements"]
    for kind, element in elements.items():
        cars = element.get("cars")
        if cars is None:
            continue
        expected = len(cars) if isinstance(cars, dict) else cars
        assert data.resolve(REGS["rac_per_element"][kind]) == expected, kind


def test_matrix_sizes_and_widths():
    # 128 RAI and 128 RAC; 15-bit address + key by 3 (+ busy indicator for RAI) [ONDE §2.2.1]
    assert by_id("rai")["count"] == by_id("rac")["count"] == 128
    assert by_id("rai")["bits"] == 15 + 2 + 2 + 2 and by_id("rac")["bits"] == 15 + 2 + 2
    assert by_id("z")["bits"] == 24 + 3 + 4  # catena, key, selection check [ONDE §2.2.2.3]


@pytest.mark.parametrize("name", ["max", "rtt_1963"])
def test_configurations_fit_in_the_matrices(name):
    """Every configured element needs one RAI and its RACs out of the 128 of each matrix."""
    elements = data.load(f"configs/{name}")["elements"]
    racs = REGS["rac_per_element"]
    count = {k: data.resolve(v) for k, v in elements.items() if k in ELEMENT_KINDS}
    assert sum(count.values()) <= by_id("rai")["count"]
    needed = sum(n * data.resolve(racs[k]) for k, n in count.items())
    assert needed <= by_id("rac")["count"]


def labels(reg: dict, language: str) -> list[str]:
    """Displayed labels, one per copy (``pdc`` → ``pdc1``, ``pdc2``)."""
    label = reg["display"][language]
    count = 1 if reg["location"] in ("map", "maq") else reg.get("count", 1)  # matrices: per element
    if isinstance(label, list):
        assert len(label) == count, reg["id"]
        return label
    return [label] if count == 1 else [f"{label}{i}" for i in range(1, count + 1)]


def base_labels(reg: dict, language: str) -> list[str]:
    label = reg["display"][language]
    return label if isinstance(label, list) else [label]


@pytest.mark.parametrize("language", ["en", "fr"])
@pytest.mark.parametrize("reg", REGISTERS, ids=lambda r: r["id"])
def test_display_case_convention(reg, language):
    """UPPER CASE = name attested in that language; lower case = emulator proposal."""
    attested = set((reg["name"][language] or "").split(", ")) - {""}
    label = reg["display"][language]
    for one in label if isinstance(label, list) else [label]:
        assert 1 <= len(one) <= 6, one
        if not one.islower():
            assert one.isupper() and one in attested, (
                f"{reg['id']}: {one} not attested in {language}"
            )


@pytest.mark.parametrize("language", ["en", "fr"])
def test_display_labels_unique_per_unit(language):
    # registers held in central memory (B / C, resume datum) are shown apart, with the memory
    regs_ = [r for r in REGISTERS if r["location"] != "central_memory"]
    in_memory = [r for r in REGISTERS if r["location"] == "central_memory"]
    central = [r for r in regs_ if r["owner"] in ("central_unit", "program_distributor")]
    common = [r for r in regs_ if r["owner"] == "every_element"]
    units = [central, in_memory] + [
        common + [r for r in regs_ if r["owner"] == kind] for kind in sorted(ELEMENT_KINDS)
    ]
    for regs in units:
        shown = [label for r in regs for label in labels(r, language)]
        assert len(shown) == len(set(shown)), shown


def test_machine_md_lists_every_register():
    text = (ROOT / "docs" / "MACHINE.md").read_text(encoding="utf-8")
    section = text[text.index("### 5.1 Registres") : text.index("### 5.2")]
    for reg in REGISTERS:
        names = {reg["name"]["fr"], reg["name"]["en"], reg["long"]["fr"]} - {None}
        assert any(n.split(" (")[0].lower() in section.lower() for n in names), reg["id"]
        for language in ("en", "fr"):
            for label in base_labels(reg, language):
                assert f"`{label}`" in section, (reg["id"], label)


def test_wiki_lists_every_register():
    text = (ROOT / "wiki" / "REGISTERS.md").read_text(encoding="utf-8")
    for reg in REGISTERS:
        assert f"`{reg['id']}`" in text, reg["id"]
        for label in base_labels(reg, "en"):
            assert f"`{label}`" in text, (reg["id"], label)

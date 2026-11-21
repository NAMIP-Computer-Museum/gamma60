"""Validation of the data tables (milestone J0)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from gamma60 import data

ROOT = Path(__file__).resolve().parents[1]
YAML_FILES = sorted(
    p.relative_to(data.DATA_DIR).with_suffix("").as_posix() for p in data.DATA_DIR.rglob("*.yaml")
)


def known_unknowns() -> set[str]:
    text = (ROOT / "docs" / "UNKNOWNS.md").read_text(encoding="utf-8")
    return set(re.findall(r"^\| (U-\d{2}) \|", text, re.MULTILINE))


@pytest.mark.parametrize("name", YAML_FILES)
def test_yaml_loads(name):
    assert isinstance(data.load(name), dict)


@pytest.mark.parametrize("name", YAML_FILES)
def test_every_hypothesis_points_to_a_known_unknown(name):
    unknowns = known_unknowns()
    tree = data.load(name)
    for path, node in data.hypotheses(tree):
        assert data.is_unknown_id(node.get("unknown")), f"{name}:{path} has no unknown: U-xx"
    for ref in data.unknown_ids(tree):
        assert ref in unknowns, f"{name}: {ref} missing from docs/UNKNOWNS.md"


@pytest.mark.parametrize("name", ["COURS", "B61"])
def test_profiles_complete(name):
    p = data.get_profile(name)
    assert p.memory_cycle_us in (10, 11)
    assert p.check_key in ("mod7_24bits", "parity9_mod3_15")
    assert p.join_count_in in ("blank_catena_x", "cut_cc")
    assert 1 <= p.memory_blocks_min <= p.memory_blocks_max == 8
    assert p.mic_entries in (128, 256)
    assert {"arit_add", "arit_mul", "arit_div"} <= set(p.times_us)


def test_default_profile_is_b61():
    assert data.get_profile().name == "B61"


def test_languages():
    assert set(data.languages()) == {"fr", "en"}
    assert data.default_language() == "en"


def _mnemonic_tables():
    d = data.load("directives")
    yield "cuts", d["cuts"]
    yield "address_instructions", d["address_instructions"]
    yield "central_directives", d["central_directives"]
    for kind, element in d["elements"].items():
        yield f"elements.{kind}", element.get("directives") or {}


@pytest.mark.parametrize("language", ["fr", "en"])
def test_no_duplicate_mnemonic_within_a_table(language):
    for table_name, table in _mnemonic_tables():
        seen: dict[str, str] = {}
        for ident, entry in table.items():
            if not (isinstance(entry, dict) and "mnemonic" in entry):
                continue
            word = data.spelling(entry["mnemonic"], language)
            if word is None:
                continue
            assert word not in seen, f"{table_name}: {word} used by {seen[word]} and {ident}"
            seen[word] = ident


def test_every_instruction_has_an_english_mnemonic():
    for table_name, table in _mnemonic_tables():
        for ident, entry in table.items():
            if isinstance(entry, dict) and "mnemonic" in entry:
                assert data.spelling(entry["mnemonic"], "en"), f"{table_name}.{ident}"


def test_encoding_matches_directives():
    enc = data.load("encoding")["synthetic_subcodes"]
    d = data.load("directives")
    assert set(enc["central_directive"]) == set(d["central_directives"])
    assert set(enc["address_op"]) == set(d["address_instructions"])
    assert len(set(enc["central_directive"].values())) == len(enc["central_directive"])
    assert max(enc["central_directive"].values()) < 32  # 5-bit field, bits 22-18


def test_encoding_prefixes_are_prefix_free():
    tks = [t["tk"] for t in data.load("encoding")["types"].values()]
    for a in tks:
        for b in tks:
            assert a == b or not b.startswith(a), f"{a} is a prefix of {b}"


def test_charset():
    chars = data.load("charset")["characters"]
    codes = [c["code"] for c in chars]
    assert len(codes) == len(set(codes)) == 64
    for c in chars:
        assert re.fullmatch(r"[01]{6}", c["code"]) and int(c["code"], 2) == c["value"]


def test_topology_covers_every_element_kind():
    topo = data.load("topology")
    classes = {k: data.resolve(v) for k, v in topo["classes"].items()}
    assert set(classes) == set(data.ELEMENT_KINDS)
    circuit_classes = {c for circuit in data.resolve(topo["circuits"]) for c in circuit["classes"]}
    assert set(classes.values()) <= circuit_classes


@pytest.mark.parametrize("name", data.config_names())
def test_configs(name):
    cfg = data.get_config(name)
    profile_limits = [data.get_profile(p) for p in data.profile_names()]
    assert any(
        p.memory_blocks_min <= cfg.memory_blocks <= p.memory_blocks_max for p in profile_limits
    )
    kinds = set(data.ELEMENT_KINDS) | {"tape_units"}
    assert set(cfg.elements) <= kinds, set(cfg.elements) - kinds
    for kind in cfg.elements:
        if kind != "tape_units":
            assert kind in cfg.classes, f"{name}: no class for {kind}"
    assert set(data.load("behavior")) <= set(cfg.behavior)

"""Every mnemonic of the reference programs is known in the language they declare (J0).

This is a lexical check only: the programs are executed from milestone J1 on.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from gamma60 import data

PROGRAMS = sorted((Path(__file__).parent / "programs").glob("*.g60b"))
PSEUDO = {"VIERGE", "NUM", "ZONE"}  # assembler pseudo-instructions (docs/TOOLCHAIN.md)
LINE = re.compile(r"^\s*(?:\d{3}\s+)?(?:\w+:\s*)?(?P<to>\S+)?")


def declared_language(path: Path) -> str:
    first = path.read_text(encoding="utf-8").splitlines()[0]
    m = re.match(r";\s*langue:\s*(\w+)", first)
    return m.group(1) if m else data.default_language()


@pytest.mark.parametrize("path", PROGRAMS, ids=lambda p: p.name)
def test_program_mnemonics_known(path):
    lang = declared_language(path)
    cuts = data.cut_index(lang)
    general = data.address_index(lang) | data.central_index(lang)
    element = None  # element named by the last cut
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split(";", 1)[0]
        to = LINE.match(line).group("to") if line.strip() else None
        if to is None or to in PSEUDO:
            continue
        if re.fullmatch(r"\d{2}", to):
            assert to in ("00", "31") or 1 <= int(to) <= 24, f"{path.name}:{number} branch {to}"
            continue
        if to in cuts:
            element = cuts[to]
            continue
        if to in general:
            continue
        assert element is not None, f"{path.name}:{number} {to} before any cut"
        assert to in data.element_index(element, lang), (
            f"{path.name}:{number} {to} unknown for {element} in language {lang}"
        )

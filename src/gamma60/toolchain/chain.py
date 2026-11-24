"""The whole chain behind ``run`` (J6): code B → subprogram → code C → code D2 → U.T. → machine.

A ``.g60b`` program run directly is a single article, implanted at its origin, with nothing
to distribute: transposition, assembly and distribution must give back exactly the code A of
the plain assembly (checked by the tests on every program of ``tests/programs/``). The machine
then runs the U.T.; the debug tables come from the source when there is one, otherwise from the
U.T. itself (labels ``ARTICLE.LABEL`` when there are several articles).
"""

from __future__ import annotations

import re
from pathlib import Path

from gamma60 import codeb, data
from gamma60.toolchain.assembler import Image, Listing, assemble
from gamma60.toolchain.distributor import ProcessingUnit, distribute
from gamma60.toolchain.linker import Linker
from gamma60.toolchain.subprogram import LinkError, from_image


def processing_unit(
    program: codeb.Program, profile: data.Profile | None = None, name: str = "program"
) -> tuple[ProcessingUnit, Image]:
    """U.T. of a complete code B program (one article, no unknown), and its plain image."""
    image = assemble(program, profile)
    sp = from_image(image, name)
    if sp.unknowns:
        names = ", ".join(f"?{n}" for n in sp.unknowns)
        raise LinkError(f"unknowns {names} have no value: link with code C / code D (J6)")
    sheet = {"articles": {1: {"sp": sp}}, "distr": {"implantation": {1: program.origin}}}
    return distribute(Linker(sheet, Path()).link(), {}, name), image


def machine_image(ut: ProcessingUnit, source: Image | None = None) -> Image:
    """What the machine loads: the words of the U.T.; debug tables from ``source`` if given."""
    if source is not None:
        program, listing = source.program, source.listing
    else:
        program, listing = program_from_ut(ut)
    return Image(
        program,
        words=dict(ut.words),
        listing=listing,
        elements=dict(ut.elements),
        joins=dict(ut.joins),
        entry=ut.entry,
    )


def program_from_ut(ut: ProcessingUnit) -> tuple[codeb.Program, list[Listing]]:
    """Debug view of a U.T. without its sources: lines and labels kept by the chain."""
    single = len(ut.layout) == 1
    labels = {
        (lab.split(".", 1)[1] if single and "." in lab else lab): a for lab, a in ut.labels.items()
    }
    by_address = {a: lab for lab, a in labels.items()}
    lines: list[codeb.Line] = []
    for a in sorted(ut.lines):
        _, number, text = ut.lines[a]
        tokens = text.split(";")[0].split()
        while tokens and (re.fullmatch(r"\d{3}", tokens[0]) or tokens[0].endswith(":")):
            tokens.pop(0)
        if not tokens:
            continue
        to, args = tokens[0], tokens[1:]
        size = 2 if to == "NUM" else int(args[0]) if to == "ZONE" and args else 1
        lines.append(codeb.Line(number, a, by_address.get(a), to, args, size, text))
    origin = min(ut.words, default=0)
    end = max(ut.words, default=-1) + 1
    program = codeb.Program(lines, labels, ut.language, ut.profile, end, origin)
    at = {ln.address: ln for ln in lines}
    listing = [Listing(a, v, at.get(a)) for a, v in sorted(ut.words.items())]
    return program, listing

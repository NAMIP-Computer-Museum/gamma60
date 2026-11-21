"""Sequential interpreter (J1): cuts, address instructions, branches, SIMU / join / STOP,
pseudo-instructions, both languages and both profiles, errors, command line."""

from fractions import Fraction
from pathlib import Path

import pytest

from gamma60 import data, seq
from gamma60.__main__ import main
from gamma60.catena import bits

PROGRAMS = Path(__file__).parent / "programs"
FORKJOIN = PROGRAMS / "forkjoin_tumlin.g60b"


def en(body: str) -> str:
    return "; langue: en\n" + body


def fr(body: str) -> str:
    return "; langue: fr\n" + body


def to_french(text: str) -> str:
    """forkjoin_tumlin in language fr: only the address mnemonic differs (L -> G)."""
    out = []
    for line in text.splitlines():
        if line.startswith("; langue:"):
            out.append("; langue: fr")
        else:
            out.append(line.replace("        L     ", "        G     "))
    return "\n".join(out)


# --- acceptance: forkjoin_tumlin --------------------------------------------------------


@pytest.mark.parametrize("profile", ["B61", "COURS"])
@pytest.mark.parametrize("language", ["en", "fr"])
def test_forkjoin_tumlin(profile, language):
    text = FORKJOIN.read_text(encoding="utf-8")
    if language == "fr":
        text = to_french(text)
    result = seq.run_text(text, profile)
    assert result.status == "halted"
    assert result.number("A").value == 12
    assert result.number("D").value == 11
    assert result.number("F").value == 132


def test_named_branch_runs_first_and_join_counter_is_reset():
    result = seq.run_file(FORKJOIN)
    texts = [t for _, _, _, t in result.trace]
    assert texts.index("ADD N - 0 1 2") < texts.index("MUL N - 0 1 2")  # I2 before I1
    blank = result.program.labels["I3"] + 1
    assert bits(result.memory.read(blank), 19, 18) == 0  # counter back to 0 after the join


def test_deterministic_trace():
    assert seq.run_file(FORKJOIN).trace == seq.run_file(FORKJOIN).trace


# --- every ARIT and LOGI mnemonic through code B, in both languages ---------------------


def _program_for(kind: str, ident: str, mnemonic: str, language: str) -> str:
    load = "L" if language == "en" else "G"
    if kind == "arithmetic":
        body = {
            "multiply_pow10": f"{mnemonic}    2 0 - 2",
            "divide_pow10": f"{mnemonic}    2 0 - 2",
            "reverse_sign": f"{mnemonic}    - 0 - 2",
            "absolute_value": f"{mnemonic}    - 0 - 2",
            "transfer": f"{mnemonic} N  - 0 - 2",
            "compare_absolute": f"{mnemonic}    - 0 1 -",
            "compare_algebraic": f"{mnemonic}    - 0 1 -",
            "round_off": f"{mnemonic}    - - - 2",
        }.get(ident, f"{mnemonic} N  - 0 1 2")
        return (
            f"; langue: {language}\n        ARIT\n        VIERGE\n"
            f"        {load} 0 X\n        {load} 1 Y\n        {load} 2 Z\n"
            f"        {body}\n        STOP\nX: NUM +7\nY: NUM +2\nZ: NUM +0\n"
        )
    return (
        f"; langue: {language}\n        LOGI\n        VIERGE\n        {load} 0 X\n"
        f"        {load} 1 Y\n"
        f"        {_logi_name('transfer_shift_to_K', language)} 0 0\n"
        f"        {_logi_name('transfer_shift_to_L', language)} 0 1\n"
        f"        {mnemonic} {16 if ident == 'divide' else 4} "
        f"{'L' if 'transfer_shift' not in ident else '0'}\n"
        f"        STOP\nX: NUM +7\nY: NUM +2\n"  # any non-zero catenae
    )


def _logi_name(ident: str, language: str) -> str:
    return {v: k for k, v in data.element_index("logical", language).items()}[ident]


def _cases():
    for kind in ("arithmetic", "logical"):
        for language in ("en", "fr"):
            for mnemonic, ident in data.element_index(kind, language).items():
                yield kind, ident, mnemonic, language


@pytest.mark.parametrize(("kind", "ident", "mnemonic", "language"), list(_cases()))
def test_every_directive_runs_from_code_b(kind, ident, mnemonic, language):
    result = seq.run_text(_program_for(kind, ident, mnemonic, language))
    assert result.status == "halted", result.message


# --- address instructions -----------------------------------------------------------------


@pytest.mark.parametrize(("lang", "load", "place"), [("en", "L", "P"), ("fr", "G", "R")])
def test_load_place_add_subtract(lang, load, place):
    text = (
        f"; langue: {lang}\n        ARIT\n        VIERGE\n        {load} 0 100\n"
        "        A 0 5\n        S 0 2\n"
        f"        {place} 0 OUT\n        STOP\nOUT: ZONE 1\n"
    )
    result = seq.run_text(text)
    assert result.memory.read(result.program.labels["OUT"]) == 103


def test_address_functions_relative_working_memory_substitution():
    text = en(
        "        ARIT\n        VIERGE\n"
        "        L 0 3 R\n"  # relative line number (origin 0)
        "        P 0 OUT\n"
        "        L 1 0 M\n"  # working memory 0 = first address after the program
        "        P 1 OUT2\n"
        "        L 2 PTR S\n"  # substitution: X <- memory[PTR]
        "        P 2 OUT3\n"
        "        STOP\nOUT: ZONE 1\nOUT2: ZONE 1\nOUT3: ZONE 1\nPTR: ZONE 1\n"
    )
    program = seq.parse(text)
    interp = seq.Interpreter(program, data.get_profile())
    interp.memory.write(program.labels["PTR"], 1234)
    result = interp.run()
    assert result.memory.read(program.labels["OUT"]) == 3
    assert result.memory.read(program.labels["OUT2"]) == program.end
    assert result.memory.read(program.labels["OUT3"]) == 1234


def test_rac_progression_and_no_progression():
    text = en(
        "        ARIT\n        VIERGE\n        L 0 X\n        L 1 X\n        L 2 R\n"
        "        TRA N - Z - 2\n"  # Z: RAC 0 back to its initial value
        "        TRA N - 1 - 2\n"  # 1: RAC 1 progresses by 2
        "        P 0 OUT0\n        P 1 OUT1\n        P 2 OUT2\n        STOP\n"
        "X: NUM +5\nR: ZONE 4\nOUT0: ZONE 1\nOUT1: ZONE 1\nOUT2: ZONE 1\n"
    )
    result = seq.run_text(text)
    labels = result.program.labels
    assert result.memory.read(labels["OUT0"]) == labels["X"]
    assert result.memory.read(labels["OUT1"]) == labels["X"] + 2
    assert result.memory.read(labels["OUT2"]) == labels["R"] + 4


def test_double_length_store():
    text = en(
        "        ARIT\n        VIERGE\n        L 0 X\n        L 2 R\n"
        "        MUL ND - Z Z S\n        STOP\nX: NUM +9999999999\nR: ZONE 4\n"
    )
    result = seq.run_text(text)
    r = result.program.labels["R"]
    from gamma60.number import Number

    p = Number.from_catenae(result.memory.read(r), result.memory.read(r + 1))
    s = Number.from_catenae(result.memory.read(r + 2), result.memory.read(r + 3))
    assert p.value + s.value == Fraction(9_999_999_999) ** 2


# --- branches -------------------------------------------------------------------------------


def _branch_program(op: str, cond: str) -> str:
    return en(
        "        ARIT\n        VIERGE\n        L 0 A\n        L 1 B\n        L 2 R\n"
        f"        {op} N - 0 1 2\n        {cond}    TAKEN\n"
        "        L 3 1\n        P 3 FLAG\n        STOP\n"
        "TAKEN:  L 3 2\n        P 3 FLAG\n        STOP\n"
        "A: NUM +3\nB: NUM +5\nR: ZONE 2\nFLAG: ZONE 1\n"
    )


@pytest.mark.parametrize(
    ("op", "cond", "flag"),
    [
        ("SUB", "08", 2),  # 3 - 5 < 0: position 8 set, branch taken
        ("SUB", "09", 1),  # not > 0: not taken
        ("ADD", "09", 2),
        ("SUB", "31", 2),  # always
        ("SUB", "00", 1),  # never
    ],
)
def test_branches(op, cond, flag):
    result = seq.run_text(_branch_program(op, cond))
    assert result.memory.read(result.program.labels["FLAG"]) == flag


def test_blank_catena_executes_as_never_branch():
    result = seq.run_text(en("        ARIT\n        VIERGE\n        VIERGE\n        STOP\n"))
    assert result.status == "halted"


# --- LOGI through code B ------------------------------------------------------------------


def test_logi_program_stores_result():
    text = en(
        "        LOGI\n        VIERGE\n        L 0 X\n        L 1 Y\n        L 2 OUT\n"
        "        TSK 0 0\n        TSL 0 1\n        ADD 24 2\n        STOP\n"
        "X: ZONE 1\nY: ZONE 1\nOUT: ZONE 1\n"
    )
    program = seq.parse(text)
    interp = seq.Interpreter(program, data.get_profile())
    interp.memory.write(program.labels["X"], 40)
    interp.memory.write(program.labels["Y"], 2)
    result = interp.run()
    assert result.memory.read(program.labels["OUT"]) == 42


# --- join variants, incidents, errors -----------------------------------------------------


def test_join_count_in_blank_catena_cours_notation():
    text = fr(
        "        SIMU        B2   R\n        VIERGE\n"
        "        ARIT\n        VIERGE\n        31          J    R\n"
        "B2:     ARIT\n        VIERGE\n        31          J    R\n"
        "J:      ARIT\n        VIERGE 1\n        G 0 1\n        R 0 OUT\n        STOP\n"
        "OUT: ZONE 1\n"
    )
    result = seq.run_text(text, "COURS")
    assert result.memory.read(result.program.labels["OUT"]) == 1
    assert sum(1 for *_, t in result.trace if t == "STOP") == 1  # one arrival continues


def test_incident_stops_the_run():
    text = en(
        "        ARIT\n        VIERGE\n        L 0 A\n        L 1 Z\n        L 2 R\n"
        "        DIV N - 0 1 2\n        STOP\nA: NUM +1\nZ: NUM +0\nR: ZONE 2\n"
    )
    result = seq.run_text(text)
    assert result.status == "incident" and "division by zero" in result.message


@pytest.mark.parametrize(
    "body",
    [
        "        DRUM 1\n        VIERGE\n        STOP\n",  # element of a later milestone
        "        ARIT\n        VIERGE\n        TA 5\n        STOP\n",  # central directive (J3)
        "        PROT X\n        VIERGE\n        STOP\nX: ZONE 2\n",  # virtual element (J4)
    ],
)
def test_unsupported_in_j1(body):
    with pytest.raises(seq.Unsupported):
        seq.run_text(en(body))


@pytest.mark.parametrize(
    "body",
    [
        "        ARIT\n        STOP\n",  # cut without blank catena
        "        ADD N - 0 1 2\n        STOP\n",  # directive before any cut
        "        ARIT\n        VIERGE\n        XYZ\n        STOP\n",  # unknown mnemonic
        "        ARIT\n        VIERGE\n        ADD N 0 1 2\n        STOP\n",  # missing slot
        "        ARIT\n        VIERGE\n        ADD Q - 0 1 2\n        STOP\n",  # invalid C.C.
        "        ARIT\n        VIERGE\n        L 0 NOWHERE\n        STOP\n",  # unknown label
        "A:      ARIT\nA:      VIERGE\n",  # label defined twice
        "        ARIT\n        VIERGE\n        31 D\nD: NUM +1\n",  # execution reaches data
    ],
)
def test_program_errors(body):
    with pytest.raises(seq.ProgramError):
        seq.run_text(en(body))


def test_unknown_language():
    with pytest.raises(seq.ProgramError):
        seq.parse("; langue: de\n        STOP\n")


def test_infinite_loop_is_detected():
    with pytest.raises(seq.ProgramError):
        seq.run_text(en("LOOP:   31    LOOP\n"), max_steps=50)


def test_numbered_lines():
    text = fr("010     ARIT\n011     VIERGE\n012     G 0 7\n013     R 0 20\n014     STOP\n")
    result = seq.run_text(text)
    assert result.memory.read(20) == 7


# --- command line ---------------------------------------------------------------------------


def test_cli_run(capsys):
    assert main(["run", str(FORKJOIN), "--trace"]) == 0
    out = capsys.readouterr().out
    assert "status: halted" in out and "+43 1320|000000" in out

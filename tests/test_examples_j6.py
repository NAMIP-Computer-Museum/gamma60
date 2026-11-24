"""J6 step 6: the examples of tests/programs/chaine/<chain>/ through the whole chain.

- ``bande_continue``: bande_continue_task.g60b split into a library subprogram
  (lib/lecture_continue.g60b), a processing subprogram and three zones, linked by code C; the
  tape drive is given by code D2 (10, or 12 with bande_continue_d12.g60d.yaml);
- ``sommes``: the standard subprogram lib/somme.g60b implanted twice.
"""

from pathlib import Path

from gamma60 import code_a, data, machine
from gamma60.elements.tape import TapeDrive
from gamma60.toolchain import chain
from gamma60.toolchain.distributor import distribute, distribute_file
from gamma60.toolchain.linker import link

CHAINE = Path("tests/programs/chaine")
BANDE, SOMMES = CHAINE / "bande_continue", CHAINE / "sommes"
REEL = Path("tests/media/fichier_6_blocs.yaml")


def _run(ut, tapes=()):
    m = machine.Machine(chain.machine_image(ut), data.get_profile(ut.profile))
    for n in tapes:
        m.tape_drives[n] = TapeDrive.load(n, REEL)
    result = m.run()
    return m, result


def test_split_continuous_reading_same_result_as_the_monolithic_program():
    ut = distribute_file(BANDE / "bande_continue.g60d.yaml")
    m, result = _run(ut, [10])
    assert result.status == "halted"
    total, nbloc = (m.memory.read(ut.labels[f"TRAIT.{x}"]) for x in ("TOTAL", "NBLOC"))
    assert (total, nbloc) == (1_057_350, 6)
    mono = machine.build(Path("tests/programs/bande_continue_task.g60b").read_text("utf-8"))
    mono.tape_drives[10] = TapeDrive.load(10, REEL)
    mono.run()
    # one more instruction: the exit of the subprogram, 31 ?FIN, then the STOP of FIN_UT
    assert m.engine.now == mono.engine.now + 20
    logi = next(e for e in m.elements.values() if e.kind == "logical")
    assert len(logi.log) == 630


def test_tape_drive_given_by_the_distribution():
    ut10 = distribute_file(BANDE / "bande_continue.g60d.yaml")
    ut12 = distribute_file(BANDE / "bande_continue_d12.g60d.yaml")
    differ = [a for a in ut10.words if ut10.words[a] != ut12.words[a]]
    assert len(differ) == 1  # LAV ?DEROUL, the only blank left to the distribution
    assert code_a.decode(ut12.words[differ[0]]).characteristic & 0x7FFF == 12
    m, result = _run(ut12, [12])
    assert result.status == "halted"
    assert m.memory.read(ut12.labels["TRAIT.TOTAL"]) == 1_057_350


def test_standard_subprogram_implanted_twice():
    prog = link(SOMMES / "sommes.g60c.yaml")
    layout = {name: (base, size) for _, name, base, size in prog.layout}
    (a, size), (b, size_b) = layout["SOMME_A"], layout["SOMME_B"]
    assert size == size_b and a != b
    # same code A, except the relocated addresses and the filled blanks
    same = sum(prog.words[a + k] == prog.words[b + k] for k in range(size))
    assert 0 < same < size
    ut = distribute(prog, {}, "sommes")
    m, result = _run(ut)
    assert result.status == "halted"
    assert m.memory.read(ut.labels["DON.RES1"]) == 10
    assert m.memory.read(ut.labels["DON.RES2"]) == 60

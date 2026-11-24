"""Command line.

- ``python -m gamma60 run <program.g60b | unit.ut.json> [--profile B61|COURS] [--trace[=regs|dd]] [--step]
  [--names en|fr] [--mode faithful|diagnostic] [--seq]``: run a code B program on the machine
  (J3: assembler, Program Distributor, Data Distributor, ARIT, LOGI); ``--seq``: sequential
  interpreter of J1 (needed for SIMU and joins until J4);
  ``--gantt[=elem|seq]`` (ASCII timeline by element or by sequence, ``--gantt-scale``,
  ``--gantt-from``, ``--gantt-to``), ``--dump <zone>``;
- ``python -m gamma60 asm <program.g60b>``: assembly listing (code A beside code B);
- ``python -m gamma60 transpose <subprogram.g60b> [-o file]``: assemblable subprogram
  (``.g60a.json``: code A with blanks, unknowns, repères; J6);
- ``python -m gamma60 assemble <sheet.g60c.yaml> [-o file] [--listing]``: assembly driven by a
  code C sheet (``.g60pa.json``: code A in place, blanks left to the distribution; J6);
- ``python -m gamma60 distribute <values.g60d.yaml | sheet.g60c.yaml | prog.g60pa.json> [-o]``:
  distribution of the symbols (code D2) → processing unit (``.ut.json``; J6);
- ``python -m gamma60 disasm <file.g60b | .ut.json | .g60pa.json | .g60a.json> [--lang en|fr]``:
  code A → code B (J6);
- ``python -m gamma60 dd <scenario.yaml>``: Data Distributor scenario (J2).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gamma60 import codeb, data, debug, gantt, machine, seq, synthetic
from gamma60.elements.tape import TapeDrive
from gamma60.number import NotANumber
from gamma60.program_distributor import MachineUnsupported
from gamma60.toolchain import chain, disassembler, distributor, linker, subprogram
from gamma60.toolchain.assembler import AsmUnsupported, assemble, listing_lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gamma60")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run a code B program")
    run.add_argument("program")
    run.add_argument("--profile", choices=["B61", "COURS"])
    run.add_argument(
        "--trace",
        nargs="?",
        const="steps",
        choices=["steps", "regs", "dd"],
        help="each instruction (steps), with the registers it changed (regs), or each DD cycle",
    )
    run.add_argument("--step", action="store_true", help="interactive step-by-step debugger")
    run.add_argument(
        "--break",
        dest="breaks",
        action="append",
        default=[],
        metavar="LABEL",
        help="run until LABEL[+k] (or ARTICLE.LABEL, or an address), then step (repeatable)",
    )
    run.add_argument(
        "--names", choices=["en", "fr"], help="language of register names (default: the program)"
    )
    run.add_argument("--mode", choices=["faithful", "diagnostic"], default="faithful")
    run.add_argument("--seq", action="store_true", help="sequential interpreter of J1")
    run.add_argument(
        "--gantt",
        nargs="?",
        const="elem",
        choices=["elem", "seq"],
        help="ASCII timeline at the end of the run: by element (elem) or by sequence (seq)",
    )
    run.add_argument("--gantt-scale", type=int, metavar="US", help="microseconds per character")
    run.add_argument("--gantt-from", type=int, default=0, metavar="US", help="window start")
    run.add_argument("--gantt-to", type=int, metavar="US", help="window end")
    run.add_argument("--config", default="max", help="machine configuration (data/configs/)")
    run.add_argument(
        "--tape", action="append", default=[], metavar="N=FILE", help="mount a reel on drive N"
    )
    run.add_argument(
        "--drum", action="append", default=[], metavar="K=FILE", help="contents of drum K"
    )
    run.add_argument(
        "--dump-tape",
        action="append",
        type=int,
        default=[],
        metavar="N",
        help="blocks of drive N at the end of the run",
    )
    run.add_argument(
        "--dump",
        nargs="+",
        action="append",
        metavar="ZONE",
        help="memory zone shown at the end of the run: <address|label> [n], or all (repeatable)",
    )
    asm = sub.add_parser("asm", help="assemble a code B program and print the listing")
    asm.add_argument("program")
    asm.add_argument("--profile", choices=["B61", "COURS"])
    tr = sub.add_parser("transpose", help="code B → assemblable subprogram (.g60a.json)")
    tr.add_argument("program")
    tr.add_argument("--profile", choices=["B61", "COURS"])
    tr.add_argument("-o", "--output", help="output file (default: beside the source)")
    asc = sub.add_parser("assemble", help="code C sheet → assembled program (.g60pa.json)")
    asc.add_argument("sheet")
    asc.add_argument("-o", "--output", help="output file (default: beside the sheet)")
    asc.add_argument("--listing", action="store_true", help="print the assembled code A")
    dis = sub.add_parser("distribute", help="code D2 values → processing unit (.ut.json)")
    dis.add_argument("source", help=".g60d.yaml (code D2), or .g60c.yaml / .g60pa.json")
    dis.add_argument("-o", "--output", help="output file (default: beside the source)")
    dis_a = sub.add_parser("disasm", help="code A → code B (a U.T. or any file of the chain)")
    dis_a.add_argument("source", help=".g60b, .ut.json, .g60pa.json or .g60a.json")
    dis_a.add_argument("--lang", choices=["en", "fr"], help="mnemonics (default: the file's)")
    dis_a.add_argument(
        "--raw", action="store_true", help="only the catenae: ignore labels, sources and tables"
    )
    dd = sub.add_parser("dd", help="run a Data Distributor scenario with synthetic elements (J2)")
    dd.add_argument("scenario")
    dd.add_argument("--profile", choices=["B61", "COURS"])
    dd.add_argument("--trace", action="store_true", help="one line per memory cycle")
    dd.add_argument("--names", choices=["en", "fr"], default="en")
    dd.add_argument("--mode", choices=["faithful", "diagnostic"], default="faithful")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    try:
        return dispatch(args)
    except codeb.ProgramError as exc:
        print(f"error: {exc}")
        return 2


def dispatch(args) -> int:
    if args.command == "dd":
        return run_dd(args)
    if args.command == "assemble":
        return run_assemble(args)
    if args.command == "distribute":
        return run_distribute(args)
    if args.command == "disasm":
        return run_disasm(args)
    if args.command == "run" and args.program.endswith(".json"):
        return run_ut(args)
    program = codeb.parse(Path(args.program).read_text(encoding="utf-8"))
    profile = data.get_profile(args.profile or program.profile)
    if args.command == "asm":
        try:
            image = assemble(program, profile)
        except AsmUnsupported as exc:
            print(f"not assembled yet: {exc}")
            return 2
        for line in listing_lines(image):
            print(line)
        return 0
    if args.command == "transpose":
        return run_transpose(args, program, profile)
    names = debug.Names(args.names or program.language)
    try:
        zones = [debug.dump_zone(program, spec) for spec in args.dump or []]
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    args.zones = zones
    if args.seq:
        if args.gantt:
            print("error: --gantt needs the machine (not --seq)")
            return 2
        return run_seq(args, program, profile, names)
    return run_machine(args, program, profile, names)


def run_ut(args) -> int:
    """``run x.ut.json``: a processing unit produced by ``distribute`` (J6)."""
    if args.seq:
        print("error: --seq needs a code B source, not a U.T.")
        return 2
    ut = distributor.ProcessingUnit.load(args.program)
    image = chain.machine_image(ut)
    profile = data.get_profile(args.profile or ut.profile)
    names = debug.Names(args.names or ut.language)
    try:
        args.zones = [debug.dump_zone(image.program, spec) for spec in args.dump or []]
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    return run_machine(args, image.program, profile, names, image)


def _observer(args, names: debug.Names, machine_run: bool, program=None):
    if args.step or args.breaks:
        print(names.say("help"))
        stepper = debug.Stepper(names)
        if args.breaks:  # run freely until a breakpoint (J6: symbolic)
            stepper.running = True
            try:
                stepper.breakpoints = {debug.resolve_address(program, b) for b in args.breaks}
            except ValueError as exc:
                raise codeb.ProgramError(f"--break: {exc}") from None
        return stepper
    if args.trace == "regs":
        observer = debug.RegisterTrace(names)
        observer.header(machine=machine_run)
        return observer
    if args.trace == "steps" and machine_run:
        return debug.InstructionTrace(names)
    return None


def _print_numbers(program, number) -> None:
    for line in program.lines:
        if line.to == "NUM" and line.label:
            try:
                n = number(line.label)
                print(f"{line.label:<10} {n}  = {float(n.value):g}")
            except NotANumber:
                print(f"{line.label:<10} (not a number)")


def _dump(args, program, memory) -> None:
    for start, count in args.zones:
        print(f"memory {start:05d} - {start + count - 1:05d}:")
        for line in debug.dump_lines(program, memory, start, count):
            print(line)


def run_machine(args, program, profile, names: debug.Names, image=None) -> int:
    if image is None:  # code B: the whole chain, one article, nothing to distribute (J6)
        try:
            ut, source = chain.processing_unit(program, profile, Path(args.program).stem)
        except AsmUnsupported as exc:
            print(f"not assembled yet: {exc}; try --seq")
            return 2
        image = chain.machine_image(ut, source)
    m = machine.Machine(
        image, profile, args.mode, _observer(args, names, True, program), args.config
    )
    for spec in args.tape:
        number, _, path = spec.partition("=")
        if int(number) not in m.tape_drives:
            print(f"error: no drive {number} in configuration {args.config}")
            return 2
        m.tape_drives[int(number)] = TapeDrive.load(int(number), path)
    for spec in args.drum:
        unit, _, path = spec.partition("=")
        drum = m.elements.get(f"drum{unit}")
        if drum is None:
            print(f"error: no drum {unit} in configuration {args.config}")
            return 2
        drum.load(path)
    if args.trace == "dd":
        m.engine.listeners.append(debug.DDTrace(names))
    try:
        result = m.run()
    except debug.Quit:
        print("status: quit")
        return 1
    except MachineUnsupported as exc:
        print(f"not supported yet: {exc}; try --seq")
        return 2
    print(f"status: {result.status} {result.message}".rstrip())
    print(f"{profile.name}, {m.engine.now} µs")
    for element in m.elements.values():
        if element.log:
            busy = sum(end - start for start, end, _ in element.log)
            n = len(element.log)
            print(f"  {names.element(element.kind):<5} {n} directive(s), {busy} µs")
    _print_numbers(program, result.number)
    _dump(args, program, m.memory)
    for number in args.dump_tape:
        for line in m.tape_drives[number].summary():
            print(line)
    if args.gantt:
        chart = gantt.Gantt(
            m,
            names,
            args.gantt_scale,
            args.gantt_from,
            args.gantt_to,
            program_name=Path(args.program).name,
        )
        print()
        for line in chart.by_element() if args.gantt == "elem" else chart.by_sequence():
            print(line)
    return 0 if result.status == "halted" else 1


def run_transpose(args, program, profile) -> int:
    try:
        image = assemble(program, profile)
    except AsmUnsupported as exc:
        print(f"not assembled yet: {exc}")
        return 2
    source = Path(args.program)
    sp = subprogram.from_image(image, source.stem.split(".")[0])
    sp.source = source.name
    out = Path(args.output) if args.output else source.with_name(sp.name + ".g60a.json")
    sp.save(out)
    print(f"{sp.name}: {sp.size} catenae, entry +{sp.entry}, {len(sp.relocations)} relocation(s)")
    for i, name in enumerate(sp.unknowns, 1):
        at = ", ".join(f"+{f.address}" for f in sp.fixups if f.name == name)
        print(f"  X{i:<3} ?{name:<12} {at}")
    for i, (name, at) in enumerate(sp.reperes.items(), 1):
        print(f"  R{i:<3} {name:<13} +{at}")
    print(f"written: {out}")
    return 0


def run_assemble(args) -> int:
    sheet = Path(args.sheet)
    prog = linker.link(sheet)
    stem = sheet.name.split(".")[0]
    out = Path(args.output) if args.output else sheet.with_name(stem + ".g60pa.json")
    prog.save(out)
    for n, name, base, size in prog.layout:
        print(f"  article {n:<3} {name:<14} {base:05d} - {base + size - 1:05d}  ({size})")
    if prog.exit is not None:
        print(f"  {linker.EXIT:<17} {prog.exit:05d}")
    print(f"entry {prog.entry:05d}")
    for s in prog.symbols:
        at = ", ".join(f"{f.address:05d}" for f in prog.fixups if f.name == s)
        print(f"  symbol {s:<14} {at}")
    if args.listing:
        for line in linker.listing_lines(prog):
            print(line)
    print(f"written: {out}")
    return 0


def run_distribute(args) -> int:
    source = Path(args.source)
    stem = source.name.split(".")[0]
    if source.name.endswith((".g60c.yaml", ".json")):  # nothing to distribute: no code D2
        ut = distributor.distribute(distributor.load_assembled(source), {}, stem)
    else:
        ut = distributor.distribute_file(source)
    out = Path(args.output) if args.output else source.with_name(stem + ".ut.json")
    ut.save(out)
    print(f"U.T. {ut.name}: {len(ut.words)} catenae, entry {ut.entry:05d}")
    for symbol, value in ut.distribution.items():
        print(f"  {symbol:<16} = {value}")
    print(f"written: {out}")
    return 0


def run_disasm(args) -> int:
    path = Path(args.source)
    if path.name.endswith(".json"):
        source = disassembler.load(path)
    else:  # code B: through the chain, like run
        program = codeb.parse(path.read_text(encoding="utf-8"))
        ut, _ = chain.processing_unit(program, data.get_profile(program.profile), path.stem)
        source = disassembler.source_of(ut)
    if args.raw:
        source = disassembler.raw(source)
    for line in disassembler.listing(source, args.lang):
        print(line)
    return 0


def run_seq(args, program, profile, names: debug.Names) -> int:
    interp = seq.Interpreter(program, profile, observer=_observer(args, names, False, program))
    try:
        result = interp.run()
    except debug.Quit:
        print("status: quit")
        return 1
    if args.trace == "steps":
        for step, address, element, text in result.trace:
            print(f"{step:5d}  {address:05d}  {element:<10}  {text}")
    print(f"status: {result.status} {result.message}".rstrip())
    _print_numbers(program, result.number)
    _dump(args, program, result.memory)
    return 0 if result.status == "halted" else 1


def run_dd(args) -> int:
    names = debug.Names(args.names)
    scenario = synthetic.load_scenario(args.scenario, args.profile, args.mode)
    if scenario.title:
        print(scenario.title)
    if args.trace:
        scenario.engine.listeners.append(debug.DDTrace(names))
    scenario.run()
    duration = scenario.until_us or scenario.engine.now
    print(f"{scenario.dd.profile.name}, {scenario.dd.cycle} µs, {duration} µs")
    for line in debug.dd_summary(scenario, names, duration):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

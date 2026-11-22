"""Command line.

- ``python -m gamma60 run <program.g60b> [--profile B61|COURS] [--trace[=regs|dd]] [--step]
  [--names en|fr] [--mode faithful|diagnostic] [--seq]``: run a code B program on the machine
  (J3: assembler, Program Distributor, Data Distributor, ARIT, LOGI); ``--seq``: sequential
  interpreter of J1 (needed for SIMU and joins until J4);
  ``--gantt[=elem|seq]`` (ASCII timeline by element or by sequence, ``--gantt-scale``,
  ``--gantt-from``, ``--gantt-to``), ``--dump <zone>``;
- ``python -m gamma60 asm <program.g60b>``: assembly listing (code A beside code B);
- ``python -m gamma60 dd <scenario.yaml>``: Data Distributor scenario (J2).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gamma60 import codeb, data, debug, gantt, machine, seq, synthetic
from gamma60.number import NotANumber
from gamma60.program_distributor import MachineUnsupported
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


def _observer(args, names: debug.Names, machine_run: bool):
    if args.step:
        print(names.say("help"))
        return debug.Stepper(names)
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


def run_machine(args, program, profile, names: debug.Names) -> int:
    try:
        image = assemble(program, profile)
    except AsmUnsupported as exc:
        print(f"not assembled yet: {exc}; try --seq")
        return 2
    m = machine.Machine(image, profile, args.mode, _observer(args, names, True))
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


def run_seq(args, program, profile, names: debug.Names) -> int:
    interp = seq.Interpreter(program, profile, observer=_observer(args, names, False))
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

"""Command line.

``python -m gamma60 run <program.g60b> [--profile B61|COURS] [--trace[=regs]] [--step]
[--names en|fr]``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gamma60 import debug, seq, synthetic
from gamma60.number import NotANumber


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gamma60")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run a code B program (sequential interpreter, J1)")
    run.add_argument("program")
    run.add_argument("--profile", choices=["B61", "COURS"])
    run.add_argument(
        "--trace",
        nargs="?",
        const="steps",
        choices=["steps", "regs"],
        help="print each instruction (steps) or each instruction and the registers it changed",
    )
    run.add_argument("--step", action="store_true", help="interactive step-by-step debugger")
    run.add_argument(
        "--names", choices=["en", "fr"], help="language of register names (default: program's)"
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

    if args.command == "dd":
        return run_dd(args)
    program = seq.parse(Path(args.program).read_text(encoding="utf-8"))
    names = debug.Names(args.names or program.language)
    observer = None
    if args.step:
        observer = debug.Stepper(names)
        print(names.say("help"))
    elif args.trace == "regs":
        observer = debug.RegisterTrace(names)
        observer.header()
    interp = seq.Interpreter(
        program, seq.data.get_profile(args.profile or program.profile), observer=observer
    )
    try:
        result = interp.run()
    except debug.Quit:
        print("status: quit")
        return 1
    if args.trace == "steps":
        for step, address, element, text in result.trace:
            print(f"{step:5d}  {address:05d}  {element:<10}  {text}")
    print(f"status: {result.status} {result.message}".rstrip())
    for line in result.program.lines:
        if line.to == "NUM" and line.label:
            try:
                n = result.number(line.label)
                print(f"{line.label:<10} {n}  = {float(n.value):g}")
            except NotANumber:
                print(f"{line.label:<10} (not a number)")
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

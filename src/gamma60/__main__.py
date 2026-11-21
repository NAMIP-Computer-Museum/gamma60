"""Command line: ``python -m gamma60 run <program.g60b> [--profile B61|COURS] [--trace]``."""

from __future__ import annotations

import argparse
import sys

from gamma60 import seq
from gamma60.number import NotANumber


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gamma60")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="run a code B program (sequential interpreter, J1)")
    run.add_argument("program")
    run.add_argument("--profile", choices=["B61", "COURS"])
    run.add_argument("--trace", action="store_true")
    args = parser.parse_args(argv)

    result = seq.run_file(args.program, args.profile)
    if args.trace:
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


if __name__ == "__main__":
    sys.exit(main())

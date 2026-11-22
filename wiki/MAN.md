# gamma60(1)

```
GAMMA60(1)                  Bull Gamma 60 emulator                  GAMMA60(1)
```

## NAME

**gamma60** - run, assemble and observe programs of the Bull Gamma 60

## SYNOPSIS

```
python -m gamma60 run program.g60b [--profile B61|COURS] [--mode faithful|diagnostic]
                  [--names en|fr] [--trace[=steps|regs|dd]] [--step]
                  [--gantt[=elem|seq]] [--gantt-scale US] [--gantt-from US] [--gantt-to US]
                  [--dump ZONE] ... [--seq]

python -m gamma60 asm program.g60b [--profile B61|COURS]

python -m gamma60 dd scenario.yaml [--profile B61|COURS] [--mode faithful|diagnostic]
                  [--names en|fr] [--trace]

python -m gamma60 [run|asm|dd] --help
```

## DESCRIPTION

**gamma60** emulates the Bull Gamma 60 (1958-1964) with a deterministic discrete-event
simulation: simulated time in microseconds, one catena (24-bit word + 3-bit key) transferred
per memory cycle, autonomous elements coordinated by the Program Distributor (PD) and the
Data Distributor (DD). The same input always gives the same results and the same trace.

Programs are written in **code B**, the symbolic code of the period, in either of its two
languages: `en` (mnemonics of the 1961 brochure, B61) or `fr` (mnemonics of the programming
course, COURS). The language is declared on the first line of the program (`; langue: en`).
They are assembled into **code A** (one instruction per catena) and loaded into memory, at
address 256 by default.

What the emulator runs today (milestone J4): the Program Distributor (cuts, address
instructions, branches, the 20 central directives, recall chains, SIMU, joins, virtual
elements), the Data Distributor, and the arithmetic (ARIT) and logical (LOGI) calculators.
Drums, tapes, cards, printers, the comparator and the transcoder come with later milestones.

Everything the sources leave open is an explicit, adjustable assumption in `data/*.yaml`,
listed in [`docs/UNKNOWNS.md`](../docs/UNKNOWNS.md) (U-xx).

## COMMANDS

**run** *program.g60b*
:   Assemble the program, load it and run it on the machine until no event is left. Print the
    final status, the simulated time, the number of directives and the busy time of each
    element, then the value of every `NUM` label of the program.

**asm** *program.g60b*
:   Assemble the program and print the listing: one line per catena, with its address, the
    code A grouped by fields and the code B source line. Data (`NUM`, `BIN`, `ZONE`) are shown
    in hexadecimal, where BCD digits can be read directly.

**dd** *scenario.yaml*
:   Run a Data Distributor scenario with synthetic elements (milestone J2) and print, for each
    element, the catenae served, the mean and maximum wait, the missed deadlines and its share
    of the memory cycles. Scenarios are in `tests/scenarios/`.

## OPTIONS

### Machine

**--profile** `B61` | `COURS`
:   Machine profile. `B61` (default, the machine as delivered in 1961): 10 us memory cycle,
    check key = parity + mod 3, ARIT times 200 / 350 / 550 us. `COURS` (the 1958-59 course):
    11 us cycle, key mod 7, ARIT times 100 / 300 / 600 us. A program may declare its profile
    with `; profil: COURS`; the option wins. Profile and language are independent.

**--mode** `faithful` | `diagnostic`
:   `faithful` (default): only the checks of the period (check keys, selection, "decoded
    directive error"). `diagnostic`: modern checks as well, e.g. a join never reached makes
    the run `blocked`, a DD request waiting more than 50 cycles is reported (scenarios).

**--seq**
:   Use the sequential interpreter of milestone J1 instead of the machine: no time, no Program
    Distributor, ARIT and LOGI only. Kept as a reference for results. Not compatible with
    `--gantt`.

### Names

**--names** `en` | `fr`
:   Language of the register names and of the messages in traces, timelines and the debugger.
    Default: the language of the program. Upper-case names are attested in that language
    (`IAR`, `RAI`, `CAR`, `RAC`, `P`, `A`…); lower-case ones are labels proposed by the
    emulator, not validated (`cpar` for RAPA, `z` for Z…). See [REGISTERS.md](REGISTERS.md).

### Traces

**--trace**, **--trace=steps**
:   One line per instruction read by the Program Distributor: simulated time (us), address,
    element served, code A grouped by fields, code B source line.

**--trace=regs**
:   The same lines, each followed by the registers changed since the previous one, marked
    with `*`: registers of the PD (`enr`, `cpar`, `ipar`, `pdir`, `pdor`, `A`, `B`, `pdc1`,
    `pdc2`) and of each element (`IAR` and its state, `i1` / `i2`, `P` `S` `O` or `K` `L`,
    `qcr`, `CAR0`-`CAR3`). A legend at the top gives the expanded name and the source of each
    label.

**--trace=dd**
:   One line per memory cycle of the Data Distributor: time, channel (DDC store → element,
    DCC element → store), gate of the class circuit, element served, quantity or instruction,
    CAR before → after (or the PD's RAPA), catena transferred, requests still waiting.

With **dd**, **--trace** gives the same per-cycle lines.

### Debugger

**--step**
:   Interactive step-by-step debugger: the run stops before each instruction the PD has just
    read and waits for a command:

    | command | effect |
    |---|---|
    | *Enter*, `s` | next instruction; the registers it changed are shown, marked `*` |
    | `r` | all registers |
    | `m` *address\|label* [*n*] | *n* catenae of memory (default 1): address, label, hexadecimal, key |
    | `b` *address\|label* | breakpoint |
    | `d` *address\|label* | delete the breakpoint |
    | `w` *element* | stop whenever the PD serves this element (`w LOGI`) |
    | `c` | continue until a breakpoint or a watched element |
    | `l` | legend of the register names |
    | `h` | help |
    | `q` | quit (status `quit`, exit status 1) |

    The end of the input acts as `c`. The debugger only reads the state of the machine: the
    run is the same with or without it.

### Results

**--dump** *ZONE*
:   Memory zone printed at the end of the run, one line per catena: address, label, the 24
    bits in hexadecimal, check key (read without checking it). *ZONE* is *address|label* [*n*]
    (n catenae, default 1) or `all` (the whole program and its working memories). Repeatable.

**--gantt**, **--gantt=elem**
:   ASCII timeline by element, printed at the end of the run. Rows: `PD` (letter of the element
    served, `F` the PD working for itself, `S` STOP), one row per element that worked
    (`[DIV===]` a directive, `~` waiting for the PD, `.` idle), `mem` (catenae transferred by
    the DD in the column), and markers `^` for SIMU and join arrivals.

**--gantt=seq**
:   ASCII timeline by sequence, one row per sequence, named after the label where it starts:
    `A`, `L`… the element working for it, `F` the PD for itself, `~` waiting for the PD, `.`
    waiting on a recall chain; it ends with `>` (SIMU or join passed), `|` (join not yet
    complete) or `S` (STOP).

**--gantt-scale** *US*
:   Microseconds per character. Default: the smallest round value (1, 2, 5, 10, 25, 50…) that
    fits the run in 100 columns. A directive shorter than 3 characters is drawn `===`.

**--gantt-from** *US*, **--gantt-to** *US*
:   Window of the timeline. A bar cut by the window has no bracket on that side.

## EXAMPLES

Run a program, then show where its result sits in memory:

```
$ python -m gamma60 run tests/programs/test-arith01.g60b --dump R 2
status: halted
B61, 740 µs
  ARIT  1 directive(s), 550 µs
X          +42 2200|000000  = 22
Y          +41 7000|000000  = 7
R          +41 3142|857142  = 3.14286
memory 00267 - 00268:
      00267  R        413142  key 1
      00268           857142  key 6
```

`41` is the exponent (one digit before the point), `3142` and `857142` the 10 digits of the
mantissa in BCD.

The same program with the timings of the course, and French names:

```
$ python -m gamma60 run tests/programs/test-arith01.g60b --profile COURS --trace=regs --names fr
```

Assembly listing:

```
$ python -m gamma60 asm tests/programs/test-arith01.g60b
00256  01 000 00 0 0 000000000000010    START:  ARIT
00257  00 00000 0 0 000000000000000     VIERGE
00258  110 00 00 0 0 000000100000111    L     0     X
00259  110 00 01 0 0 000000100001001    L     1     Y
00260  110 00 10 0 0 000000100001011    L     2     R
00261  1111 00111101100000001011        DIV   N     - 0 1 2
...
```

Two branches working at the same time, seen as a timeline:

```
$ python -m gamma60 run tests/programs/parallele.g60b --gantt
parallele.g60b - B61 - 2040 us - 1 char = 25 us
us     0                   500                 1000                1500                2000
       |---------+---------|---------+---------|---------+---------|---------+---------|-
PD     FF.FLLLLL.AAAAA...L...L...............AA........................LL.AAAA..........S
ARIT   ....~~~~~~.....[DIV==================]............................~.....[ADD====].
LOGI   .~~~.....[K]~~~~...[L]~.[MUL===================================]~.................
mem    21212111.12111.131.1..1.............12121......................12131111.22.....121
       ^                                       ^                         ^
       ^ 20 us SIMU ; 1000 us JOIN 1/2 ; 1660 us JOIN 2/2
```

The same run by sequence, and a program whose two branches share the only ARIT:

```
$ python -m gamma60 run tests/programs/parallele.g60b --gantt=seq
$ python -m gamma60 run tests/programs/forkjoin_tumlin.g60b --gantt=seq
```

Zoom on part of a run, 10 us per character:

```
$ python -m gamma60 run tests/programs/parallele.g60b --gantt --gantt-scale 10 \
      --gantt-from 500 --gantt-to 1100
```

Step through a program, stop when LOGI is served, look at memory:

```
$ python -m gamma60 run tests/programs/parallele.g60b --step
(g60) w LOGI
(g60) c
watch LOGI
(g60) m K 3
      00291  K        0004D2  key 1
      00292  L        000BB9  key 1
      00293  M        000000  key 0
(g60) q
status: quit
```

A Data Distributor scenario: the drum is served before ARIT and never misses its position:

```
$ python -m gamma60 dd tests/scenarios/drum_arit.yaml --trace --names fr
```

## FILES

`tests/programs/*.g60b`
:   Example programs in code B, described in `tests/programs/README.md`: `test-arith01-03`,
    `arit_logi`, `fibonacci`, `pi`, `parallele`, `forkjoin_tumlin`…

`tests/scenarios/*.yaml`
:   Data Distributor scenarios for the **dd** command.

`data/*.yaml`
:   Tables of the machine and every assumption (profiles, timings, priorities, code A
    encoding, registers, behaviour, configurations).

## EXIT STATUS

**0**
:   The program halted normally (`status: halted`); **asm** and **dd** succeeded.

**1**
:   The run ended with an incident (`status: incident`, e.g. an exponent overflow), was
    `blocked`, or the debugger was quit (`status: quit`).

**2**
:   Invalid program (`error: …`), code not supported yet (`not assembled yet`, `not supported
    yet`), invalid `--dump` zone, or `--gantt` with `--seq`.

## NOTES

- The program (or scenario) is the **first argument after the command**, before any option:
  `--trace`, `--gantt` and `--dump` take optional or variable values, so a program name
  written after them would be taken as their value (`run --trace prog.g60b` fails; write
  `run prog.g60b --trace`).
- Program header lines: `; langue: en|fr`, `; profil: B61|COURS`, `; origine: N` (load
  address, default 256, after the table of the recall chain registers).
- Pseudo-instructions of the assembler, not of the period: `VIERGE [m]` (blank catena after a
  cut; `m`: join count in COURS notation), `NUM ±d` (semi-logarithmic number, 2 catenae),
  `BIN n` (24-bit binary integer), `ZONE n` (n catenae at 0).
- Unicode is used only in a few messages (`µs`); traces and timelines are plain ASCII.

## SEE ALSO

[INSTRUCTIONS.md](INSTRUCTIONS.md) (codes A and B, every instruction),
[REGISTERS.md](REGISTERS.md) (register names), [CONCURRENCY.md](CONCURRENCY.md) (SIMU, joins,
recall chains), [MEMORY.md](MEMORY.md) (catenae and number formats),
[`docs/TOOLCHAIN.md`](../docs/TOOLCHAIN.md) (code B format, assembler),
[`docs/UNKNOWNS.md`](../docs/UNKNOWNS.md) (assumptions U-xx).

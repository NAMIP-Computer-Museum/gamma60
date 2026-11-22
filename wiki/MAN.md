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
                  [--dump ZONE] ... [--seq] [--config NAME]
                  [--tape N=FILE] ... [--drum K=FILE] ... [--dump-tape N] ...

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

What the emulator runs today (milestone J5): the Program Distributor (cuts, address
instructions, branches, the 20 central directives, recall chains, SIMU, joins, virtual
elements), the Data Distributor, the arithmetic (ARIT) and logical (LOGI) calculators, the
general comparator (COMP), the magnetic drums and the tape uniselectors with their drives
(discontinuous mode). The transcoder, cards, printers, paper tape and the desk come later.

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

**--config** *NAME*
:   Machine configuration in `data/configs/` (default `max`: 8 memory blocks, ARIT, LOGI, COMP,
    4 drums, 10 uniselectors, 48 tape drives wired as on B61 p.54). `rtt_1963` is the RTT
    installation of 1963.

### Media

**--tape** *N*`=`*FILE*
:   Mount a reel on tape drive *N* (repeatable). *FILE* is YAML: `blocks:` a list of blocks
    (lists of catenae, as numbers or `"0x…"` strings) and tape marks (`mark`), and optionally
    `write_protected: true`. Drives without a reel are empty.

**--drum** *K*`=`*FILE*
:   Initial contents of drum *K* (repeatable): YAML `{address: [catenae…]}`, with the
    continuous code B addresses 0-25 599. Otherwise the drum holds zeros.

**--dump-tape** *N*
:   At the end of the run, list the blocks of drive *N* (repeatable): length and first
    catenae of each block, tape marks, current position.

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
:   ASCII timeline by element, printed at the end of the run: the Program Distributor, each
    element that worked, the memory traffic, and the SIMU and join events. A legend follows.
    Every code is listed in [TIMELINE CODES](#timeline-codes).

**--gantt=seq**
:   ASCII timeline by sequence, one row per sequence, named after the label where it starts,
    showing which element works for it, when it waits and how it ends. A legend follows. See
    [TIMELINE CODES](#timeline-codes).

**--gantt-scale** *US*
:   Microseconds per character. Default: the smallest round value (1, 2, 5, 10, 25, 50…) that
    fits the run in 100 columns. A directive shorter than 3 characters is drawn `===`.

**--gantt-from** *US*, **--gantt-to** *US*
:   Window of the timeline. A bar cut by the window has no bracket on that side.

## TIMELINE CODES

Both timelines are plain ASCII. Column *c* covers [*c* × *scale*, (*c* + 1) × *scale*[
microseconds from the start of the window; the ruler and every row have exactly one character
per column, and the last column holds the end of the run. A legend in the language of `--names`
is printed under each timeline, with the letters of the elements present.

### Both views

| Code | Where | Meaning |
|---|---|---|
| title line | first line | program, profile, total time, `(A-B us)` for a window, `1 char = N us` |
| `us` / `seq.` | start of the second line | title of the axis (view by element / by sequence) |
| numbers | second line | time in microseconds, each one starting on its tick |
| `\|` | ruler | labelled tick, every 20 columns |
| `+` | ruler | half tick, every 10 columns |
| `-` | ruler | other columns |

### View by element (`--gantt`)

Row `PD` (`DP` with `--names fr`), the Program Distributor:

| Code | Meaning |
|---|---|
| `A`, `L`, `C`, `D`, `M`… | the PD reads an instruction for that element (first letter of its name, see below) |
| `F` | the PD works for itself: start, SIMU, its own recall chain |
| `S` | STOP |
| `.` | the PD is free |

When several instructions fall in one column, an element letter wins over `F`.

One row per element that worked, titled `ARIT`, `LOGI`, `COMP`, `DRUM1`, `MATA2`…
(`TAMB1`, `DERU2`… with `--names fr`):

| Code | Meaning |
|---|---|
| `[` | start of a directive |
| `]` | end of a directive |
| `ADD`, `DIV`, `TCD`, `TRA`… | code B mnemonic of the directive, in the language of `--names`, when it fits in the bar |
| `K`, `L` | short forms of TSK / TCK (load K) and TSL / TCL (load L) |
| `=` | the rest of a directive |
| `===` (no brackets) | a directive shorter than 3 columns: the element is busy |
| `=` instead of `[` or `]` | bar cut by `--gantt-from` / `--gantt-to`: the directive began before, or ends after, the window |
| `~` | the element waits for the PD (instruction request raised) |
| `.` | idle |

Row `mem`, the Data Distributor:

| Code | Meaning |
|---|---|
| `1` … `9` | catenae transferred in the column (9 or more: `9`) |
| `.` | no transfer |

Event markers, on the two lines under `mem`:

| Code | Meaning |
|---|---|
| `^` | an event in this column |
| `20 us SIMU` | a SIMU forks the sequence at that time |
| `1000 us JOIN 1/2` | arrival number 1 at a join that waits for 2 |

### View by sequence (`--gantt=seq`)

Row title: the label where the sequence starts (entry point, branch of a SIMU, or the label of
a join once passed), cut to 6 characters; `@00266` (its address) when there is no label.

| Code | Meaning |
|---|---|
| `A`, `L`, `C`, `D`, `M`… | an element works for this sequence: the PD reads its instructions for that element, or the element executes its directive |
| `F` | the PD works for itself for this sequence (SIMU, blank catena of the PD's chain) |
| `~` | the sequence waits for the PD (instruction request, or the PD's own chain) |
| `.` | the sequence waits on the recall chain of a busy element |
| blank | the sequence does not exist yet, or has ended |
| `>` | ends by a fork (SIMU) or a join passed: the work goes on under the label of the join |
| `\|` | stops at a join not yet complete |
| `S` | ends by STOP |

`.` means *idle* on an element row but *waiting on a recall chain* on a sequence row.

### Element letters

First letter of the displayed name, so it depends on `--names`:

| Element | `en` | `fr` |
|---|---|---|
| ARIT | `A` | `A` |
| LOGI | `L` | `L` |
| COMP | `C` | `C` |
| drum | `D` (DRUM) | `T` (TAMB) |
| uniselector | `M` (MATA) | `D` (DERU) |

`D` thus means a drum in English and a uniselector in French; the legend under each timeline
gives the letters actually used (`A=ARIT D=DRUM1,DRUM2`). With the card units, the printer,
the paper tape and the transcoder (milestone J8) several elements will share a letter (`C`,
`P`, `T`): this will be resolved then.

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

legend:
  [DIV===] directive (code B mnemonic)   === short directive   ~ waiting for the PD   . idle
  PD: letter of the element served (A=ARIT L=LOGI)   F the PD for itself   S STOP   . free
  mem: catenae transferred by the DD in the column (1-9, . none)   ^ events listed above
```

The same run by sequence: BRA stops at the join (`|`), BRL passes it (`>`) and the work goes
on as FIN:

```
$ python -m gamma60 run tests/programs/parallele.g60b --gantt=seq
...
START  >
BRL     F~~LLLLLLLL~~~~~~LLLLL~LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL>
BRA       FF~~~~~AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA|
FIN                                                                       AAAA~AAAAAAAAAS

legend:
  letter of the element working for the sequence (A=ARIT L=LOGI)   F the PD for itself
  ~ waiting for the PD   . waiting on a recall chain (busy element)   blank: not running
  end: > fork (SIMU) or join passed   | stops at a join not yet complete   S STOP
```

A program whose two branches share the only ARIT: the second one waits on ARIT's recall
chain (`.`) until the first is done:

```
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

Read a block from tape drive 3 into memory, then show the reel and the buffer:

```
$ python -m gamma60 run tests/programs/lecture_bande.g60b --tape 3=tests/media/bloc_128.yaml       --dump-tape 3 --dump TAMPON 2
...
memory 00268 - 00269:
      00268  TAMPON   000001  key 1
      00269           000002  key 2
drive 3: 3 block(s), position 1
    0   128 catenae  000001 000002 000003 000004 000005 000006 ...
    1  tape mark
    2    16 catenae  111111 222222 333333 444444 000005 000006 ...
```

A drum transfer hiding 30 divisions of ARIT behind the rotation of the drum:

```
$ python -m gamma60 run tests/programs/tambour_arit.g60b --gantt
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

`tests/media/*.yaml`
:   Tape reels for **--tape** (e.g. `bloc_128.yaml`).

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
    yet`), invalid `--dump` zone, `--gantt` with `--seq`, or a drive or drum missing from the
    configuration.

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

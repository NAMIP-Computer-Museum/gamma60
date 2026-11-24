# Instruction set

How the Gamma 60 was programmed: the four "codes" of its programming chain, then every
instruction of the central unit and of each element.

> This page is an English presentation of [`docs/ISA.md`](../docs/ISA.md) and
> [`docs/TOOLCHAIN.md`](../docs/TOOLCHAIN.md), which prevail. Main sources: B61 chapter III and
> the "Gamma 60 code B table of instructions" (B61 p.62-66, page images in
> [`archives/photos/`](../archives/photos/)); COURS p.33-60 for code A and the central
> directives. Machine-readable tables: [`data/directives.yaml`](../data/directives.yaml) and
> [`data/encoding.yaml`](../data/encoding.yaml).

See also [ARCHITECTURE.md](ARCHITECTURE.md) (elements and classes),
[MEMORY.md](MEMORY.md) (§3, instructions in memory), [CONCURRENCY.md](CONCURRENCY.md) (cuts,
`SIMU`, join, `PROT` / `LIBE`).

> **What is known, and what is not.**
> - **Known**: the mnemonics, the fields of code B, the semantics, and in code A the **type
>   prefixes and the position of every field**.
> - **Not known**: the **binary value of most sub-codes** in code A (which bits mean `MUL`,
>   which mean `ADD`…), i.e. the mapping between code B and code A (U-01). The emulator's
>   assembler and decoder therefore use a **reconstructed encoding**: stable, documented in
>   `data/encoding.yaml`, and to be replaced as soon as a source gives the real values. In the
>   tables below, the code A column shows only what is known (prefix and fields); unknown
>   sub-codes are written *sub-code (U-01)*.

---

## 1. The four codes

The Gamma 60 programming chain uses four levels, called *codes*. [MAIT ; B61 p.28-30]

| Code | What it is | Who writes it | Status |
|---|---|---|---|
| **B** | symbolic program, one instruction per line | the programmer | well documented |
| **A** | binary machine code, one 24-bit catena per instruction | produced by translation of code B | structure known, sub-codes not (U-01) |
| **C** | assembly sheet: how subprograms are linked and placed | the programmer | partly documented |
| **D** | distribution and launch values: final addresses, unit numbers, jobs | the operator | partly documented |

### 1.1 Code A: the binary structure

An instruction is **one catena** (24 bits + check key). The type is a **prefix code** (TK)
read from the left. [COURS p.33-52 ; B61 p.15, p.29-30] Bits are numbered 24 (left) to 1
(right).

| TK (bits) | Type | Remaining fields |
|---|---|---|
| `00` (24-23) | **Branch** | 22-18 condition (0 never, 1-24 = bit of register A, 31 always) · 17 d · 16 s · 15-1 address |
| `01` (24-23) | **Cut** | 22-20 kind (7 values) · 19-18 *m* (join) · 17 d · 16 s · 15-1 element number or address |
| `10` (24-23) | **Central directive** | 22-18 directive (32 codes, 20 used) · 17 d · 16 s · 15-1 X |
| `110` (24-22) | **Address instruction** | 21-20 operation (load, place, add, subtract) · 19-18 CAR number · 17 d · 16 s · 15-1 X |
| `1111` (24-21) | **Element directive** | with a free variable: 20-18 type (≤ 8) · 17 d · 16 s · 15-1 X; without: 20-1 specific to the element |
| `1110` | undocumented | (U-24) |

- **Address function**: bit 17 *d* = differential (relative to the instruction's own address;
  negative offsets as complement to 32,768), bit 16 *s* = substitution (indirect). *d* is
  applied first, then *s*.
- A catena whose 7 leftmost bits are 0 (a blank catena, or data) executes as a **"never"
  branch**. [COURS p.42]
- Example [COURS p.44]: "always branch, 10 lines further, differential" =
  `00 11111 1 0 000000000001010`.

### 1.2 Code B: the symbolic structure

A line of code B has **13 characters** in four zones. [B61 p.28-30]

| Zone | Width | Use |
|---|---|---|
| **T.O.** (type of operation) | 4 | cut: 4 letters · element directive: 3 letters, right-aligned · branch and central directive: 2 characters · address instruction: 1 letter |
| **C.C.** (complementary codes) | 2 | depends on the instruction |
| **X** (free variable / address) | 5 | decimal value ≤ 32,767, right-aligned |
| **A.F.** (address function) | 2 | column 1: `R` (relative; `M` for a working memory, COURS) · column 2: `S` (substitution) |

Code B and code A correspond **one to one**. The width of the T.O. reflects a hierarchy: cuts,
then directives (which free the Program Distributor), then branches, central directives and
address instructions (which do not). [B61 p.28-30]

**Two languages.** Code B exists in English (`en`, B61, 1961) and French (`fr`, COURS,
~1958-59). The two documents describe the same machine: the difference is a translation (G
*garnir* → L *load*, R *ranger* → P *place*), not a change of the machine. In the tables
below, the code B pattern is written in `en`, and the `en` / `fr` column gives both spellings.
The French spellings of the element directives come from the French version of the code B
tables [TFR], identical line by line to B61's; only the console (`DESK`) has no recorded
French spelling (U-29).

### 1.3 Code C: the assembly sheet

After translation, each subprogram is an "assemblable subprogram": code A with blanks, plus a
table of unknowns and labels. The **code C sheet** drives the assembly: numbered list of
subprograms and of working zones (buffers, sort areas), links between subprograms
(`SPy.Xn = SPz.Rm`), constants (`SPy.Xn = constant`), load address of the first subprogram,
entry point. The assembler condenses, links, and lists what is still unknown. [MAIT]

In the emulator (J6), a subprogram declares its labels visible to code C with `REP LABEL…` and
its unknowns as `?NAME` in a free variable (or `BIN ?NAME` for a whole catena); the code C sheet
is a modern YAML file (`.g60c.yaml`). Neither format is historical: the period layout of the
sheets is not known (U-52, U-53). See [MAN.md](MAN.md) (`transpose`, `assemble`) and
[`docs/TOOLCHAIN.md`](../docs/TOOLCHAIN.md).

### 1.4 Code D: distribution and launch

The remaining values (memory address, drum address, unit or element number, zone length) are
supplied at **distribution** time, by console orders or **code D2** cards. The result is an
executable, frozen **UT** (*unité de traitement*). The GGU system adds **D1** (launch
parameters) and **D3** (jobs). [MAIT ; B61 p.48]

In the emulator (J6), code D2 is a YAML file (`.g60d.yaml`, one value per symbol, written as in
code B) and the UT a JSON file (`.ut.json`) that `run` executes (U-54); D1 and D3 come with the
GGZ (J7).

---

## 2. Central unit instructions

These are executed by the Program Distributor itself, not by an element.

### 2.1 Cuts (TK `01`)

A cut hands the sequence over to an element. C.C. = number *m* of **additional** join
conditions (blank, 1, 2 or 3 → wait for 1, 2, 3 or 4 sequences). Every cut is followed by a
**blank catena**. [B61 p.31 ; table p.62-66]

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `ARIT m` | ARIT / ARIT | `01` · kind *(U-01)* · m · element number | cut on the arithmetic calculator |
| `LOGI m` | LOGI / LOGI | idem | cut on the logical calculator |
| `TRAN m` | TRAN / TRAD | idem | cut on the transcoder |
| `COMP m` | COMP / COMP | idem | cut on the comparator |
| `DRUM m  n  RS` | DRUM / TAMB | idem; X = element number | cut on drum *n* |
| `CARR m  n  RS` | CARR / LECT | idem | cut on card reader *n* |
| `CARP m  n  RS` | CARP / PECT | idem | cut on card reader-punch *n* |
| `PRIN m  n  RS` | PRIN / IMPR | idem | cut on printer *n* |
| `MATA m  n  RS` | MATA / DERU | idem | cut on tape uniselector *n* |
| `TAPR m  n  RS` | TAPR / LEBA | idem | cut on paper-tape reader *n* |
| `TAPP m  n  RS` | TAPP / PEBA | idem | cut on paper-tape punch *n* |
| `DESK m  n  RS` | DESK / *not recorded* (U-29) | idem | cut on the console |
| `PROT m  x  RS` | PROT / PROT | `01` · kind *(U-01)* · m · X = image address | take a virtual element (lock) |
| `LIBE m  x  RS` | LIBE / LIBE | idem | release a virtual element |
| `SIMU m  x  RS` | SIMU / SIMU | `01` · kind *(U-01)* · X = second branch | start two sequences (fork) |
| `STOP` | STOP / STOP | `01` · kind *(U-01)* | end of sequence |

`RS` stands for the optional address function `R` and/or `S`. In COURS, the C.C. of a cut
instead marks two **special cuts**: `A` (without releasing the requesting element) and `B`
(without checking whether the element is busy), and the join count goes in the X of the blank
catena. [COURS p.39, p.51-52]

### 2.2 Branches (TK `00`)

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `00    x  RS` | 00 / 00 | `00 00000` · d s · X | never (no-op) |
| `31    x  RS` | 31 / 31 | `00 11111` · d s · X | always |
| `nn    x  RS` (01-24) | 01-24 / 01-24 | `00` · n · d s · X | if bit *n* of register A is 1 |

Register A holds the qualitative catena of the element being served, or any catena loaded by
`TA`. A "never" can be turned into an "always" by program (`SA`, `SN`, `RR`). [B61 p.31]

### 2.3 Address instructions (TK `110`)

They apply to the element of the preceding cut. C.C. = CAR number (0-3). [B61 table p.62-66]

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `L  c  x  RS` | L / G | `110` · op *(U-01)* · c · d s · X | load CAR *c* with X |
| `P  c  x  RS` | P / R | idem | store CAR *c* at address X |
| `A  c  x  RS` | A / A | idem | add X to CAR *c* |
| `S  c  x  RS` | S / S | idem | subtract X from CAR *c* |

### 2.4 Central directives (TK `10`)

Executed by the Program Distributor, which they do **not** release. A.F. column 1 may be `R`
or `M`. Semantics from COURS p.53-60; B61 table p.62-66 for the `en` names.

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `PI    x  RS` | PI / RI | `10` · directive *(U-01)* · d s · X | memory[X] ← instruction number (return address) |
| `LE    x  RS` | LE *(hyp., U-28)* / GE | idem | element number register RNE ← X |
| `PE    x  RS` | PE *(hyp., U-28)* / RE | idem | memory[X] ← RNE |
| `TA    x  RS` | TA / TA | idem | register A ← memory[X] |
| `PA    x  RS` | PA / RA | idem | memory[X] ← register A |
| `TB    x  RS` | TB / TB | idem | register B ← memory[X] |
| `PB    x  RS` | PB / RB | idem | memory[X] ← register B |
| `LB    x  RS` | LB / GB | idem | B ← X (15 right bits) |
| `AB    x  RS` | AB / AB | idem | B ← B + X (15 bits, no carry) |
| `SB    x  RS` | SB / SB | idem | B ← B − X (15 bits) |
| `CB    x  RS` | CB / CB | idem | compare B with X; result in register A, bits 1-6 |
| `SQ` | SQ / SQ | idem, no X | B ← memory[B] |
| `SI` | SI / SI | idem, no X | execute the instruction at address B |
| `SN    x  RS` | SN / FJ | idem | set the branch at X to "never" |
| `SA    x  RS` | SA / FT | idem | set the branch at X to "always" |
| `RR    x  RS` | RR / FI | idem | reverse the switch at X |
| `FZ    x  RS` | FZ / FZ | idem | memory[X] ← all zeros |
| `FO    x  RS` | FO / FU | idem | memory[X] ← all ones |
| `IC    x  RS` | IC / DI | idem | iteration control on memory[X], [X+1]; sets bit 14 (zero) or 15 of A |
| `CP    x  RS` | CP / PC | idem | memory[X] + 1 (15 bits); B receives the old value |

`LE` and `PE` are not in the B61 table: they are COURS's `GE` / `RE`, with English names
assumed by analogy (G → L, R → P). The line-to-mnemonic reading of `SQ` and `SI` on B61 p.63
is to be re-checked.

---

## 3. Processing elements

Element directives have TK `1111`. Their code A is `1111` · *sub-code (U-01)* · fields.

### 3.1 ARIT, arithmetic calculator

*Class 1 · shared (recall chain) · see [ARCHITECTURE.md](ARCHITECTURE.md).* Works on
semi-logarithmic decimal numbers ([MEMORY.md](MEMORY.md) §2.3). [B61 p.36, table ; COURS p.66-68]

Operands **O1, O2, R** (in X): `0-3` = CAR with progression; `Z F S T` / `Z U D T` = CAR 0-3
without progression; `P` = register P (not as O2). **dp** = position of the decimal point of
the result (0-10; none = floating). C.C.1 = `P` programmed point, `N` normalised, `R` / `A`
normalised and rounded (`R` assumed, U-05). C.C.2 = `D`: double-length result (20 digits).

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `ADD cc dp O1 O2 R` | ADD / ADD | `1111` · sub-code *(U-01)* · fields | R ← O1 + O2 |
| `SUB cc dp O1 O2 R` | SUB / SOU | idem | R ← O1 − O2 |
| `MUL cc dp O1 O2 R` | MUL / MUL | idem | R ← O1 × O2 |
| `DIV c  dp O1 O2 R` | DIV / DIV | idem | R ← O1 ÷ O2, no remainder (C.C. P or N) |
| `DIR cc dp O1 O2 R` | DIR / DIR | idem | division with remainder |
| `TRA cc dp O1 R` | TRA / TER | idem | R ← O1 |
| `MPT    n  O1` | MPT / MPD | idem | multiply by 10ⁿ (n = 0-15) |
| `DPT    n  O1` | DPT / DPD | idem | divide by 10ⁿ |
| `RSI` | RSI / ISI | idem | reverse the sign of P |
| `AVA` | AVA / PVA | idem | absolute value |
| `CAV       O1 O2` | CAV / CVA | idem | compare absolute values |
| `CAL       O1 O2` | CAL / CAL | idem | compare algebraic values |
| `ROF` | ROF / ARR | idem | round off |

Operands of `MPT`, `DPT`, `CAV`, `CAL` are uncertain in the B61 table. The French table shows
operands O1 and R for `ISI` (`RSI`) and `PVA` (`AVA`), and possibly R for `ARR` (`ROF`) (U-31).

### 3.2 LOGI, logical calculator

*Class 0 according to ONDE, class 1 according to MAIT (U-09) · shared.* Works in binary on
registers K and L. X gives a shift or bit count (0-23); R = CAR 0-3, `Z F S T` / `Z U D T`,
or `L`. [B61 table p.62-66]

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `TSK  n …` | TSK / TCK | `1111` · sub-code *(U-01)* · fields | transfer with shift into K |
| `TSL  n …` | TSL / TCL | idem | transfer with shift into L |
| `TKL` | TKL / TKL | idem | transfer K into L |
| `SHL  n` | SHL / MCL | idem | shift L left |
| `IKL  n` | IKL / IKL | idem | insert K into L |
| `FZL` | FZL / FZL | idem | fill L with zeros |
| `FOL` | FOL / FUL | idem | fill L with ones |
| `ADD …` | ADD / ADD | idem | binary addition |
| `SUB …` | SUB / SOU | idem | binary subtraction |
| `MUL …` | MUL / MUL | idem | binary multiplication |
| `DIV …` | DIV / DIV | idem | binary division |
| `FLC` | FLC / FCL | idem | replace L by its complement |
| `INT …` | INT / INT | idem | logical intersection (AND) |
| `REU …` | REU / REU | idem | logical union (OR) |
| `BLC …` | BLC / CBL | idem | binary and logical comparison |

### 3.3 COMP, comparator

*Class 1 · shared.* Works on zones of 1 to 255 catenae. [B61 table p.62-66]

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `OWC c  n  RS` | OWC / CMP | `1111` · sub-code *(U-01)* · d s · X | simple comparison (C.C. = CAR 1 or 2) |
| `TWC   n  RS` | TWC / CDB | idem | comparison with two bounds |
| `DEL   n  RS` | DEL / EFL | idem | erase a zone |
| `TSS c  n  RS` | TSS / TRR | idem | transfer memory → memory |

### 3.4 TRAN, transcoder

*Class 1 · shared.* Converts between card, tape, printer, processing and storage forms,
driven by **clichés** (4 per catena) held in a microprogram store (MIC). [B61 table p.62-66 ;
TFR p.3]

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `MIC c` | MIC / GMI | `1111` · sub-code *(U-01)* · fields | load the MIC (C.C. left/right: `L`/`R` in `en`, uncertain; `G`/`D` in `fr`) |
| `BCP cc p` | BCP / CAT | idem | Bull cards → processing form (p = part of the MIC, 1-9) |
| `ICP cc p` | ICP / CET | idem | IBM cards → processing form |
| `BCS cc p` | BCS / CAM | idem | Bull cards → storage form |
| `ICS cc p` | ICS / CEM | idem | IBM cards → storage form |
| `PBC cc p` | PBC / TCA | idem | processing form → Bull cards |
| `PTP cc p` | PTP / BPT | idem | paper tape → processing form |
| `PPT cc p` | PPT / TBP | idem | processing form → paper tape |
| `PPR cc p` | PPR / TIP | idem | processing form → printer |
| `PTS cc p` | PTS / TVM | idem | processing form → storage form |
| `STP cc p` | STP / MVT | idem | storage form → processing form |
| `STS cc p` | STS / MVM | idem | storage form → storage form |
| `RCL cc` | RCL / RCL | idem | go to the cliché (C.C. `en`: A or blank, I or 0; `fr`: G or blank, E, S or —) |
| `END S` | END / FIN | idem | end of transcoding (C.C. `S` in `en`, `R` in `fr`) |

Clichés (`en` / `fr`): positioning AW/MA, NW/MN, AN/NA, NS/NS, BN/BN, AZ/TZ, and CE
("numeric with certification", French table only); execution TO/TU, TN/TL, IO/EU, IN/EL,
OO/SU, ON/SL, WO/KU, WN/KL, RO/RU, RN/RL, RP/RP, CQ/CQ (N ≤ 63). See
[`docs/ISA.md`](../docs/ISA.md) §3 and §7.

---

## 4. Input / output elements

*Class 3 (cards, printer) and class 4 (paper tape) · assigned to one program, no recall
chain.* [B61 table p.62-66 ; TFR p.4-5] In the French table, hoppers are `M1`/`M2`
(*magasin*, `en` `H1`/`H2`) and brushes `b2`/`b5` (`en` `RS2`/`RS5`).

### 4.1 Card reader (CARR) and card reader-punch (CARP)

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `SPR 1` / `SPR 2` | SPR / SCL | `1111` · sub-code *(U-01)* · fields | select stacker 1 / 2 after RS2 |
| `SPP 1` / `SPP 2` | SPP / SCP | idem | select stacker 1 / 2 after RS5 |
| `REA M1` | REA / LEC | idem | read from hopper 1 (C.C. uncertain) |
| `REA B1` | REA / LEC | idem | read, split track after RS5 (C.C. uncertain) |
| `PUN H1` / `H2` / `P` | PUN / PER | idem | punch from hopper 1 / 2, or without feeding a card (CARP only) |
| `CLE B2` / `H2` / `P` | CLE / API | idem | clear the track (after reading / after H2 / after punching) |
| `DMF` | DMF / DMF | idem | handling request, end of file |
| `DMI` | DMI / DMI | idem | handling request, incident |

### 4.2 Printer (PRIN)

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `SKI   n` | SKI / SDF | `1111` · sub-code *(U-01)* · X | skip *n* lines (≤ 255) on the second paper |
| `PRI   n` | PRI / IMP | idem | skip on the first paper, then print |
| `DMF` | DMF / DMF | idem | handling request, end of file |
| `DMI` | DMI / DMI | idem | handling request, incident |

### 4.3 Paper-tape reader (TAPR) and punch (TAPP)

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `REA   n` | REA / LIR (reader) | `1111` · sub-code *(U-01)* · X | read *n* catenae (reader) |
| `PUN   n` | PUN / PBA (punch) | idem | punch *n* catenae (punch) |
| `DMN` | DMN / DMN | idem | handling request, normal |
| `DMI` | DMI / DMI | idem | handling request, incident |

### 4.4 Console (DESK)

The console is addressed by the cut `DESK`; its directives are not in the B61 table. Whether
it counts as an element is discussed (U-27).

---

## 5. Auxiliary memories

*Class 2.* The drum is shared (recall chain); tape units are assigned to one program.
[B61 table p.62-66 ; TFR p.5]

### 5.1 Drum (DRUM)

| Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|
| `DAO   a` | DAO / DAO | `1111` · sub-code *(U-01)* · X | set the origin address on the drum (track × 256 + position) |
| `TCD   n` | TCD / TRT | idem | transfer *n* catenae memory → drum |
| `TDC   n` | TDC / TTR | idem | transfer *n* catenae drum → memory |

`TRT` (*transfert mémoire rapide → tambour*) and `TTR` (*tambour → mémoire rapide*) [TFR p.5].

### 5.2 Magnetic tape (MATA, uniselector)

| Group | Code B (`en`) | `en` / `fr` | Code A | Effect |
|---|---|---|---|---|
| Preparatory | `WRI   u` | WRI / ECR | `1111` · sub-code *(U-01)* · X | write on tape unit *u* |
| Preparatory | `REF   u` | REF / LAV | idem | read forward |
| Preparatory | `REB   u` | REB / LAR | idem | read backward |
| Execution | `TRA` | TRA / TRA | idem | read with transfer |
| Execution | `JUM` | JUM / SAU | idem | read without transfer (skip a block) |
| Execution | `DEL` | DEL / EFF | idem | erase |
| Execution | `WRM` | WRM / ECM | idem | write a block mark |
| Service | `SPO   u` | SPO / REB | idem | rewind |
| Service | `SPN   u` | SPN / REM | idem | rewind and request handling |
| Service | `MAI   u` | MAI / MAI | idem | handling request, incident |
| Service | `MAN   u` | MAN / MAN | idem | handling request, normal |

Beware: `REB` means *read backward* in `en` but *rebobinage* (rewind) in `fr`.

---

## 6. Example

Read a tape block into a buffer protected by a lock, in `en` (from
[`tests/programs/lecture_bande.g60b`](../tests/programs/lecture_bande.g60b)):

```
T.O.  C.C.  X       A.F.
PROT        IMAGE          take the lock
(blank)
MATA        1              cut on tape uniselector 1        (fr: DERU)
(blank)
REF         3              preparatory: read forward, unit 3 (fr: LAV)
L     0     TAMPON         CAR 0 ← buffer address           (fr: G)
TRA                        read one block with transfer
LIBE        IMAGE          release the lock
(blank)
STOP
```

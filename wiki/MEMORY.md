# Central memory

The Gamma 60 has one **central store** (*mémoire centrale*, also called *mémoire rapide*, MR)
shared by every unit of the machine. Instructions and data live side by side in it. This page
describes how the store is built and what a word of it, a **catena**, can hold.

> This wiki is an English presentation derived from the reference specification, written in
> French: [`docs/MACHINE.md`](../docs/MACHINE.md) §2-4, §5.1 and §9 for this page. In case of
> disagreement, `docs/` prevails.

Source keys in square brackets (B61, COURS, ONDE…) are defined in
[`docs/SOURCES.md`](../docs/SOURCES.md); page numbers are the printed ones. Where the 1958-59 course
(COURS) and the 1961 brochure (B61) disagree, both values are given (machine profiles, see
[`data/profiles.yaml`](../data/profiles.yaml)).

Code B exists in two languages, a translation of the same machine: `en` (B61) and `fr`
(COURS). Localized items such as mnemonics are written **`en` / `fr`**, e.g. `L` / `G` for
"load". The full table is [`data/directives.yaml`](../data/directives.yaml).

---

## 1. Physical implementation

### Ferrite-core blocks
- The store is made of **ferrite cores**, selected by the **half-current** (coincident-current)
  method. [ONDE]
- Cores are grouped in **blocks**. A block is **24 stacked planes of 64 × 64 cores**, i.e.
  4,096 cores per plane. Seen the other way round, a block is **4,096 columns of 24 cores**:
  each column holds one 24-bit word, the catena. [B61 p.10]
- Each column also carries **3 check-key bits**, so a stored catena is 27 bits wide
  (24 + 3). [B61 p.26 ; ONDE]
- A store has **2 to 8 blocks** [B61 p.10 ; ONDE], or 1 to 8 according to the earlier
  documents [COURS ; BPD].
- Reading is **destructive** and is followed by a rewrite; each core is threaded by 4 wires;
  the address register has 17 flip-flops; the current generators use vacuum tubes. [ONDE]
- The store was designed by J. Chopin and H. Badoc (1958-59); a full 32K-catena store
  measured about 3.2 × 2.2 × 0.8 m and drew 7.5 kVA. [FEB]

### Capacity
Addresses run from **0 to 32,767** (15 bits), one address per catena. [B61 p.10]

| Blocks | Catenae | Bits | Decimal digits (6 per catena) | Characters (4 per catena) |
|---|---|---|---|---|
| 2 | 8,192 | 196,608 | 49,152 | 32,768 |
| 4 | 16,384 | 393,216 | 98,304 | 65,536 |
| 8 | 32,768 | 786,432 | 196,608 | 131,072 |

Catena counts from [B61 p.11]; the other columns are computed from them (the OCR of the
printed table is partly unreadable).

### Timing and access
- **One catena** goes in or out of the store **per memory cycle**, for the whole machine;
  there is no parallel access. [B61 p.11]
- Memory cycle: **10 µs** [B61 ; ONDE] or **11 µs** [COURS ; BPD]. Access time equals the
  cycle time, for any address. [B61 p.11] (profile parameter `memory_cycle_us`)
- Every catena passes through a single **register Z** on its way in or out. [COURS p.5 ;
  ONDE p.21]
- Units never talk to each other directly: the store is the "meeting place", and every
  transfer goes through the Data Distributor (DT), one catena per cycle. [B61 p.20-24]

### Check key
The 3 extra bits hold a check key computed on the 24 data bits. The rule depends on the
machine profile (`check_key` in `data/profiles.yaml`):

| Profile | Key | Source |
|---|---|---|
| B61 | 1 parity bit over bits 16-24, plus 2 bits = remainder mod 3 of bits 1-15 read as an integer. The split matches the instruction layout (§3). | [B61 p.26] |
| COURS | remainder of the 24-bit number divided by 7 (also used for partial 15- or 9-bit transfers) | [COURS p.11-12] |

---

## 2. Logical content: the catena

A **catena** (plural *catenae*) is the 24-bit word of the Gamma 60 and the unit of every
transfer. Bits are numbered **1 (rightmost, least significant) to 24 (leftmost, most
significant)**. [B61 p.15, p.26]

The same address may hold an instruction at one moment and data at another: nothing in the
catena says what it is. [B61 p.10]

A catena can hold [B61 p.15-17]:

| Content | Layout |
|---|---|
| **Instruction** (code A) | one catena per instruction (§3) |
| **Decimal digits** | 6 digits in BCD (§2.1) |
| **Alphanumeric characters** | 4 characters of 6 bits (§2.2) |
| **Pure binary number** | positive integer of 24 bits |
| **Qualitative / geographical catena** | 24 independent flags |
| **Half of an arithmetic number** | sign, exponent and 10-digit mantissa over 2 catenae (§2.3) |

### 2.1 Decimal digits (BCD)
Each decimal digit is coded on 4 bits (**binary-coded decimal**), so a catena holds
**6 digits**. B61 example: `1001 1000 0110 0000 0010 0011` = 986023. [B61 p.15]

### 2.2 Alphanumeric characters (internal code)
Each character is coded on **6 bits**, so a catena holds **4 characters**. Example from B61:
`000010 010101 001100 001100` = `BULL`. [B61 p.17]

- 64 codes: **60 characters** (26 letters, 10 digits, 23 signs, space) and 4 unused codes.
- A code is **2 high bits (column) + 4 low bits (row)**.
- Digits are their BCD value with `10` in front: `7` = `10 0111`.
- Read as numbers 0-63, letters come before digits, which gives the usual sort order.

The table below is generated from [`data/charset.yaml`](../data/charset.yaml) [B61 p.16].
In parentheses: the **punched-card code** for that character (card rows, at most 3 holes per
column). For letters and digits it is the standard Bull code, except that the letters O and I
have their own codes, distinct from the digits 0 and 1. [B61 p.17]

| Low 4 bits | High bits `00` | High bits `01` | High bits `10` | High bits `11` |
|---|---|---|---|---|
| `0000` | space (none) | `P` (8-4) | `0` (0) | `Δ` (9-7-0) |
| `0001` | `A` (7-11) | `Q` (8-5) | `1` (1) | `:` (9-7-1) |
| `0010` | `B` (7-0) | `R` (8-6) | `2` (2) | `'` (9-7-2) |
| `0011` | `C` (7-1) | `S` (9-11) | `3` (3) | `×` (9-7-3) |
| `0100` | `D` (7-2) | `T` (9-0) | `4` (4) | `%` (9-7-4) |
| `0101` | `E` (7-3) | `U` (9-1) | `5` (5) | `<` (9-7-5) |
| `0110` | `F` (7-4) | `V` (9-2) | `6` (6) | `>` (9-7-6) |
| `0111` | `G` (7-5) | `W` (9-3) | `7` (7) | `/` (9-7) |
| `1000` | `H` (7-6) | `X` (9-4) | `8` (8) | `(` (9-8-0) |
| `1001` | `I` (8-12) | `Y` (9-5) | `9` (9) | `)` (9-8-1) |
| `1010` | `J` (8-11) | `Z` (9-6) | `*` (12) | `−` (9-8-2) |
| `1011` | `K` (8-0) | `.` (11) | `,` (9-8-11) | `+` (9-8-3) |
| `1100` | `L` (8-1) | *unused* | `◊` (9-12) | `≠` (9-8-4) |
| `1101` | `M` (8-2) | *unused* | `-` (9-8) | `Π` (9-8-5) |
| `1110` | `N` (8-3) | *unused* | `£` (9-7-11) | `Σ` (9-8-6) |
| `1111` | `O` (7-12) | *unused* | `$` (9-7-12) | `□` (9-8-12) |

Three glyphs are blurred on the scan and are read as probable: `*` (`101010`), the short
dash `-` (`101101`, hyphen) and the long dash `−` (`111010`, minus sign) (U-22).

### 2.3 Arithmetic numbers ("semi-logarithmic" form)
The arithmetic unit (ARIT) works only on numbers in **semi-logarithmic** form, i.e. decimal
floating point. A number takes **two consecutive catenae**. [B61 p.17-18 ; COURS p.61-72]

**Layout** [B61 p.18]:

```
            1st catena                                   2nd catena
 bit 24  23-21   20-17   16-13 12-9  8-5   4-1   |  24-21 20-17 16-13 12-9  8-5   4-1
 ┌────┬───────┬───────┬─────┬─────┬─────┬─────┐  ┌─────┬─────┬─────┬─────┬─────┬─────┐
 │sign│ exp.  │ exp.  │ m1  │ m2  │ m3  │ m4  │  │ m5  │ m6  │ m7  │ m8  │ m9  │ m10 │
 │    │ tens  │ units │     │     │     │     │  │     │     │     │     │     │     │
 └────┴───────┴───────┴─────┴─────┴─────┴─────┘  └─────┴─────┴─────┴─────┴─────┴─────┘
  1 b    3 b     4 b    ←──────────── 10-digit mantissa, BCD ─────────────→
```

- **Sign**: bit 24 of the first catena, **0 = +, 1 = −** (sign and magnitude). [B61 p.18]
- **Exponent**: two decimal digits. The tens digit (0-7) is in binary on bits 23-21, the
  units digit (0-9) in BCD on bits 20-17. The stored exponent **E** therefore runs from
  00 to 79. [B61 p.18]
- **Bias of 40**: 40 is added to the true exponent so that no negative exponent is ever
  stored. True exponent = **E − 40**. [B61 p.18]
- **Mantissa**: 10 BCD digits m1…m10 (4 in the first catena, 6 in the second), read as a
  fraction **0.m1m2…m10**: the decimal point is just to the left of m1. [B61 p.17-18]

**Value** = (−1)^sign × 0.m1m2…m10 × 10^(E − 40)

**Two ways to use the same format** [B61 p.18 ; COURS p.67-68], chosen by the first
complementary code (C.C.1) of each ARIT directive:

| Mode | Rule | C.C.1 (`en` / `fr`) |
|---|---|---|
| **Floating point** (normalized) | exponent chosen so that 0.1 ≤ mantissa < 1 (m1 ≠ 0): best relative precision; ARIT normalizes automatically | `N` / `N`; with rounding `R` / `A` (`R` assumed, U-05) |
| **Fixed point** (*virgule programmée*) | the decimal point stays at the same place for results of the same kind, as in accounting | `P` / `P` |

In fixed point the exponent is always **between 40 and 50**. The number of decimals is
**50 − E**, which B61 calls the "position of the decimal point", from 10 (point before m1,
E = 40) down to 0 (point after m10, E = 50). The `dp` field of an ARIT directive gives this
position for the result. [B61 p.18 ; ISA.md §3]

**Examples** [B61 p.18]:

| Number | 1st catena | 2nd catena | Comment |
|---|---|---|---|
| + 0.00482 | `+ 39 0482` | `000000` | E = 39 → 0.0482 × 10⁻¹; mantissa not normalized |
| + 325.42 | `+ 43 3254` | `200000` | floating point: 0.32542 × 10³ |
| + 4832 | `+ 50 0000` | `004832` | fixed point, decimal point in position 0 |
| + 4832 | `+ 45 0483` | `200000` | fixed point, decimal point in position 5 (4832.00000) |

Bit pattern of the first example: `0 011 1001 0000 0100 1000 0010` / `0000 0000 0000 0000 0000 0000`.

**Range** (derived from the format, not stated in the sources): normalized magnitudes from
0.1 × 10⁻⁴⁰ = 10⁻⁴¹ up to just under 10³⁹; 10 significant digits.

**In the arithmetic unit**, registers P (main), S (secondary) and O hold 2 catenae each. P and
S together form a 20-digit accumulator; the exponent of the number in S is 10 lower than that
of P. Results can be stored in single length (P) or double length (P + S, 4 catenae, C.C.2 =
`D`). ARIT checks its results with a remainder mod 7 ("casting out sevens"). [B61 p.35-36 ;
COURS p.61-72]

### 2.4 Qualitative and geographical catenae
The 24 bits can be read as 24 independent flags. A **geographical catena** describes the
structure of a set of data. A **qualitative catena** records the results of an operation:
each element has one, and the Program Distributor copies it into register A, where
conditional branches test it bit by bit. [B61 p.17, p.23] The meaning of each bit per
element is in [`data/qualitative.yaml`](../data/qualitative.yaml).

---

## 3. Instructions in memory

An instruction (**code A**) is **one catena**. A program is a series of instructions at
consecutive addresses. [B61 p.15] The catena splits into two parts [B61 p.15]:

- **bits 24-16** (9 bits): the type of instruction and its conditions;
- **bits 15-1** (15 bits): an operand, i.e. an address (0-32,767), a length, an element
  number or a binary value.

The type is given by a **prefix code (TK)** read from the left [COURS p.33-52]:

| TK | Category | Role, in one line |
|---|---|---|
| `00` | **Branch** | jump never / always / if bit n of register A is 1 |
| `01` | **Cut** (*coupure*) | hand the sequence over to an element (`ARIT`, `DRUM` / `TAMB`…), fork (`SIMU`), join, stop (`STOP`) |
| `10` | **Central directive** | executed by the Program Distributor itself (registers A and B, counters, switches) |
| `110` | **Address instruction** | load or update a current-address register of the element: load `L` / `G`, place `P` / `R`, add `A` / `A`, subtract `S` / `S` |
| `1111` | **Element directive** | operation carried out by the element (`ADD` / `ADD`, `SUB` / `SOU`, `OWC` / `CMP`, `TDC` / `TTR`…) |
| `1110` | undocumented | — (U-24) |

Bits 17 and 16 carry the **address function**: bit 17 = differential (relative) address,
bit 16 = substitution (indirect address). [B61 p.29 ; COURS p.44-49] A catena whose 7
leftmost bits are 0, for instance a blank catena, executes as a **"never" branch**,
i.e. it does nothing. [COURS p.42]

The binary values of most sub-codes are not known and are reconstructed (U-01,
[`data/encoding.yaml`](../data/encoding.yaml)). Each category is described in detail in
**[INSTRUCTIONS.md](INSTRUCTIONS.md)**; see also [`docs/ISA.md`](../docs/ISA.md).

---

## 4. Memory layout

The central store holds much more than one program and its data. Because the elements share
it and never talk to each other, it is also where the **control information** of the machine
lives: queue links, lock images, buffers for input/output. [`docs/MACHINE.md`](../docs/MACHINE.md) §5.1, §9.

### 4.1 What lives in the store, and what does not

| In the central store | Placed by | Source |
|---|---|---|
| **Resident supervisor GGZ** (tables, operator dialogue, loading, buffers, incident handling) | system, at the **start** of memory | [MAI] |
| **I1 / I2 of every real element** (called B / C in COURS): head and tail of its recall chain | system, at "specialised addresses" (exact addresses unknown, U-30) | [ONDE §2 ; COURS p.24-31] |
| **Programs** (UT), with a **blank catena** after every cut, used at run time as queue link or join counter | loader; relative addresses (`R`) make code relocatable | [COURS p.24-31, p.47-49] |
| **Virtual element images**: 2 catenae per lock (busy bit + head, tail) | programmer, anywhere (COURS uses 1,000 and 1,001) | [COURS p.27-31] |
| **Working memories** (*mémoires de manœuvre*, A.F. `M`) | placed at the **end of the subprogram** | [COURS p.47-49] |
| **I/O zones**: each card, tape or printer operation needs its own memory zone, protected by a virtual element | program / supervisor | [AVG p.59 ; B61 p.42] |
| Data: numbers (2 catenae each), alphanumeric text (4 characters per catena), tables | program | §2 |

| **Not** in the store | Where |
|---|---|
| RAI (next instruction of each element, with its busy bit) and RAC (current data addresses) | register matrices of the central unit [B61 p.22-23 ; COURS p.14] |
| Registers A (analysis) and B (operator), registers of the Program Distributor | central unit [COURS p.14 ; B61 p.23] |
| Drum and tape contents | the peripheral itself; copied in and out by transfer directives |

### 4.2 A typical map

Illustrative only: the sources give the order of the parts (supervisor first, working memories
after the code), not their sizes or addresses. Addresses below are **our assumption**.

```
address  0 ┌──────────────────────────────────────────────┐
           │ GGZ resident supervisor (tables, buffers…)   │  [MAI]
           │ I1/I2 of each real element (2 catenae each)  │  U-30: "specialised addresses"
           ├──────────────────────────────────────────────┤
           │ UT 1: code (cuts + blank catenae)            │
           │       working memories (end of subprogram)   │
           │       lock images, I/O zones, data           │
           ├──────────────────────────────────────────────┤
           │ UT 2: …                                      │
           ├──────────────────────────────────────────────┤
           │ free                                         │
  32,767   └──────────────────────────────────────────────┘
```

Several programs (UT) share the store at once: this is what multiprogramming means here. A
program can be launched only if the elements **and the memory zone** it needs are free. [B61
p.47-48]

### 4.3 Examples

The three programs below are test programs of this project
([`tests/programs/`](../tests/programs/)). They are loaded at an **arbitrary base address**
(4000, 5000, 6000); line *n* is at base + *n*.

**a) Fork / join with data after the code** ([`forkjoin_tumlin.g60b`](../tests/programs/forkjoin_tumlin.g60b),
from [TS]: `a = b×c ; d = d+e ; f = a×d`)

| Address | Contents | Role |
|---|---|---|
| 4000-4001 | `SIMU I2` + blank | fork; the blank links the continuation in the DP's own chain |
| 4002-4008 | `ARIT` + blank, 3 × `L`, `MUL`, branch | branch I1: a = b × c |
| 4009-4015 | `ARIT` + blank, 3 × `L`, `ADD`, branch | branch I2: d = d + e (waits in ARIT's recall chain if I1 holds ARIT) |
| 4016-4022 | `ARIT 1` + blank, 3 × `L`, `MUL`, `STOP` | join; the blank is the **join counter** |
| 4023-4034 | b, c, d, e, a, f | 6 numbers × 2 catenae (semi-logarithmic) |

Only ARIT is used, so the two branches do not really overlap: the second waits in ARIT's queue,
whose head and tail are ARIT's I1/I2 (system area) and whose link is the blank at 4010.

**b) Tape read into a protected buffer** ([`lecture_bande.g60b`](../tests/programs/lecture_bande.g60b))

| Address | Contents | Role |
|---|---|---|
| 5000-5001 | `PROT IMAGE` + blank | take the lock on the buffer |
| 5002-5003 | `MATA 1` / `DERU 1` + blank | cut on tape uniselector 1 |
| 5004-5006 | `REF 3` / `LAV 3`, `L 0 TAMPON` / `G 0 TAMPON`, `TRA` | read one block from tape unit 3 into the buffer |
| 5007-5009 | `LIBE IMAGE` + blank, `STOP` | release the lock, end |
| 5010-5011 | IMAGE | virtual element: busy bit + head, tail (initialised to 0) |
| 5012-5139 | TAMPON | 128-catena I/O zone |

**c) Working memories** ([`namip_classement.g60b`](../tests/programs/namip_classement.g60b),
from [NAM], language `fr`)

The program sorts C against A and B, then adds them. All its operands are **working memories**
(A.F. `M`), numbered from the end of the code: M0-3 = C, M4-5 = running total, M6-9, M10-13,
M14-17 = the three positions. An operand written `G 1 6 M` ("load CAR1 with working memory 6")
becomes, after assembly, an offset from the current line (differential address, bit 17).
[COURS p.47-49]

| Address | Contents |
|---|---|
| 6020-6053 | code (lines 020-053 transcribed; 019 and the end are missing): `COMP` + blank, comparisons (`CDB`), copies (`TRR`), `ARIT` + blank, additions |
| 6054-6071 | working memories M0-M17 |

---

See also [ARCHITECTURE.md](ARCHITECTURE.md) and [CONCURRENCY.md](CONCURRENCY.md) (how the blank catenae hold queue links and join counters).

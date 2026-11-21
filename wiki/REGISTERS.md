# Registers

The Gamma 60 has few programmer-visible registers, and most of them are not where a modern
reader expects. The **central unit** holds two working registers (A and B), the registers of
the **Program Distributor**, and two core matrices with the **instruction address** and the
**data addresses of every element**. Each **element** has its own buffer and qualitative
registers, plus the registers it computes with. Some "registers" are not registers at all but
**catenae in central memory** at agreed addresses.

> This wiki is an English presentation derived from the reference specification, written in
> French: [`docs/MACHINE.md`](../docs/MACHINE.md) §5.1 for this page. In case of disagreement,
> `docs/` prevails. The machine-readable list, used by the emulator, is
> [`data/registers.yaml`](../data/registers.yaml); the identifiers in the last column of each
> table are its `id`s.

Source keys in square brackets (B61, COURS, ONDE…) are defined in
[`docs/SOURCES.md`](../docs/SOURCES.md); page numbers are the printed ones. Abbreviations are
expanded in [`docs/GLOSSARY.md`](../docs/GLOSSARY.md).

Sizes are in bits. A catena is 24 bits of data plus 3 bits of check key. A size marked *(hyp.)*
is not given by the sources: it is an assumption of the emulator, listed in
[`docs/UNKNOWNS.md`](../docs/UNKNOWNS.md) (U-39 unless stated otherwise).

## Naming convention

Each register has a **display name** in each language of the emulator, used by traces and the
debugger (`--names en` or `--names fr`). The case of the display name tells where it comes from:

- **UPPER CASE**: a name **attested** by a source in that language. English: the 1961 brochure
  (B61) or Bataille (BAT72); French: the programming course (COURS), ONDE or the French tables
  (TFR).
- **lower case**: the **initials of the expanded name, proposed by the emulator, not
  validated**. The expanded English name is then a translation, marked *(emulator)*.

So `IAR` (B61) and `RAI` (COURS) are period names, while `cpar` is the emulator's English name
for the French `RAPA` (*current program address register*: it holds the IAR of the element
being served, the "PAR" of BAT72). `z` is lower case in English because no English source names
the Z register. A register with several copies is numbered on display (`pdc1`, `pdc2`, `CAR0` to
`CAR3`).

---

## 1. Central unit

| Display `en` / `fr` | Expanded name `en` / `fr` | Size | Role | Where | Source | `id` |
|---|---|---|---|---|---|---|
| `z` / `Z` | *store register (emulator)* / registre Z | 31 (24 + 3 key + 4 selection check) | Every catena read from or written to memory passes through it, on its way to or from the channels. | central unit | COURS p.5; ONDE §2.2.2.3 p.20-21 | `z` |
| `A` / `A` | analysis register / registre d'analyse | 24 | Receives the qualitative catena of the element being served; tested by the branch instructions 01-24. | central unit | B61 p.23, p.31; COURS p.54 | `a` |
| `B` / `B` | operator register / registre opérateur | 24 | Small computations on its 15 right-hand bits (address arithmetic, counters). | central unit | B61 p.32; COURS p.55 | `b` |
| `IAR` / `RAI` | Instruction Address Register / Registre d'Adresse Instruction | 128 × 21 (15 address + 2 key + 2 busy + 2 selection) | Next instruction of each element, with its **busy indicator** (idle / active), duplicated for checking. PAR in BAT72. | matrix MAP | B61 p.22; COURS p.8, p.14; ONDE §2.2.1 p.16 | `rai` |
| `CAR` / `RAC` | Current Address Register / Registre d'Adresse Courante | 128 × 19 (15 address + 2 key + 2 selection) | Current data address of an element; +1 (or −1) at each transfer. 1 to 4 per element. Also D.A.R. (B61 p.22) and DAR (BAT72). | matrix MAQ | B61 p.22-23; COURS p.8, p.14; ONDE §2.2.1 p.16 | `rac` |

The address registers are not in the elements: they sit in two **ferrite-core matrices** of the
central unit, MAP (program addresses) and MAQ (data addresses), with 128 registers each.
[ONDE §2.2.1 p.16] An element number therefore selects one IAR and up to four CARs.

## 2. Program Distributor

| Display `en` / `fr` | Expanded name `en` / `fr` | Size | Role | Source | `id` |
|---|---|---|---|---|---|
| `enr` / `RNE` | *element number register (emulator)* / Registre Numéro d'Élément | 7 [p.53]; 15 on p.14 (U-23) | Number of the element being served; selects its IAR and CARs. | COURS p.13-14, p.53 | `rne` |
| `cpar` / `RAPA` | *current program address register (emulator)* / Registre Adresse de Programme Actuel | 15 | Address of the current instruction, read through a transfer request to the Data Distributor. | COURS p.14 | `rapa` |
| `ipar` / `RAPP` | *incremented program address register (emulator)* / Registre Adresse de Programme Progressé | 15 | RAPA + 1; copied into RAPA for the next instruction, or into the IAR after the directive that starts the element. | COURS p.14-15 | `rapp` |
| `pdir` / `REDP` | *program distributor input register (emulator)* / Registre d'Entrée du Distributeur de Programme | 24 | Receives each instruction read. | COURS p.14 | `redp` |
| `pdor` / `RSDP` | *program distributor output register (emulator)* / Registre de Sortie du Distributeur de Programme | 24 | Output of the distributor; receives RAPP at each branch (return address). | COURS p.14-15, p.42, p.54 | `rsdp` |
| `srr` / `rmr` | *SIMU reserve register (emulator)* / registre spécial de mise en réserve | 15 *(hyp.)* | Holds RAPP (the ordinary branch) while the distributor runs the extraordinary branch of a SIMU. | COURS p.17 | `simu_reserve` |
| `pdc` / `cdp` (×2) | *program distributor chain (emulator)* / chaîne propre du DP | 2 × 15 *(hyp.)* | Head and tail of the sequences waiting for the distributor itself (SIMU, LIBE). Its link with the reserve register is not stated (U-39). | COURS p.36-38 | `pd_chain` |

**One instruction, step by step** [COURS p.14-15]: the number of the element being served goes
into RNE; its IAR is copied into RAPA (through the MAP matrix and register Z); RAPP = RAPA + 1;
the distributor asks the Data Distributor for the catena at address RAPA, which arrives in
REDP; it executes it (loads a CAR, sends a directive through RSDP, stores into memory through
RSDP, or handles a cut or a branch); then RAPA ← RAPP, and so on until the directive that starts
the element: then IAR ← RAPP and RNE is cleared. A branch forces RAPA to the given address and
sends RAPP into RSDP. [COURS p.15-16]

## 3. Registers of every element

| Display `en` / `fr` | Expanded name `en` / `fr` | Size | Role | Where | Source | `id` |
|---|---|---|---|---|---|---|
| `i1`, `i2` / `B`, `C` | temporary storage registers (B61 p.24) / registres de chaîne de reprise (I1, I2 in ONDE) | 2 × 15 *(hyp.)* | Head and tail of the element's **recall chain** (its wait queue). | central memory, at "specialized addresses" (U-30) | B61 p.24-25; COURS p.24-31; ONDE §2 | `chain_head_tail` |
| `br` / `RLN` | buffer register / Registre de Liaison | 24 | One-catena buffer between the memory cycle (10 or 11 µs) and the element's own speed. | element | B61 p.23; COURS p.8 | `rln` |
| `qcr` / `rcq` | *qualitative catena register (emulator)* / registre catène qualitatif | 24 | The element's indicators; sent to register A when the distributor serves the element. | element | B61 p.23; COURS p.74, p.110 | `qualitative` |

## 4. Registers of particular elements

| Element | Display `en` / `fr` | Expanded name `en` / `fr` | Size | Role | Source | `id` |
|---|---|---|---|---|---|---|
| ARIT | `P` / `P` | principal / principal | 2 catenae | First operand, then result (high digits). P + S form the accumulator. | B61 p.35; COURS p.65 | `arit_p` |
| ARIT | `S` / `S` | secondary / secondaire | 2 catenae | Low digits; same sign as P, exponent of P − 10. | B61 p.35; COURS p.65 | `arit_s` |
| ARIT | `O` / `O` | operand / opérande | 2 catenae | Second operand. | B61 p.35; COURS p.65 | `arit_o` |
| LOGI | `K` / `K` | K register | 24 | Shift register, serial access: first operand (filter, multiplicand, divisor). | B61 p.39; COURS p.110 | `logi_k` |
| LOGI | `L` / `L` | L register | 24 | Shift register, serial access: receives the result. | B61 p.39; COURS p.110 | `logi_l` |
| COMP | `or` / `ro` (×2) | *operand registers (emulator)* / registres opérandes | 2 × 24 | Operand of CAR 0; operand of CAR 1 or 2 (alternately, for a two-limit comparison). | COURS p.75 | `comp_operand` |
| COMP | `lr` / `rl` | *length register (emulator)* / registre longueur | 8 | Zone length in catenae (≤ 255), counted down at each catena. | COURS p.75 | `comp_length` |
| TRAN | `ir` / `re` | *input register (emulator)* / registre d'entrée | 24 | Data to translate, read character by character (unused for cards). | COURS p.86 | `tran_input` |
| TRAN | `or` / `S` | *output register (emulator)* / registre de sortie | 24 | Result, built character by character (unused for cards). | COURS p.86, p.89 | `tran_output` |
| TRAN | `cr` / `C` | *cliché register (emulator)* / registre cliché | 24 | The translation pattern (*cliché*), delivered code by code. | COURS p.86, p.89 | `tran_cliche` |
| TRAN | `dqr` / `rdq` | *directive and qualitative register (emulator)* / registre directive et catène qualitatif | 24 *(hyp.)* | Receives the directives; the qualitative catena is built in it. | COURS p.87 | `tran_directive` |
| TRAN | `ii`, `oi` / `ie`, `is` | *input and output indexes (emulator)* / index des registres d'entrée et de sortie | 2 × 5 *(hyp.)* | Current position in the input and output registers. | COURS p.89, p.108 | `tran_index` |
| TRAN | `cdr` / `rd` | *count-down register (emulator)* / registre de décomptage | 15 *(hyp.)* | Counts the zone down; reaching 0 ends the operation. | COURS p.108-109 | `tran_countdown` |
| TRAN | `tm` / `mt` | *transposition matrix (emulator)* / matrice de transposition | 12 × 24 = 288 | Row-to-column transposition of punched cards. | COURS p.87; ONDE §3.2 | `tran_transposition` |
| TRAN | `MIC` / `MIC` | M.I.C. (not expanded by B61) / Matrice d'Interprétation des Codes | 128 × 20 [COURS] / 256 entries [B61] / 128 × 21 [ONDE] (U-12) | Code interpretation matrix, loaded by program (Bull, IBM, internal codes…). | COURS p.87; B61 p.38, p.64; ONDE §3.2 | `tran_mic` |
| TRAN | `rd` / `dr` | *resume datum (emulator)* / datum de reprise | 4 catenae | Saves the input and output registers and their indexes, in central memory (1m-4m). | COURS p.108 | `tran_resume_datum` |
| Drum | `ear` / `RAE` | *element address register (emulator)* / Registre Adresse dans l'Élément | 15 *(hyp.)* | Drum address (track × 256 + position), set by the DAO directive; advances with the CAR. | B61 p.53; COURS p.153 | `drum_rae` |
| Uniselector | `blr` / `rlb` | *block length register (emulator)* / registre de longueur de bloc | 24 *(hyp.)* | Receives the length catena at the head of a tape block and checks the reading. | COURS p.141 | `uniselector_block_length` |
| Printer | `lm` / `ml` | *line memory (emulator)* / mémoire d'une ligne | one line of 120 characters | Core memory of one print line; checks the hammers by echo. | ONDE §2 p.10 | `printer_line_memory` |
| Printer | `lsc` / `ci` (×2) | *line-spacing counters (emulator)* / compteurs d'interlignes | 2 × 8 | One per paper feed; loaded by SDF and IMP, counted down during the skip (≤ 255 lines). | COURS p.134; ONDE §2.5.3 p.27 | `printer_spacing_counters` |

## 5. Current address registers per element

Each element type has a fixed number of CARs, taken from the MAQ matrix:

| Element | CARs | Use | Source |
|---|---|---|---|
| ARIT, LOGI | 4 | General-purpose, numbered 0-3. | B61 p.35; COURS p.110 |
| COMP | 3 | 0 = variable or first term; 1 and 2 = limits or second term. | B61 p.36-37; COURS p.75 |
| TRAN | 3 | 0 = source, 1 = destination, 2 = cliché. | COURS p.88-89 |
| Drum | 1 | Central-memory side of the transfer (the drum side is the RAE). | COURS p.153 |
| Uniselector | 1 (2 in continuous mode) | In continuous mode the uniselector is seen as a **double element**, with 2 IARs and 2 CARs. | COURS p.141, p.148 |
| Card reader-punch | 2 | 0 = read result or card to punch; 1 = data to compare with the check reading. | COURS p.125 |
| Printer | 1 | Line to print. | COURS p.134 |
| Card reader, paper tape, desk | 1 *(hyp.)* | Not found in the sources. | U-39 |

The maximum configuration of the emulator ([`data/configs/max.yaml`](../data/configs/max.yaml):
one of each processing element, 4 drums, 10 uniselectors, 8 printers, 8 card units, 8
paper-tape units and the desk) needs 57 CARs, well within the 128 of the matrix.

---

See also [ARCHITECTURE.md](ARCHITECTURE.md) (the elements and the distributors),
[MEMORY.md](MEMORY.md) (what sits in central memory) and [CONCURRENCY.md](CONCURRENCY.md)
(how B / C, the recall chain registers, queue the waiting sequences).

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
[`docs/SOURCES.md`](../docs/SOURCES.md); page numbers are the printed ones. Names are given as
**`en` / `fr`**: `en` is the 1961 brochure (B61) or Bataille (BAT72), `fr` the programming
course (COURS). "—" means the English sources do not name the register. Abbreviations are
expanded in [`docs/GLOSSARY.md`](../docs/GLOSSARY.md).

Sizes are in bits. A catena is 24 bits of data plus 3 bits of check key. A size marked *(hyp.)*
is not given by the sources: it is an assumption of the emulator, listed in
[`docs/UNKNOWNS.md`](../docs/UNKNOWNS.md) (U-39 unless stated otherwise).

---

## 1. Central unit

| Name `en` / `fr` | Size | Role | Where | Source | `id` |
|---|---|---|---|---|---|
| — / Z | 31 (24 + 3 key + 4 selection check) | Every catena read from or written to memory passes through it, on its way to or from the channels. | central unit | COURS p.5; ONDE §2.2.2.3 p.20-21 | `z` |
| A / A | 24 | **Analysis** register: receives the qualitative catena of the element being served; tested by the branch instructions 01-24. | central unit | B61 p.23, p.31; COURS p.54 | `a` |
| B / B | 24 | **Operator** register: small computations on its 15 right-hand bits (address arithmetic, counters). | central unit | B61 p.32; COURS p.55 | `b` |
| IAR / RAI | 128 × 21 (15 address + 2 key + 2 busy + 2 selection) | Next instruction of each element, with its **busy indicator** (idle / active), duplicated for checking. | matrix MAP | B61 p.22; COURS p.8, p.14; ONDE §2.2.1 p.16 | `rai` |
| DAR / RAC | 128 × 19 (15 address + 2 key + 2 selection) | Current data address of an element; +1 (or −1) at each transfer. 1 to 4 per element. | matrix MAQ | B61 p.22-23; COURS p.8, p.14; ONDE §2.2.1 p.16 | `rac` |

The address registers are not in the elements: they sit in two **ferrite-core matrices** of the
central unit, MAP (program addresses) and MAQ (data addresses), with 128 registers each.
[ONDE §2.2.1 p.16] An element number (7 bits) therefore selects one IAR and up to four DARs.
The register is called CAR (*current address register*) in B61, DAR in BAT72.

## 2. Program Distributor

| Name `en` / `fr` | Size | Role | Source | `id` |
|---|---|---|---|---|
| — / RNE | 7 (15 on one page, U-23) | Number of the element being served; selects its IAR and DARs. | COURS p.14, p.53 | `rne` |
| — / RAPA | 15 | Address of the instruction being read. | COURS p.14 | `rapa` |
| — / RAPP | 15 | RAPA + 1; copied into the IAR after a directive. | COURS p.14-15 | `rapp` |
| — / REDP | 24 | Receives each instruction read. | COURS p.14 | `redp` |
| — / RSDP | 24 | Output of the distributor; receives RAPP at each branch (return address). | COURS p.15, p.42, p.54 | `rsdp` |
| — / own chain of the PD | 2 × 15 *(hyp.)* | Head and tail of the sequences waiting for the distributor itself (SIMU, LIBE). | COURS p.36-38 | `pd_chain` |

## 3. Registers of every element

| Name `en` / `fr` | Size | Role | Where | Source | `id` |
|---|---|---|---|---|---|
| I1, I2 / B, C | 2 × 15 *(hyp.)* | Head and tail of the element's **recall chain** (its wait queue). | central memory, at "specialized addresses" (U-30) | B61 p.24-25; COURS p.24-31; ONDE §2 | `chain_head_tail` |
| buffer register / RLN | 24 | One-catena buffer between the memory cycle (10 or 11 µs) and the element's own speed. | element | B61 p.23; COURS p.8 | `rln` |
| — / qualitative catena register | 24 | The element's indicators; sent to register A when the distributor serves the element. | element | B61 p.23; COURS p.74, p.110 | `qualitative` |

## 4. Registers of particular elements

| Element | Name `en` / `fr` | Size | Role | Source | `id` |
|---|---|---|---|---|---|
| ARIT | P / P | 2 catenae | **Principal**: first operand, then result (high digits). P + S form the accumulator. | B61 p.35; COURS p.65 | `arit_p` |
| ARIT | S / S | 2 catenae | **Secondary**: low digits; same sign as P, exponent of P − 10. | B61 p.35; COURS p.65 | `arit_s` |
| ARIT | O / O | 2 catenae | **Operand**: second operand. | B61 p.35; COURS p.65 | `arit_o` |
| LOGI | K / K | 24 | Shift register, serial access: first operand (filter, multiplicand, divisor). | B61 p.39; COURS p.110 | `logi_k` |
| LOGI | L / L | 24 | Shift register, serial access: receives the result. | B61 p.39; COURS p.110 | `logi_l` |
| COMP | — / operand registers | 2 × 24 | Operand of CAR 0; operand of CAR 1 or 2 (alternately, for a two-limit comparison). | COURS p.75 | `comp_operand` |
| COMP | — / length register | 8 | Zone length in catenae (≤ 255), counted down at each catena. | COURS p.75 | `comp_length` |
| TRAN | — / input register | 24 | Data to translate, read character by character (unused for cards). | COURS p.86 | `tran_input` |
| TRAN | — / output register (S) | 24 | Result, built character by character (unused for cards). | COURS p.86, p.89 | `tran_output` |
| TRAN | — / cliché register (C) | 24 | The translation pattern (*cliché*), delivered code by code. | COURS p.86, p.89 | `tran_cliche` |
| TRAN | — / directive and qualitative register | 24 *(hyp.)* | Receives the directives; the qualitative catena is built in it. | COURS p.87 | `tran_directive` |
| TRAN | — / input and output indexes | 2 × 5 *(hyp.)* | Current position in the input and output registers. | COURS p.89, p.108 | `tran_index` |
| TRAN | — / count-down register | 15 *(hyp.)* | Counts the zone down; reaching 0 ends the operation. | COURS p.108-109 | `tran_countdown` |
| TRAN | — / transposition matrix | 12 × 24 = 288 | Row-to-column transposition of punched cards. | COURS p.87; ONDE §3.2 | `tran_transposition` |
| TRAN | — / MIC | 128 × 20 [COURS] / 256 entries [B61] / 128 × 21 [ONDE] (U-12) | Code interpretation matrix, loaded by program (Bull, IBM, internal codes…). | COURS p.87; B61 p.38; ONDE §3.2 | `tran_mic` |
| TRAN | — / resume datum | 4 catenae | Saves the input and output registers and their indexes, in central memory (1m-4m). | COURS p.108 | `tran_resume_datum` |
| Drum | — / RAE | 15 *(hyp.)* | Drum address (track × 256 + position), set by the DAO directive; advances with the DAR. | B61 p.53; COURS p.153 | `drum_rae` |
| Uniselector | — / block length register | 24 *(hyp.)* | Receives the length catena at the head of a tape block and checks the reading. | COURS p.141 | `uniselector_block_length` |
| Printer | — / line memory | one line of 120 characters | Core memory of one print line; checks the hammers by echo. | ONDE §2 p.10 | `printer_line_memory` |
| Printer | — / line-spacing counters | 2 × 8 | One per paper feed; loaded by SDF and IMP, counted down during the skip (≤ 255 lines). | COURS p.134; ONDE §2.5.3 p.27 | `printer_spacing_counters` |

## 5. Data address registers per element

Each element type has a fixed number of DARs, taken from the MAQ matrix:

| Element | DARs | Use | Source |
|---|---|---|---|
| ARIT, LOGI | 4 | General-purpose, numbered 0-3. | B61 p.35; COURS p.110 |
| COMP | 3 | 0 = variable or first term; 1 and 2 = limits or second term. | B61 p.36-37; COURS p.75 |
| TRAN | 3 | 0 = source, 1 = destination, 2 = cliché. | COURS p.88-89 |
| Drum | 1 | Central-memory side of the transfer (the drum side is the RAE). | COURS p.153 |
| Uniselector | 1 (2 in continuous mode) | In continuous mode the uniselector is seen as a **double element**, with 2 IARs and 2 DARs. | COURS p.141, p.148 |
| Card reader-punch | 2 | 0 = read result or card to punch; 1 = data to compare with the check reading. | COURS p.125 |
| Printer | 1 | Line to print. | COURS p.134 |
| Card reader, paper tape, desk | 1 *(hyp.)* | Not found in the sources. | U-39 |

The maximum configuration of the emulator ([`data/configs/max.yaml`](../data/configs/max.yaml):
one of each processing element, 4 drums, 10 uniselectors, 8 printers, 8 card units, 8
paper-tape units and the desk) needs 57 DARs, well within the 128 of the matrix.

---

See also [ARCHITECTURE.md](ARCHITECTURE.md) (the elements and the distributors),
[MEMORY.md](MEMORY.md) (what sits in central memory) and [CONCURRENCY.md](CONCURRENCY.md)
(how B / C, the recall chain registers, queue the waiting sequences).

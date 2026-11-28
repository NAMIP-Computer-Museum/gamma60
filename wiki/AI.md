# AI in this project

This project is also an experiment in AI-assisted work: an AI assistant helps with reading the
sources and with writing the code, while a human directs the work and reviews it. This page
explains how the AI was used at each phase.

See also [REFERENCES.md](REFERENCES.md) and the working rules in [`CLAUDE.md`](../CLAUDE.md).

---

## 1. The assistant

| | |
|---|---|
| Assistant | **Claude**, by Anthropic |
| Model | **Claude Opus 5.5** (model id `claude-opus-5-5`) |
| Interfaces | **Claude on the web** (claude.ai) for the scanning and the document study; then **Claude Code**, Anthropic's command-line agent, working directly in the repository (it reads files, runs the tests, edits and commits) |
| Traceability | commits written with Claude Code carry the line `Co-Authored-By: Claude Opus 5.5` |

The work went through two stages:

1. **Claude on the web.** The OCR correction (§2) and the document study (§3) were carried
   out in conversations on claude.ai. It produced an **initial kit** to start the development: the first reference
   documents, the tables of `data/` and the working rules.
2. **Claude Code.** Everything after that was done in the repository with Claude Code: the
   emulator (§4), and also part of the documentation work, such as consolidating and
   reorganising `docs/` and the wiki, and adding new sources.

The human sets the goals and validates every plan before the assistant starts working. Commits
and pushes happen only on request. The rules the assistant must follow are written in
[`CLAUDE.md`](../CLAUDE.md), which it reads at the start of every session. Two of them matter
most:
- **never invent a historical fact**;
- **cite a source for every claim**.

## 2. Phase 1: scanning the documentation (OCR correction)

The primary sources are 1958-1961 Bull documents: the 1961 brochure (B61), the programming
course (COURS) and the instruction tables. They exist only as scans. This phase was carried
out with Claude on the web.

- **OCR correction.** The AI compares the OCR text with the page images and corrects it. Some
  OCR errors are documented as such: for example, "code D" in COURS and "code DB" in B61 are
  misreadings of "code B" (U-14 in [`docs/UNKNOWNS.md`](../docs/UNKNOWNS.md)).
- **Structured transcription.** The French instruction tables (TFR) are a scan with no OCR
  layer. They were transcribed into structured data
  (`archives/docs/Bull-Gamma60-Instructions-FR.yaml`) and checked against the images.
- **Unreadable passages stay unknowns.** When a passage cannot be read, it is not guessed: it
  becomes an unknown. For example, positions 2-6 of a LOGI result code are unreadable in COURS
  p.119, so they are recorded as U-38 with a stated hypothesis.

## 3. Phase 2: studying the documentation

This phase was carried out with Claude on the web. It produced the initial kit, which Claude
Code then consolidated and completed.

### 3.1 Classifying the sources by period

Each source has a key (B61, COURS, DR-E, MAIT…) and a precise reference in
[`docs/SOURCES.md`](../docs/SOURCES.md). The [references page](REFERENCES.md) sorts the
sources into three periods:

1. **Contemporary Bull publications**: the preliminary description, the Dreyfus papers of
   1958, COURS (about 1958-59), B61 (1961), *L'Onde électrique* (1960).
2. **Related work of the time**: multiprogramming, fork/join, semaphores, flowcharts (Ryle,
   Conway, Dijkstra…).
3. **Retrospective analyses**: written after the machine's working life, from Bataille (1971)
   to the FEB and NAM-IP testimonies.

The period of a source determines how much weight it carries. Two examples:
- COURS (about 1958-59) and B61 (1961) describe two states of the machine. This gives the two
  emulator profiles, *COURS* and *B61*, and the two languages of code B, `fr` and `en`.
- A later account (Maître 1997, Leclerc 1988) is treated as secondary, and its notation is not
  taken as the original one.

### 3.2 Systematic traceability

- **Text extraction.** [`tools/fetch_refs.sh`](../tools/fetch_refs.sh) extracts the text of
  the PDFs and HTML pages of `archives/docs/` into `refs/txt/`. That text is not versioned, but
  Claude Code can search it while coding. It is used for two things:
  - pulling out the technical details needed to implement the machine: code A fields, timings,
    directive semantics;
  - checking each citation against its page.

  A text file that has already been corrected is never overwritten, because some of them have
  better OCR than the automatic extraction.
- **Sources.** Every claim in `docs/` cites a file of `archives/` and a page or section. The
  code and the tests refer to the same keys. For example, the tests reproduce the worked
  examples of B61 p.18 and COURS p.61-72.
- **Hypotheses.** Everything uncertain lives in `data/*.yaml`, never in the code. An uncertain
  value is written `{value, status: hypothesis, unknown: U-xx}`, and a test checks that every
  hypothesis points to an entry of `UNKNOWNS.md`. A new source can therefore correct the
  emulator by editing data, not code.
- **Two modes.**
  - `faithful` applies only the checks of the period.
  - `diagnostic` adds modern checks, such as overlapping processing units or a JOIN never
    reached.

### 3.3 Global study and cross-checking

The AI reads the whole corpus and builds a single reference specification in French:
- [`docs/MACHINE.md`](../docs/MACHINE.md): the machine;
- [`docs/ISA.md`](../docs/ISA.md): the instruction set;
- [`docs/TAPE.md`](../docs/TAPE.md): magnetic tapes;
- [`docs/TOOLCHAIN.md`](../docs/TOOLCHAIN.md): the toolchain;
- [`docs/HISTORY.md`](../docs/HISTORY.md): the history.

Every fact cites its source by page or section. When several sources describe the same point,
the specification compares them:
- the COURS mnemonics against the B61 mnemonics;
- the instruction timings of the two profiles;
- the delivery dates from the calendar chart against the FEB pages.

The wiki is derived from `docs/`, which prevails.

### 3.4 Finding the gaps

What no source settles is recorded in [`docs/UNKNOWNS.md`](../docs/UNKNOWNS.md), which
currently has 59 entries (U-01 to U-59). Each entry gives:
- the question;
- what the sources say, or how they disagree;
- the hypothesis chosen;
- where that hypothesis can be adjusted.

Typical gaps:
- the binary values of most code A sub-codes (U-01);
- the full priority order of the Data Distributor (U-03);
- the formats of the code C and code D sheets (U-14, U-53);
- disagreements between witnesses: for example, Leclerc describes assembly done on card
  sorting machines, while COURS and Maître describe an assembly program (U-58).

## 4. Phase 3: coding the emulator

### 4.1 Explicit conventions for choices that are not from the period

Where the emulator has to choose something the sources do not give, the choice is marked so
that it can never be mistaken for a historical fact:
- **UPPERCASE vs lowercase names.** A register name in UPPERCASE is attested in the displayed
  language: `RAPA` in French (COURS), `PAR` in English (BAT72). A name in lowercase is
  proposed by the emulator and not validated: RAPA is displayed `cpar` in English, and Z is
  displayed `z` because no English source names it.
- **Two languages for code B.** Every mnemonic exists in both forms, `en` (B61) and `fr`
  (COURS), for example `L` / `G`. A guessed spelling is marked with its U-xx.
- **Reconstructed encodings.** The code A sub-codes that the sources do not give use a stable
  synthetic table, labelled as reconstructed (U-01).
- **Modern file formats.** The toolchain files (`.g60c.yaml`, `.g60d.yaml`, `.ut.json`…) are
  stated to be modern formats ("none of what follows is a format of the period",
  [`docs/TOOLCHAIN.md`](../docs/TOOLCHAIN.md)). Only the steps of the process come from the
  sources: transposition, assembly (code C), distribution (code D).

### 4.2 Progressive milestones

The work proceeds one milestone at a time, following [`docs/ROADMAP.md`](../docs/ROADMAP.md).
For each milestone:
1. the assistant rereads the roadmap and proposes a detailed plan;
2. the human validates it, or corrects it;
3. the assistant implements it step by step, with tests;
4. after the milestone, the assistant updates the roadmap and the unknowns.

The test programs of `tests/programs/` must always pass. The suite currently has 832 tests.

| Milestone | Content | Status |
|---|---|---|
| **J0** | Package skeleton, pytest and ruff; loading and validation of the `data/` tables; the hypothesis convention (`status: hypothesis` + `unknown: U-xx`) | ✅ done |
| **J1** | Functional core, without time: 27-bit catenae and memory keys, exact decimal numbers, ARIT (13 directives), LOGI (15 directives), sequential interpreter | ✅ done |
| **J2** | Discrete-event engine (simulated time in µs), core store, Data Distributor (priority chain, valves, channels, one transfer per cycle); debugging (named registers in `en` / `fr`, step by step) | ✅ done |
| **J3** | Program Distributor (DP): instruction queue, address registers, decoding of code A, breaks, branches, central directives; minimal assembler code B → code A; ARIT and LOGI as timed elements | ✅ done |
| **J4** | Concurrency: restart chains, SIMU, JOIN, PROT/LIBE; ASCII timelines | ✅ done |
| **J5** | Class 2 (drum, uniselectors, tape drives) and COMP; **J5b**: continuous running of the tapes | ✅ done |
| **J6** | Complete toolchain: transposition (code B → code A), assembly (code C), distribution (code D → processing unit); symbolic debugging (labels, source lines, breakpoints by label) | ✅ done |
| **J7** | Minimal GGZ (the operating system): loading processing units, allocating I/O, several processing units at once; occupancy statistics | planned |
| **J8** | Classes 3-4 (multiplexer, cards, printer, paper tape), TRAN, desk with its 8 × 8 lights; the `facture` program | planned |

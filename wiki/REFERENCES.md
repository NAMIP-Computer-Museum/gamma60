# References

The sources behind this project, grouped by kind. The authoritative list, with keys used in
citations, is [`docs/SOURCES.md`](../docs/SOURCES.md); this page only arranges it. PDF files are
in [`archives/docs/`](../archives/docs/), page photos in [`archives/photos/`](../archives/photos/).

See also [ARCHITECTURE.md](ARCHITECTURE.md), [MEMORY.md](MEMORY.md), [CONCURRENCY.md](CONCURRENCY.md).

---

## 1. Technical publications by Bull (contemporary with the machine)

Manuals, brochures and papers written by Compagnie des Machines Bull or its engineers while the
machine was designed and built. These are the primary sources for the emulator.

| Key | Reference | Year | File / link |
|---|---|---|---|
| B61 | Compagnie des Machines Bull, *Gamma 60 Data Processing System* (68 p.). **Main source for the instruction set.** | 1961 | [PDF](../archives/docs/Bull-1961-Gamma60-Data-Processing-System.pdf) · [online](https://api.nakala.fr/embed/10.34847/nkl.5cae626j/23663bbffb4f6bf1450270f16f2f80186e0a3060) |
| COURS | Compagnie des Machines Bull, *Cours de programmation Gamma 60* (166 p., with errata): code A, Program Distributor registers, timings in cycles. French. | ~1958-59 | [PDF](../archives/docs/Bull-cours-programmation-gamma60.pdf) |
| BPD | Compagnie des Machines Bull, *Gamma 60 Preliminary Description* (20 p.): an earlier design. | — | [PDF](../archives/docs/Bull-Gamma60-Preliminary-Description.pdf) · [online](https://api.nakala.fr/embed/10.34847/nkl.db8d9ni9/b0be0561c298eaa82f324bdd58ec7e50da263181) |
| TFR | Compagnie des Machines Bull, code B instruction tables, **French version** (5 p., undated): same structure as the B61 tables p.62-66, with the French mnemonics. Scan without OCR, plus a checked structured transcription (YAML). | — | [PDF](../archives/docs/Bull-Gamma60-instructions-FR-NOOCR.pdf) · [YAML](../archives/docs/Bull-Gamma60-Instructions-FR.yaml) |
| DR-W | P. Dreyfus, "System Design of the Gamma 60", *WJCC*, p.130-133. | 1958 | [PDF](../archives/docs/Dreyfus-WJCC-1958-System-Design.pdf) · [ACM](https://dl.acm.org/doi/10.1145/1457769.1457805) |
| WJCC58 | *Proceedings of the Western Joint Computer Conference: Contrasts in Computers* (full proceedings, contain DR-W). | 1958 | [PDF](../archives/docs/WJCC-1958-Contrasts-Computers.pdf) |
| DR-E | P. Dreyfus, "Programming Design Features of the Gamma 60 Computer", *EJCC*, p.174-181. | 1958 | [PDF](../archives/docs/Dreyfus-EJCC-1958-Programming-Design-Features.pdf) · [ACM](https://dl.acm.org/doi/10.1145/1458043.1458080) |
| ONDE | Davous, Bataille, Harrand, "Le Gamma 60", *L'Onde électrique* n°405 (FEB transcription). French. | 1960 | [PDF](../archives/docs/Davous-OndeElectrique-1960-Gamma60.pdf) · [online](http://www.feb-patrimoine.com/projet/gamma60/gamma60_bataille2.pdf) |

## 2. Related work (concepts: multiprogramming, fork/join, semaphores, flowcharts)

Papers by others that discuss the same ideas, either at the time or as the later reference for a
concept. Used to place the Gamma 60 in context ([CONCURRENCY.md](CONCURRENCY.md)), not as sources
for the machine itself.

| Key | Reference | Year | Topic | File / link |
|---|---|---|---|---|
| GIL | F.B. and L.M. Gilbreth, "Process Charts — First Steps in Finding the One Best Way to Do Work", ASME annual meeting. | 1921 | process charts (ancestor of flowcharts) | [PDF](../archives/docs/Gilbreth-ASME-1921-Processc-Charts.pdf) |
| GOLD | H.H. Goldstine, J. von Neumann, *Planning and Coding of Problems for an Electronic Computing Instrument*, part II vol. 1, IAS. | 1947 | flow diagrams | [PDF](../archives/docs/Goldstine-IASECP-1946-PlanningCoding.pdf) |
| RYLE | B.L. Ryle, "Multiple programming data processing", *CACM* 4(2), p.99-101 (mentions the Gamma 60). | 1961 | multiprogramming | [PDF](../archives/docs/Ryle-CommACM-1961-Multiprogramming.pdf) · [ACM](https://dl.acm.org/doi/10.1145/366105.366132) |
| NEK | M.R. Nekora, "Comment on a paper on parallel processing", *CACM* 4(2), p.103 (mentions the Gamma 60). | 1961 | parallel processing | [PDF](../archives/docs/Nekora-CommACM-Note-Parallel-Processing.pdf) · [ACM](https://dl.acm.org/doi/10.1145/366105.366139) |
| CONW | M.E. Conway, "A Multiprocessor System Design", *FJCC*, p.139-146: origin of the names FORK and JOIN (according to BAT72). | 1963 | fork / join | [PDF](../archives/docs/Conway-FJCC-1963-Multiprocessor-System-Design.pdf) |
| DIJ68 | E.W. Dijkstra, "The Structure of the 'THE'-Multiprogramming System", *CACM* 11(5), p.341-346: semaphores, P/V, waiting list (p.345). | 1968 | semaphores | [PDF](../archives/docs/Dijkstra-ACM-1968-Structure-THE-Multiprogramming-System.pdf) |

## 3. Retrospective analyses (after the machine's working life)

Looking back at the Gamma 60: assessments, histories, testimonies, museum pages.

| Key | Reference | Year | File / link |
|---|---|---|---|
| BAT72 | M. Bataille, "The Gamma 60: the computer that was ahead of its time", *Honeywell Computer Journal* 5(3), p.99-105; reprinted in ACM SIGARCH CAN 1(2), 1972. | 1971 | [PDF](../archives/docs/Bataille-HCJournal-1971-Gamma60-Ahead-of-its-time.pdf) · [ACM](https://dl.acm.org/doi/10.1145/641276.641278) |
| HBC75 | "GAMMA 60 GOOD BYE", *Honeywell Bull Contact* (Honeywell Bull periodical). Not yet consulted. | Feb. 1975 | — (to be digitised) |
| TS | T.J. Tumlin, M. Smotherman, "An Evaluation of the Design of the Gamma 60". | 1993 | [PDF](../archives/docs/Tumlin-Histoire-Info-1993-Eval-Design-Gamma60.pdf) · [online](https://db.aconit.org/dbmedia_0/pdf_10/10174.pdf) |
| MAI | A. Maître, "Histoire du G 60 — Le logiciel", FEB site. French. | 1997 | [online](http://www.feb-patrimoine.com/projet/gamma60/histoire_du_gamma_60_logiciel_maitre.htm) |
| MAS | C. Massuard, "Petite synthèse…", FEB site. French. | 1997 | [online](http://www.feb-patrimoine.com/histoire/systemes_ord/g6002.htm) |
| AVG | J. Bourboulon (ed.), *L'Aventure Gamma 60*, Hermès/Lavoisier (page photos only). French. | 2005 | `archives/photos/aventure-gamma60-*` |
| NAM | NAM-IP Infos 2018/1-3, "Préservation : l'ordinateur Bull Gamma 60" (includes a sort program in code B). French. | 2018 | [online](http://pionnier.nam-ip.be/NAM-ip-Info201801-Pres1.html) · [photo](../archives/photos/namip-2018-programme-classement.jpg) |
| FEB-CHR | FEB, chronology "The dawn of electronics 1949-1964". | — | [online](http://www.feb-patrimoine.com/histoire/english/chronoa4.htm) |
| RTT | G. Natan / histoireinform, "Gamma 60 Bull à RTT". French. | — | [online](http://www.histoireinform.com/Histoire/+infos2/chr4rtt.htm) |
| SMO | M. Smotherman, "Bull Gamma 60 (1958)". | — | [online](https://people.computing.clemson.edu/~mark/g60.html) |
| EPOCH | "Bull Gamma 60", fosse.fr. | — | [online](https://fosse.fr/en/1960/bull-gamma-60.html) |

BAT72 is by M. Bataille, a co-author of ONDE, but it looks back at the machine as a whole, so it
is listed here.

## 4. Still to find

Bosset (ICIP 1959); Duverger (*Revue de l'Automatisme* 1958; *RGCF* 1961); Kilner (*Computer
Bulletin* 1960); Yarbrough (*CACM* 1960); the Bull code C programming brochure; the ANMT Roubaix
archives, Bull collection 2012 007; a copy of HBC75.

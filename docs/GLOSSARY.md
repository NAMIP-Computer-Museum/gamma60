# Glossary of abbreviations

Abbreviations, acronyms and mnemonics used for the Gamma 60, sorted in **English alphabetical
order** of the `en` form. Machine-readable mnemonics live in [`directives.yaml`](../data/directives.yaml);
the facts and their sources are in [`docs/`](../docs/), which prevails.

- **en**: form used by B61 (1961) or by Bataille (BAT72, Fig. 1); **fr**: form used by COURS
  and by the French code B tables (TFR). "—" = no form in that language; "?" = not recorded
  (U-29); *(hyp.)* = assumed spelling.
- **Expanded form**: the full name as given (or described) by the sources, `en` / `fr`.
- One line per meaning: a mnemonic used by several elements with different meanings (`ADD`,
  `DEL`, `REA`, `TRA`…) has one line per element. Watch the cross-language homonyms: `CP`,
  `DI`, `REB`, `R`, `P` (noted in the table).

| en | fr | Expanded form (en / fr) | Category | Description |
|---|---|---|---|---|
| A | A | Add / Additionner | Address instruction | Add X to a current address register (CAR / RAC). |
| A | A | Register A (analysis) / registre A (analyse) | Register | 24-bit register of the central unit; receives the qualitative catena of the element served; tested bit by bit by conditional branches. |
| A.F. | F.A. | Address Function / Fonction d'Adresse | Code B field | 2 columns: `R` (relative / differential) and `S` (substitution); `M` (working memory) in COURS. |
| AB | AB | Add to B / Addition dans B (15 positions) | Central directive | B ← B + X on the 15 right bits, without carry. |
| ADD | ADD | Addition / Addition | ARIT directive | R ← O1 + O2, decimal. |
| ADD | ADD | Binary addition / Addition binaire | LOGI directive | Binary addition in register L. |
| AN | NA | Arithmetic Number / Nombre Arithmétique | TRAN cliché | Semi-logarithmic number with exponent, without sign. |
| ARIT | ARIT | Arithmetic calculator / Calculateur arithmétique | Element, cut | Decimal arithmetic element (class 1); also the cut that calls it. |
| AVA | PVA | Absolute VAlue / Prise de Valeur Absolue | ARIT directive | Absolute value (operands: U-31). |
| AW | MA | Alphanumeric Word / Mot Alphanumérique | TRAN cliché | 4 characters of 6 bits (internal code). |
| AZ | TZ | Numeric, all zeros / Numérique avec codage de Tous les Zéros | TRAN cliché | Numeric word, zeros included (secondary positioning). |
| B | B | Register B (operator) / registre B (opérateur) | Register | 24-bit register of the central unit; computations on its 15 right bits. |
| B61 | B61 | Bull 1961 brochure | Profile | Machine profile of 1961 (10 µs cycle, parity + mod 3 key; default) and source key. |
| BCP | CAT | Bull Cards → Processing / CArtes BULL vers Traitement | TRAN directive | Phase: Bull cards to processing form. |
| BCS | CAM | Bull Cards → Storage / CArtes BULL vers Mémorisation | TRAN directive | Phase: Bull cards to storage form. |
| BLC | CBL | Binary and Logical Comparison / Comparaison Binaire et Logique | LOGI directive | Compares K and L; result in the qualitative catena. |
| BN | BN | BiNary / BiNaire | TRAN cliché | Binary (1 monade). |
| C.C. | C.C. | Complementary Codes / Codes Complémentaires | Code B field | 2 characters, use depends on the instruction (join count, CAR number, mode…). |
| CAL | CAL | Compare ALgebraic / Comparaison ALgébrique | ARIT directive | Compare O1 and O2 algebraically. |
| CAR | RAC | Current Address Register / Registre d'Adresse Courante | Register | 1 to 4 per element (matrix MAQ); data address, +1 or −1 per transfer. Also DAR (BAT72), RAQ. |
| CARP | PECT | CArd Reader-Punch / PErforateur de Cartes | Element, cut | Card reader-punch (class 3). |
| CARR | LECT | CArd Reader / LECTeur de cartes | Element, cut | Card reader (class 3). |
| CAV | CVA | Compare Absolute Values / Comparaison en Valeur Absolue | ARIT directive | Compare \|O1\| and \|O2\|. |
| CB | CB | Compare with B / Comparaison dans B (15 positions) | Central directive | Compare B with X; result in register A, bits 1-6. |
| — | CE | — / numérique avec CErtification | TRAN cliché | Numeric with certification; French table only (TFR p.3). |
| CLE | API | CLEar the track / Avancement de PIste | Card directive | Clear the track (after reading, after hopper 2, after punching). |
| CM | MC (MR) | Central Memory / Mémoire Centrale (mémoire rapide) | Unit | Ferrite-core store, 15-bit addresses, 27-bit catenae; shared by all elements. |
| COMP | COMP | Generalized comparator / Comparateur général | Element, cut | Compares, transfers and erases zones of 1-255 catenae (class 1). |
| COURS | COURS | Cours de programmation Gamma 60 | Profile | Machine profile ~1958-59 (11 µs cycle, mod 7 key) and source key. |
| CP | UC | Central Processor / Unité Centrale | Unit | Program Distributor + Data Distributor + register matrices (BAT72 Fig. 1). Not to be confused with the directive `CP`. |
| CP | PC | Counter Progression / Progression de Compteur | Central directive | memory[X] + 1 (15 bits); B receives the old value. Beware: `PC` / `CP` swap between languages. |
| CQ | CQ | Character to Qualitative / envoi d'un Caractère dans le catène Qualitatif | TRAN cliché | Write one character into the qualitative catena. |
| D1, D2, D3 | D1, D2, D3 | Code D cards | Toolchain | Distribution values: D2 (addresses, units, lengths → UT), D1 (launch parameters), D3 (jobs). |
| DAO | DAO | Désignation d'Adresse d'Origine (drum) | Drum directive | Set the origin address on the drum (track × 256 + position). |
| DAR | RAC | Data Address Register (BAT72) | Register | Same as CAR. |
| DCC | — | Data Collection Channel / canal de collecte | Channel | Elements → central memory (BAT72 Fig. 1). |
| DD | DT | Data Distributor / Distributeur de Données (de Transferts) | Unit | Arbitrates memory transfers, one per cycle, by priority chain; opens the class gates. |
| DDC | — | Data Distribution Channel / canal de distribution | Channel | Central memory → elements (BAT72 Fig. 1). |
| DEL | EFL | DELete (erase) / EFfacement avec Longueur | COMP directive | Erase a zone of n catenae. |
| DEL | EFF | DELete (erase) / EFFacement | Tape directive | Erase (execution). |
| DESK | ? | Console / pupitre | Element, cut | Operator console; status discussed (U-27); no French spelling recorded (U-29). |
| DIR | DIR | DIvide with Remainder / Division avec Reste | ARIT directive | Division keeping the remainder. |
| DIV | DIV | DIVide / DIVision normale | ARIT directive | Division without remainder. |
| DIV | DIV | Binary DIVision / DIVision binaire | LOGI directive | Binary division. |
| DMF | DMF | Demande de Manipulation, Fin de fichier | Card, printer directive | Handling request, end of file (lights on machine and console). |
| DMI | DMI | Demande de Manipulation sur Incident | I/O directive | Handling request after an incident. |
| DMN | DMN | Demande de Manipulation Normale | Paper tape directive | Normal handling request. |
| DPT | DPD | Divide by Power of Ten / Division par une Puissance De dix | ARIT directive | Divide by 10ⁿ (n = 0-15). |
| DRUM | TAMB | Magnetic drum / TAMBour magnétique | Element, cut | Shared auxiliary memory (class 2). |
| DTR | DTQ | Data Transfer Request / Demande de Transfert de Quantité | Signal | Request to the DD for one catena transfer; the PD issues them too (BAT72). Called DTD in `EMULATOR_DESIGN.md`. |
| END | FIN | END of transcoding / FIN de traduction | TRAN directive | End of a transcoding phase (C.C. `S` / `R`). |
| FLC | FCL | Fill L with Complement / Forçage au Complément dans L | LOGI directive | Replace L by its complement. |
| FO | FU | Fill with Ones / Forçage à « Un » | Central directive | memory[X] ← all ones. |
| FOL | FUL | Fill L with Ones / Forçage à Un dans L | LOGI directive | L ← all ones. |
| FZ | FZ | Fill with Zeros / Forçage à Zéro | Central directive | memory[X] ← all zeros. |
| FZL | FZL | Fill L with Zeros / Forçage à Zéro dans L | LOGI directive | L ← all zeros. |
| — | GGU | (expansion unknown) | System software | Operating system: kernel ≈ 3,800 words, memory maps, job handling (MAI). |
| — | GGZ | (expansion unknown) | System software | Resident supervisor at the start of memory (MAI). |
| H1, H2 | M1, M2 | Hopper / Magasin | Card C.C. | Card hoppers 1 and 2. |
| I1, I2 | B, C | Recall-chain registers / registres de chaîne de reprise | Register | Head and tail of an element's recall chain, in central memory at specialised addresses (ONDE; U-30). |
| IAR | RAI | Instruction Address Register | Register | Same as PAR. |
| IC | DI | Iteration Control / Décomptage d'Itération | Central directive | Count down on memory[X], [X+1]; sets bit 14 or 15 of A. Beware: `DI` is also the French name of ITR. |
| ICP | CET | IBM Cards → Processing / Cartes IBM vers Traitement | TRAN directive | Phase: IBM cards to processing form. |
| ICS | CEM | IBM Cards → Storage / Cartes IBM vers Mémorisation | TRAN directive | Phase: IBM cards to storage form. |
| IKL | IKL | Insert K in L / Insertion de K dans L | LOGI directive | Insert bits of K into L. |
| IN | EL | Ignore N input characters / Annulation de l'Entrée avec Longueur | TRAN cliché | Skip 2-63 input characters. |
| INT | INT | INTersection / INTersection logique | LOGI directive | Logical AND. |
| IO | EU | Ignore One input character / Annulation d'Un caractère à l'Entrée | TRAN cliché | Skip one input character. |
| ITR | DI | Instruction Transfer Request / Demande d'Instruction | Signal | Line raised by an element to get its next directive from the PD. Called DTI in `EMULATOR_DESIGN.md`. |
| JUM | SAU | JUMp (skip a block) / SAUt | Tape directive | Read a block without transfer. |
| K, L | K, L | Registers K and L | Register | 24-bit shift registers of LOGI; result in L. Also `L` as an operand R of LOGI. |
| L | G | Load / Garnir | Address instruction | Load a CAR / RAC with X. |
| LB | GB | Load B / Garnissage de B (15 positions) | Central directive | B ← X on the 15 right bits. |
| LE *(hyp.)* | GE | Load Element number / Garnissage de l'Élément | Central directive | RNE ← X; English spelling assumed (U-28). |
| LIBE | LIBE | LIBEration of a virtual element / LIBÉration d'élément virtuel | Cut | Release a lock (virtual element). |
| LOGI | LOGI | Logical calculator / Calculateur logique | Element, cut | Binary serial element (class 0 per ONDE and BAT72, class 1 per MAI: U-09). |
| — | M | — / Mémoire de manœuvre | A.F. (COURS) | Operand is a working memory, placed at the end of the subprogram. |
| MAI | MAI | MAnipulation, Incident | Tape directive | Handling request after an incident. |
| MAN | MAN | MAnipulation, Normal | Tape directive | Normal handling request. |
| — | MAP | Matrice des RAI (RAP) | Register matrix | Core matrix holding the RAI of every element (128 × 15 b + busy bit). |
| — | MAQ | Matrice des RAC (RAQ) | Register matrix | Core matrix holding the CARs / RACs of every element. |
| MATA | DERU | Magnetic tape (uniselector) / DÉRouleur de Ruban magnétique | Element, cut | Tape uniselector and its tape units (class 2). |
| MIC | GMI | load MIC / Garnissage MIC | TRAN directive | Load the MIC (C.C. `L`/`R` / `G`/`D`: left / right half). |
| MIC | MIC | — / Matrice d'Interprétation des Codes | TRAN component | Core matrix used by the transcoder to convert codes (U-12). |
| MPT | MPD | Multiply by Power of Ten / Multiplication par une Puissance De dix | ARIT directive | Multiply by 10ⁿ (n = 0-15). |
| MUL | MUL | MULtiply / MULtiplication | ARIT directive | R ← O1 × O2. |
| MUL | MUL | Binary MULtiplication / MULtiplication binaire | LOGI directive | Binary multiplication. |
| NS | NS | Number with Sign / Nombre avec Signe | TRAN cliché | Semi-logarithmic number with sign, for ARIT. |
| NW | MN | Numeric Word / Mot Numérique | TRAN cliché | Numeric word, 4 bits per character. |
| O1, O2, R | O1, O2, R | Operand 1, Operand 2, Result | ARIT / LOGI fields | Operands in X: `0-3` (CAR with progression), `Z F S T` / `Z U D T`, `P` (not in O2), `L` for LOGI. |
| OO | SU | Output One space / injection d'un espace à la Sortie (Un) | TRAN cliché | Write one space to the output. |
| ON | SL | Output N spaces / injection d'espaces à la Sortie avec Longueur | TRAN cliché | Write 2-63 spaces to the output. |
| OWC | CMP | One-Way Comparison (simple) / CoMParaison simple | COMP directive | Simple comparison (C.C. = CAR 1 or 2). |
| P | R | Place / Ranger | Address instruction | Store a CAR / RAC at address X. Beware: `R` is also the A.F. and the operand R. |
| P | P | Register P | Register | ARIT accumulator (2 catenae); also C.C.1 `P`: programmed decimal point. |
| P, S, O | P, S, O | ARIT registers | Register | P accumulator, S second half (double length), O operand; 2 catenae each. |
| PA | RA | Place A / Rangement de A | Central directive | memory[X] ← register A. |
| PAR | RAI (RAP) | Program Address Register / Registre d'Adresse d'Instruction | Register | Next instruction of each element; matrix MAP in the central unit; with busy bit. Also IAR. |
| PB | RB | Place B / Rangement de B | Central directive | memory[X] ← register B. |
| PBC | TCA | Processing → Bull Cards / Traitement vers CArtes BULL | TRAN directive | Phase: processing form to Bull cards. |
| PD | DP | Program Distributor / Distributeur de Programme | Unit | Reads instructions and hands directives to elements; executes cuts, branches, address and central instructions. |
| PE *(hyp.)* | RE | Place Element number / Rangement de l'Élément | Central directive | memory[X] ← RNE; English spelling assumed (U-28). |
| PI | RI | Place Instruction number / Rangement n° d'Instruction | Central directive | memory[X] ← instruction number (return address). |
| PPR | TIP | Processing → PRinter / Traitement vers ImPrimante | TRAN directive | Phase: processing form to printer. |
| PPT | TBP | Processing → Paper Tape / Traitement vers Bande Perforée | TRAN directive | Phase: processing form to paper tape. |
| PRI | IMP | PRInt / IMPression | Printer directive | Skip on the first paper, then print one line. |
| PRIN | IMPR | PRINter / IMPRimante | Element, cut | Printer (class 3). |
| PROT | PROT | PROTection (virtual element) / coupure sur élément virtuel | Cut | Take a lock (virtual element); wait in its FIFO if busy. |
| PTP | BPT | Paper Tape → Processing / Bande Perforée vers Traitement | TRAN directive | Phase: paper tape to processing form. |
| PTS | TVM | Processing → Storage / Traitement Vers Mémorisation | TRAN directive | Phase: processing form to storage form. |
| PUN | PER | PUNch / PERforation | Card directive | Punch from hopper 1 / 2, or without feeding (CARP). |
| PUN | PBA | PUNch / Perforer la BAnde | Paper tape directive | Punch n catenae. |
| R | R | Relative / Relatif | A.F. | Differential address (bit 17). Beware: `R` is also the French `Ranger` (place). |
| R *(hyp.)* | A | Rounded / Arrondi | ARIT C.C.1 | Normalised and rounded (U-05). |
| — | RAE | Registre d'Adresse Élément (COURS) | Register | Local drum address register, set by DAO. |
| — | RAPA | Registre d'Adresse Programme A (?) | Register | Address of the instruction being read (PD). |
| — | RAPP | Registre d'Adresse Programme P (?) | Register | RAPA + 1; copied into the RAI after a directive (PD). |
| RCL | RCL | Return to CLiché / Renvoi au CLiché | TRAN directive | Start the clichés (C.C. `A`/`I`/`0` / `G`/`E`/`S`). |
| REA | LEC | REAd / LECture | Card directive | Read from hopper 1, or split track (C.C. M1 / B1). |
| REA | LIR | REAd / LIRe | Paper tape directive | Read n catenae. |
| REB | LAR | REad Backward / Lecture ARrière | Tape directive | Preparatory: read backward. Beware: French `REB` = rewind (en `SPO`). |
| — | REDP | Registre d'Entrée du DP (?) | Register | Receives each instruction read (PD, 24 b). |
| REF | LAV | REad Forward / Lecture AVant | Tape directive | Preparatory: read forward. |
| REU | REU | Union / RÉUnion logique | LOGI directive | Logical OR. |
| RLN | RLN | — / Registre de LiaisoN | Register | One-catena buffer in each element, decoupling memory cycle and element rhythm. |
| RN | RL | Write N constants without advancing / Injection de n constantes sans avancer (Longueur) | TRAN cliché | 2-63 constants, output address unchanged. |
| — | RNE | Registre du Numéro d'Élément (?) | Register | Number of the element being served; selects its RAI / RAC (PD). |
| RO | RU | Write One constant without advancing / Injection d'Une constante sans avancer | TRAN cliché | One constant, output address unchanged. |
| ROF | ARR | Round OFf / ARRondi | ARIT directive | Round (operands: U-31). |
| RP | RP | Return to Program / Retour au Programme | TRAN cliché | End of the cliché sequence. |
| RR | FI | Reverse switches / Forçage Inversion « jamais-toujours » | Central directive | Swap never / always on the branch at X. |
| RS1, RS2, RS5 | b1, b2, b5 | Reading Station / brosse | Card C.C. | Card reading brushes (double reading RS1/RS2, punch check RS5). |
| — | RSDP | Registre de Sortie du DP (?) | Register | Output of the PD; receives RAPP at each branch (return address). |
| RSI | ISI | Reverse SIgn / Inversion de SIgne | ARIT directive | Reverse the sign (operands: U-31). |
| S | S | Subtract / Soustraire | Address instruction | Subtract X from a CAR / RAC. |
| S | S | Substitution | A.F. | Indirect address (bit 16). |
| SA | FT | Set Always / Forçage à « Toujours » | Central directive | Set the branch at X to "always". |
| SB | SB | Subtract from B / Soustraction dans B (15 positions) | Central directive | B ← B − X on the 15 right bits. |
| SHL | MCL | SHift Left / Maintien Cadré de L | LOGI directive | Shift L left. |
| SI | SI | Substitute Instruction / Substitution d'Instruction | Central directive | Execute the instruction at address B. |
| SIMU | SIMU | SIMUltaneous sequence launch / lancement de séquence SIMUltanée | Cut | Fork: start the named branch and the continuation. |
| SKI | SDF | SKIp / Saut Deuxième Feuillet | Printer directive | Skip n lines (≤ 255) on the second paper. |
| SN | FJ | Set Never / Forçage à « Jamais » | Central directive | Set the branch at X to "never". |
| SPN | REM | rewind + handling request / REbobinage et deMande de manipulation | Tape directive | Rewind and request handling. |
| SPO | REB | rewind / REBobinage | Tape directive | Rewind. |
| SPP | SCP | Select stacker after RS5 / Sélection Clapet après b5 | Card directive | Choose stacker 1 / 2 after the punch-check brush. |
| SPR | SCL | Select stacker after RS2 / Sélection CLapet après b2 | Card directive | Choose stacker 1 / 2 after the reading brush. |
| SQ | SQ | Substitute Quantity / Substitution de Quantité dans B | Central directive | B ← memory[B]. |
| STOP | STOP | End of sequence / Fin de séquence | Cut | Ends the sequence and the thread. |
| STP | MVT | Storage → Processing / Mémorisation Vers Traitement | TRAN directive | Phase: storage form to processing form. |
| STS | MVM | Storage → Storage / Mémorisation Vers Mémorisation | TRAN directive | Phase: storage form to storage form. |
| SUB | SOU | SUBtract / SOUstraction | ARIT directive | R ← O1 − O2. |
| SUB | SOU | Binary SUBtraction / SOUstraction binaire | LOGI directive | Binary subtraction. |
| T.O. | T.O. | Type of Operation / Type d'Opération | Code B field | 1 to 4 characters: cut, directive, branch, central directive or address instruction. |
| TA | TA | Transfer to A / Transfert dans A | Central directive | Register A ← memory[X]. |
| TAPP | PEBA | TApe Punch / PErforateur de BAnde | Element, cut | Paper-tape punch (class 4). |
| TAPR | LEBA | TApe Reader / LEcteur de BAnde perforée | Element, cut | Paper-tape reader (class 4). |
| TB | TB | Transfer to B / Transfert dans B | Central directive | Register B ← memory[X]. |
| TCD | TRT | Transfer Core → Drum / TRansfert mémoire rapide → Tambour | Drum directive | Transfer n catenae from central memory to drum. |
| TDC | TTR | Transfer Drum → Core / Transfert Tambour → mémoire Rapide | Drum directive | Transfer n catenae from drum to central memory. |
| TK | TK | Type de catène (?) | Code A field | Prefix code of an instruction: `00` branch, `01` cut, `10` central, `110` address, `1111` element directive. |
| TKL | TKL | Transfer K to L / Transfert de K dans L | LOGI directive | L ← K. |
| TN | TL | Transfer N characters / Transfert avec Longueur | TRAN cliché | Transcode 2-63 characters. |
| TO | TU | Transfer One character / Transfert d'Un caractère | TRAN cliché | Transcode one character. |
| TRA | TER | TRAnsfer / TransfERt | ARIT directive | R ← O1. |
| TRA | TRA | TRAnsfer (execute) / exécution avec TRAnsfert | Tape directive | Execute the preparatory directive with an actual transfer. |
| TRAN | TRAD | TRANscoder / TRADucteur | Element, cut | Code conversion and editing, driven by clichés and the MIC (class 1). |
| TSK | TCK | Transfer with Shift into K / Transfert Cadré dans K | LOGI directive | Load K with a circular shift. |
| TSL | TCL | Transfer with Shift into L / Transfert Cadré dans L | LOGI directive | Load L with a circular shift. |
| TSS | TRR | Transfer Store → Store / TRansfert mémoire Rapide → mémoire Rapide | COMP directive | Memory-to-memory transfer (C.C. = CAR 1 or 2). |
| TWC | CDB | Two-Way (two bounds) Comparison / Comparaison à Deux Bornes | COMP directive | Compare a value with two bounds. |
| — | UT | — / Unité de Traitement | Toolchain | Executable program, assembled (code C) and distributed (D2), values frozen. |
| WN | KL | Write N constants / injection de constantes avec Longueur | TRAN cliché | Write 2-63 constants. |
| WO | KU | Write One constant / injection d'Une constante | TRAN cliché | Write one constant. |
| WRI | ECR | WRIte / ÉCRiture | Tape directive | Preparatory: write. |
| WRM | ECM | WRite block Mark / ÉCriture d'un bloc Marque | Tape directive | Write a block (tape) mark. |
| X | X | Free variable / variable libre | Code B field | 5 decimal digits ≤ 32,767: address, quantity, length, element number. |
| — | Z | Registre Z | Register | 31-bit register of the central unit (catena, key, selection check); every catena read from or written to memory passes through it. See [REGISTERS](../wiki/REGISTERS.md). |
| Z F S T | Z U D T | Zero, First, Second, Third / Zéro, Un, Deux, Trois | ARIT / LOGI operands | CAR 0-3 without progression. |

Cut names, branches (`00` never, `31` always, `01`-`24` conditional) and code letters are the
same in both languages unless shown otherwise. Expanded forms of some `en` mnemonics are not
spelled out by B61 and are inferred from the table descriptions (e.g. `OWC`, `TWC`, `SPO`);
letter-by-letter expansions marked (?) are not given by the sources. `I1`, `I2` are ONDE's
names, `B`, `C` COURS's; `DAR`, `PAR`, `ITR`, `DTR`, `DDC`, `DCC` are BAT72's.

# Architecture de l'émulateur

## Principes
- **Simulation à événements discrets** : une file de priorité d'événements datés (µs),
  traitée dans l'ordre (date, numéro de séquence) ⇒ déterminisme total.
- **Temps simulé**, jamais l'horloge réelle. Option « temps réel » pour l'affichage seulement.
- **Données d'abord** : tout paramètre incertain est lu dans `data/`.

## Modules (`src/gamma60/`)
| Module | Rôle |
|---|---|
| `data.py` | accès aux tables de `data/` ; `resolve()` des hypothèses `{value, status, unknown}` (J0) |
| `codeb.py` | analyse du code B (`.g60b`, langues `fr` / `en`, en-têtes `; langue:`, `; profil:`, `; origine:`), commune à l'interpréteur et à l'assembleur (J3) |
| `code_a.py` | code A : préfixes TK et champs [COURS p.33-52] ; sous-codes et disposition des directives d'ARIT et de LOGI reconstruits (U-01) ; `encode`, `decode`, forme binaire groupée par champs (J3) |
| `seq.py` | interpréteur séquentiel du code B (J1), sans temps ; gardé comme référence de résultats (`run --seq`) |
| `engine.py` | file d'événements, horloge simulée, traces et écouteurs (J2) |
| `catena.py` | catène 27 bits ; clé selon le profil : `parity9_mod3_15` (B61) ou `mod7_24bits` (COURS) ; codages DCB / alpha / binaire |
| `number.py` | nombres semi-logarithmiques : mantisse entière 10 chiffres, exposant biaisé 40, clé mod 7 |
| `memory.py` | mémoire centrale (blocs, adresses 15 b, contrôle de sélection) |
| `registers.py` | matrice des RAC (MAQ) au J2, tailles lues dans `registers.yaml` ; au J3 : RAI (MAP), RNE, RAPA, RAPP, REDP, RSDP, A et B, indices d'occupation |
| `data_distributor.py` | DD / DT (J2) : file des DTQ, 1 transfert par cycle, chaîne de priorité (`priorities.yaml`), vannes par circuit de classe sur les canaux DDC / DCC (`topology.yaml`), multiplexeur c34 à tour de rôle ; le DP lit à l'adresse de son RAPA |
| `synthetic.py` | éléments synthétiques (continus, périodiques avec échéance) et scénarios YAML (`tests/scenarios/`) pour tester le DD (J2) |
| `program_distributor.py` | PD / DP (J3) : file des DI (priorité par classe) ; cycle RNE, A, RAPA ← RAI, RAPP, lecture par le DD dans REDP ; fonctions d'adresse d / s ; instructions d'adresse, branchements, 20 directives centrales ; envoi des directives par RSDP (RAI ← RAPP) ; coupures normales et STOP. J4 : générateur de commandes ; ordre (1)-(4) d'une coupure [COURS p.38] ; RAI ← coupure + 1 ; chaînes de reprise des éléments (table B / C en mémoire, U-30) et du DP ; SIMU ; JOIN ; PROT / LIBE ; coupures spéciales |
| `core/arit.py`, `core/logi.py` | calcul pur d'ARIT et de LOGI, sans temps (J1), appelé par les éléments |
| `elements/base.py` | machine à états d'un élément (repos, attente, opération) ; travail d'une directive écrit comme un générateur de commandes (lecture, écriture par le DD, attente) (J3) |
| `elements/processing.py` | ARIT et LOGI comme éléments (J3) : opérandes et résultats par le DD, calcul de `core/`, durées de `timings.yaml` ; `comp.py`, `tran.py` au J5-J8 |
| `elements/comparator.py` | COMP (J5) : CMP, CDB, EFL, TRR, demandes anticipées et RAC finaux du COURS |
| `elements/drum.py` | tambour (J5) : rotation, RAE, attente de position, tour perdu |
| `elements/tape.py` | unisélecteurs et dérouleurs (J5, J5b) : bobines, blocs, blocs-marques, service autonome ; `UniselectorUnit` partagé par les deux éléments de programme d'un unisélecteur ; marches discontinue et continue (voir `TAPE.md`) |
| `elements/cards.py`, `printer.py`, `tape_paper.py`, `desk.py` | E/S des classes 3-4 (J8) |
| `system/ggz.py` | superviseur minimal : tables des éléments et des UT, chargement, attribution des E/S |
| `toolchain/` | `assembler.py` (J3) : code B → image en code A, deux passes, fonctions d'adresse R / M (différentiel) et S, listing ; J6 : `subprogram.py` (sous-programme assemblable : vides, inconnues, repères, relocation), `linker.py` (assemblage par code C), `distributor.py` (code D2 → U.T.), `chain.py` (chaîne complète derrière `run`, image de la machine à partir d'une U.T.), `disassembler.py` (code A → code B) ; voir `TOOLCHAIN.md` |
| `machine.py` | la machine J3 : moteur, mémoire, DD, DP, ARIT et LOGI ; chargement de l'image et démarrage par le DP (convention de l'émulateur jusqu'au chargeur GGZ du J7) |
| `debug.py` | traces et débogueur (J2, enrichi à chaque jalon) : libellés de `registers.yaml` selon `--names en` ou `fr`, `--trace=regs`, `--step` (registres, mémoire, points d'arrêt), `--dump` (zone mémoire en fin d'exécution : adresse, étiquette, 24 bits en hexadécimal, clé) ; lecture seule sur l'état de la simulation |
| `gantt.py` | chronogrammes ASCII d'une exécution (`run --gantt`), calculés après coup sur la trace : par élément (PD, éléments, occupation de la mémoire, marqueurs SIMU / JOIN) ou par séquence (élément qui travaille pour elle, attente du DP ou d'une chaîne de reprise, fin par JOIN ou STOP) ; échelle automatique (≤ 100 colonnes) ou `--gantt-scale`, fenêtre `--gantt-from` / `--gantt-to` |
| `__main__.py` | `run <prog>` sur la machine (`--seq` : interpréteur J1), `asm <prog>` (listing), `dd <scénario>` |

## Interfaces clés
- Un élément ne parle qu'à deux arbitres : `request_instruction()` (DI, ITR chez BAT72) et
  `DataDistributor.request(port, car, direction, nature=…)` (DTQ, DTR chez BAT72). Il ne lit
  jamais le programme. Le DD le rappelle en fin de cycle : `transfer_done(request, value)` ou
  `transfer_incident(request, reason)` (`key`, `selection`).
- Le DP est le seul à manipuler RAI, RAC, I1/I2, registres A et B ; il est lui-même client du
  DD pour ses lectures en mémoire [BAT72 p.102].
- Vocabulaire : noms du COURS dans le code (RAI, RAC, DI, DTQ…) ; équivalents anglais de BAT72
  (PAR, DAR, ITR, DTR, DDC, DCC) dans `docs/GLOSSARY.md`.
- Chaque directive est décrite par : mnémonique, opérandes (CAR utilisés), durée (fixe,
  par catène ou fonction des données), effets sur le catène qualitatif.

## Modes
- `faithful` : seuls les contrôles d'époque (clés, mod 7, incidents d'E/S).
- `diagnostic` : + directive inconnue pour l'élément, chevauchement de zones d'UT, JOIN
  jamais atteint (détection d'attente infinie), catène vierge manquante, usage d'un élément
  d'E/S non attribué à l'UT.

## Traces et mesures
Trace par événement (date, élément, état, adresse) ; statistiques : occupation de chaque
élément, attentes DI/DTQ, longueur des chaînes de reprise, saturation du DP et des canaux.

Débogage (`debug.py`) : `--trace=regs` affiche après chaque pas les registres modifiés
(marqués `*`) ; `--step` avance pas à pas (instruction, événement), affiche tous les registres
(`r`), la mémoire (`m <adr> [n]`), pose des points d'arrêt (`b <étiquette|adresse>`). Noms
affichés : champ `display` de `data/registers.yaml`, en `en` ou en `fr` (`--names`), avec une
légende qui donne pour chaque libellé sa forme développée et sa source, ou « emulator label ».
Le débogueur ne fait que lire l'état : la trace reste identique avec ou sans pas à pas.

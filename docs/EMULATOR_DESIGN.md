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
| `seq.py` | interpréteur séquentiel provisoire du code B (J1) : coupures ARIT / LOGI, adresses, branchements, SIMU / JOIN / STOP ; remplacé par le DP au J3 |
| `engine.py` | file d'événements, horloge simulée, traces |
| `catena.py` | catène 27 bits ; clé selon le profil : `parity9_mod3_15` (B61) ou `mod7_24bits` (COURS) ; codages DCB / alpha / binaire |
| `number.py` | nombres semi-logarithmiques : mantisse entière 10 chiffres, exposant biaisé 40, clé mod 7 |
| `memory.py` | mémoire centrale (blocs, adresses 15 b, contrôle de sélection) |
| `registers.py` | matrices RAI (MAP) et RAC (MAQ), registres RNE, RAPA, RAPP, REDP, RSDP, A et B, indices d'occupation |
| `data_distributor.py` | DD / DT : file des DTQ, 1 transfert par cycle, chaîne de priorité, vannes par circuit de classe sur les canaux DDC / DCC (`topology.yaml`) |
| `program_distributor.py` | PD / DP : file des DI ; lit le programme par des DTQ ; interprétation C, A, B, directives centrales ; chaînes de reprise ; JOIN ; SIMU ; éléments virtuels |
| `core/arit.py`, `core/logi.py` | calcul pur d'ARIT et de LOGI, sans temps (J1), appelé par les éléments |
| `elements/base.py` | machine à états d'un élément (repos, attente DI, servi, exécution : calcul / attente DTQ / transfert) |
| `elements/arit.py`, `logi.py`, `comp.py`, `tran.py` | éléments de traitement (directives de `data/directives.yaml`) |
| `elements/drum.py`, `mata.py`, `cards.py`, `printer.py`, `tape_paper.py`, `desk.py` | mémoires auxiliaires et E/S |
| `system/ggz.py` | superviseur minimal : tables des éléments et des UT, chargement, attribution des E/S |
| `toolchain/` | transposition code B → code A, assemblage (code C), distribution (code D) → UT |
| `debug.py` | traces et débogueur (J2, enrichi à chaque jalon) : libellés de `registers.yaml` selon `--names en` ou `fr`, `--trace=regs`, `--step` (registres, mémoire, points d'arrêt) ; lecture seule sur l'état de la simulation |
| `__main__.py` | `python -m gamma60 run <prog> [--profile] [--trace]` (J1) ; `asm` au J3 |

## Interfaces clés
- Un élément ne parle qu'à deux arbitres : `request_instruction()` (DI, ITR chez BAT72) et
  `request_transfer(car_index, direction)` (DTQ, DTR chez BAT72). Il ne lit jamais le programme.
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

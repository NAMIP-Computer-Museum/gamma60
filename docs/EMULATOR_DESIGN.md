# Architecture de l'émulateur

## Principes
- **Simulation à événements discrets** : une file de priorité d'événements datés (µs),
  traitée dans l'ordre (date, numéro de séquence) ⇒ déterminisme total.
- **Temps simulé**, jamais l'horloge réelle. Option « temps réel » pour l'affichage seulement.
- **Données d'abord** : tout paramètre incertain est lu dans `data/`.

## Modules (`src/gamma60/`)
| Module | Rôle |
|---|---|
| `engine.py` | file d'événements, horloge simulée, traces |
| `catena.py` | catène 27 bits, clés (parité 9 b, mod 3 sur 15 b), codages DCB / alpha / binaire |
| `number.py` | nombres semi-logarithmiques : mantisse entière 10 chiffres, exposant biaisé 40, clé mod 7 |
| `memory.py` | mémoire centrale (blocs, adresses 15 b, contrôle de sélection) |
| `registers.py` | matrices RAP/IAR et CAR/RAQ, registres A et B, indices d'occupation |
| `data_distributor.py` | arbitre des DTD (1 transfert par cycle), priorité par table |
| `program_distributor.py` | arbitre des DTI ; interprétation C, A, B, directives centrales ; chaînes de reprise ; JOIN ; SIMU ; éléments virtuels |
| `elements/base.py` | machine à états d'un élément (repos, attente DTI, servi, exécution : calcul / attente DTD / transfert) |
| `elements/arit.py`, `logi.py`, `comp.py`, `tran.py` | éléments de traitement (directives de `data/directives.yaml`) |
| `elements/drum.py`, `mata.py`, `cards.py`, `printer.py`, `tape_paper.py`, `desk.py` | mémoires auxiliaires et E/S |
| `system/ggz.py` | superviseur minimal : tables des éléments et des UT, chargement, attribution des E/S |
| `toolchain/` | transposition code B → code A, assemblage (code C), distribution (code D) → UT |
| `cli.py` | `python -m gamma60 run|asm|trace` |

## Interfaces clés
- Un élément ne parle qu'à deux arbitres : `request_instruction()` (DTI) et
  `request_transfer(car_index, direction)` (DTD). Il ne lit jamais le programme.
- Le DP est le seul à manipuler RAP, CAR, I1/I2, registres A et B.
- Chaque directive est décrite par : mnémonique, opérandes (CAR utilisés), durée (fixe,
  par catène ou fonction des données), effets sur le catène qualitatif.

## Modes
- `faithful` : seuls les contrôles d'époque (clés, mod 7, incidents d'E/S).
- `diagnostic` : + directive inconnue pour l'élément, chevauchement de zones d'UT, JOIN
  jamais atteint (détection d'attente infinie), catène vierge manquante, usage d'un élément
  d'E/S non attribué à l'UT.

## Traces et mesures
Trace par événement (date, élément, état, adresse) ; statistiques : occupation de chaque
élément, attentes DTI/DTD, longueur des chaînes de reprise, saturation du DP et des canaux.

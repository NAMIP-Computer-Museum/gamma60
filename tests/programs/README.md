# Programmes de référence

Écrits en **code B** (profil B61, langue `en`, sauf mention), chargés par défaut à l'adresse 256
(après la table des registres B / C des chaînes de reprise, U-30) ; chaque fichier déclare sa langue
en première ligne (`; langue: fr|en`). Depuis J0, `tests/test_programs_mnemonics.py`
vérifie que chaque mnémonique est connu dans la langue déclarée. Champs de B61 (voir `docs/ISA.md`),
mise en forme moderne (voir `docs/TOOLCHAIN.md`). Pseudo-instructions de l'assembleur
(non historiques) : `VIERGE` (catène vierge obligatoire après une coupure), `NUM` (nombre
semi-logarithmique sur 2 catènes), `BIN n` (entier binaire sur 1 catène), `ZONE n` (réserve n
catènes), étiquettes `NOM:`.

Colonnes : `T.O.  C.C.  X  A.F.` ; pour les directives ARIT, X = `dp O1 O2 R`
(`-` = rien ; O1/O2/R = n° de CAR 0-3, Z/F/S/T, ou P).

| Fichier | Ce qu'il teste | Résultat attendu |
|---|---|---|
| `forkjoin_tumlin.g60b` | SIMU, deux séquences sur ARIT (sérialisées par la chaîne de reprise), JOIN à 2 appels ; sur la machine depuis J4 ; pas de gain de temps (un seul ARIT : les branches sont sérialisées), voir `parallele.g60b` | A = 12, D = 11, F = 132 ; avec 1 ARIT, I1 et I2 se succèdent |
| `parallele.g60b` | SIMU, une branche ARIT (DIV) et une branche LOGI (MUL) en même temps, puis JOIN sur ARIT (J4) | R = 22 / 7 + 1 = 4,142857142 ; M = 1234 × 3001 ; la DIV se déroule pendant le MUL |
| `tambour_arit.g60b` | SIMU : écriture puis relecture de 8 catènes sur le tambour 1 pendant 30 divisions d'ARIT, puis JOIN (J5) | COPIE = SOURCE ; les divisions se font pendant les attentes de rotation (≈ 40,8 ms au total) |
| `facture.g60b` | fork vers DRUM, TRAN et ARIT, JOIN à 3 appels vers COMP ; attend TRAN (J8) | MONTANT = 37,50 ; durée ≈ celle du tambour, pas la somme |
| `namip_classement.g60b` (J5, encadré par `tests/test_storage.py` : données et STOP) | extrait (lignes 020-052) d'un programme d'époque (NAM-IP 2018), profil COURS, langue `fr` : COMP à deux bornes, branchements sur le qualitatif, TRR, ARIT | somme dans le cumul ; ordre trié dans 2 cas sur 3 (voir note) |
| `bande_continue.g60b` | marche continue des bandes : élément double DERU 1 / DERU 2, séquence de lancement de COURS p.148-149 (lignes 10-13 reconstituées, U-51), bloc-marque, regroupement ; `--tape 10=tests/media/fichier_6_blocs.yaml` | 7 enchaînements sans arrêt, 1 arrêt ; ZA = 5000…, ZB = 9000… ; `--gantt` : `:` = attente du circuit |
| `bande_continue_task.g60b` | variante de `bande_continue` : chaque bloc est additionné par LOGI (SIMU TRAIT) pendant que le ruban lit le suivant (double tampon ZA / ZB) ; `--tape 10=tests/media/fichier_6_blocs.yaml` | TOTAL = 1 057 350 (0x102246), NBLOC = 6 : le bloc 9000 qui suit la marque est lu (en ZB) mais pas traité ; toujours 7 enchaînements et 1 arrêt : traitement ≈ 20,1 ms par bloc pour ≈ 21,2 ms entre deux blocs ; `--gantt` : LOGI travaille pendant les TRA |
| `lecture_bande.g60b` | élément virtuel d'E/S (PROT/LIBE), unisélecteur, opération unique, priorité DTD ; sur la machine depuis J5 avec `--tape 3=tests/media/bloc_128.yaml` | bloc lu dans TAMPON ; un catène transféré toutes les ≈190 µs |
| `pi.g60b` | pi par la formule de Machin (16 arctan 1/5 - 4 arctan 1/239) ; sous-programme ATAN appelé deux fois (PI / RI et retour par branchement à substitution), arrêt quand un terme ne change plus la somme (CAL, position 3) ; mode arrondi ; machine J3 seulement | VALPI = 3,141592653 (10 chiffres exacts) |
| `fibonacci.g60b` | les N premiers termes de Fibonacci dans RESULT (N = constante `BIN`) : RAC en fenêtre glissante, boucle comptée par IC (DI), branchement sur la position 14 de A ; machine J3 seulement (directives centrales) | RESULT = 1, 1, 2, 3, 5, … 6765 pour N = 20 ; 2 TRA + 18 ADD |
| `arit_logi.g60b` | une séquence ARIT → LOGI → ARIT par coupures normales (J3), langue `fr` | S = 42, T = 84 ; M = MOT1 ∧ MOT2 ; ARIT 550 µs, LOGI 270 µs (B61) |
| `test-arith01.g60b` | ARIT seul : DIV en virgule normalisée | R = 22 / 7 = 3,142857142 (10 chiffres, tronqué) |
| `test-arith02-overflow.g60b` | MUL normalisé : 10^20 × 10^19, exposant 80 > 79 | incident ligne 9 (U-35), R inchangé |
| `test-arith03-underflow.g60b` | MUL normalisé : 10^-21 × 10^-21, exposant −1 < 0 | incident ligne 10 par défaut ; R = +0 avec `exponent_underflow: zero` (U-35) |

## Chaîne d'outils (J6)

Sous-programmes avec repères (`REP`) et inconnues (`?NOM`), liés par une feuille de code C
(`.g60c.yaml`) et distribués par une feuille de code D2 (`.g60d.yaml`) ; formats modernes
(U-52 à U-54), voir `docs/TOOLCHAIN.md`. `distribute` écrit l'U.T. (`.ut.json`, non versionnée)
à côté de la feuille : `python -m gamma60 distribute <feuille>` puis `python -m gamma60 run <u.t.>`.

| Fichier | Ce qu'il teste | Résultat attendu |
|---|---|---|
| `lib/lecture_continue.g60b` | sous-programme de bibliothèque : la lecture en marche continue de `bande_continue_task`, zones, traitement, sortie et dérouleur en inconnues | (non exécutable seul : `run` refuse ses inconnues) |
| `lib/somme.g60b` | sous-programme standard : somme LOGI de N catènes ; zone, N, résultat et retour en inconnues | (idem) |
| `chaine/bande_continue/bande_continue.g60c.yaml` + `.g60d.yaml` | `bande_continue_task` découpé : `lib/lecture_continue` + `chaine/bande_continue/traitement_bloc.g60b` + zones ZA, ZB, ZTR en articles ; dérouleur 10 donné par D2 ; `--tape 10=tests/media/fichier_6_blocs.yaml` | TRAIT.TOTAL = 1 057 350, TRAIT.NBLOC = 6, comme le programme d'un seul tenant ; 20 µs de plus (la sortie `31 ?FIN` vers FIN_UT) |
| `chaine/bande_continue/bande_continue_d12.g60d.yaml` | le même programme assemblé, distribué pour le dérouleur 12 ; `--tape 12=…` | même résultat ; les deux U.T. ne diffèrent que par la catène de `LAV ?DEROUL` |
| `chaine/sommes/sommes.g60c.yaml` | `lib/somme.g60b` implanté deux fois (SOMME_A, SOMME_B), avec `chaine/sommes/principal.g60b` et `chaine/sommes/donnees.g60b` | DON.RES1 = 10, DON.RES2 = 60 |

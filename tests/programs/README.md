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
| `lecture_bande.g60b` | élément virtuel d'E/S (PROT/LIBE), unisélecteur, opération unique, priorité DTD ; sur la machine depuis J5 avec `--tape 3=tests/media/bloc_128.yaml` | bloc lu dans TAMPON ; un catène transféré toutes les ≈190 µs |
| `pi.g60b` | pi par la formule de Machin (16 arctan 1/5 - 4 arctan 1/239) ; sous-programme ATAN appelé deux fois (PI / RI et retour par branchement à substitution), arrêt quand un terme ne change plus la somme (CAL, position 3) ; mode arrondi ; machine J3 seulement | VALPI = 3,141592653 (10 chiffres exacts) |
| `fibonacci.g60b` | les N premiers termes de Fibonacci dans RESULT (N = constante `BIN`) : RAC en fenêtre glissante, boucle comptée par IC (DI), branchement sur la position 14 de A ; machine J3 seulement (directives centrales) | RESULT = 1, 1, 2, 3, 5, … 6765 pour N = 20 ; 2 TRA + 18 ADD |
| `arit_logi.g60b` | une séquence ARIT → LOGI → ARIT par coupures normales (J3), langue `fr` | S = 42, T = 84 ; M = MOT1 ∧ MOT2 ; ARIT 550 µs, LOGI 270 µs (B61) |
| `test-arith01.g60b` | ARIT seul : DIV en virgule normalisée | R = 22 / 7 = 3,142857142 (10 chiffres, tronqué) |
| `test-arith02-overflow.g60b` | MUL normalisé : 10^20 × 10^19, exposant 80 > 79 | incident ligne 9 (U-35), R inchangé |
| `test-arith03-underflow.g60b` | MUL normalisé : 10^-21 × 10^-21, exposant −1 < 0 | incident ligne 10 par défaut ; R = +0 avec `exponent_underflow: zero` (U-35) |

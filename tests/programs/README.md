# Programmes de référence

Écrits en **code B** (profil B61, langue `en`, sauf mention) ; chaque fichier déclare sa langue
en première ligne (`; langue: fr|en`). Depuis J0, `tests/test_programs_mnemonics.py`
vérifie que chaque mnémonique est connu dans la langue déclarée. Champs de B61 (voir `docs/ISA.md`),
mise en forme moderne (voir `docs/TOOLCHAIN.md`). Pseudo-instructions de l'assembleur
(non historiques) : `VIERGE` (catène vierge obligatoire après une coupure), `NUM` (nombre
semi-logarithmique sur 2 catènes), `ZONE n` (réserve n catènes), étiquettes `NOM:`.

Colonnes : `T.O.  C.C.  X  A.F.` ; pour les directives ARIT, X = `dp O1 O2 R`
(`-` = rien ; O1/O2/R = n° de CAR 0-3, Z/F/S/T, ou P).

| Fichier | Ce qu'il teste | Résultat attendu |
|---|---|---|
| `forkjoin_tumlin.g60b` | SIMU, deux séquences sur ARIT (sérialisées par la chaîne de reprise), JOIN à 2 appels | A = 12, D = 11, F = 132 ; avec 1 ARIT, I1 et I2 se succèdent |
| `facture.g60b` | fork vers DRUM, TRAN et ARIT, JOIN à 3 appels vers COMP | MONTANT = 37,50 ; durée ≈ celle du tambour, pas la somme |
| `namip_classement.g60b` | extrait (lignes 020-052) d'un programme d'époque (NAM-IP 2018), profil COURS, langue `fr` : COMP à deux bornes, branchements sur le qualitatif, TRR, ARIT | somme dans le cumul ; ordre trié dans 2 cas sur 3 (voir note) |
| `lecture_bande.g60b` | élément virtuel d'E/S (PROT/LIBE), unisélecteur, opération unique, priorité DTD | bloc lu dans TAMPON ; un catène transféré toutes les ≈190 µs |
| `test-arith01.g60b` | ARIT seul : DIV en virgule normalisée | R = 22 / 7 = 3,142857142 (10 chiffres, tronqué) |
| `test-arith02-overflow.g60b` | MUL normalisé : 10^20 × 10^19, exposant 80 > 79 | incident ligne 9 (U-35), R inchangé |
| `test-arith03-underflow.g60b` | MUL normalisé : 10^-21 × 10^-21, exposant −1 < 0 | incident ligne 10 par défaut ; R = +0 avec `exponent_underflow: zero` (U-35) |

# Programmes de référence

Écrits en **code B** (profil B61, langue `en`, sauf mention) ; chaque fichier déclare sa langue
en première ligne (`; langue: fr|en`). Champs de B61 (voir `docs/ISA.md`),
mise en forme moderne (voir `docs/TOOLCHAIN.md`). Pseudo-instructions de l'assembleur
(non historiques) : `VIERGE` (catène vierge obligatoire après une coupure), `NUM` (nombre
semi-logarithmique sur 2 catènes), `ZONE n` (réserve n catènes), étiquettes `NOM:`.

Colonnes : `T.O.  C.C.  X  A.F.` ; pour les directives ARIT, X = `dp O1 O2 R`
(`-` = rien ; O1/O2/R = n° de CAR 0-3, Z/F/S/T, ou P).

| Fichier | Ce qu'il teste | Résultat attendu |
|---|---|---|
| `forkjoin_tumlin.g60b` | SIMU, deux séquences sur ARIT (sérialisées par la chaîne de reprise), JOIN à 2 appels | A = 12, D = 11, F = 132 ; avec 1 ARIT, I1 et I2 se succèdent |
| `facture.g60b` | fork vers DRUM, TRAN et ARIT, JOIN à 3 appels vers COMP | MONTANT = 37,50 ; durée ≈ celle du tambour, pas la somme |
| `namip_classement.g60b` | programme d'époque (NAM-IP 2018), profil COURS, langue `fr` : COMP à deux bornes, branchements sur le qualitatif, TRR, ARIT | somme dans le cumul ; ordre trié dans 2 cas sur 3 (voir note) |
| `lecture_bande.g60b` | élément virtuel d'E/S (PROT/LIBE), unisélecteur, opération unique, priorité DTD | bloc lu dans TAMPON ; un catène transféré toutes les ≈190 µs |

# Feuille de route

| Jalon | Contenu | Critère d'acceptation |
|---|---|---|
| **J0** | Squelette du paquet, CI locale (pytest, ruff), chargement des YAML de `data/` | `pytest` vert ; YAML validés |
| **J1** | `engine`, `catena` (clé selon profil), `number`, `memory`, `registers` (RNE, RAPA, RAPP, REDP, RSDP, A, B, matrices RAI + indice d'occupation, RAC) ; décodage code A par préfixe TK (`encoding.yaml`) ; DP minimal (C, A, D, B toujours/jamais/conditionnel, STOP) ; ARIT (ADD SUB MUL DIV TRA) | `forkjoin_tumlin` donne f correct ; trace déterministe ; tests unitaires mod 7 et exposant biaisé |
| **J2** | DD avec priorités (DTD), DTI avec priorités, durées de `timings.yaml` | Temps simulé d'ARIT conforme (200/350/550 µs) ; tambour prioritaire sur ARIT |
| **J3** | Chaînes de reprise (registres B/C + catène vierge), SIMU (branche extraordinaire d'abord), JOIN (bits 19-18), PROT/LIBE (bit 24 de l'image), coupures spéciales, ordre d'exploitation de la coupure (COURS p.38), directives centrales | Deux séquences concurrentes sur ARIT sérialisées ; JOIN 3 branches |
| **J4** | DRUM, MATA (unisélecteur + dérouleurs), COMP, LOGI ; règles E/S (1 opération, UT unique) | `lecture_bande` ; `facture` (fork TAMB/TRAN/ARIT + JOIN) |
| **J5** | Transposition code B → code A (encodage synthétique U-01), assemblage code C, distribution code D | Les programmes de `tests/programs/` passent par la chaîne complète |
| **J6** | GGZ minimal : chargement d'UT, attribution des E/S, plusieurs UT simultanées | 2 UT indépendantes en parallèle, mesures d'occupation |
| **J7** | TRAN (MIC, phases, clichés), cartes, imprimante, pupitre ; visualisation (8×8 voyants) | Conversion cartes → impression d'un petit fichier |


Chaque jalon : mettre à jour `docs/diagrams/gamma60_sysml.puml` si le modèle change ; les deux profils (COURS, B61) doivent rester exécutables.

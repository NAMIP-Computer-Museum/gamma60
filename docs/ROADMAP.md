# Feuille de route

Ordre retenu : d'abord un **cœur fonctionnel** (ARIT et LOGI calculent juste, sans notion de
temps), puis le **tissu de communication** de la machine tel que le montre BAT72 fig. 1
(Distributeur de Données, canaux DDC / DCC, vannes par classe, demandes DTQ et DI), puis le
Distributeur de Programme, la simultanéité et les autres éléments. Les fonctions de calcul de
J1 sont pures : les jalons suivants les appellent sans les réécrire.

| Jalon | Contenu | Critère d'acceptation |
|---|---|---|
| **J0** ✅ | Squelette du paquet `src/gamma60/`, pytest et ruff ; chargement et validation des YAML de `data/` ; convention `status: hypothesis` + `unknown: U-xx` sur les valeurs incertaines ; points de cohérence ouverts ; topologie des classes dans `data/topology.yaml`, surchargeable par `data/configs/` (classes, vannes, 2 circuits pour c2, multiplexeur c3-c4 : U-32) | `pytest` vert ; YAML validés ; chaque hypothèse de `data/` renvoie à une entrée de `UNKNOWNS.md` |
| **J1** ✅ | **Cœur fonctionnel, sans temps** : `catena` (27 bits, clé selon le profil), `number` (semi-logarithmique, mantisse entière de 10 chiffres, exposant biaisé 40, mod 7), ARIT (13 directives : virgule programmée, normalisée, arrondie, double longueur, catène qualitatif), LOGI (15 directives sur K et L) ; interpréteur séquentiel minimal (une séquence, RAC, sans DP réel) | Tests unitaires (mod 7, exposant biaisé, exemples de B61 et du COURS) ; `forkjoin_tumlin` exécuté en séquentiel donne f |
| **J2** | `engine` (événements discrets, temps simulé en µs) ; mémoire centrale ; **DD** : chaîne de priorité, vannes par classe, canaux DDC / DCC, file des DTQ, un transfert par cycle ; testé avec des éléments synthétiques | Arbitrage déterministe (même entrée → même trace) ; débit d'un cycle de 10 / 11 µs selon le profil ; priorité des classes respectée |
| **J3** | **DP** : file des DI, matrices RAI (+ indice d'occupation) et RAC, registres RNE, RAPA, RAPP, REDP, RSDP, A, B ; décodage du code A par préfixe TK ; coupures, adresses, branchements, directives centrales, STOP ; le DP lit le programme **par des DTQ** [BAT72 p.102] ; assembleur minimal code B → code A (codage reconstruit, U-01) ; ARIT et LOGI branchés comme éléments avec les durées de `timings.yaml` | Programmes de test exécutés sur le moteur ; temps d'ARIT conformes (200 / 350 / 550 µs en B61) |
| **J4** | **Simultanéité** : chaînes de reprise (I1/I2 et catène vierge, U-30), SIMU (branche extraordinaire d'abord), JOIN (bits 19-18), PROT/LIBE (bit 24 de l'image), coupures spéciales du profil COURS, ordre d'exploitation de la coupure (COURS p.38) | Deux séquences concurrentes sur ARIT sérialisées ; JOIN à 3 branches ; `forkjoin_tumlin` en parallèle |
| **J5** | Classe 2 (tambour, unisélecteurs et dérouleurs), COMP ; règles d'E/S (une opération, UT unique) | `lecture_bande` ; `facture` (fork TAMB / TRAN / ARIT + JOIN, TRAN simulé ou différé) |
| **J6** | Chaîne d'outils complète : transposition code B → code A, assemblage code C, distribution code D → UT | Tous les programmes de `tests/programs/` passent par la chaîne complète |
| **J7** | GGZ minimal : chargement d'UT, attribution des E/S, plusieurs UT simultanées | 2 UT indépendantes en parallèle ; mesures d'occupation |
| **J8** | Classes 3-4 (multiplexeur, cartes, imprimante, bande perforée), TRAN (MIC, phases, clichés), pupitre ; visualisation (8 × 8 voyants) | Conversion cartes → impression d'un petit fichier |

**J0 terminé** : paquet `src/gamma60/` (`data.py`), 39 tests (`tests/test_data.py`,
`tests/test_programs_mnemonics.py`), tables `topology.yaml` et `behavior.yaml`, convention des
hypothèses appliquée à `data/`. Reste ouvert : images PlantUML à régénérer (pas de `plantuml.jar`).

**J1 terminé** : `catena.py` (clés des deux profils), `number.py`, `memory.py`, `core/arit.py`
(13 directives), `core/logi.py` (15 directives), `seq.py` + `python -m gamma60 run` ; 203 tests,
dont chaque directive ARIT et LOGI en test unitaire et depuis le code B dans les deux langues, et
les exemples chiffrés de B61 p.18, COURS p.61-72 et p.112-119. `forkjoin_tumlin` : A = 12,
D = 11, F = 132 (profils B61 et COURS, langues `en` et `fr`). Sémantique reportée dans
`MACHINE.md` §8 ; U-31 résolu ; U-35 à U-38 ouverts. Point 19 levé : le programme NAM-IP est un
extrait (lignes 019 et 053 en pointillés sur la feuille) ; il commence par COMP (J5).

Chaque jalon : mettre à jour `UNKNOWNS.md` et, si le modèle change,
`docs/diagrams/gamma60_sysml.puml` ; les deux profils (COURS, B61) et les deux langues du code B
(`fr`, `en`) doivent rester utilisables.

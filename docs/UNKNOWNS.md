# Inconnues, contradictions et hypothèses retenues (v2)

Règle : toute hypothèse est réglable dans `data/` ; le code n'en dépend jamais en dur.
Quand une source tranche une question, la déplacer dans `MACHINE.md` avec sa référence.
« Résolu » = tranché par une source citée.

| Id | Question | État des sources | Hypothèse / décision | Réglage |
|---|---|---|---|---|
| U-01 | Valeurs binaires des sous-codes (sorte de coupure, type d'adresse, n° de directive centrale, directives d'élément) | **Partiel** : préfixes TK et champs connus [COURS p.33-52] ; valeurs non données | table synthétique stable, marquée reconstruite | `data/encoding.yaml` |
| U-02 | Place des C.C. en code A | **Résolu en partie** : C.C. des coupures = m (bits 19-18), C.C. des adresses = n° RAC (19-18) ; directives d'élément sans variable libre : 20 bits propres (?) | — | `encoding.yaml` |
| U-03 | Ordre complet des priorités DTQ | principes [B61 p.24 ; COURS p.6] ; pas de liste | urgence physique ; quantités avant instructions à nature égale ; exception lecteur de cartes | `priorities.yaml` |
| U-04 | Ordre complet des priorités DI | « préétabli » ; classes décroissantes [MAI] | classes 0 > 1 > 2 > 3 > 4 | `priorities.yaml` |
| U-05 | C.C.1 d'ARIT | **Partiel** : P programmée, N normalisée, A normalisée avec arrondi [COURS p.67-68] ; B61 donne « P, N ou R » sans définir R [table p.62] | R (langue `en`) = A (langue `fr`) : *rounded* / arrondi, cf. ARR → ROF | `directives.yaml` |
| U-06 | Positions 1-6 du qualitatif d'ARIT | **Résolu** : > < = ≥ ≤ ≠ [B61 p.35 ; COURS p.72] | — | `qualitative.yaml` |
| U-07 | Profils du catène qualitatif | **Partiel** : ARIT, COMP, bandes, cartes, registre A (CB, DI) ; manquent imprimante, tambour, LOGI, TRAN | à compléter | `qualitative.yaml` |
| U-08 | Durées | **Partiel** : LOGI et COMP en cycles [COURS] ; DP ≈ 6 cycles par directive ; temps interne d'ARIT non séparé des transferts | voir `timings.yaml` | `timings.yaml` |
| U-09 | Classe de LOGI | c0 [ONDE] / c1 [MAI] | c0 | `configs/*.yaml` |
| U-10 | Enchaînement après l'opération d'un élément d'E/S | **Partiel** : distinction préparatoire / opératoire [COURS p.40-42] | DI après chaque directive ; le DP poursuit la séquence | — |
| U-11 | Réaction à une erreur de clé ou de mod 7 | incident signalé (qualitatif) | incident + arrêt en mode faithful | — |
| U-12 | Taille de la MIC | 256 [B61] / 128 × 20 b [COURS] / 128 × 21 b [ONDE] | profil | `profiles.yaml` |
| U-13 | Protection mémoire entre UT | aucune trace matérielle ; topogrammes GGU | aucune en faithful | mode |
| U-14 | Formats de cartes code B / C / D | B : 13 car. ; C : « code plus complet » [B61 p.28] ou feuille d'assemblage [MAI] ; D non décrit | formats modernes | `TOOLCHAIN.md` |
| U-15 | Sémantique des directives centrales | **Résolu** [COURS p.53-60] | — | `ISA.md` |
| U-16 | Place du DP dans la chaîne du DT | exemple lecteur de cartes [COURS p.6] | selon la nature de l'élément servi | `priorities.yaml` |
| U-17 | Cycle MC | 10 µs [B61, ONDE] / 11 µs [COURS, BPD] | profil | `profiles.yaml` |
| U-18 | « Une opération par appel » vs préparatoire + exécution (bandes) | **Expliqué** : directive préparatoire = renseignement, une seule directive opératoire | — | diagnostic |
| U-19 | Clé de contrôle | parité + mod 3 [B61] / mod 7 sur 24 b [COURS] | profil | `profiles.yaml` |
| U-20 | Compte du JOIN en code B | C.C. [B61] / X de la catène vierge [COURS] ; en code A : bits 19-18 | profil (assembleur) | `profiles.yaml` |
| U-21 | Code carte Bull standard (machines électromécaniques) | décrit en une phrase [B61 p.17] ; reconstruction : 24 lettres sur zones 7/8/9 × (11, 0, 1-6), I et O = 1 et 0 | non utilisé par l'émulateur | — |
| U-22 | Trois glyphes du code interne (10-1010, 10-1101, 11-1010) | scan peu net [B61 p.16] | *, trait d'union, moins | `charset.yaml` |
| U-23 | Largeur du RNE | 7 b [COURS p.53] / 15 b [COURS p.14] | 7 b | — |
| U-24 | Préfixe TK `1110` | non documenté | inutilisé ; diagnostic si rencontré | `encoding.yaml` |
| U-25 | Conservation de P/S/O d'ARIT d'une séquence à l'autre | non dit ; aucun mécanisme de sauvegarde | contenus non garantis : le programme doit tout recharger | — |
| U-26 | Place exacte du test de JOIN dans l'exploitation de la coupure ; remise à zéro du compteur | non détaillé | test avant activation ; remise à 0 au déclenchement | — |
| U-27 | Statut du pupitre | élément [ONDE, table B61] / « pas un élément d'E/S » [B61 p.47] | élément de classe 0, hors limite des 40 E/S | — |
| U-28 | Mnémoniques anglais (B61) de GE / RE (RNE ← X ; mémoire[X] ← RNE) | décrites en COURS p.53-60 ; absentes de la table B61 p.62-66 | LE / PE, par analogie GB→LB, RI→PI, RA→PA, RB→PB (G→L, R→P) | `directives.yaml` |
| U-29 | Mnémoniques français (COURS) de DESK, TRAN, tambour (hors DAO), unisélecteur, cartes, imprimante, bande perforée, clichés ; lien TRT [COURS] ↔ TCD / TDC [B61] | présents dans COURS (p.83-154) mais non relevés | langue `fr` absente : l'assembleur accepte la forme `en` (avertissement en mode diagnostic) | `directives.yaml` |
| U-30 | Adresses des registres I1/I2 (B/C, tête et queue de la chaîne de reprise) de chaque élément réel | « en Mémoire Centrale à des adresses spécialisées » [ONDE §2] ; adresses non données | une table de 2 catènes par numéro d'élément, en début de mémoire, hors zone allouable aux UT | `data/configs/*.yaml` (à créer au J0) |

## Pistes documentaires
- Bosset, ICIP 1959 (logique interne) ; Duverger 1958 et 1961 ; brochure Bull de programmation
  (code C) ; *L'Aventure Gamma 60* (chronologie, comités de direction) ; archives ANMT Roubaix
  (fonds 2012 007 Bull) et Archives départementales de Seine-Saint-Denis.

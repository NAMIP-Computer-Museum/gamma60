# Jeu d'instructions du Gamma 60 (code B, codage code A)

Source principale : B61, chapitre III et tables « The Gamma 60 code B table of instructions »
(PDF `refs/pdf/bull-1961-gamma60-data-processing-system.pdf`, pages 62 à 66 ; images dans
`refs/photos/bull-1961-tables-p-62.png` … `-66.png`). Vérifier sur les images en cas de doute :
l'OCR des tables est inutilisable.

**Ce qui est connu** : mnémoniques, champs, sémantique. **Ce qui ne l'est pas** : la valeur
binaire (code A) de chaque mnémonique — voir `UNKNOWNS.md` (U-01).

## 1. Format

### Code A (machine) — 1 catène [COURS p.33-52 ; B61 p.15, p.29-30]
Le type de catène (TK) est un **code préfixe** lu à gauche :

| TK | Type | Champs |
|---|---|---|
| `00` (24-23) | B branchement | 22-18 condition (0 jamais, 1-24 = bit de A, 31 toujours) · 17 d · 16 s · 15-1 adresse |
| `01` (24-23) | C coupure | 22-20 sorte (7) · 19-18 m (JOIN) · 17 d · 16 s · 15-1 n° élément ou adresse |
| `10` (24-23) | D centrale | 22-18 directive (32 codes, 20 utilisés) · 17 d · 16 s · 15-1 X |
| `110` (24-22) | A adresse | 21-20 type (G/L, R/P, A, S) · 19-18 n° de RAC · 17 d · 16 s · 15-1 X |
| `1111` (24-21) | D élément | avec variable libre : 20-18 type (≤ 8) · 17 d · 16 s · 15-1 X ; sans : 20-1 propres à l'élément |
| `1110` | non documenté (?) | — |

- d (bit 17) : adressage différentiel, écart à l'instruction, négatif en complément à 32 768 ;
  s (bit 16) : substitution ; d puis s.
- Une catène dont les 7 bits de gauche sont à 0 (catène vierge, donnée) vaut un branchement
  « jamais ».
- Valeurs binaires des sous-codes (sorte de coupure, type d'adresse, n° de directive centrale,
  directives d'élément) : **inconnues** (U-01) ; voir `data/encoding.yaml`.
- Exemple (COURS p.44) : « 31, 10 lignes plus loin, en différentiel » =
  `00 11111 1 0 000000000001010`.

### Code B (symbolique) — 13 caractères [B61 p.28-30]
| Zone | Largeur | Rôle |
|---|---|---|
| T.O. (type d'opération) | 4 | coupure : 4 car. ; directive d'élément : 3 car. cadrés à droite ; branchement et directive centrale : 2 car. ; instruction d'adresse : 1 car. |
| C.C. (codes complémentaires) | 2 | usage selon l'instruction |
| X (variable libre / adresse) | 5 | valeur décimale ≤ 32 767, cadrée à droite |
| A.F. (fonction d'adresse) | 2 | col. 1 : R (ou M pour certaines directives centrales) ; col. 2 : S |

Correspondance code B ↔ code A biunivoque. La largeur du T.O. reflète la hiérarchie :
coupures, puis directives (qui libèrent le DP), puis branchements/directives centrales/
adresses (qui ne libèrent pas le DP).

## 2. Instructions de l'unité centrale

### Coupures (C)
| Élément | T.O. | C.C. | X | A.F. |
|---|---|---|---|---|
| Calculateur arithmétique | ARIT | JOIN : rien, 1, 2 ou 3 | — | — |
| Calculateur logique | LOGI | idem | — | — |
| Traducteur | TRAN | idem | — | — |
| Comparateur | COMP | idem | — | — |
| Tambour | DRUM | idem | n° d'élément | R, S |
| Lecteur de cartes | CARR | idem | n° d'élément | R, S |
| Lecteur-perforateur | CARP | idem | n° d'élément | R, S |
| Imprimante | PRIN | idem | n° d'élément | R, S |
| Bande magnétique (unisélecteur) | MATA | idem | n° d'élément | R, S |
| Lecteur de bande perforée | TAPR | idem | n° d'élément | R, S |
| Perforateur de bande | TAPP | idem | n° d'élément | R, S |
| Pupitre | DESK | idem | n° d'élément | R, S |
| Coupure sur élément virtuel | PROT | idem | adresse de l'image de l'élément virtuel | R, S |
| Libération d'élément virtuel | LIBE | idem | idem | R, S |
| Lancer deux séquences | SIMU | idem | adresse de la 2e branche | R, S |
| Fin de séquence | STOP | — | — | — |

C.C. d'une coupure = nombre de conditions *supplémentaires* (JOIN) : 1, 2, 3 ⇒ attendre
2, 3, 4 séquences.

### Branchements (B)
| Opération | T.O. | X | A.F. |
|---|---|---|---|
| Jamais | 00 | adresse de saut | R, S |
| Toujours | 31 | idem | R, S |
| Conditionnel | 01 à 24 | idem | R, S |

Conditionnel n : effectif si le bit n du registre A vaut 1 (registre A = catène qualitatif
de l'élément servi, ou toute catène chargée par TA). Un « jamais » peut être transformé en
« toujours » par programme (SN/SA/RR).

### Instructions d'adresse (A)
| Opération | T.O. | C.C. | X | A.F. |
|---|---|---|---|---|
| Charger un CAR | L | n° de CAR 0-3 | adresse ou quantité | R, S |
| Ranger le contenu d'un CAR | P | idem | adresse de rangement | R, S |
| Ajouter au CAR | A | idem | quantité | R, S |
| Soustraire du CAR | S | idem | quantité | R, S |

Elles concernent l'élément de la coupure précédente.

### Directives centrales (exécutées par le DP, ne le libèrent pas)
| Opération | T.O. | X | A.F. |
|---|---|---|---|
| Ranger le numéro d'instruction | PI | adresse | R ou M ; S |
| Contrôle d'itération | IC | adresse | idem |
| Progression de compteur | CP | adresse | idem |
| Transférer dans A | TA | adresse | idem |
| Ranger le contenu de A | PA | adresse | idem |
| Transférer dans B | TB | quantité ou adresse (adresse si A.F. = S) | idem |
| Ranger le contenu de B | PB | idem | idem |
| Charger B (15 bits droits) | LB | idem | idem |
| Ajouter dans B (15 bits droits) | AB | idem | idem |
| Soustraire de B (15 bits droits) | SB | idem | idem |
| Comparer au contenu de B (15 bits) | CB | idem | idem |
| Substituer la quantité de B | SQ | — | — |
| Substituer une instruction | SI | — | — |
| Basculer un branchement en « jamais » | SN | adresse | idem |
| Basculer un branchement en « toujours » | SA | adresse | idem |
| Inverser les aiguillages | RR | adresse | idem |
| Remplir de zéros | FZ | adresse | idem |
| Remplir de uns | FO | adresse | idem |

(Correspondance ligne ↔ mnémonique lue sur l'image p.63 ; à revérifier : SQ, SI.)

## 3. Directives des éléments de traitement

### ARIT (13 directives)
| Opération | T.O. | C.C.1 | C.C.2 | X : dp | X : O1 O2 R |
|---|---|---|---|---|---|
| Addition | ADD | P, N ou R **(?)** | D ou rien | 0-10 ou rien | oui |
| Soustraction | SUB | idem | idem | idem | oui |
| Multiplication | MUL | idem | idem | idem | oui |
| Division sans reste | DIV | P ou N | — | 0-10 ou rien | oui |
| Division avec reste | DIR | P ou N | D ou rien | idem | oui |
| Transfert | TRA | P ou N | D ou rien | idem | O1, R |
| Multiplier par 10^n | MPT | — | — | n = 0-15 | O1 **(?)** |
| Diviser par 10^n | DPT | — | — | n = 0-15 | O1 **(?)** |
| Inverser le signe de P | RSI | — | — | — | — |
| Valeur absolue | AVA | — | — | — | — |
| Comparer valeurs absolues | CAV | — | — | — | O1 O2 **(?)** |
| Comparer valeurs algébriques | CAL | — | — | — | O1 O2 **(?)** |
| Arrondir | ROF | — | — | — | — |

- dp = position de la virgule du résultat (virgule fixe) ; « rien » = flottant **(?)**.
- O1, R : `0-3` (CAR avec progression), `Z F S T` (CAR sans progression), `P` (registre P).
  O2 : idem sauf P. Pas de fonction d'adresse.
- C.C.2 = D : résultat double longueur (P+S, 20 chiffres).
- Sens de P / N / R en C.C.1 : non établi (U-05).

### LOGI (15 directives)
| Opération | T.O. |
|---|---|
| Transfert avec décalage dans K | TSK |
| Transfert avec décalage dans L | TSL |
| Transférer K dans L | TKL |
| Décalage à gauche dans L | SHL |
| Insérer K dans L | IKL |
| Remplir L de zéros | FZL |
| Remplir L de uns | FOL |
| Addition | ADD |
| Soustraction | SUB |
| Multiplication | MUL |
| Division | DIV |
| Remplacer L par son complément | FLC |
| Intersection logique | INT |
| Réunion logique | REU |
| Comparaison binaire et logique | BLC |

X : dp = nombre de positions de décalage ou de bits concernés (0-23) ; R = CAR 0-3, Z F S T,
ou L (sans objet pour les deux premières).

### COMP (4 directives)
| Opération | T.O. | C.C. | X | A.F. |
|---|---|---|---|---|
| Comparaison simple | OWC | CAR 1 ou 2 | nombre de catènes (≤ 255) | R, S |
| Comparaison à deux bornes | TWC | — | idem | R, S |
| Effacement | DEL | — | idem | R, S |
| Transfert MC → MC | TSS | CAR 1 ou 2 | idem | R, S |

### TRAN
| Opération | T.O. | C.C. | X |
|---|---|---|---|
| Charger la MIC | MIC | L ou R **(?)** | — |
| Cartes Bull → forme traitement | BCP | P, N ou rien ; S ou rien | partie de la MIC utilisée (1-9) |
| Cartes IBM → forme traitement | ICP | idem | idem |
| Cartes Bull → forme stockage | BCS | idem | idem |
| Cartes IBM → forme stockage | ICS | idem | idem |
| Forme traitement → cartes Bull | PBC | idem | idem |
| Bande perforée → forme traitement | PTP | idem | idem |
| Forme traitement → bande perforée | PPT | idem | idem |
| Forme traitement → imprimante | PPR | idem | idem |
| Forme traitement → forme stockage | PTS | idem | idem |
| Forme stockage → forme traitement | STP | idem | idem |
| Forme stockage → forme stockage | STS | idem | idem |
| Aller au cliché | RCL | A ou rien ; I ou 0 | — |
| Fin de transcodage | END | S | — |

Clichés (4 par catène) — positionnement principal : AW (mot alphanumérique 6 b/car.),
NW (mot numérique 4 b/car.), AN (nombre arithmétique sans signe), NS (avec signe),
BN (binaire) ; secondaire : AZ (numérique, zéros compris) ; exécution : TO, TN (transcoder
1 / N car.), IO, IN (sauter en entrée), OO, ON (blancs en sortie), WO, WN (écrire),
RO, RN (écrire sans avancer l'adresse de sortie), RP (retour au programme),
CQ (écrire un caractère dans le catène qualitatif). N ≤ 63.

## 4. Directives des entrées-sorties

### Lecteur-perforateur / lecteur de cartes
| Opération | T.O. | C.C. |
|---|---|---|
| Choisir la case 1 / 2 après RS2 | SPR | 1 / 2 |
| Choisir la case 1 / 2 après RS5 | SPP | 1 / 2 |
| Lire depuis le magasin 1 | REA | M1 **(?)** |
| Lire, piste dédoublée après RS5 | REA | B1 **(?)** |
| Perforer depuis le magasin 1 / 2 | PUN | H1 / H2 |
| Perforer sans alimenter de carte | PUN | P |
| Dégager la piste (après lecture / après H2 / après perforation) | CLE | B2 / H2 / P |
| Demande de manipulation normale (fin de fichier) | DMF | — |
| Demande de manipulation sur incident | DMI | — |

### Bande perforée
Lecteur : REA (X = nombre de catènes), DMN, DMI. Perforateur : PUN (X = nombre de catènes),
DMN, DMI.

### Imprimante
| Opération | T.O. | X |
|---|---|---|
| Saut sur le 2e papier | SKI | nombre d'interlignes ≤ 255 |
| Saut sur le 1er papier + impression | PRI | idem |
| Demande de manipulation (fin de fichier) | DMF | — |
| Demande de manipulation (incident) | DMI | — |

## 5. Directives des mémoires auxiliaires

### Bande magnétique (unisélecteur)
| Groupe | Opération | T.O. | X |
|---|---|---|---|
| Préparatoires | Écrire / lire avant / lire arrière | WRI / REF / REB | n° de dérouleur (ou adresse si A.F.) |
| Exécution | Lire avec transfert / sans transfert (saut) / effacer / écrire bloc-marque | TRA / JUM / DEL / WRM | — |
| Service | Rembobiner / rembobiner + demande de manipulation / demande incident / demande normale | SPO / SPN / MAI / MAN | n° de dérouleur |

### Tambour
| Opération | T.O. | X |
|---|---|---|
| Désigner l'adresse d'origine sur le tambour | DAO | adresse tambour |
| Transfert MC → tambour | TCD | nombre de catènes |
| Transfert tambour → MC | TDC | nombre de catènes |

## 6. Exemple (forme B61)
Saut relatif : `Br 15 R` écrit en ligne 5 ⇒ code A : bit 17 = 1, adresse = 10.
Saut indirect relatif : `29RS` ⇒ R appliqué puis S.

Exemple ancien (BPD, mnémoniques antérieurs) : transfert MC → tambour de 12 catènes :
`TAMB 1` / `GO 108` / `DAO 17.400` / `TRI 12` — à rapprocher de `DRUM`, `L`, `DAO`, `TCD`
dans B61 (le code a évolué entre les deux documents).


## 7. Correspondance des mnémoniques COURS (~1958-59) ↔ B61 (1961)

| Domaine | COURS | B61 |
|---|---|---|
| Coupures | ARIT LOGI TRAD COMP TAMB LECT PECT IMPR DERU LEBA PEBA · PROT LIBE SIMU STOP | ARIT LOGI TRAN COMP DRUM CARR CARP PRIN MATA TAPR TAPP DESK · PROT LIBE SIMU STOP |
| Coupures spéciales | C.C. A (sans libération), C.C. B (sans test d'occupation) | — (C.C. = JOIN) |
| Adresse | G R A S | L P A S |
| Directives centrales | RI GE RE TA RA TB RB GB AB SB CB SQ SI FT FJ FI FU FZ DI PC | PI — — TA PA TB PB LB AB SB CB SQ SI SA SN RR FO FZ IC CP |
| ARIT | ADD SOU MUL DIV DIR TER MPD DPD ISI PVA CVA CAL ARR | ADD SUB MUL DIV DIR TRA MPT DPT RSI AVA CAV CAL ROF |
| ARIT C.C.1 | P N A | P N R |
| ARIT sans progression | Z U D T | Z F S T |
| LOGI | TCK TCL TKL MCL IKL FZL FUL FCL ADD SOU MUL DIV INT REU CNL | TSK TSL TKL SHL IKL FZL FOL FLC ADD SUB MUL DIV INT REU BLC |
| COMP | CMP CDB EFL TRR | OWC TWC DEL TSS |
| Tambour | DAO TRT … | DAO TCD TDC |

### Sémantique des directives centrales [COURS p.53-60]
- RI/PI : mémoire[X] ← n° d'instruction (adresse de retour, depuis RSDP).
- GE / RE : RNE ← X / mémoire[X] ← RNE.
- TA, TB : registre ← mémoire[X] (24 b, substitution implicite) ; RA/PA, RB/PB : rangement.
- GB/LB : B ← X (15 b droits) ; AB, SB : B ± X sans report ; CB : compare → A positions 1-6.
- SQ : B ← mémoire[B] ; SI : exécute l'instruction d'adresse B (sans X ni FA).
- FT/SA, FJ/SN, FI/RR : forcer le branchement en X à toujours / jamais / inverser.
- FU/FO, FZ : mettre mémoire[X] à tout 1 / tout 0.
- DI/IC : décomptage d'itération sur mémoire[X] et [X+1] ; A position 14 (zéro) ou 15.
- PC/CP : mémoire[X] (15 b) + 1 ; B reçoit l'ancienne valeur.

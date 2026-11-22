# Le Bull Gamma 60 — spécification de référence (v2)

Synthèse de ce qui est documenté. Chaque fait porte sa source (clés en fin de fichier ; pages
imprimées). Ce qui est incertain ou contradictoire est marqué **(?)** et détaillé dans
`UNKNOWNS.md`. Jeu d'instructions : `ISA.md`. Technologie matérielle : `HARDWARE.md`.
Histoire : `HISTORY.md`.

**Deux états de la machine coexistent dans les sources** (voir §12 et `data/profiles.yaml`) :
- profil **COURS** : *Cours de programmation Gamma 60* (~1958-59) — cycle 11 µs, clé mod 7 ;
- profil **B61** : *Gamma 60 Data Processing System* (1961) — cycle 10 µs, clé parité + mod 3.

Les mnémoniques diffèrent aussi (français dans COURS, anglais dans B61), mais c'est la langue
du document, pas la machine : le code B existe en deux langues `fr` / `en`, indépendantes du
profil (`data/directives.yaml`, `ISA.md` §7).

---

## 1. Principe général

- Éléments spécialisés et autonomes autour d'une mémoire centrale commune, « lieu de
  rendez-vous » ; aucune liaison directe entre éléments. [B61 p.20-21]
- Canaux communs : distribution (MC → éléments), collecte (éléments → MC), un canal
  distributeur d'instructions ; une ligne de demande d'instruction (DI) et une ligne de demande
  de transfert (DTQ/DTD) par élément. [B61 p.21 ; COURS p.4-8 ; BPD]
- Unité centrale = Distributeur de Programme (DP) + Distributeur de Données/Transferts (DT) +
  matrices de registres + mémoire. [B61 p.21 ; COURS p.4]
- Machine à programme enregistré (von Neumann) : instructions et données dans la même mémoire,
  aux mêmes adresses ; le DP passe par le DT pour lire les instructions. [B61 p.8, p.10, p.24]
- Plusieurs séquences, d'un même programme ou de problèmes indépendants, s'exécutent
  simultanément. [B61 p.20]

## 2. Mémoire centrale (« mémoire rapide », MR)

| Caractéristique | Valeur | Source |
|---|---|---|
| Technologie | tores de ferrite, sélection par demi-courant | ONDE |
| Taille | 1 à 8 blocs [COURS, BPD] ou 2 à 8 [B61, ONDE] de 4 096 catènes | |
| Capacités (B61) | 2 blocs : 8 192 catènes ; 4 : 16 384 ; 8 : 32 768 | B61 p.11 |
| Bloc | 24 niveaux (+3 de clé) de 64 × 64 tores ; contrôle de sélection | B61 p.10 ; ONDE |
| Cycle / accès | 10 µs [B61, ONDE] ; 11 µs [COURS, BPD] (?) | |
| Débit | un catène par cycle pour toute la machine | B61 p.11 |
| Registre Z | passage obligé de tout catène (31 positions selon ONDE) | COURS p.5 ; ONDE p.21 |

## 3. Catène, codages, clés

- **Catène** : 24 bits + 3 bits de clé (27). Bits numérotés de 1 (droite) à 24 (gauche).
  [B61 p.15, p.26]
- Contenus : instruction (code A) ; 6 chiffres DCB ; 4 caractères de 6 bits ; binaire 24 bits ;
  catène qualitatif ou « géographique » (24 indicateurs). [B61 p.15-17]
- **Code interne alphanumérique** : 60 caractères (26 lettres, 10 chiffres, 23 signes, espace) ;
  code = 2 bits de colonne + 4 bits de ligne ; chiffres = DCB précédé de `10` ; lettres avant
  chiffres ; 4 codes inutilisés. Table complète : `data/charset.yaml`. [B61 p.16-17]
- **Code carte du Gamma 60** : code Bull standard pour lettres et chiffres (1 trou pour un
  chiffre, 2 pour une lettre, zones 7/8/9), étendu : O (7-12) et I (8-12) distincts de 0 et 1,
  signes sur 3 trous au plus. [B61 p.17] Le code Bull standard lui-même n'est pas tabulé dans
  nos sources (U-21).
- **Clé de contrôle** :
  - B61 : 1 bit de parité des bits 16-24 + 2 bits = reste mod 3 des bits 1-15 (vus comme un
    entier) ; découpage aligné sur celui des instructions. [B61 p.26]
  - COURS : reste de la division par 7 du nombre de 24 bits (aussi pour les transferts
    partiels de 15 ou 9 bits). [COURS p.11-12]

## 4. Nombres arithmétiques

- 2 catènes : signe (1 b) + 1er chiffre d'exposant (3 b) ; 2e chiffre d'exposant (4 b) ;
  10 chiffres DCB de mantisse (4 dans la 1re catène, 6 dans la 2e). [B61 p.18]
- Signe : bit 24 de la 1re catène, 0 = +, 1 = − (signe et valeur absolue). Chiffre des
  dizaines de l'exposant en binaire (0-7, bits 23-21), chiffre des unités en DCB (0-9,
  bits 20-17). [B61 p.18]
- Exposant biaisé de 40 (stocké E = 0-79, exposant réel E − 40) pour éviter les exposants
  négatifs. Mantisse m1…m10 lue comme la fraction 0.m1…m10 :
  valeur = ± 0.m1…m10 × 10^(E − 40). [B61 p.18]
- Virgule flottante (normalisée) : exposant choisi pour que 0,1 ≤ mantisse < 1 (m1 ≠ 0),
  normalisation automatique par ARIT. Virgule programmée : exposant entre 40 et 50 ; nombre
  de décimales (« position de la virgule », 10 à 0) = 50 − E. [B61 p.18]
- Exemples [B61 p.18] : + 0,00482 = `+ 39 0482 | 000000` (non normalisé) ; + 325,42 en
  flottant = `+ 43 3254 | 200000` ; + 4832 = `+ 50 0000 | 004832` (virgule en position 0)
  ou `+ 45 0483 | 200000` (position 5).

## 5. Unité centrale

### 5.1 Registres
Liste lisible par programme : `data/registers.yaml` (tailles incertaines marquées U-23, U-39) ;
vue anglaise : `wiki/REGISTERS.md`.

**Noms affichés** (colonne « Affichage `en` / `fr` », utilisée par les traces et le débogueur) :
- **MAJUSCULES** : nom attesté dans la langue affichée (`en` : B61, BAT72 ; `fr` : COURS,
  ONDE, TFR) ;
- **minuscules** : initiales de la forme développée, proposées par l'émulateur, **non
  validées** ; la forme développée anglaise est alors une traduction de l'émulateur.

Un registre en plusieurs exemplaires est indexé à l'affichage (`pdc1`, `pdc2`, `CAR0`-`CAR3`).
Exemples : RAPA s'affiche `cpar` en anglais (*current program address register* ; le RAI de
l'élément servi, PAR chez BAT72) ; Z s'affiche `z`, car aucune source anglaise ne le nomme.

**Unité centrale et Distributeur de Programme**

| Registre | Affichage `en` / `fr` | Taille | Rôle | Emplacement | Source |
|---|---|---|---|---|---|
| Z | `z` / `Z` | 31 b (24 + 3 de clé + 4 de contrôle de sélection) | passage obligé de tout catène entre la mémoire et les canaux | UC | COURS p.5 ; ONDE §2.2.2.3 p.20-21 |
| RNE (Registre Numéro d'Élément) | `enr` / `RNE` | 7 b [p.53] ; 15 b selon p.14 (U-23) | n° de l'élément servi ; sélectionne ses RAI/RAC | DP | COURS p.13-14, p.53 |
| RAPA (Registre Adresse de Programme Actuel) | `cpar` / `RAPA` | 15 b | adresse de l'instruction courante, lue par une demande de transfert au DT | DP | COURS p.14 |
| RAPP (Registre Adresse de Programme Progressé) | `ipar` / `RAPP` | 15 b | RAPA + 1 ; recopié dans RAPA pour l'instruction suivante, ou dans le RAI après la directive qui lance l'élément | DP | COURS p.14-15 |
| REDP (Registre d'Entrée du Distributeur de Programme) | `pdir` / `REDP` | 24 b | reçoit chaque instruction lue | DP | COURS p.14 |
| RSDP (Registre de Sortie du Distributeur de Programme) | `pdor` / `RSDP` | 24 b | sortie du DP ; reçoit RAPP à chaque branchement (adresse de retour, rangée par RI) | DP | COURS p.14-15, p.42, p.54 |
| Chaîne propre du DP (registres B et C du DP) | `pdc` / `cdp` (×2) | 2 registres (taille non donnée, U-39) | tête et queue des séquences en attente du DP (SIMU, LIBE) ; B est le « registre spécial de mise en réserve » de COURS p.17 | DP | COURS p.17, p.36-38 |
| Registre A (analyse) | `A` / `A` | 24 b | reçoit le catène qualitatif ; testé par les branchements 01-24 | UC | B61 p.23, p.31 ; COURS p.54 |
| Registre B (opérateur) | `B` / `B` | 24 b | calculs sur les 15 bits droits | UC | B61 p.32 ; COURS p.55 |
| RAI (Registre d'Adresse Instruction ; IAR, PAR) | `IAR` / `RAI` | 128 × 21 b : 15 d'adresse + 2 de clé par 3 + **indice d'occupation dédoublé** (2) + 2 de contrôle de sélection | prochaine instruction de chaque élément | matrice MAP de l'UC | B61 p.22 ; COURS p.8, p.14 ; ONDE §2.2.1 p.16 |
| RAC (Registre d'Adresse Courante ; CAR, DAR, RAQ) | `CAR` / `RAC` | 128 × 19 b : 15 d'adresse + 2 de clé par 3 + 2 de contrôle de sélection ; 1 à 4 par élément | adresses courantes, +1 (ou −1) par transfert | matrice MAQ de l'UC | B61 p.22-23 ; COURS p.8, p.14 ; ONDE §2.2.1 p.16 |

Cycle d'une instruction [COURS p.14-15] : RNE ← n° de l'élément servi ; RAPA ← son RAI (par la
matrice MAP et le registre Z) ; RAPP ← RAPA + 1 ; le DP demande au DT le catène d'adresse
RAPA, qui arrive dans REDP ; il l'exécute (chargement d'un RAC, directive par RSDP, rangement
en MC par RSDP, coupure ou branchement) ; puis RAPA ← RAPP, et ainsi de suite jusqu'à la
directive qui lance l'élément : alors RAI ← RAPP et le RNE est effacé. Un branchement force
RAPA à l'adresse indiquée et envoie RAPP dans RSDP. [COURS p.15-16]

**Registres de chaque élément**

| Registre | Affichage `en` / `fr` | Taille | Rôle | Emplacement | Source |
|---|---|---|---|---|---|
| Registres de chaîne de reprise B, C (I1, I2 chez ONDE ; *temporary storage registers* chez B61) | `i1`, `i2` / `B`, `C` | 2 adresses (taille non donnée, U-39) | tête et queue de la chaîne de reprise | MC, adresses spécialisées (U-30) | B61 p.24-25 ; COURS p.24-31 ; ONDE §2 |
| Registre de Liaison (RLN ; *buffer register* chez B61) | `br` / `RLN` | 1 catène | tampon entre le cycle mémoire et le rythme de l'élément | élément | B61 p.23 ; COURS p.8 |
| Registre catène qualitatif | `qcr` / `rcq` | 24 b | indicateurs de l'élément, envoyés au registre A quand le DP le sert | élément | B61 p.23 ; COURS p.74, p.110 |

**Registres propres à certains éléments**

| Élément | Registre | Affichage `en` / `fr` | Taille | Rôle | Source |
|---|---|---|---|---|---|
| ARIT | P (principal) | `P` / `P` | 2 catènes | 1er opérande puis résultat (poids forts) ; P + S = accumulateur | B61 p.35 ; COURS p.65 |
| ARIT | S (secondaire) | `S` / `S` | 2 catènes | poids faibles, même signe que P, exposant de P − 10 | B61 p.35 ; COURS p.65 |
| ARIT | O (opérande) | `O` / `O` | 2 catènes | 2e opérande | B61 p.35 ; COURS p.65 |
| LOGI | K, L | `K`, `L` / `K`, `L` | 24 b chacun, à décalage, accès série | opérandes ; résultat dans L | B61 p.39 ; COURS p.110 |
| COMP | registres opérandes | `or` / `ro` (×2) | 1 catène chacun | opérande du RAC 0 ; opérande du RAC 1 ou 2 | COURS p.75 |
| COMP | registre longueur | `lr` / `rl` | 8 b (≤ 255) | longueur des zones, décomptée à chaque catène | COURS p.75 |
| TRAN | registre d'entrée | `ir` / `re` | 1 catène | données à traiter, lues caractère par caractère (inutilisé pour les cartes) | COURS p.86 |
| TRAN | registre de sortie (S) | `or` / `S` | 1 catène | résultat, composé caractère par caractère (inutilisé pour les cartes) | COURS p.86, p.89 |
| TRAN | registre cliché (C) | `cr` / `C` | 1 catène | cliché, fourni code-cliché par code-cliché | COURS p.86, p.89 |
| TRAN | registre directive et catène qualitatif | `dqr` / `rdq` | non donnée (U-39) | directives reçues du DP ; qualitatif formé pendant le travail | COURS p.87 |
| TRAN | index des registres d'entrée et de sortie | `ii`, `oi` / `ie`, `is` | non donnée (U-39) | position courante dans les registres d'entrée et de sortie | COURS p.89, p.108 |
| TRAN | registre de décomptage | `cdr` / `rd` | non donnée (U-39) | décompte la zone ; son passage par 0 termine l'opération | COURS p.108-109 |
| TRAN | matrice de transposition | `tm` / `mt` | 12 × 24 = 288 b | transposition lignes → colonnes des cartes | COURS p.87 ; ONDE §3.2 |
| TRAN | MIC (Matrice d'Interprétation des Codes ; « M.I.C. » chez B61) | `MIC` / `MIC` | 128 × 20 b [COURS] / 256 adresses [B61] / 128 × 21 b [ONDE] (U-12) | interprétation des codes, garnie par programme | COURS p.87 ; B61 p.38, p.64 ; ONDE §3.2 |
| TRAN | datum de reprise | `rd` / `dr` | 4 catènes en MC (1m-4m) | sauvegarde des registres d'entrée, de sortie et de leurs index | COURS p.108 |
| Tambour | RAE (Registre Adresse dans l'Élément) | `ear` / `RAE` | non donnée (U-39) | adresse tambour (piste × 256 + position), posée par DAO ; progresse avec le RAC | B61 p.53 ; COURS p.153 |
| Unisélecteur | registre de longueur de bloc | `blr` / `rlb` | non donnée (U-39) | reçoit le catène longueur de tête de bloc ; contrôle la lecture | COURS p.141 |
| Imprimante | mémoire d'une ligne | `lm` / `ml` | 1 ligne (120 caractères), à tores | contrôle de la frappe par écho | ONDE §2 p.10 |
| Imprimante | 2 compteurs d'interlignes | `lsc` / `ci` (×2) | sauts ≤ 255 interlignes | un par feuillet ; chargés par SDF et IMP, décomptés pendant le saut | COURS p.134 ; ONDE §2.5.3 p.27 |

**Nombre de RAC par élément** : ARIT 4 et LOGI 4, banalisés [B61 p.35 ; COURS p.110] ; COMP 3,
spécialisés [B61 p.36-37 ; COURS p.75] ; TRAN 3 (source, destination, cliché) [COURS p.88-89] ;
tambour 1 [COURS p.153] ; unisélecteur 1, ou 2 en marche continue, où il est vu comme un élément
double avec 2 RAI et 2 RAC [COURS p.141, p.148] ; lecteur-perforateur de cartes 2 [COURS p.125] ;
imprimante 1 [COURS p.134]. Lecteur de cartes, bande perforée et pupitre : non trouvé (U-39).

### 5.2 Distributeur de Programme (DP)
- Circuits de priorité sur les lignes DI ; une fois un élément choisi : RNE ← n°, catène
  qualitatif → registre A, RAPA ← RAI. [COURS p.6, p.14-15 ; B61 p.23]
- Lit et exécute instructions d'adresse, branchements et directives centrales **sans se
  libérer**, jusqu'à une directive d'élément (envoyée, RAI ← RAPP) ou une coupure ; il ne sert
  aucune autre demande entre-temps. [B61 p.28 ; COURS p.14-17]
- Ordre de traitement d'une coupure normale : (1) activer l'élément cité ou mettre la séquence
  dans sa chaîne s'il est occupé ; (2) vider la chaîne propre du DP ; (3) reprendre la chaîne
  de l'élément demandeur ou le libérer ; (4) servir une nouvelle DI. [COURS p.38]
- Ordre de grandeur : un dérouleur occupe le DP ≈ 100 µs pour lire un bloc en ≈ 50 ms ;
  canaux occupés 5 % de ce temps. [B61 p.24] Réception d'une directive par LOGI : 6 cycles,
  délais de priorité compris. [COURS p.120]

### 5.3 Distributeur de Données / Transferts (DT)
- Un transfert par cycle ; ordre préétabli selon la nature des éléments (tambour avant ARIT,
  sinon perte d'un tour de 20 ms). [B61 p.23-24]
- Chaque élément a un registre tampon d'un catène (RLN), rempli ou vidé par la mémoire en un
  cycle, puis traité au rythme de l'élément : le tambour (100 µs par catène) n'occupe ainsi le
  canal qu'un cycle sur dix, les neuf autres restant disponibles. [B61 p.23]
- Le RAC de l'élément augmente de un à chaque transfert, de sorte qu'il contient toujours
  l'adresse du catène suivant. [B61 p.22-23]
- Pour une même nature d'élément, les demandes de quantités passent avant les demandes
  d'instructions ; mais le DP passe avant COMP quand il alimente un lecteur de cartes (pour
  éviter un arrêt mécanique). [COURS p.6]
- Le DP passe par le DT pour ses propres lectures. [B61 p.24] Il émet pour cela des demandes
  de transfert « comme les autres unités ». [BAT72 p.102]
- Vocabulaire anglais de BAT72 (fig. 1) : Central Memory (CM), Central Processor (CP),
  Program Distributor (PD), Data Distributor (DD), Program Address Register (PAR = RAI),
  Data Address Register (DAR = RAC), Data Distribution / Collection Channels (DDC / DCC),
  Instruction / Data Transfer Request (ITR = DI / DTR = DTQ). Le DD organise une chaîne de
  priorité et commande l'ouverture des canaux par des vannes (*gates*) propres à chaque
  classe. Schéma redessiné : `archives/images/Gamma60-architecture-classes.svg`.
  [BAT72 p.100-101, fig. 1]

## 6. Éléments

### 6.1 Définition, états et cycle
- Élément = circuits de traitement + circuits de commande (programme local câblé) ; prend
  l'initiative des échanges (DI, DTQ). [B61 p.22]
- **États** [COURS p.13] : repos (aucune séquence) ; activité (RAI significatif), avec deux
  aspects : **attente** (ligne DI levée) et **opération** (travail autonome).
  - repos/activité = **indice d'occupation**, dans une position annexe du RAI, dédoublé pour le
    contrôle [ONDE p.5, p.16] ;
  - attente/opération = état de la ligne DI, non mémorisé. [COURS p.14]
- Registre de liaison (RLN, errata) : tampon d'un catène qui découple le cycle mémoire du
  rythme de l'élément. [COURS p.8 ; B61 p.23]
- **Catène qualitatif** : indicateurs d'un bit regroupés et transmis au registre A au moment
  où le DP sert l'élément ; pas d'interrogation à la demande. [B61 p.23 ; COURS p.6, p.15]
  Profils : `data/qualitative.yaml`.
- Numérotation : RNE de 7 bits ⇒ 128 éléments ; les tambours sont numérotés à partir de 100.
  [COURS p.51]

### 6.2 Directives préparatoires et opératoires [COURS p.40-42]
- Préparatoire : renseignement seulement (ex. DAO du tambour, sens et n° de dérouleur) ; le DP
  la transmet, exploite sa chaîne, puis sert les priorités ; l'élément redemande ensuite.
- Opératoire : lance le travail autonome ; RAI ← RAPP ; termine l'instruction complète.

### 6.3 Classes et raccordement [ONDE §2.1, §4.1 ; MAI]
- 5 ensembles de circuits d'armoire : c0, c1, 2 × c2, c3+c4 ; multiplexeur pour c3-c4
  (≤ 20 éléments, 2 au plus) ; 8 voies dans l'UC, 5 utilisées en standard.
- BAT72 parle de « 6 special circuits » de raccordement (c0, c1, c2 « 2 circuits », c3, c4) ;
  sa figure 1 montre 4 blocs (c0, c1, c2, c3-4) ; comptes divergents (U-32). [BAT72 p.100]
- c0 : pupitre (et LOGI selon ONDE et BAT72 ; c1 selon MAI ?) ; c1 : ARIT, COMP, TRAN ; c2 : tambours,
  unisélecteurs ; c3 : cartes, imprimantes ; c4 : bande perforée, machines à écrire.
- BAT72 : ARIT en décimal codé binaire, chiffres de 4 bits, contrôle mod 7 ; tambour 25 600
  catènes, 200 par piste. [BAT72 p.104]
- Répartition « suivant leurs performances et le degré d'urgence de leurs demandes de
  transfert ». ONDE annonce « 4 classes » mais en décrit 5 (0 à 4). [ONDE §3]
- Classe 3 : le Multiplexeur intercale sur le canal les catènes des éléments lents (cartes,
  imprimantes) ; classe 4 : éléments à très faible débit, raccordés par ce multiplexeur ou
  par un multiplexeur spécialisé. [ONDE §3.4-3.5]

### 6.4 Éléments partageables et d'E/S [AVG p.59 ; B61 p.42]
- Cartes, bande perforée, imprimantes, bandes : attribués à une seule UT, pas de chaîne de
  reprise, une seule opération par appel, zone MC obligatoire gérée par un élément virtuel.
- Éléments de traitement et tambour : partageables, avec chaîne de reprise.
- ≤ 40 éléments d'E/S ; un lecteur-perforateur compte pour 2 ; ≤ 12 pistes de cartes dont
  ≤ 6 lecteurs-perforateurs.

## 7. Simultanéité : coupures, SIMU, JOIN, chaînes, éléments virtuels

- Séquence élémentaire = d'une coupure à la suivante ; toutes ses instructions concernent
  l'élément de la coupure. [B61 p.28]
- **Catène vierge** obligatoire après chaque coupure (sur la branche ordinaire pour SIMU) :
  bits 1-15 = lien de chaîne ; bits 19-18 = compteur d'appels du JOIN ; exécutée, elle vaut un
  branchement « jamais » (7 bits de gauche à 0). [COURS p.35, p.42 ; B61 p.25]
- **Activation** : une coupure charge le RAI de l'élément cité avec l'adresse de la catène
  vierge qui la suit (coupure + 1) ; l'élément commence donc par l'exécuter, comme un
  branchement « jamais ». [COURS p.24, p.42]
- **Chaîne de reprise** : FIFO chaînée (registres B/C + catènes vierges) ; évite blocage et
  interblocage. [B61 p.24-25 ; COURS p.24-31] Si l'élément cité est actif : si C est vide,
  B = C = coupure + 1 ; sinon l'adresse coupure + 1 est écrite dans la catène vierge d'adresse
  C, puis C = coupure + 1. À sa libération : RAI ← B ; B ← contenu de la catène vierge
  d'adresse B, remise à 0 ; si B devient 0, C ← 0. Les séquences reprennent dans l'ordre où
  elles se sont présentées. [COURS p.24-26]
- **Exploitation d'une coupure normale**, dans l'ordre : (1) mettre en activité l'élément cité,
  ou mettre la séquence en attente sur sa chaîne ; (2) exploiter la chaîne propre du DP ;
  (3) exploiter la chaîne de l'élément demandeur, ou le libérer ; (4) seulement alors, servir
  une DI, qui n'est pas forcément celle de l'élément cité. [COURS p.38]
- **SIMU** : RAPA ← adresse de la branche extraordinaire, traitée d'abord ; RAPP (la catène
  vierge de la branche ordinaire) va dans les registres B et C propres au DP, chaînés comme
  ceux d'un élément ; le « registre spécial de mise en réserve » de COURS p.17 est ce B.
  Cascades permises sur les deux branches ; chaque branche commence par une coupure, sauf
  une qui continue de travailler pour l'élément qui a appelé la cascade. [COURS p.17, p.36-37]
- **JOIN** : coupure avec m = 1, 2 ou 3 conditions supplémentaires (bits 19-18) ; noté dans le
  C.C. de la coupure [B61 p.31] ou dans le X de la catène vierge [COURS p.52] selon le profil.
  La coupure n'est effective qu'à son (m + 1)-ième appel ; les appels sont comptés dans les
  positions 18-19 de la catène vierge qui la suit ; possible sur toute coupure sauf STOP.
  [COURS p.17-18, p.34-35] Sort des séquences arrivées avant la dernière : U-26.
- **Coupures spéciales** : « sans libération » de l'élément demandeur (C.C. A), qui ne permet
  donc pas l'exploitation de sa chaîne, et « sans observation de la disponibilité » (C.C. B),
  qui fait passer la séquence avant celles qui attendent sur la chaîne de l'élément et suppose
  son RAI libéré par une coupure de l'autre type ; pour les programmes d'incident.
  [COURS p.39, p.51]
- **Éléments virtuels** : PROT/LIBE sur une catène-image ; bit 24 = indice d'occupation,
  bits 1-15 = tête de chaîne (errata COURS p.31) ; 2e catène-image = queue. [COURS p.27-31 ;
  B61 p.25] PROT sur un élément libre pose l'indice et la séquence continue ; sur un élément
  occupé, elle attend sur sa chaîne, puis étapes (2), (3), (4). LIBE sans séquence en attente
  enlève l'indice ; sinon la première séquence en attente passe dans la chaîne propre du DP et
  sa catène vierge est effacée ; la séquence en cours continue dans les deux cas. [COURS p.37]
  Comparaison (contexte) : le sémaphore de Dijkstra (1968) associe aussi une liste d'attente
  à une variable partagée (opérations P/V), mais l'ordre de sortie de la liste y est
  explicitement indéfini [DIJ68 p.345, note 2] ; la chaîne d'un élément virtuel est FIFO
  [COURS p.27-31].

## 8. Éléments un par un

### ARIT [B61 p.35-36 ; COURS p.61-72 ; ONDE]
- Registres P (principal), S (secondaire, effacé avant chaque opération), O ; 2 catènes chacun ;
  P+S = accumulateur de 20 chiffres. 4 RAC banalisés (0-3 ; sans progression : Z U D T
  [COURS] ou Z F S T [B61]).
- C.C.1 : P (virgule programmée), N (normalisée), A (normalisée avec arrondi) [COURS] ;
  « P, N ou R » dans la table B61. C.C.2 : D (double capacité).
- Qualitatif : comparaisons en positions 1-6 (> < = ≥ ≤ ≠) ; signe du résultat 7 (= 0),
  8 (< 0), 9 (> 0) ; dépassement en virgule programmée → incident.
- Contrôle par reste mod 7 (« preuve par 7 »). Additionneur parallèle ; multiplication par
  multiples ×2, ×5, ≤ 3 additions par chiffre.
- Temps globaux : B61 200 / 350 / 550 / 150 µs (add / mul / div / cmp, transferts compris) ;
  COURS 100 / 300 / 600 µs.
- **Sémantique des directives** [COURS p.65-72 ; B61 p.35-36] :
  - P reçoit le 1er opérande et le résultat ; O le 2e opérande, toujours pris en MR (pas de
    `P` en O2) ; S reçoit les poids faibles, même signe que P, exposant de P − 10.
  - Les opérandes sont cadrés automatiquement selon leurs exposants ; le résultat est comparé
    à 0 (qualitatif 7 = 0, 8 < 0, 9 > 0), y compris pour le transfert.
  - C.C.1 `N` : normalisé (un report à gauche décale à droite et augmente l'exposant ; on ne
    perd jamais de poids forts). `P` : virgule à la borne V (0-10) du registre P, exposant
    = 50 − V ; poids forts perdus ⇒ incident (B61 : dépassement signalé au qualitatif).
    `A` / `R` : normalisé puis arrondi (`MUL.A` = `MUL.N` + `ARR`).
  - Arrondi au plus proche : ajout de 5 au premier chiffre de S, report éventuel sur le dernier
    chiffre de P ; porte toujours sur la dernière position de P.
  - C.C.2 `D` (double capacité) : range P puis S (4 catènes) ; le RAC résultat est alors
    obligatoirement sans progression (Z U D T / Z F S T).
  - Opérandes O1, O2, R : `0-3` RAC avec progression (+2 par nombre), `Z U D T` / `Z F S T`
    RAC ramené à sa valeur initiale, `P` (registre P ; pas en O2 ; en R : résultat laissé dans
    l'accumulateur).
  - ADD, SOU/SUB, MUL : S effacé avant l'opération, même si O1 = P ; SOU : O1 − O2.
  - DIV / DIR : quotient dans S, reste dans P ; DIV transfère S dans P (puis en R), DIR range
    le reste ; C.C.1 porte sur le quotient (virgule à 0 : division arrêtée aux unités) ;
    `D` n'a de sens que pour DIR (reste puis quotient à des adresses successives).
  - TER/TRA : R ← O1 par le registre P, mis sous la forme demandée (P / N) ; S effacé sauf si
    O1 = P ; perte de poids forts ⇒ incident. Interdit sur des catènes non numériques
    (tétrade non DCB ⇒ incident).
  - MPD/MPT, DPD/DPT : exposant ± V (0-15), sans décalage ni C.C.1 ; `D` possible si O1 = P.
  - ISI/RSI, PVA/AVA : transfert O1 → R avec inversion de signe / valeur absolue ; ni C.C.1, ni
    V, ni O2 ; S effacé sauf si O1 = P (alors `D` possible). [COURS p.71 ; TFR p.2]
  - CVA/CAV, CAL : comparaison de O1 et O2 (valeurs absolues / algébriques), sans cadrage
    préalable ; résultat au qualitatif 1-6 (> < = ≥ ≤ ≠) ; rien en R. [COURS p.71-72 ; B61 p.35]
  - ARR/ROF : opérande P + S, arrondi sur la dernière position de P, R = destination ; S effacé
    à la fin. [COURS p.72]
  - Preuve par 7 : clé = reste de la division décimale de chaque opérande par 7 ; l'opération
    est refaite sur les clés et comparée à la clé du résultat. [COURS p.66 ; B61 p.35]
  - Points non tranchés (zéro, troncature, reste de DIR, signalement des incidents) : U-35 à
    U-37.

### LOGI [B61 p.39-40 ; COURS p.111-121]
- Registres K et L, 24 b, à décalage série ; résultat dans L ; 4 RAC.
- Opère en série, « ce qui conduit à un opérateur très simple ». [ONDE §3.1]
- Chargement de K et L par deux directives avec décalage circulaire à droite de V positions.
- Qualitatif : L > K, L < K, L = K, inclusion, exclusion, réunion tout à 1.
- **Sémantique des directives** [COURS p.110-119] : directives sans variable libre ; X = `V`
  (« l », 00 à 24 : décalage, longueur ou les deux) et `R` (RAC 0-3 avec progression, Z U D T
  sans progression, ou `L` : résultat laissé dans L). « Les l premières positions » = les l bits
  de droite (bits 1 à l).
  - TCK / TCL : charge K / L depuis la MR (adresse du RAC cité en R) avec rotation à droite de
    l positions (contenu maintenu sur tout le registre) ; `L` en R sans objet.
  - Toutes les autres, sauf CBL : rangement de L en MR si un RAC est cité en R (L conservé).
  - TKL : L ← l bits de droite de K, reste de L effacé ; K inchangé.
  - MCL/SHL : rotation de L à droite de l positions (décalage à gauche de n = rotation de 24 − n).
  - IKL : l bits de droite de L ← ceux de K, reste de L maintenu ; puis K et L tournés à droite
    de l positions.
  - FZL / FUL (FOL) : l bits de droite de L forcés à 0 / 1, puis rotation de L de l positions.
  - ADD / SOU (SUB) : L ← L + (l bits de droite de K) ; SOU donne |L − K| (« redressé ») ;
    K inchangé.
  - MUL : multiplicande = l bits de droite de K ; multiplicateur dans L ; produit dans L cadré
    à droite ; bits 24 − l de K effacés ; somme des capacités ≤ 24.
  - DIV : diviseur = l bits de droite de K ; dividende dans L (≤ 23 bits) ; quotient dans les
    24 − l bits de droite de L, reste dans les l bits de gauche ; bits 24 − l de K effacés ;
    quotient trop long ⇒ incident.
  - FCL/FLC : complément des l bits de droite de L, cadrage inchangé.
  - INT / REU : ET / OU des l bits de droite de K et L, résultat dans L (reste de L inchangé).
  - CBL/BLC : compare les l bits de droite de K et de L ; K et L inchangés ; rien en R ;
    qualitatif 1 L > K … 6 (comparaisons, positions 2-6 illisibles dans l'OCR : U-38),
    7 L inclus dans K, 8 non inclus, 9 K inclus dans L, 10 non inclus, 11 K et L disjoints,
    12 empiètement, 13 réunion tout à 1, 14 réunion avec au moins un 0. [COURS p.118-119]
  - Temps (cycles MR) : alimentation d'une directive 6 ; TCK/TCL 6 + l/2 ; MCL, IKL, FZL, FUL
    l/2 ; TKL, ADD, FCL, INT, REU, CBL 12 ; SOU 24 ; MUL 6 + 12n − l/2 ; DIV 24 + 12(24 − l) ;
    rangement + 3. [COURS p.120-121]
- Temps (cycles MR) : réception d'une directive 6 ; ADD 12 ; SOU 24 ; MUL 6 + 12n (n = nombre
  de 1 du multiplicateur) ; rangement + 3. [COURS p.120-121]

### COMP [B61 p.36-37 ; COURS p.73-78]
- Zones de 1 à 255 catènes, binaire pur, poids fort d'abord ; deux registres d'opérande, un
  registre de longueur ; 3 RAC spécialisés (0 variable ; 1, 2 bornes ou 2e terme).
- Travaille en parallèle, comme ARIT. [ONDE §3.2]
- Fonctions secondaires : seul transfert MC → MC ; effacement de zone.
- Temps : B61 30 / 50 / 10 µs par catène ; COURS 5+3L, 5+5L, 2+L, 2+3L cycles.
- Incidents : 16-17 décomptage, 18-19 comparaison, 20-21 transfert, 22 directive décodée
  erronée, 23 longueur > 255, 24 regroupement.
- Directives : X = longueur en catènes (≤ 255) ; une longueur nulle n'exécute rien et laisse le
  qualitatif vierge ; RAC 0 implicite ; le C.C. nomme le RAC 1 ou 2 quand un seul est utilisé
  (CMP, TRR). [COURS p.75]
- Déroulement : les demandes de transfert des opérandes sont émises en avance sur la
  comparaison ; le travail s'arrête à la première inégalité ou au passage à 0 du décomptage ;
  en fin de CMP, le RAC 0 contient l'adresse du dernier catène comparé + 3, le RAC 1 ou 2
  + 2 ; en fin de CDB, les trois + 2 ; pour une longueur de 1 ou 2, contenu initial + longueur.
  EFL et TRR : RAC avancés de la longueur. [COURS p.75-77]
- Qualitatif de CDB : 1 x > p et q ; 2 x < p et q ; 3 p ≤ x ≤ q ; 4 x = p ; 5 x = q ;
  6 p < x < q ; 7 x nul ; 8 x tout à 1. CMP : 1 > ; 2 < ; 3 = ; 4-10 lus sur un scan partiel
  (U-49). [COURS p.76-77]

### TRAN (TRAD) [B61 p.37-39 ; COURS p.83-110]
- Transcodage, mise en page, condensation/expansion, transposition ligne → colonne des cartes,
  mise en forme semi-logarithmique.
- Six sous-ensembles qui se comportent comme des éléments indépendants, chacun avec ses propres
  demandes de transfert (chaînes de priorité locales) : matrice de transposition, matrice
  d'interprétation des codes (MIC), entrée, sortie, directive, cliché. La MIC est regarnie par
  programme selon le code voulu (Bull, IBM, interne). [ONDE §3.2]
- Registres d'entrée, de sortie S, directive + catène qualitatif, index, décompteur ;
  datum de reprise de 4 mémoires en MC.
- MIC : 256 adresses [B61] / 128 × 20 b [COURS] / 128 × 21 b [ONDE] (?) ; matrice de
  transposition.
- Programme en deux niveaux : directives de phase puis RCL ; clichés (4 par catène) lus par
  DTQ sans passer par le DP. RAC0 source, RAC1 destination, RAC2 cliché.
- ≈ 15-20 µs par caractère ; contrôle de parité par caractère.

### Tambour (DRUM / TAMB) [B61 p.12, p.53 ; COURS p.152-154 ; ONDE]
- 128 pistes ; 204 catènes physiques par piste dont 200 adressables ; 3 000 tr/min (2 975
  selon ONDE) ; tour 20 ms ; accès moyen 10 ms ; 100 µs [B61] ou 98 µs [COURS] par catène.
- 1 RAC (adresse MC) ; adresse tambour dans le registre local RAE, posée par DAO :
  piste × 256 + position (0-199), adresses discontinues. Jusqu'à 4 tambours.
- 98 µs par position (20 000 / 204) ; 100 µs en moyenne sur un long transfert, la zone de
  4 positions servant à la commutation de piste : les « 100 µs » de B61 sont donc une moyenne.
  [COURS p.152-153]
- En code B, DAO prend l'adresse continue 0-25 599 ; le programme de transposition la convertit
  en piste × 256 + position. RAE et RAC progressent à chaque catène ; au changement de piste,
  le RAE progresse de 57. Après un transfert, le qualitatif porte le RAE final dans ses
  15 positions de droite. [COURS p.153-154]
- Un catène qui n'est pas servi à temps coûte un tour de 20 ms. [B61 p.24]

### Unisélecteurs et dérouleurs (MATA / DERU) [B61 p.13, p.26, p.53-55 ; COURS p.137-151]
- L'élément est l'unisélecteur (≤ 10, 2 groupes de 5, 24 dérouleurs par groupe, 48 au total ;
  un dérouleur peut être desservi par 2 ou 3 unisélecteurs [ONDE §3.3]) ;
  câblage : U1, U2 → dérouleurs 1-12 ; U3 → 5-16 ; U4, U5 → 13-24. Petits Gamma 60 :
  3 unisélecteurs, 6-8 dérouleurs ; la plupart : 5 et 12-18.
- Bande mylar 12,7 mm, 8 pistes : catène sur 6 pistes × 4 colonnes ; clé sur la 7e (en face
  des 3 premières colonnes) ; parité par colonne sur la 8e.
- Blocs de 16 à 4 095 catènes, avec un catène de longueur (en bits) en tête et en fin ;
  espaces de 2 cm ; 27,5 catènes/cm ; bobines 730 m / 1 100 m (1,6 / 2,4 M catènes).
- 1,90 m/s ; 190 µs par catène instantané [B61, ONDE] ; 266 µs [COURS] (?) ; moyenne
  230 µs [B61] / 315 µs [COURS] avec les espaces. Lecture 2 sens, écriture avant avec
  relecture. Registre de longueur de bloc ; mémoires par dérouleur (interdiction d'écriture,
  occupation).
- Modes discontinu / continu (« programmes standard ») ; blocs-marques de 16 catènes à 0 ;
  JUM (lecture sans transfert) ; DEL (zones défectueuses).
- Le catène longueur donne, selon le COURS, le nombre de catènes du bloc : il n'est pas
  transféré mais gardé dans un registre de l'unisélecteur ; en écriture, le bloc est composé en
  mémoire avec ses deux catènes longueur, et le RAC pointe le premier. [COURS p.140-141]
- Lecture avant : le RAC progresse ; lecture arrière : il est garni de l'adresse du dernier
  catène et régresse ; l'image en mémoire est la même. [COURS p.141]
- Marche discontinue : 5 ms d'accélération et 5 ms de décélération par bloc ; rebobinage à
  3 m/s (4 min pour 730 m). [COURS p.138-139]
- Directives : préparatoires (ECR / WRI, LAV / REF, LAR / REB), avec le n° du dérouleur,
  rémanentes au-delà des coupures ; d'exécution, sans variable libre (TRA, SAU / JUM,
  EFF / DEL, ECM / WRM) ; de service (REB / SPO, REM / SPN, MAN, MAI), après lesquelles
  l'unisélecteur redemande aussitôt une instruction pendant que le dérouleur travaille seul et
  signale son occupation (position 21) ; une directive d'exécution sur un dérouleur occupé
  attend la fin du service. La coupure porte sur l'unisélecteur, qui a le RAC et la chaîne de
  reprise. [COURS p.145-147]
- Qualitatif : 15 ou 16 interdiction d'écriture (U-48), 18 mauvaise lecture ou enregistrement,
  19 bloc-marque, 20 approche de fin de bande, 21 dérouleur occupé, avec 23 ; 24 incidents
  nécessitant une intervention (sécurité d'appel, circuits). [COURS p.137-150]

### Cartes [B61 p.42-43]
- 300 cartes/min ; magasin H1 3 000 ; piste secondaire S (800 vierges) ; case de réception
  2 800 ; cases Sp1, Sp2 de 700 ; double lecture RS1/RS2 ; contrôle de perforation RS5 ;
  mouvements partiels de piste ; interclassement lecture + perforation ≈ 300 cartes/min.
- D.M.F. / D.M.I. allument des voyants sur la machine et le pupitre.

### Imprimante [B61 p.45-47]
- 120 positions, 59 caractères, 300 lignes/min ; cylindre 300 tr/min ; contrôle par écho des
  marteaux ; papier ≤ 180 espacements, pas 1/8", interligne 1/6", perforations Carroll ;
  double entraînement indépendant (2 carbones) ; saut contrôlé par perforation rectangulaire
  (« référence de feuille » dans le qualitatif) ; SKI = saut du 2e papier ; mémoire tampon
  d'une ligne [ONDE].

### Bande perforée [B61 p.43-45]
- Lecteur photoélectrique 5/8 pistes, 300 car/s, 2 sens, 3 caractères par catène, contrôle
  d'imparité (8 pistes) ; perforateur 25 car/s non contrôlé.

### Pupitre [B61 p.47-48 ; ONDE ; MAI]
- Machine à écrire (10 car/s) ; programme résident de « gestion de la machine à écrire » ;
  lancement d'un programme si les éléments et la zone mémoire sont disponibles ; lecteur et
  perforateur de bande pour le journal. Seule source d'interruption prioritaire. Statut
  d'élément discuté (?) : « pas un élément d'E/S » [B61 p.47] mais coupure DESK.

## 9. Logiciel système et mémoire [MAI ; B61 p.48]
- GGZ : superviseur résident en début de mémoire (tables, opérateur, chargement, tampons,
  incidents) ; GGU : noyau ≈ 3 800 mots, topogrammes, implantation fixe ou variable, mise en
  attente des UT, jobs (D3).
- UT = programme assemblé (code C) puis distribué (D2), valeurs figées ; phases (overlays).
- Contenu de la MC : outre les programmes et données, les registres I1/I2 (B/C) de chaque
  élément « en Mémoire Centrale à des adresses spécialisées » [ONDE §2] (adresses : U-30) ;
  les catènes-image des éléments virtuels, à des adresses choisies par le programmeur (ex. 1 000
  et 1 001) [COURS p.27-31] ; les catènes vierges dans le code [COURS p.24-31] ; les mémoires de
  manœuvre, placées à la fin du sous-programme [COURS p.47-49] ; la zone MC associée à chaque
  opération d'E/S [AVG p.59 ; B61 p.42]. Hors MC : RAI, RAC (matrices de l'UC), registres A et B,
  registres du DP. [B61 p.22-23 ; COURS p.14]

## 10. Contrôles [B61 p.26, p.35 ; ONDE]
Clé sur tous les transferts ; mod 7 dans ARIT ; parité TRAN et bande perforée ; double lecture
des cartes ; relecture bande ; écho imprimante ; contrôle de sélection d'adresse en MC ;
décodage des directives (COMP position 22).

## 11. Divergences connues

| Sujet | Valeurs | Sources |
|---|---|---|
| Cycle MC | 10 µs / 11 µs | B61, ONDE / COURS, BPD |
| Clé | parité + mod 3 / mod 7 | B61 / COURS |
| Temps ARIT | 200/350/550 / 100/300/600 µs | B61 / COURS |
| JOIN en code B | C.C. de la coupure / X de la catène vierge | B61 / COURS |
| Bande | 190 / 266 µs ; 230 / 315 µs moyen ; 27,5 / ~30 cat/cm | B61 / COURS ; ONDE |
| Tambour | 100 / 98 µs par catène | B61 / COURS |
| MIC | 256 / 128×20 / 128×21 | B61 / COURS / ONDE |
| RNE | 7 / 15 bits | COURS p.53 / p.14 |
| Classe de LOGI | 0 / 1 | ONDE / MAI |
| Pupitre | élément / pas un élément d'E/S | ONDE, table B61 / texte B61 |
| Coquilles B61 | accès tambour « 10 µs » (10 ms) ; « 37 768 » (32 768) ; « nine » phases (11) | B61 p.12, 29, 38 |

## 12. Profils
`data/profiles.yaml` réunit les paramètres qui changent entre COURS et B61. L'émulateur doit
pouvoir fonctionner avec l'un ou l'autre ; défaut : B61 (machine livrée).

Les écarts de pure traduction (mnémoniques, lettres des RAC sans progression Z U D T / Z F S T,
C.C.1 d'ARIT A / R) ne sont pas des divergences de machine : ils relèvent de la langue du
code B (`fr` / `en`, `data/directives.yaml`).

## Clés des sources
Voir `SOURCES.md`. B61 = Bull 1961 ; COURS = Bull, *Cours de programmation Gamma 60* ;
BPD = *Preliminary Description* ; ONDE = *L'Onde électrique* 1960 ; DR-W/DR-E = P. Dreyfus
1958 ; BAT72 ; TS ; MAI ; MAS ; AVG ; NAM.

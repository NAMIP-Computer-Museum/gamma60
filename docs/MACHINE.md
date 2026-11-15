# Le Bull Gamma 60 — spécification de référence (v2)

Synthèse de ce qui est documenté. Chaque fait porte sa source (clés en fin de fichier ; pages
imprimées). Ce qui est incertain ou contradictoire est marqué **(?)** et détaillé dans
`UNKNOWNS.md`. Jeu d'instructions : `ISA.md`. Technologie matérielle : `HARDWARE.md`.
Histoire : `HISTORY.md`.

**Deux états de la machine coexistent dans les sources** (voir §12 et `data/profiles.yaml`) :
- profil **COURS** : *Cours de programmation Gamma 60* (~1958-59) — mnémoniques françaises,
  cycle 11 µs, clé mod 7 ;
- profil **B61** : *Gamma 60 Data Processing System* (1961) — mnémoniques anglaises, cycle
  10 µs, clé parité + mod 3.

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
| Capacités (B61) | 2 blocs : 8 192 catènes ; 4 : 16 384 ; 8 : 32 768 | B61 p.12 |
| Bloc | 24 niveaux (+3 de clé) de 64 × 64 tores ; contrôle de sélection | B61 p.10 ; ONDE |
| Cycle / accès | 10 µs [B61, ONDE] ; 11 µs [COURS, BPD] (?) | |
| Débit | un catène par cycle pour toute la machine | B61 p.12 |
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
- Exposant biaisé de 40 (stocké 0-79). Virgule flottante (normalisée) ou virgule programmée
  (exposant entre 40 : 10 décimales, et 50 : 0 décimale). [B61 p.18]

## 5. Unité centrale

### 5.1 Registres

| Registre | Taille | Rôle | Emplacement | Source |
|---|---|---|---|---|
| RNE | 7 b (15 selon p.14 ?) | n° de l'élément servi ; sélectionne ses RAI/RAC | DP | COURS p.14, p.53 |
| RAPA | 15 b | adresse de l'instruction lue | DP | COURS p.14 |
| RAPP | 15 b | RAPA + 1 ; recopié dans le RAI après une directive | DP | COURS p.14-15 |
| REDP | 24 b | reçoit chaque instruction lue | DP | COURS p.14 |
| RSDP | 24 b | sortie du DP ; reçoit RAPP à chaque branchement (adresse de retour, rangée par RI) | DP | COURS p.15, p.42, p.54 |
| Chaîne propre du DP | 2 registres | séquences en attente du DP (SIMU, LIBE) | DP | COURS p.36-38 |
| Registre A (analyse) | 24 b | reçoit le catène qualitatif ; testé par les branchements 01-24 | UC | B61 p.23, p.31 ; COURS p.54 |
| Registre B (opérateur) | 24 b | calculs sur les 15 bits droits | UC | B61 p.32 ; COURS p.54 |
| RAI (IAR, RAP) | 128 × 15 b + clé + **indice d'occupation dédoublé** | prochaine instruction de chaque élément | matrice MAP de l'UC | B61 p.22 ; COURS p.8, p.14 ; ONDE p.5, p.16 |
| RAC (CAR, DAR, RAQ) | 128 × 15 b, 1 à 4 par élément | adresses courantes, +1 (ou −1) par transfert | matrice MAQ de l'UC | B61 p.22-23 ; COURS p.8, p.14 |
| Registres B et C de chaque élément | 15 b | tête et queue de la chaîne de reprise | MC, adresses spécialisées (ONDE) | B61 p.24-25 ; COURS p.24-31 |

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
- Pour une même nature d'élément, les demandes de quantités passent avant les demandes
  d'instructions ; mais le DP passe avant COMP quand il alimente un lecteur de cartes (pour
  éviter un arrêt mécanique). [COURS p.6]
- Le DP passe par le DT pour ses propres lectures. [B61 p.24]

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
- c0 : pupitre (et LOGI selon ONDE ; c1 selon MAI ?) ; c1 : ARIT, COMP, TRAN ; c2 : tambours,
  unisélecteurs ; c3 : cartes, imprimantes ; c4 : bande perforée, machines à écrire.

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
- **Chaîne de reprise** : FIFO chaînée (registres B/C + catènes vierges) ; évite blocage et
  interblocage. [B61 p.24-25 ; COURS p.24-31]
- **SIMU** : le DP traite d'abord la branche extraordinaire, la suite ordinaire passant par sa
  chaîne propre ; en cascade, chaque branche commence par une coupure. [COURS p.36-37]
- **JOIN** : coupure avec m = 1, 2 ou 3 conditions supplémentaires (bits 19-18) ; noté dans le
  C.C. de la coupure [B61 p.31] ou dans le X de la catène vierge [COURS p.52] selon le profil.
- **Coupures spéciales** : « sans libération » de l'élément demandeur (C.C. A) et « sans
  observation de la disponibilité » (C.C. B), pour les programmes d'incident. [COURS p.39, p.51]
- **Éléments virtuels** : PROT/LIBE sur une catène-image ; bit 24 = indice d'occupation,
  bits 1-15 = tête de chaîne (errata COURS p.31) ; 2e catène-image = queue. [COURS p.27-31 ;
  B61 p.25]

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

### LOGI [B61 p.39-40 ; COURS p.111-121]
- Registres K et L, 24 b, à décalage série ; résultat dans L ; 4 RAC.
- Chargement de K et L par deux directives avec décalage circulaire à droite de V positions.
- Qualitatif : L > K, L < K, L = K, inclusion, exclusion, réunion tout à 1.
- Temps (cycles MR) : réception d'une directive 6 ; ADD 12 ; SOU 24 ; MUL 6 + 12n (n = nombre
  de 1 du multiplicateur) ; rangement + 3. [COURS p.120-121]

### COMP [B61 p.36-37 ; COURS p.73-78]
- Zones de 1 à 255 catènes, binaire pur, poids fort d'abord ; deux registres d'opérande, un
  registre de longueur ; 3 RAC spécialisés (0 variable ; 1, 2 bornes ou 2e terme).
- Fonctions secondaires : seul transfert MC → MC ; effacement de zone.
- Temps : B61 30 / 50 / 10 µs par catène ; COURS 5+3L, 5+5L, 2+L, 2+3L cycles.
- Incidents : 16-17 décomptage, 18-19 comparaison, 20-21 transfert, 22 directive décodée
  erronée, 23 longueur > 255, 24 regroupement.

### TRAN (TRAD) [B61 p.37-39 ; COURS p.83-110]
- Transcodage, mise en page, condensation/expansion, transposition ligne → colonne des cartes,
  mise en forme semi-logarithmique.
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

### Unisélecteurs et dérouleurs (MATA / DERU) [B61 p.13, p.26, p.53-55 ; COURS p.137-151]
- L'élément est l'unisélecteur (≤ 10, 2 groupes de 5, 24 dérouleurs par groupe, 48 au total) ;
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

## 10. Contrôles [B61 p.26, p.35 ; ONDE]
Clé sur tous les transferts ; mod 7 dans ARIT ; parité TRAN et bande perforée ; double lecture
des cartes ; relecture bande ; écho imprimante ; contrôle de sélection d'adresse en MC ;
décodage des directives (COMP position 22).

## 11. Divergences connues

| Sujet | Valeurs | Sources |
|---|---|---|
| Cycle MC | 10 µs / 11 µs | B61, ONDE / COURS, BPD |
| Clé | parité + mod 3 / mod 7 | B61 / COURS |
| Mnémoniques | anglaises / françaises | B61 / COURS, BPD |
| Temps ARIT | 200/350/550 / 100/300/600 µs | B61 / COURS |
| JOIN en code B | C.C. de la coupure / X de la catène vierge | B61 / COURS |
| RAC sans progression | Z F S T / Z U D T | B61 / COURS |
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

## Clés des sources
Voir `SOURCES.md`. B61 = Bull 1961 ; COURS = Bull, *Cours de programmation Gamma 60* ;
BPD = *Preliminary Description* ; ONDE = *L'Onde électrique* 1960 ; DR-W/DR-E = P. Dreyfus
1958 ; BAT72 ; TS ; MAI ; MAS ; AVG ; NAM.

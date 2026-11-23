# Bandes magnétiques du Gamma 60 : ruban, blocs, contrôles, marche discontinue et continue

Description technique détaillée du sous-système de bandes magnétiques, tel que documenté, puis
de sa modélisation dans l'émulateur (`src/gamma60/elements/tape.py`). Les faits viennent de
`archives/docs/Bull-cours-programmation-gamma60.pdf` [COURS], de
`archives/docs/Bull-1961-Gamma60-Data-Processing-System.pdf` [B61] et de
`archives/docs/Davous-OndeElectrique-1960-Gamma60.pdf` [ONDE]. Ce qui n'est pas documenté est
marqué *hypothèse* avec son inconnue (U-xx, voir `UNKNOWNS.md`). Voir aussi `MACHINE.md`
(§ Unisélecteurs et dérouleurs) et `ISA.md` (directives).

Pages du COURS : numéros imprimés en bas de page.

Les mnémoniques sont donnés en `en` (B61) / `fr` (COURS) : MATA / DERU pour l'élément
unisélecteur.

## 1. Le ruban

### 1.1 Support et pistes
- Ruban de mylar de 12,7 mm, couvert d'oxyde magnétique ; les catènes y sont enregistrés tels
  qu'en mémoire rapide, en général en code interne [COURS p.136].
- 8 pistes parallèles, **aucune piste de service** : ni prémarquage, ni signalisation des zones
  défectueuses ; le ruban n'a besoin d'aucune préparation [COURS p.136].
- Une **colonne** est l'ensemble des 8 monades côte à côte sur les 8 pistes. Un catène occupe
  **4 colonnes consécutives** [COURS p.136-137 ; B61 p.13, p.26] :

  | Pistes | Contenu |
  |---|---|
  | 1-6 | les 24 monades du catène (6 × 4) |
  | 7 | les 3 monades de la clé du catène, en face des 3 premières colonnes ; la 4e reste inutilisée |
  | 8 | une clé de parité par colonne, sur les 6 monades de données de la colonne |

  La clé de la piste 7 est la clé du catène en mémoire : « clef par 7 » dans le COURS
  (profil COURS : mod 7), parité des 9 bits de poids fort + reste mod 3 des 15 bits de poids
  faible dans B61 (profil B61) [COURS p.137 ; B61 p.26].

### 1.2 Enregistrement
- **Modulation de phase** : chaque monade est représentée par deux points magnétisés en sens
  opposés ; c'est le sens du changement de magnétisation qui donne 0 ou 1. Ce codage rend
  moins sensible aux défauts d'homogénéité de l'oxyde et permet l'**auto-synchronisation
  piste par piste** à la lecture, sans piste d'horloge [COURS p.136].
- À la lecture, une monade produit 1 front (monades voisines différentes) ou 2 fronts
  (monades voisines égales), dont un seul, au centre, est significatif. Chaque front
  significatif ouvre une fenêtre d'environ 3/4 de monade pendant laquelle les autres fronts sont
  ignorés ; ce mécanisme absorbe des écarts de vitesse de 1 à 2 % [COURS p.139-140].

### 1.3 Densité, vitesse, débit
Les deux documents divergent ; l'émulateur prend la valeur du profil.

| Grandeur | COURS (~1958-59) | B61 (1961) |
|---|---|---|
| densité | 79 monades/cm par piste, soit environ 20 catènes/cm [p.137] | 27,5 catènes/cm [p.13] |
| fréquence par piste | 15 kc/s [p.139] | 21 kc/s [p.13] |
| temps d'un catène | 266 µs [p.139] | 190 µs [p.13] |
| temps moyen, espaces compris (blocs de 250) | 315 µs [p.139] | 230 µs [p.13] |
| capacité 730 m / 1 100 m (blocs de 250) | 1,2 M / 1,8 M catènes [p.138] | 1,6 M / 2,4 M catènes [p.13] |

Valeurs communes : vitesse de défilement 1,90 m/s en lecture comme en écriture ; lecture d'une
bobine de 730 m en marche continue en 6 min 20 s (9 min 30 s pour 1 100 m) ; rebobinage
autonome à 3 m/s en moyenne (pointe 3,8 m/s), soit 4 min pour 730 m [COURS p.139 ; B61 p.13].

Vérification (calcul, pas une source) : en B61, un bloc de 250 catènes occupe 250 / 27,5 ≈
9,1 cm, plus 2 cm d'espace : 11,1 cm à 190 cm/s ≈ 58 ms, soit ≈ 234 µs par catène, ce qui
retrouve les 230 µs. En COURS : 12,5 + 2 = 14,5 cm ≈ 76 ms, soit ≈ 305 µs (315 µs annoncés).

## 2. Organisation en blocs

### 2.1 Pourquoi des blocs
On ne lit ou n'écrit correctement qu'à la vitesse normale ; le ruban ne peut ni s'arrêter ni
repartir sur un dixième de millimètre. Les catènes sont donc groupés en **blocs**, séparés par
des **espaces d'arrêt-marche** non enregistrés : le bloc est le *quantum* de lecture et
d'écriture, on ne s'arrête qu'entre deux blocs [COURS p.137].

### 2.2 Structure d'un bloc normal
Sur le ruban, dans le sens avant [COURS p.137] :

```
 ... E | P | L | U .................... U | L | P | E ...
       |2 c|1 c|  16 à 4 095 catènes      |1 c|2 c|
```

| Zone | Longueur | Rôle |
|---|---|---|
| **E** espace d'arrêt-marche | 2 cm | magnétisé en continu sur toutes les pistes ; comprend l'espace d'arrêt proprement dit et la distance entre tête d'écriture et tête de lecture [COURS p.137, p.142] |
| **P** zone pilote | 2 catènes (8 colonnes) | `0 10 10 10 0` sur chaque piste : déclenche l'auto-synchronisation |
| **L** catène longueur | 1 catène | longueur de la zone utile, en binaire ; en tête **et** en fin de bloc, pour lire dans les deux sens |
| **U** zone utile | 16 à 4 095 catènes | l'information |

- **Zone pilote** : les 6 premières monades `0 1 0 1 0 1` n'ont que des fronts significatifs ;
  le premier front après l'espace (magnétisé en continu) peut être parasite, mais la base de
  temps qu'il déclenche masque le front suivant, et le front d'après est forcément significatif.
  Une seule paire `0 1` suffirait ; trois paires garantissent la prise de synchronisme malgré
  l'imprécision de la frontière. Les deux `0` finaux annoncent que le catène suivant est le
  catène longueur [COURS p.140-141].
- **Unité du catène longueur** : « mesurée en catènes » [COURS p.137], « expressed in bits »
  [B61 p.13]. L'émulateur suit le COURS (nombre de catènes).
- Le catène longueur n'est pas transmis en mémoire : l'unisélecteur le garde dans un registre et
  contrôle ainsi la longueur du bloc, que la directive ne peut pas donner (les blocs successifs
  ont des longueurs différentes) [COURS p.141].

### 2.3 Blocs-marque
- Blocs spéciaux de **16 catènes de zéros sur toutes les pistes**, avec une zone pilote au
  début et à la fin, **sans catène longueur** ; 16 parce que c'est la longueur minimale d'un
  bloc [COURS p.138 ; B61 p.54].
- **Reconnaissance** : la piste 8 porte une clé d'**imparité** ; une colonne d'un bloc normal
  contient donc toujours au moins un 1, même si ses 6 monades de données sont nulles. Une colonne
  entièrement nulle après les deux zéros de fin de zone pilote ne peut venir que d'un
  bloc-marque. Une seule suffirait ; par sécurité, l'unisélecteur attend **3 colonnes de zéros**
  avant de signaler la position 19 du qualitatif. Le bloc n'est pas transmis en mémoire
  [COURS p.138].
- **Écriture** par une directive spéciale (ECM / WRM), sans composer le bloc en mémoire
  [COURS p.138 ; B61 p.54].
- **Usage** : prévus pour marquer début et fin de ruban, ils servent en pratique à séparer
  fichiers, sous-fichiers et groupes d'articles. Une partie de fichier est encadrée de
  blocs-marque et de deux **blocs d'identification** identiques (un pour chaque sens de
  recherche) ; on cherche en sautant les blocs sans transfert (SAU / JUM) et l'on ne transfère
  que le bloc qui suit chaque marque, pour l'analyser [COURS p.144 ; B61 p.54].

### 2.4 Bobines
Bobines standard de 730 m et 1 100 m [COURS p.138 ; B61 p.13]. L'approche de la fin est
détectée par une **cellule photoélectrique** dont le faisceau, tangent à la bobine, est
découvert quand il reste environ 5 m de ruban : position 20 du qualitatif, « incident normal
d'exploitation » [COURS p.139].

## 3. Redondance et contrôles

Le ruban est jugé plus fragile que les autres supports : son contrôle est renforcé
[COURS p.137].

| Contrôle | Portée | Source |
|---|---|---|
| clé du catène (piste 7) | chaque catène ; même clé qu'en mémoire | COURS p.137 ; B61 p.26 |
| parité impaire par colonne (piste 8) | chaque colonne de 6 monades ; sert aussi à reconnaître les blocs-marque | COURS p.137-138 |
| catène longueur aux deux bouts | longueur contrôlée par l'unisélecteur, lecture dans les deux sens | COURS p.137, p.141 |
| zone pilote aux deux bouts | synchronisation dans les deux sens | COURS p.137 |
| relecture immédiate | à l'écriture, la tête de lecture en aval relit ce qui vient d'être écrit, en conditions « marginales » | COURS p.139, p.142-143 ; B61 p.53 |
| commutateur d'interdiction d'écriture | sur chaque dérouleur (programmes, fichiers de base) | COURS p.144 |
| sécurité d'appel | dérouleur non relié à l'unisélecteur, ou déjà pris par un autre | COURS p.151 |

Il n'y a **pas de code correcteur** : la redondance détecte, le programme corrige en relisant,
en réécrivant ou en sautant la zone.

### 3.1 Mauvaise lecture
La lecture se poursuit jusqu'à la fin du bloc, puis l'incident est signalé en position 18
(avec 23). Le programme d'incident relit le bloc **en sens inverse**, puis **en sens
normal**, pour écarter une mauvaise lecture fugitive, avant d'arrêter éventuellement le
dérouleur pour une intervention manuelle [COURS p.141].

### 3.2 Mauvais enregistrement
Signalé en position 18 par la relecture ; le bloc s'écrit quand même en entier
[COURS p.142]. Procédure du COURS (organigramme p.143) :

```
relecture arrière du bloc
├─ bonne → récriture du bloc au même endroit
│          ├─ bonne    → retour au programme : défaut fugitif des circuits
│          └─ mauvaise → (suite ci-dessous)
└─ mauvaise → saut d'un bloc en marche arrière (SAU / JUM)
              → effacement (EFF / DEL) d'environ 12 cm
              → récriture du bloc à la suite de la zone effacée → retour au programme
```

- L'effacement est une magnétisation continue de toutes les pistes : il allonge l'espace
  d'arrêt-marche et couvre le défaut ; 12 cm correspondent à un bloc moyen de 250 catènes. Si
  le bloc est plus long et que le défaut est à sa fin, on recommence [COURS p.142-143,
  p.147].
- Une relecture arrière bonne et une récriture mauvaise n'a rien d'invraisemblable : la
  relecture d'écriture est faite en conditions marginales, la lecture normale non ; c'est le
  signe d'un oxyde faible [COURS p.142-143].
- À la relecture, les zones effacées se lisent comme des espaces d'arrêt-marche un peu longs
  [B61 p.55].

### 3.3 Pas de mise à jour partielle
L'écriture est cadencée par une horloge externe fixe (15 kc/s par piste) ; avec les variations
de vitesse du ruban, un même bloc n'occupe pas toujours la même longueur. On ne peut donc pas
remplacer un bloc au milieu d'un ruban, même par un bloc de même longueur ; c'est d'ailleurs
contraire à un contrôle organisé, qui garde les rubans d'origine [COURS p.142].

## 4. Unisélecteurs et dérouleurs

### 4.1 Séparation
Un dérouleur ne lit ou n'écrit qu'une petite fraction du temps où il est immobilisé (quelques
pour cent dans une conversion carte-ruban ou ruban-imprimante). Par économie, le Gamma 60 a
moins de circuits de programme local que de dérouleurs : ces circuits, les **unisélecteurs**,
sont les vrais éléments ; un dérouleur n'est qu'un appareil connecté à un unisélecteur le temps
d'un travail. La coupure, le RAC et la chaîne de reprise appartiennent à l'unisélecteur
[COURS p.144-146 ; B61 p.53-54].

### 4.2 Câblage [COURS p.145 ; B61 p.54]
- Au plus 10 unisélecteurs, en 2 groupes de 5 ; au plus 24 dérouleurs par groupe (48 au total) ;
  un dérouleur n'est relié qu'à des unisélecteurs de son groupe.
- Dans un groupe : U1, U2 → dérouleurs 1-12 ; U3 → 5-16 ; U4, U5 → 13-24. Chaque unisélecteur
  dessert 12 dérouleurs ; chaque dérouleur est relié à 2 ou 3 unisélecteurs.
- Groupe partiellement équipé : U1 ; U1-U3 ; ou U1-U5. Petits Gamma 60 : 3 unisélecteurs et
  6 à 8 dérouleurs ; la plupart : 5 et 12 à 18 [B61 p.54].
- 10 unisélecteurs occuperaient déjà la machine 50 % du temps ; 20 dérouleurs saturent les
  canaux [B61 p.53-54].

### 4.3 Directives [COURS p.146-148 ; B61 p.54]

| Groupe | `en` | `fr` | Effet |
|---|---|---|---|
| préparatoire | WRI | ECR | écriture, dérouleur n° X |
| préparatoire | REF | LAV | lecture avant, dérouleur n° X |
| préparatoire | REB | LAR | lecture arrière, dérouleur n° X |
| exécution | TRA | TRA | un bloc, avec transfert, selon la préparatoire |
| exécution | JUM | SAU | lire un bloc sans transfert (sans objet après ECR) |
| exécution | DEL | EFF | effacer ~12 cm |
| exécution | WRM | ECM | écrire un bloc-marque |
| service | SPO | REB | rebobiner |
| service | SPN | REM | rebobiner puis demander une manipulation (lampe verte) |
| service | MAN | MAN | demander une manipulation normale (lampe verte) |
| service | MAI | MAI | demander une manipulation incident (lampe rouge) |

Attention : REB est la lecture arrière en `en` et le rebobinage en `fr`.

- **Préparatoires** : relient le dérouleur à l'unisélecteur de la coupure et préparent le type
  de marche, sans rien lancer ; leur effet **subsiste au-delà des coupures**.
- **Exécution** : sans variable libre ; portent sur **un bloc**, de longueur lue sur le ruban.
  L'unisélecteur ne fait sa demande d'instruction (DI) qu'à la fin du bloc. Plusieurs blocs
  demandent une boucle.
- **Service** : l'unisélecteur refait une DI dès que le dérouleur a reçu l'ordre ; le
  dérouleur travaille seul et signale son occupation (position 21). Une directive d'exécution
  sur un dérouleur occupé est mémorisée et attend la fin du service ; si l'unisélecteur sert
  d'autres unités de traitement, on teste plutôt la position 21 dans une boucle d'attente.
- En lecture avant, le RAC reçoit l'adresse du premier catène et progresse ; en lecture
  arrière, celle du dernier et régresse : l'image en mémoire est la même. En écriture, le bloc
  est composé en mémoire avec ses deux catènes longueur et le RAC désigne le premier ; le
  dérouleur écrit lui-même les zones pilotes, puis appelle le catène longueur, et autant de
  catènes plus un qu'il indique [COURS p.141-142].

### 4.4 Catène qualitatif [COURS p.150-151]
Certaines positions viennent des circuits de l'unisélecteur, d'autres du dérouleur connecté
(interdiction d'écriture, occupation) : chaque dérouleur a ses propres mémoires, recopiées dans
l'unisélecteur par la directive préparatoire.

| Positions | Signification |
|---|---|
| 24, 23, 17 | incident dans les circuits de l'unisélecteur |
| 24, 17 | sécurité d'appel |
| 24, 22, 17 | incident mécanique ou électrique du dérouleur |
| 23, 16 | interdiction d'écriture, après ECR (15 en COURS p.144 : U-48) |
| 23, 18 | mauvaise lecture ou mauvais enregistrement |
| 23, 19 | bloc-marque lu |
| 23, 20 | approche de la fin du ruban |
| 23, 21 | dérouleur occupé |

La position 24 regroupe ce qui demande une intervention humaine, la position 23 ce qu'un
programme peut traiter.

## 5. Marche discontinue

Chaque directive d'exécution porte sur un bloc et l'unisélecteur ne redemande une instruction
qu'à la fin du bloc : le ruban **s'arrête à chaque bloc** [COURS p.148].

- **5 ms** de décélération pour s'arrêter, **5 ms** d'accélération pour retrouver la vitesse
  normale [COURS p.139].
- Les deux têtes doivent être dans l'espace à l'arrêt ; l'espace de 2 cm inclut la distance
  entre têtes [COURS p.142].
- Un unisélecteur peut servir **plusieurs dérouleurs en alternance** : chaque séquence commence
  par une coupure sur l'unisélecteur et sa directive préparatoire, et la chaîne de reprise de
  l'unisélecteur les départage (« système ouvert ») ; seul le premier des deux éléments de
  l'unisélecteur est alors utilisé [COURS p.146, p.149].
- Défaut : près du débit maximum, la fréquence des arrêts-marches est mauvaise pour la mécanique
  et les rampes réduisent le débit [COURS p.148].

**Modèle de l'émulateur** (*hypothèse U-47*) : rampes à accélération constante ; pendant les
deux rampes le ruban parcourt 2 × ½ × 5 ms × 1,90 m/s = 0,95 cm, le reste de l'espace
(1,05 cm) passe à pleine vitesse (5 526 µs). Durée d'une directive TRA sur un bloc de *n*
catènes, profil B61 :

```
5 000 (accélération) + 5 526 (reste de l'espace) + (2 + 1 + n + 1 + 2) × 190 + 5 000 (décélération)
```

## 6. Marche continue

### 6.1 Principe [COURS p.139, p.148 ; B61 p.54]
Si le traitement d'un bloc prend moins de temps que sa lecture, le ruban peut tourner **sans
s'arrêter entre les blocs** : les espaces d'arrêt-marche défilent à la vitesse normale ; c'est
la base des 315 µs (COURS) ou 230 µs (B61) par catène en moyenne. B61 présente les deux
méthodes, discontinue et continue, comme programmées une fois pour toutes en **« programmes
standard »**, et recommande la marche continue quand la durée du travail dépend du ruban.

### 6.2 L'unisélecteur, élément double [COURS p.148]
Un unisélecteur n'a qu'**un** circuit d'échange de quantités, mais **deux éléments de
programme** : l'unité centrale le voit comme un **élément double**, avec deux numéros d'élément
consécutifs (un pair, un impair), deux RAI et deux RAC (chacun appelé RAC 0). Pendant qu'un
élément exécute la directive d'un bloc, l'autre, libre, reçoit la directive du bloc suivant :
aucune discontinuité. Les directives sont les mêmes qu'en marche discontinue ; seule la
séquence de lancement change.

### 6.3 Séquence de lancement [COURS p.148-149]
Le COURS donne sa structure en 16 lignes, catènes vierges omises :

```
 1. DERU 1         liaison unisélecteur-dérouleur
 2. LAV 10
 3. SIMU 4         lance deux fois la séquence 4
 4. FI 5           inverse l'aiguillage 5
 5. 31/00 8
 6. DERU 1
 7. 31 9
 8. DERU 2
 9. SIMU 14        microsimultanéité
10.-13.            bascule de zones M.R.
14. G 0            résultat de la bascule précédente
15. TRA
16. 31 4
```

- La SIMU de la ligne 3 lance deux fois la séquence 4 ; grâce au FI, celle-ci met en activité
  successivement l'élément 1 puis l'élément 2, qui demandent tour à tour la séquence 9. Le
  `G 0` de la ligne 14 garnit donc tantôt le RAC de l'élément 1, tantôt celui de l'élément 2.
- La SIMU de la ligne 9 fait la **bascule de zones** pendant que TRA se déroule
  (« microsimultanéité ») : TRA est sur la branche extraordinaire, exécutée la première.
- Le retour sur l'un ou l'autre élément se fait par le branchement 31 de la ligne 16 vers le FI.
- LAV n'est **pas** répété après les coupures 6 et 8 : rémanent, il est inutile, et il serait
  **nuisible** : exécuté pendant les transferts de l'autre élément, sur le circuit unique, il
  les perturberait.

### 6.4 Règles [COURS p.149-150]
- **Mauvaise lecture ou enregistrement (18)** : il faut s'arrêter à la fin du bloc, comme en
  discontinu. La directive en attente dans l'autre élément est **organiquement bloquée** : elle
  ne s'exécute pas et provoque une nouvelle DI de son élément. Le programme d'incident regroupe
  les deux éléments sur une **coupure à 2 conditions** (JOIN), puis applique la correction du
  § 3.
- **Bloc-marque (19)** : la position 19 apparaît, mais la directive en attente **n'est pas
  bloquée** : on lit encore le bloc suivant (qui peut lui-même être une marque) et l'on profite
  du 19 pour arrêter le ruban à la fin de ce second bloc.
- **Système fermé** : un unisélecteur en marche continue ne peut pas avoir de chaîne de reprise.
  Si d'autres séquences peuvent le demander pour d'autres dérouleurs, le programme doit les
  protéger par un blocage explicite, sans compter sur la chaîne de reprise. Exemple du COURS :
  interclassement de quelques mouvements dans un gros fichier permanent ; le fichier résultat
  s'écrit en continu, mais le fichier permanent doit s'arrêter à chaque mouvement, et son
  unisélecteur sert alors aussi le fichier mouvements. Par opposition, l'unisélecteur qui sert
  plusieurs dérouleurs en discontinu est un « système ouvert ».

### 6.5 Gain
Par bloc, la marche continue économise les deux rampes moins le temps qu'elles auraient mis à
parcourir leur part d'espace : 5 ms dans le modèle de l'émulateur. Pour un bloc de 250 catènes
en B61, cela fait 59,2 ms au lieu de 64,2 ms (≈ 8 %) ; pour des blocs de 50 catènes, 21,2 ms
au lieu de 26,2 ms (≈ 19 %). Il faut aussi que le traitement suive : sinon la directive
suivante arrive en retard et le ruban s'arrête.

## 7. Modélisation dans l'émulateur

| Élément documenté | Émulateur |
|---|---|
| dérouleur (bobine, position, interdiction, occupation, lampe) | `TapeDrive` ; bobine en YAML (`--tape N=fichier.yaml`, `--dump-tape N`) ; liste de blocs, `mark` pour un bloc-marque |
| unisélecteur k | `UniselectorUnit` : circuit, dérouleur connecté, mode rémanent, registre de longueur, file des directives en attente, compteurs `handovers` / `stops` |
| ses deux éléments de programme | deux `Uniselector`, MATA / DERU 2k − 1 et 2k, numéros consécutifs (U-44) |
| câblage B61 p.54 | `uniselector_wiring` (`data/topology.yaml`) ; dérouleur non relié : 24, 17 et incident |
| bloc | 2 catènes pilote + longueur + *n* + longueur + 2 catènes pilote, à `tape_per_catena` µs (profil) |
| directive TRA en marche continue | si le circuit est occupé, la directive attend (`park`) la fin du bloc en cours ; ce temps est affiché `:` dans `--gantt` |
| 18 en marche continue | la directive en attente n'est pas exécutée ; elle rend 18 et 23 et son élément redemande une instruction |
| préparatoire pendant un transfert | mode `diagnostic` : avertissement |
| chaîne de reprise sur un unisélecteur en marche continue | mode `diagnostic` : avertissement « système fermé » |

Données : `data/timings.yaml` (`tape`, `tape_block`, `tape_continuous`),
`data/behavior.yaml` (`tape`), `data/encoding.yaml` (`free_variable_layouts.uniselector`),
`data/topology.yaml` (`unit_numbers.uniselector`).

### 7.1 Hypothèses
- **U-44** : en code B, `DERU n` / `MATA n` désigne l'élément n (1-20) ; les éléments 2k − 1 et
  2k forment l'unisélecteur k ; leurs numéros d'élément (RNE) suivent `unit_numbers`.
- **U-47** : rampes linéaires, reste de l'espace à pleine vitesse ; 3 cycles par directive
  préparatoire ou de service ; bobine de 730 m.
- **U-48** : une écriture rend la suite du ruban illisible ; interdiction d'écriture en
  position 16 ; un catène non servi à temps et une lecture au-delà du dernier bloc donnent une
  mauvaise lecture (18).
- **U-50** : la directive du bloc suivant doit **déjà attendre** à la fin du bloc en cours ;
  sinon le ruban s'arrête (5 ms) et repart (5 ms) ; l'espace défile en 2 cm / 1,90 m/s ≈
  10,5 ms.
- **U-51** : lignes 10-13 de la séquence de lancement reconstituées avec le registre B
  (`PTR ← (ZA + ZB) − PTR`), branche ordinaire de la ligne 9 terminée par un STOP, catènes
  vierges ajoutées.

### 7.2 Non modélisé
- les clés et la parité ne sont pas calculées sur le ruban : la bobine contient des catènes
  sans défaut, et la mauvaise lecture n'apparaît que par débordement ou lecture hors des blocs ;
- la synchronisation, les variations de vitesse, la longueur physique variable des blocs ;
- les incidents 24 / 22 du dérouleur et les incidents de circuits de l'unisélecteur.

### 7.3 Exemple
`tests/programs/bande_continue.g60b` transcrit la séquence de lancement (U-51) et lit en
marche continue `tests/media/fichier_6_blocs.yaml` (6 blocs de 50 catènes, un bloc-marque, un
dernier bloc lu après la marque) :

```
python -m gamma60 run tests/programs/bande_continue.g60b --tape 10=tests/media/fichier_6_blocs.yaml --gantt
```

Le ruban fait 7 enchaînements sans arrêt et s'arrête une seule fois, à la fin du bloc qui suit
la marque. Sur le chronogramme, les deux éléments DERU1 / DERU2 alternent ; `:` marque la
directive qui attend la fin du bloc de l'autre élément.

`tests/programs/bande_continue_task.g60b` ajoute le traitement : à la fin de chaque bloc, une
branche `SIMU TRAIT` fait additionner par LOGI les 50 catènes du bloc, pendant que la séquence
relance aussitôt l'élément et que le ruban lit le bloc suivant (double tampon ZA / ZB). Le
traitement d'un bloc dure environ 20,1 ms (surtout le temps du Distributeur de Programme pour
lire les instructions de la boucle), juste moins que l'intervalle entre deux blocs (≈ 21,2 ms) :
le ruban ne s'arrête toujours pas [COURS p.139], mais la marge n'est que d'environ 1 ms.
Le bloc qui suit la marque est lu quand même (§ 6.4) mais n'appartient plus au fichier :
le programme teste la fin du fichier avant de lancer le traitement, et ce bloc n'est pas traité.

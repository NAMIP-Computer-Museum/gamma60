# Chaîne d'outils (reconstitution)

## 1. La chaîne historique

« La programmation du GAMMA 60 se fera donc en deux phases : a) la codification ligne à ligne,
en forme de sous-programme […] sans se soucier de l'implantation en Mémoire Rapide ; b)
l'assemblage de ces différents sous-programmes et leur implantation » [COURS p.44]. Les
sous-programmes d'usage général sont regroupés en bibliothèques et assemblés par un « master
program » qui rend les adresses relatives absolues une fois l'implantation décidée [DR-E
p.178]. Maître décrit la chaîne réalisée [MAIT §Sous-programmes, §Assemblage & code C,
§G.G.Z.] :

1. **Transposition** code B → code A, sous-programme par sous-programme : le sous-programme
   est « transposé, vérifié, au besoin corrigé, listé et rangé dans une bibliothèque -
   généralement sur bande - sous forme d'un sous-programme assemblable, comportant des
   instructions et mémoires en code A (avec des vides) et une table d'inconnues et de repères
   destinée à l'assemblage ». Chaque entrée et chaque sortie reçoit une valeur symbolique.
2. **Assemblage** piloté par la feuille **code C** : le programmeur liste et numérote les
   sous-programmes, y compris les zones de manœuvre (tampon, zone de tri…), avec pour chacun
   la liste de ses inconnues (X) ; colonnes « assembl. » : liaisons `SPy.Xn = SPz.Rm` et
   affectations `SPy.Xn = constante` ; colonnes « distr. » : adresse d'implantation (au moins
   du premier sous-programme), repère d'entrée, inconnue de sortie liée à un repère
   symbolique, symbole de distribution pour les inconnues fixées plus tard (numéro d'appareil,
   nombre d'articles, liaison vers un sous-programme résident du superviseur) ; phases.
   L'assembleur « condensera les sous-programmes et les zones, effectuera les liaisons et les
   affectations validées et constituera une table des inconnues avec leurs symboles ».
3. **Distribution** : les valeurs des inconnues symboliques (adresse mémoire, adresse tambour,
   numéro d'appareil ou d'élément, longueur de zone…) sont données par ordres du pupitre ou
   par cartes **code D2** ; le résultat est une **U.T.** (unité de traitement) exécutable,
   rangée en bibliothèque : « tout est figé » ; seuls certains paramètres peuvent être changés
   par ordre pupitre au lancement. La GGU ajoute D1 (lancement paramétré) et D3 (jobs)
   [MAIT §G.G.U.] (U-54).

Les adresses externes d'un sous-programme passent souvent par une mémoire de manœuvre placée à
sa fin et utilisée par substitution (`Jump to 29RS`) [B61 p.29 ; COURS p.45]. Selon LEC, les
assemblages se faisaient aussi « à la trieuse et à l'interclasseuse, sur cartes perforées »
(U-58).

**Ce qui n'est pas connu** : la disposition des feuilles et des cartes B, C et D ; la façon de
déclarer une inconnue ou un repère sur la feuille de code B ; la syntaxe exacte des liaisons
(`SPy.Xn = SPz.Rm` est la notation de Maître) ; la forme physique de l'U.T. (U-14, U-52 à U-54).
L'émulateur garde le fonctionnement attesté et invente des **formats modernes**, marqués
hypothèses : rien de ce qui suit n'est un format d'époque.

## 2. Dans l'émulateur (J6)

```
prog.g60b ──transpose──► prog.g60a.json ─┐
lib/*.g60b ─transpose──► *.g60a.json ────┼─assemble (code C : .g60c.yaml)─► .g60pa.json
                                         ┘                                        │
                                       distribute (code D2 : .g60d.yaml) ◄────────┘
                                                     │
                                                     ▼
                                               prog.ut.json ──run──► machine
```

| Commande | Entrée | Sortie | Module |
|---|---|---|---|
| `asm` | `.g60b` | listing (code A à côté du code B) | `toolchain/assembler.py` |
| `transpose` | `.g60b` | sous-programme assemblable `.g60a.json` | `toolchain/subprogram.py` |
| `assemble` | feuille de code C `.g60c.yaml` | programme assemblé `.g60pa.json` (`--listing`) | `toolchain/linker.py` |
| `distribute` | feuille de code D2 `.g60d.yaml` (ou `.g60c.yaml` / `.g60pa.json` sans symbole) | U.T. `.ut.json` | `toolchain/distributor.py` |
| `run` | `.g60b` ou `.ut.json` | exécution | `toolchain/chain.py` |
| `disasm` | `.g60b`, `.ut.json`, `.g60pa.json`, `.g60a.json` | code A → code B (`--lang en\|fr`) | `toolchain/disassembler.py` |

Une feuille de code C ou D2 peut nommer directement des `.g60b` (transposés à la volée) ou un
`.g60c.yaml` (assemblé à la volée). Les fichiers produits ne sont pas versionnés ; le code A y
est écrit en hexadécimal (`"words": {"0": "400002", …}`), comme dans les listings et `--dump`.

**`run x.g60b`** passe par toute la chaîne : un seul article, implanté à l'origine du programme,
rien à distribuer. Le test `tests/test_chain.py` vérifie, pour chaque programme de
`tests/programs/`, que la chaîne donne la même trace (enregistrement par enregistrement), la
même mémoire et le même statut que l'assemblage seul du J3, et qu'une U.T. relue depuis son
JSON, sans source, fait de même. `run` refuse un programme qui a encore des inconnues.

### 2.1 Code B : sous-programmes (U-52)

- **`REP ETIQ…`** (pseudo-instruction, aucune catène) : déclare des **repères**, étiquettes
  visibles du code C, numérotés R1, R2… dans l'ordre de déclaration. Une étiquette non déclarée
  reste interne au sous-programme.
- **`?NOM`** : une **inconnue**, partout où une variable libre est permise (branchement,
  instruction d'adresse, coupure, SIMU, directive avec variable libre), avec `R` (différentiel)
  ou `S` (substitution), pas avec `M`. **`BIN ?NOM`** : une catène entière à remplir (par
  exemple une adresse utilisée par `RS`, la forme de B61 p.29). Un même nom employé plusieurs
  fois est une seule inconnue ; numérotation X1, X2… dans l'ordre de première apparition.
- La transposition note, pour chaque vide, la conversion à appliquer quand la valeur arrive :
  `abs` (telle quelle), `diff` (écart à la catène, avec `R`), `unit:<coupure>` (numéro d'unité
  → numéro d'élément, comme `DERU n` en code B, U-44), `drum` (adresse tambour continue → piste
  × 256 + position, comme `DAO`). Elle note aussi chaque X qui contient une adresse absolue
  interne (étiquette sans `R`) : c'est la relocation [DR-E p.178].
- La taille d'un sous-programme compte ses mémoires de manœuvre (`M`), placées après le code
  [COURS p.47-49].

`.g60a.json` : code A numéroté depuis 0 (vides à 0), inconnues et leurs emplois, repères,
relocations, éléments des directives, comptes des JOIN, table des étiquettes et des lignes.

### 2.2 Code C : assemblage (U-53)

```yaml
articles:                     # numérotés : sous-programmes ET zones
  1: {sp: ../lib/lecture_continue.g60b, nom: LECT}   # .g60b ou .g60a.json
  2: {sp: traitement_bloc.g60b, nom: TRAIT}          # nom : défaut = nom du fichier
  3: {zone: 50, nom: ZA}                             # zone : son début est le repère R1
assembl:                      # colonnes « assembl. »
  - LECT.?ZA = ZA.R1          # SPy.Xn = SPz.Rm (numéros ou noms : 1.X1 = 2.R1)
  - TRAIT.X2 = 50             # SPy.Xn = constante
distr:                        # colonnes « distr. »
  implantation: {1: 256}      # au moins le premier article ; les autres suivent
  entree: LECT.R1             # défaut : entrée du premier sous-programme
  sortie: LECT.?FIN           # inconnue de sortie → FIN_UT
  symboles:                   # laissées à la distribution (style bloc : « ? » gêne {…})
    LECT.?DEROUL: DEROULEUR
```

- **Condensation** : chaque article sans implantation imposée suit le précédent ; un
  chevauchement est une erreur.
- **FIN_UT** : une catène STOP ajoutée après le dernier article ; l'inconnue de sortie y est
  liée (hypothèse : la sortie vers le superviseur n'est pas décrite).
- **Erreurs** : inconnue ni liée ni symbolisée (« si toutes les inconnues sont affectées, le
  programme après assemblage sera exécutable » [MAIT]), premier article sans implantation,
  inconnue affectée deux fois, repère ou article inexistant, zone désignée autrement que par
  R1, sous-programmes transposés pour deux profils différents.
- Un même sous-programme peut être implanté plusieurs fois (articles distincts, `nom`
  différents), chacun avec ses liaisons.

`.g60pa.json` : code A aux adresses définitives, vides restants avec leur symbole et leur
conversion, plan d'implantation, étiquettes `ARTICLE.ETIQ`, lignes, FIN_UT.

### 2.3 Code D2 : distribution (U-54)

```yaml
programme: bande_continue.g60c.yaml   # ou .g60pa.json
valeurs:
  DEROULEUR: 10
```

Une valeur par symbole, écrite comme en code B : numéro d'unité pour une coupure, adresse
tambour continue pour `DAO`, adresse ou longueur sinon ; la conversion notée à la
transposition s'applique. Le type de la valeur (les quatre types de MAIT) n'est pas déclaré :
il découle de l'endroit du vide. Erreurs : symbole sans valeur, valeur pour un symbole
inexistant, valeur non entière ou hors limites.

`.ut.json` : code A complet et figé, entrée, FIN_UT, valeurs distribuées (pour mémoire), et les
tables de débogage. La table des éléments requis par l'U.T. (attribution des E/S) est reportée
au J7. D1 (lancement paramétré), D3 (jobs), phases et modification au pupitre : J7 et au-delà.

### 2.4 Débogage symbolique

- Trace (`--trace`) et pas à pas : adresse symbolique `ETIQ+k` (`ARTICLE.ETIQ+k` pour une U.T.
  de plusieurs articles) et numéro de ligne du code B.
- `--break ETIQ[+k]` (répétable) : exécution libre jusqu'au point d'arrêt, puis pas à pas ;
  les commandes `b`, `d`, `m` du pas à pas et `--dump` acceptent `ETIQ±k`, `ARTICLE.ETIQ`, une
  adresse, ou une étiquette seule si un seul article la porte.
- `--dump` : colonne `ETIQ+k`.
- `disasm` : code A → code B, cibles en symbolique, source d'origine en commentaire ; un `NUM`
  est décodé en valeur décimale exacte (`NUM +3.14`). `--raw` ne lit que les catènes, comme
  en mémoire : ni étiquettes, ni source, ni marques de données (une donnée décodable est lue
  comme une instruction) ; l'élément d'une directive est celui de la dernière coupure lue. Les
  étiquettes sont reconstruites à partir du code A : `Lnnnnn` pour une cible de code
  (branchement, SIMU, FJ / FT / FI), `Dnnnnn` pour une adresse de donnée (L / P, directives
  centrales à adresse, PROT / LIBE, catène lue par substitution) ; le X de LE, LB, AB, SB, CB,
  A et S est une quantité [COURS p.53-60] et reste un nombre, même quand il sert d'adresse
  (`GB ZA` devient `GB 311`). Le code A
  seul ne dit ni quelles catènes sont des données, ni à quel élément s'adresse une directive
  d'élément : ces informations viennent des tables de la chaîne ; le compte du JOIN est montré
  en C.C. de la coupure (forme B61, U-20).

### 2.5 Exemples

`tests/programs/lib/` (sous-programmes de bibliothèque) et `tests/programs/chaine/<chaîne>/` (feuilles C
et D2), décrits dans `tests/programs/README.md` : `bande_continue_task` découpé
(`lib/lecture_continue` + traitement + zones), le dérouleur choisi par D2 (10 ou 12), et
`lib/somme` implanté deux fois.

## 3. Code B : format des fichiers `.g60b`

Fichier texte, une instruction par ligne, champs séparés par des espaces ou en colonnes fixes
(T.O. 4, C.C. 2, X 5, A.F. 2), étiquettes `ETIQ:`, commentaires `;`. Mnémoniques : `ISA.md`.

- **Langue** : la première ligne peut déclarer `; langue: fr` (mnémoniques du COURS) ou
  `; langue: en` (B61, par défaut) ; la langue est indépendante du profil machine.
  L'assembleur et le désassembleur lisent les deux orthographes dans `data/directives.yaml` ;
  une orthographe `fr` non relevée (U-29, seul DESK) est remplacée par la forme `en`, avec
  avertissement en mode diagnostic.
- **En-têtes** : `; profil: COURS|B61` (défaut : profil par défaut de `profiles.yaml` ; fixe
  notamment la place du compte du JOIN) ; `; origine: n` (adresse de chargement ; défaut 256,
  après la table des registres B / C des chaînes de reprise, U-30).
- Une ligne peut commencer par un numéro de ligne à 3 chiffres (comme les feuilles de
  programmation d'époque, ex. `namip_classement.g60b`), puis une étiquette `ETIQ:`.
- **Pseudo-instructions** (non historiques) : `VIERGE [m]` (catène vierge ; `m` = compte du
  JOIN en notation COURS), `NUM ±d` (nombre semi-logarithmique sur 2 catènes, forme
  normalisée), `BIN n` (entier binaire sur une catène, 0 ≤ n < 2^24, ou `BIN ?NOM`),
  `ZONE n` (n catènes à zéro), `REP ETIQ…` (repères, J6).
- Champs des directives sans variable libre : ARIT `[C.C.] V O1 O2 R` (4 cases, `-` = vide ;
  C.C. = 1re lettre P / N / A (`fr`) ou R (`en`), 2e lettre D) ; LOGI `V R`. Les fonctions
  d'adresse (`R`, `S`, `M`) suivent les champs obligatoires, ce qui lève l'ambiguïté avec une
  étiquette nommée `R`.
- Une coupure est toujours suivie d'une ligne `VIERGE` (catène vierge).

## 4. Assembleur (transposition) : précisions

- Deux passes (étiquettes, puis codage), listing par `asm`.
- Fonctions d'adresse [COURS p.47-49] : `R` (étiquette, ou numéro de ligne de la feuille relatif
  à l'origine) et `M` (mémoire de manœuvre n, placée après le programme) deviennent un écart
  différentiel (bit d), négatif en complément à 32 768 ; `S` = bit s.
- Le compte du JOIN s'écrit dans le C.C. de la coupure [B61 p.31] ou dans le X de la catène
  vierge [COURS p.52] : l'assembleur suit `profiles.yaml` (U-20).
- Coupures numérotées : X = numéro de l'unité, converti en numéro d'élément (U-44) ; DAO :
  adresse tambour continue 0-25 599 convertie en piste × 256 + position [COURS p.154].
- Directives codées : ARIT et LOGI (disposition reconstruite, U-01) ; depuis J5, COMP, tambour
  et unisélecteurs (variable libre, U-01). TRAN et les E/S des classes 3-4 : J8.
- « Code C » au sens de B61 p.28 (« code plus complet » de la brochure de programmation) :
  peut-être la même chose que la feuille d'assemblage de MAIT (U-14).

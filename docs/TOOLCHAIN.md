# Chaîne d'outils (reconstitution)

Chaîne historique [MAI ; B61 p.28-30] :

1. **Transposition** code B → code A, sous-programme par sous-programme ; contrôle de
   vraisemblance ; listing ; résultat = « sous-programme assemblable » (code A avec vides +
   table des inconnues et repères).
2. **Assemblage** piloté par la feuille **code C** : liste numérotée des sous-programmes et
   des zones de manœuvre (tampons, zones de tri) ; liaisons `SPy.Xn = SPz.Rm` ;
   affectations `SPy.Xn = constante` ; adresse d'implantation du 1er sous-programme ;
   repère d'entrée (colonnes « distr. »). L'assembleur condense, lie, et produit la table
   des inconnues restantes.
3. **Distribution** : valeurs restantes (adresse mémoire, adresse tambour, n° d'appareil
   ou d'élément, longueur de zone) fournies par ordres pupitre ou cartes **code D2** ⇒
   **UT** exécutable, figée. GGU ajoute D1 (paramètres de lancement) et D3 (jobs).

## État dans l'émulateur
- **J3** : `src/gamma60/toolchain/assembler.py` transpose le code B (`fr` ou `en`) en une image
  mémoire en code A, en deux passes (étiquettes, puis codage), avec un listing :
  `python -m gamma60 asm prog.g60b` (adresse, code A groupé par champs, ligne source). Fonctions
  d'adresse : `R` (étiquette, ou numéro de ligne de la feuille relatif à l'origine) et `M`
  (mémoire de manœuvre) deviennent un écart différentiel (bit d) ; `S` = bit s. Origine :
  ligne `; origine: n` (0 par défaut). Seules les directives d'ARIT et de LOGI sont codées
  (disposition reconstruite, U-01) ; les autres éléments arrivent au J5-J8.
- **J6** : assemblage (code C), distribution (code D) → UT.

## Formats proposés pour l'émulateur
- **Code B** : fichier texte `.g60b`, une instruction par ligne, champs séparés par des
  espaces ou en colonnes fixes (T.O. 4, C.C. 2, X 5, A.F. 2), étiquettes symboliques
  permises (`ETIQ:`), commentaires `;`. Respecter les mnémoniques de `ISA.md`.
  **Langue** : la première ligne peut déclarer `; langue: fr` (mnémoniques du COURS) ou
  `; langue: en` (B61, par défaut) ; la langue est indépendante du profil machine.
  L'assembleur et le désassembleur lisent les deux orthographes dans `data/directives.yaml` ;
  une orthographe `fr` non relevée (U-29, seul DESK) est remplacée par la forme `en`, avec
  avertissement en mode diagnostic. Une ligne `; profil: COURS|B61` peut suivre (défaut :
  profil par défaut de `profiles.yaml`) ; elle fixe notamment la place du compte du JOIN.
  Une ligne peut commencer par un numéro de ligne à 3 chiffres (comme les feuilles de
  programmation d'époque, ex. `namip_classement.g60b`), puis une étiquette `ETIQ:`.
  Pseudo-instructions (non historiques) : `VIERGE [m]` (catène vierge ; `m` = compte du JOIN en
  notation COURS), `NUM ±d` (nombre semi-logarithmique sur 2 catènes, forme normalisée), `BIN n` (entier binaire
  sur un catène, 0 ≤ n < 2^24, pour les compteurs du registre B et des directives DI / PC),
  `ZONE n` (réserve n catènes à zéro).
  Champs des directives sans variable libre : ARIT `[C.C.] V O1 O2 R` (4 cases, `-` = vide ;
  C.C. = 1re lettre P / N / A (`fr`) ou R (`en`), 2e lettre D) ; LOGI `V R`. Les fonctions
  d'adresse (`R`, `S`, `M`) suivent les champs obligatoires, ce qui lève l'ambiguïté avec une
  étiquette nommée `R`.
  Une coupure est toujours suivie d'une ligne `VIERGE` (catène vierge) — l'assembleur peut
  l'insérer automatiquement en mode diagnostic avec un avertissement.
- **Code C** : YAML (`.g60c.yaml`) : sous-programmes, zones, liaisons, implantation, entrée.
- **Code D** : YAML (`.g60d.yaml`) : valeurs de distribution.
- **UT** : JSON (image mémoire + table des éléments requis + point d'entrée).

Ces formats sont modernes et **non historiques** (U-14) ; garder une couche de conversion
si l'on retrouve les vrais formats de cartes.

## Précisions (v2)
- Les F.A. du code B : R = numéro de ligne relatif, M = numéro de mémoire de manœuvre ; les
  mémoires de manœuvre sont placées à la fin du sous-programme ; R et M deviennent un écart
  différentiel (bit d) ; S = bit s [COURS p.47-49].
- Le compte du JOIN s'écrit dans le C.C. de la coupure [B61] ou dans le X de la catène
  vierge [COURS] : l'assembleur suit `profiles.yaml`.
- « Code C » : feuille d'assemblage [MAI] ou « code plus complet » de la brochure de
  programmation [B61 p.28] — nature exacte à établir (U-14).

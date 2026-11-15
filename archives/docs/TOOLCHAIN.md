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

## Formats proposés pour l'émulateur
- **Code B** : fichier texte `.g60b`, une instruction par ligne, champs séparés par des
  espaces ou en colonnes fixes (T.O. 4, C.C. 2, X 5, A.F. 2), étiquettes symboliques
  permises (`ETIQ:`), commentaires `;`. Respecter les mnémoniques de `ISA.md`.
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

# Émulateur Bull Gamma 60 — instructions pour Claude Code

## But du projet
Émuler le Bull Gamma 60 (1958-1964) : un moteur à événements discrets qui reproduit le
comportement dynamique de la machine (Distributeur de Programme, Distributeur de Transferts,
éléments autonomes, chaînes de reprise, multiprogrammation), plus la chaîne d'outils d'époque
(code B → code A, assemblage, distribution → UT).

## Où trouver quoi (à lire selon le besoin, pas d'import automatique)
- `docs/MACHINE.md` — la machine telle que documentée, chaque fait sourcé.
- `docs/ISA.md` — jeu d'instructions (code B) et codage en code A ; correspondance COURS ↔ B61.
- `docs/UNKNOWNS.md` — inconnues + hypothèse par défaut + réglage associé.
- `docs/GLOSSARY.md` — sigles et abréviations, `en` / `fr`, forme développée.
- `docs/EMULATOR_DESIGN.md` — architecture logicielle ; `docs/TOOLCHAIN.md` — chaîne d'outils.
- `docs/TAPE.md` — bandes magnétiques : ruban, blocs, contrôles, marches discontinue et continue.
- `docs/ROADMAP.md` — jalons et critères d'acceptation. Travailler jalon par jalon.
- `docs/HARDWARE.md`, `docs/HISTORY.md` — contexte (non nécessaire à l'émulation).
- `docs/SOURCES.md` — bibliographie ; PDF dans `archives/docs/`,
  texte extrait dans `refs/txt/` pour chercher (grep) dans les sources.
- `docs/diagrams/` — modèle SysML v7 (PlantUML) ; `docs/` fait foi en cas de désaccord.
- `wiki/` — présentation en anglais, dérivée de `docs/` (qui fait foi) ; navigable depuis le
  dépôt, liens relatifs. Un fait nouveau va d'abord dans `docs/`, avec sa source.
- `data/` — tables : `encoding`, `directives`, `qualitative`, `timings`, `priorities`,
  `profiles`, `charset` (code interne 6 bits + code carte), `topology` (classes, circuits),
  `behavior` (comportements non documentés), `registers` (registres de l'UC, du DP et des
  éléments), `configs/`.
  Valeur incertaine = `{value, status: hypothesis, unknown: U-xx}` (vérifié par les tests).
- `archives/` — sources versionnées : `docs/` (PDF), `photos/` (photos de pages citées),
  `images/` (photos de la machine, contexte).
- `tools/fetch_refs.sh` — extrait le texte des PDF et pages HTML d'`archives/docs/` vers `refs/txt/`.
- `COMM.md` — plan d'une présentation du projet (notes, hors émulateur).

## Règles non négociables
1. **Ne jamais inventer un fait historique.** Toute information manquante va dans
   `docs/UNKNOWNS.md`, avec une hypothèse marquée et rendue réglable.
2. **Tout ce qui est incertain vit dans `data/*.yaml`**, jamais en dur dans le code.
3. **Deux profils de machine** (`data/profiles.yaml`) : COURS (~1958-59 : cycle 11 µs, clé
   mod 7) et B61 (1961 : cycle 10 µs, clé parité + mod 3 ; profil par défaut). Les deux
   doivent rester exécutables. **Indépendamment**, le code B existe en deux langues
   (`data/directives.yaml`) : `fr` (mnémoniques du COURS) et `en` (mnémoniques de B61, par
   défaut). L'écart de mnémoniques entre les deux documents est une traduction, pas une
   évolution de la machine ; toute combinaison profil × langue est valide.
4. **Simulation à événements discrets, déterministe**, temps simulé en microsecondes.
   Pas de threads, pas d'asyncio, pas d'horloge réelle. Même entrée → même trace.
5. **Arithmétique décimale exacte** pour ARIT : mantisse entière de 10 chiffres, exposant
   biaisé de 40, contrôle mod 7. Jamais de float binaire.
6. **Mémoire = catènes de 27 bits** (24 + 3 de clé, calculée selon le profil).
7. **Deux modes** : `faithful` (seuls les contrôles d'époque, y compris « directive décodée
   erronée ») et `diagnostic` (contrôles modernes : préfixe 1110, chevauchement d'UT, JOIN
   jamais atteint, catène vierge manquante…).
8. **Tests obligatoires** ; les programmes de `tests/programs/` doivent toujours passer.
9. Toute affirmation ajoutée dans `docs/` cite sa source (fichier de `archives/docs/` ou `archives/photos/` + page/§).

## Conventions
- Python ≥ 3.11, paquet `src/gamma60/`, tests `pytest`, lint `ruff`.
- Code, identifiants et commentaires en anglais ; documentation de référence (`docs/*.md`)
  en français ; wiki (`wiki/`) en anglais. Tout élément localisé (mnémoniques,
  codes complémentaires, lettres des RAC…) est donné dans les deux langues du code B,
  `en` (B61) et `fr` (COURS), par exemple `L` / `G` ; orthographe supposée marquée (U-xx).
- Registres nommés comme dans le cours : RNE, RAPA, RAPP, REDP, RSDP, A, B, RAI (+ indice
  d'occupation), RAC, registres B/C de chaîne de reprise, RLN. Noms affichés (traces,
  débogueur) : champ `display` de `data/registers.yaml`, en `en` et en `fr` ; MAJUSCULES = nom
  attesté dans cette langue, minuscules = initiales proposées par l'émulateur, non validées
  (ex. `cpar` / `RAPA`, `z` / `Z`).
- Éléments nommés par les mnémoniques B61 (ARIT, LOGI, TRAN, COMP, DRUM, CARR, CARP, PRIN,
  MATA, TAPR, TAPP, DESK) ; mnémoniques français dans `data/directives.yaml`.

## Commandes
- Environnement : `python -m venv .venv` puis `.venv/Scripts/pip install -e .[dev]`
- Tests : `pytest -q` · Lint : `ruff check . && ruff format --check .`
- Lancer un programme : `python -m gamma60 run tests/programs/<nom>.g60b|<u.t.>.ut.json [--profile COURS]
  [--trace | --trace=regs | --trace=dd | --step | --break ETIQ[+k]] [--names en|fr] [--mode diagnostic]
  [--dump <adresse|étiquette> [n] | --dump all] [--gantt[=elem|seq]] [--config max]
  [--tape N=fichier.yaml] [--drum K=fichier.yaml] [--dump-tape N]`
  (machine : DP avec simultanéité, DD, ARIT, LOGI ; `--seq` : interpréteur J1, sans temps)
- Listing d'assemblage : `python -m gamma60 asm tests/programs/<nom>.g60b`
- Chaîne d'outils (J6, `docs/TOOLCHAIN.md`) : `transpose <sp>.g60b` → `.g60a.json` ;
  `assemble <feuille>.g60c.yaml [--listing]` → `.g60pa.json` ; `distribute <feuille>.g60d.yaml`
  → `.ut.json` ; `disasm <fichier> [--lang en|fr]` (exemples : `tests/programs/chaine/<chaîne>/`)
- Scénario du Distributeur de Données : `python -m gamma60 dd tests/scenarios/<nom>.yaml
  [--profile COURS] [--trace] [--names fr] [--mode diagnostic]`

## Méthode de travail
- Avant un jalon : relire ROADMAP.md, proposer un plan, attendre validation.
- Après un jalon : mettre à jour ROADMAP.md, UNKNOWNS.md et, si besoin, les diagrammes.
- `refs/` (texte extrait) n'est pas versionné : résumer et citer les sources, ne jamais les recopier.

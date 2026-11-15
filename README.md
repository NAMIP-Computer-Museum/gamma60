# gamma60-emu

Émulateur (en construction) du Bull Gamma 60, grand ordinateur français de 1958-1960,
première machine conçue autour de l'exécution simultanée d'éléments autonomes, avec des
primitives de type fork/join (SIMU, coupures de jonction) dans son jeu d'instructions.

- Spécification : `docs/` (commencer par `docs/MACHINE.md`, puis `docs/ISA.md`).
- Tables modifiables : `data/` (dont le code interne des caractères : `data/charset.yaml`).
- Programmes de référence : `tests/programs/` (dont un programme d'époque publié par le NAM-IP).
- Sources : `docs/SOURCES.md`. Les PDF sont dans `archives/docs/` ;
  `tools/fetch_refs.sh` en extrait le texte dans `refs/txt/` (non versionné).

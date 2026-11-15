# Diagrammes SysML (PlantUML) — v7

Source : `gamma60_sysml.puml` (9 diagrammes) ; rendus PNG et SVG à côté.
Régénérer : `java -jar plantuml.jar -charset UTF-8 -tpng gamma60_sysml.puml`.

| Fichier | Contenu |
|---|---|
| `gamma60_bdd_structure` | blocs : DP et ses registres, DT (avec l'exception du lecteur de cartes), matrices RAI (+ indice d'occupation) et RAC, registres A et B, canaux, éléments réels (attribut `occupé`), unisélecteurs (câblage) et dérouleurs (format de bande), cartes, imprimante, bande perforée, pupitre, élément virtuel |
| `gamma60_bdd_types` | catène, code A par préfixe TK et champs, code B, catène vierge, catène qualitatif, caractère interne et code carte, bloc de bande, profils de machine |
| `gamma60_ibd` | flux : MC ↔ DT, DI/DTQ, canaux, classes |
| `gamma60_stm_element` | repos / activité (attente, opération), directives préparatoires et opératoires |
| `gamma60_act_cycle` | cycle d'instruction du DP (décisions sur TK et sur le bit testé de A) |
| `gamma60_act_coupure` | exploitation d'une coupure (ordre COURS p.38) |
| `gamma60_obj_chaines` | chaîne de reprise (registres B/C, catènes vierges) et catènes-image |
| `gamma60_act_forkjoin` | SIMU + JOIN en code B |
| `gamma60_sd_es` | lecture d'un bloc de bande |

v6 intègre le *Cours de programmation* (COURS) ; v7 ajoute les détails relus dans B61 (codes des caractères, bandes, unisélecteurs, périphériques, pupitre). Les points « (?) » renvoient à
`docs/UNKNOWNS.md`. Les documents de `docs/` font foi en cas de désaccord.

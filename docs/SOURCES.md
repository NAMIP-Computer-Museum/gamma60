# Sources

PDF dans `archives/docs/` ; texte extrait dans `refs/txt/<même nom>.txt` (non versionné, voir `tools/fetch_refs.sh`) ;
photos de pages dans `archives/photos/`.

| Clé | Référence | Fichier (`archives/docs/` sauf mention)                       | En ligne |
|---|---|---------------------------------------------------------------|---|
| B61 | Compagnie des Machines Bull, *Gamma 60 Data Processing System*, 1961 (68 p., ANMT Roubaix 2012 007 / 3198, numérisé 2024, projet JuraSTIC). **Source principale de l'ISA.** | `Bull-1961-Gamma60-Data-Processing-System.pdf`                | https://api.nakala.fr/embed/10.34847/nkl.5cae626j/23663bbffb4f6bf1450270f16f2f80186e0a3060 |
| COURS | Compagnie des Machines Bull, *Cours de programmation Gamma 60* (~1958-59, 166 p., errata) — codage du code A, registres du DP, algorithmes, temps en cycles | `Bull-cours-programmation-gamma60.pdf`                        | — (document fourni) |
| BPD | Compagnie des Machines Bull, *Gamma 60 Preliminary Description* (20 p., même fonds) — conception antérieure | `Bull-Gamma60-Preliminary-Description.pdf`                    | https://api.nakala.fr/embed/10.34847/nkl.db8d9ni9/b0be0561c298eaa82f324bdd58ec7e50da263181 |
| TFR | Compagnie des Machines Bull, tables d'instructions du code B, version française (5 p., sans titre ni date ; I instructions centrales, II éléments de traitement, III entrée-sortie, IV stockage) — même structure que les tables B61 p.62-66, mnémoniques du COURS. Scan sans OCR ; transcription structurée : `Bull-Gamma60-Instructions-FR.yaml` (vérifiée sur les images) | `Bull-Gamma60-instructions-FR-NOOCR.pdf` | — (document fourni) |
| ONDE | Davous, Bataille, Harrand, « Le Gamma 60 », *L'Onde électrique* n°405, déc. 1960 (retranscription FEB) | `Davous-OndeElectrique-1960-Gamma60.pdf`                      | http://www.feb-patrimoine.com/projet/gamma60/gamma60_bataille2.pdf |
| DR-W | Philippe Dreyfus, « System Design of the Gamma 60 », WJCC, mai 1958, p.130-133 | `Dreyfus-WJCC-1958-System-Design.pdf`                         | https://dl.acm.org/doi/10.1145/1457769.1457805 |
| DR-E | Philippe Dreyfus, « Programming Design Features of the Gamma 60 Computer », EJCC, déc. 1958, p.174-181 | `Dreyfus-EJCC-1958-Programming-Design-Features.pdf`           | https://dl.acm.org/doi/10.1145/1458043.1458080 |
| BAT72 | M. Bataille, « The Gamma 60: the computer that was ahead of its time », *Honeywell Computer Journal* 5(3), 1971, p.99-105 ; repris dans ACM SIGARCH CAN 1(2), 1972 (version archivée : le reprint) | `Bataille-HCJournal-1971-Gamma60-Ahead-of-its-time.pdf`       | https://dl.acm.org/doi/10.1145/641276.641278 |
| HBC75 | « GAMMA 60 GOOD BYE », *Honeywell Bull Contact*, février 1975 (périodique Honeywell Bull) — référence signalée par l'utilisateur, non consultée | — (à numériser) | — |
| TS | T.J. Tumlin, M. Smotherman, « An Evaluation of the Design of the Gamma 60 » | `Tumlin-Histoire-Info-1993-Eval-Design-Gamma60.pdf`           | https://db.aconit.org/dbmedia_0/pdf_10/10174.pdf |
| RYLE | B.L. Ryle, « Multiple programming data processing », CACM 4(2), 1961, p.99-101 | `Ryle-CommACM-1961-Multiprogramming.pdf`                      | https://dl.acm.org/doi/10.1145/366105.366132 |
| NEK | M.R. Nekora, « Comment on a paper on parallel processing », CACM 4(2), 1961, p.103 | `Nekora-CommACM-Note-Parallel-Processing.pdf`                 | https://dl.acm.org/doi/10.1145/366105.366139 |
| MAI | A. Maître, « Histoire du G 60 — Le logiciel » (1997), site FEB | —                                                             | http://www.feb-patrimoine.com/projet/gamma60/histoire_du_gamma_60_logiciel_maitre.htm |
| MAS | C. Massuard, « Petite synthèse… » (1997), site FEB | —                                                             | http://www.feb-patrimoine.com/histoire/systemes_ord/g6002.htm |
| AVG | J. Bourboulon (dir.), *L'Aventure Gamma 60*, Hermès/Lavoisier, 2005 (photos de pages) | `archives/photos/aventure-gamma60-*.jpg/png`                  | — (ouvrage) |
| NAM | NAM-IP Infos 2018/1-3, « Préservation : l'ordinateur Bull Gamma 60 » (dont un programme de classement en code B : `archives/photos/namip-2018-programme-classement.jpg`) | —                                                             | http://pionnier.nam-ip.be/NAM-ip-Info201801-Pres1.html |
| RTT | G. Natan / histoireinform, « Gamma 60 Bull à RTT » | —                                                             | http://www.histoireinform.com/Histoire/+infos2/chr4rtt.htm |
| SMO | M. Smotherman, « Bull Gamma 60 (1958) » | —                                                             | https://people.computing.clemson.edu/~mark/g60.html |
| EPOCH | « Bull Gamma 60 », fosse.fr | —                                                             | https://fosse.fr/en/1960/bull-gamma-60.html |
| WJCC58 | *Proceedings of the Western Joint Computer Conference : Contrasts in Computers*, Los Angeles, 6-8 mai 1958, AIEE, mars 1959 (actes complets ; contiennent DR-W) | `WJCC-1958-Contrasts-Computers.pdf`                           | — |
| CONW | M.E. Conway, « A Multiprocessor System Design », *Proc. Fall Joint Computer Conference*, 1963, p.139-146 — origine des noms FORK et JOIN (selon BAT72) | `Conway-FJCC-1963-Multiprocessor-System-Design.pdf`           | — |
| DIJ68 | E.W. Dijkstra, « The Structure of the "THE"-Multiprogramming System », *Communications of the ACM* 11(5), mai 1968, p.341-346 — sémaphores, opérations P/V, liste d'attente (p.345) | `Dijkstra-ACM-1968-Structure-THE-Multiprogramming-System.pdf` | — |
| GOLD | H.H. Goldstine, J. von Neumann, *Planning and Coding of Problems for an Electronic Computing Instrument*, partie II, vol. 1, IAS, Princeton, 1er avril 1947 (contexte : organigrammes) | `Goldstine-IASECP-1946-PlanningCoding.pdf`                    | — |
| GIL | F.B. et L.M. Gilbreth, « Process Charts — First Steps in Finding the One Best Way to Do Work », ASME, réunion annuelle, New York, 5-9 déc. 1921 (contexte : diagrammes de processus) | `Gilbreth-ASME-1921-Processc-Charts.pdf`                      | — |
| FEB-CHR | FEB, chronologie « The dawn of electronics 1949-1964 » | —                                                             | http://www.feb-patrimoine.com/histoire/english/chronoa4.htm |
| FEB | Fédération des Équipes Bull (feb-patrimoine.com) : pages sur le Gamma 60 (mémoire, SNCF, livraisons) ; à détailler page par page | — | http://www.feb-patrimoine.com/ (pages précises à compléter) |
| CAL | Graphique « Calendrier des installations clients », 1957-1974 (origine à documenter, probablement AVG) | `archives/images/Gamma60-calendrier.jpg` | — |
| MEUSE | *La Meuse*, 6 juillet 1961, « Gamma 60, l'ensemble électronique le plus puissant de Belgique au service des T.T. bruxellois » (coupure de presse) | `archives/images/Gamma60-RTT-1961.jpg` | — |
| WIKI | Wikipédia, articles « Gamma 60 » et « Compagnie des Machines Bull » (contexte ; référence secondaire, versions à dater) | — | (URL à compléter) |
| PERRET | Lettre de J. Perret à IBM France, 16 avril 1955, proposant le mot « ordinateur » (citée par HISTORY.md ; copie non archivée) | — | (à compléter) |
| UTT | A. Utterson, sur *Alphaville* (Godard, 1965) et le Gamma 60 (référence exacte à compléter) | — | (à compléter) |
| ENC | encyclopedia.com, histoire de la Compagnie des Machines Bull (nom « Gamma 60 ») | — | (URL à compléter) |

## À rechercher
Bosset (ICIP 1959) ; Duverger (Revue de l'Automatisme 1958 ; RGCF 1961) ; Kilner (Computer
Bulletin 1960) ; Yarbrough, « Some thoughts on parallel processing », CACM oct. 1960 ;
brochure Bull de programmation (code C) ; archives ANMT Roubaix, fonds 2012 007 Bull.

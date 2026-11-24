# Technologie matérielle

Utile pour le contexte, les temps et une éventuelle visualisation ; l'émulateur fonctionnel n'en
dépend pas. Sources : ONDE (description physique), B61, FEB, NAM.

## Logique
- Trois « structures » standard [ONDE] : amplificateur direct (PNP anti-saturation + NPN saturé ;
  bouclé = bascule), amplificateur inverse (2 PNP), interrupteur de rythmes (NPN +
  transformateur d'impulsions, préamplificateur PNP).
- Logique à deux couches de diodes germanium à pointes (≤ 6 groupes de 4 diodes) ; sortance 6
  (30 pour un interrupteur) ; retard ≤ 0,8 µs au pire cas.
- Transistors germanium (Radiotechnique/Philips, pnp adaptés livrés en 1959) [NAM] ; quelques
  tubes de puissance dans l'unité centrale seulement [B61 p.4].
- ≈ 3 600 « sections » de 4 amplificateurs par machine [B61 p.5].

## Horloge
5 rythmes à 200 kHz (impulsions de 1 µs toutes les 5 µs, décalées) ; rythme F à 100 kHz ;
cycle de 10 µs découpé en 10 intervalles ; générateur central à tubes, distribution par
bifilaires blindés de 100 Ω [ONDE].

## Mémoires à tores
- Matrices planes (RAI, RAC, MIC, transposition) : sélection par tiers de courant, cycle 10 µs.
- Mémoire centrale : demi-courant, 4 fils par tore, lecture destructive + réécriture ; registre
  d'adresse de 17 bascules ; générateurs de courant à tubes [ONDE] ; conçue par J. Chopin et
  H. Badoc (1958-59) ; 32 K mots ≈ 3,2 × 2,2 × 0,8 m, 7,5 kVA [FEB].

## Périphériques
- Tambour : 2 975 tr/min, 128 têtes, 6 120 impulsions par piste (204 catènes de 30 bits),
  repris des machines Bull antérieures [ONDE].
- Bandes : mylar 12,7 mm, modulation de phase, 1,90 m/s, puits à dépression, démarrage/arrêt
  ≈ 1 ms ; commutation CEL par diodes silicium ; « dérouleur fictif » de maintenance [ONDE].
- Cartes, imprimante, bande perforée : voir MACHINE.md §8.
- Configuration maximale citée par MAIT §b : jusqu'à 10 unisélecteurs regroupant jusqu'à 48
  dérouleurs (bobines de 730 m, 6 min 20 s, 1,6 M mots ; ou 1 100 m, 9 min 30 s, 2,4 M mots) ;
  jusqu'à 4 tambours (accès moyen 10 ms, 26 K mots) ; jusqu'à 20 éléments d'entrée-sortie sur
  2 multiplexeurs au plus : jusqu'à 4 lecteurs et lecteurs-perforateurs de cartes (300 cartes
  par minute), jusqu'à 8 imprimantes à simple ou double entraînement (300 ou 600 lignes par
  minute), lecteurs-perforateurs de bande, machines à écrire.

## Construction
Boîtiers (6 × 16,5 cm) et plaquettes de diodes (13,5 × 8 cm) ; section = 4 structures ;
alvéole = 28 sections ; baies de 6 ou 9 alvéoles ; fiches AMP serties ; alimentation 220 V
non stabilisée + régulation par baie ; test marginal ; « simulateur banal » ; documentation de
câblage sur cartes perforées [ONDE]. Surface d'installation jusqu'à ≈ 370 m².
Salle type selon NAM 2018/3 : 300 à 400 m², faux plancher d'environ 30 cm, groupe
moteur-générateur d'environ 300 kVA, séquenceur à tubes pour la mise sous tension des unités
dans l'ordre, climatisation à 18 °C et 60 % d'humidité relative.

## Pupitre
Machine à écrire ; pas-à-pas par cycle, par instruction canonique, par instruction complète ;
arrêt sur adresse affichée (« comparaison pupitre ») ; 8 × 8 voyants pour 8 programmes [ONDE ; MAIT].

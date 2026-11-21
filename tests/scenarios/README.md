# Scénarios du Distributeur de Données (J2)

Éléments synthétiques qui demandent des transferts au DD, pour observer l'arbitrage cycle par
cycle : `python -m gamma60 dd tests/scenarios/<nom>.yaml [--trace] [--names fr] [--profile COURS]`.

| Scénario | Ce qu'il montre |
|---|---|
| `drum_arit.yaml` | le tambour (1 catène / 100 µs) passe avant ARIT en rafale [B61 p.23-24] ; avec `dtd_order: [arithmetic, drum]`, il rate ses positions |
| `tape.yaml` | un dérouleur occupe environ 5 % des cycles [B61 p.24] |
| `multiplexer.yaml` | les éléments des classes 3-4 servis à tour de rôle derrière la vanne c34 (U-43) |
| `quantity_first.yaml` | quantités avant instructions [COURS p.6] ; lecture du DP au rang de l'élément servi (U-16) |

Champs d'un client : `name`, `kind` (type d'élément de `topology.yaml`, ou `program_distributor`),
`pattern` (`continuous` | `periodic` + `period_us`), `count`, `direction` (`read` = mémoire →
élément, `write`), `address` (valeur initiale du RAC, ou RAPA pour le DP), `rac`, `step` (+1 / −1),
`nature` (`quantity` | `instruction`), `rank_as`, `start_us`. Champs du scénario : `title`,
`profile`, `until_us` (fenêtre [0, until_us[), `memory_blocks`, `dtd_order`, `behavior`.

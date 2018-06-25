# Data Structures
Main classes are `Pick`, `Order`, `Batch` are `Warehouse` to discribe the provided data. Main class for optimization is `Model`.

### `Pick`
Should hold all about a pick in an order, eg at least:
- `id`
- `order_id` (Auftrag)
- `date` (Datum)
- `node_id`(Lagerort)
- ... everything else in csv file: Auftrag;Datum;Lagerort;Begin Komm. am;Begin Komm. um;Ende Komm. am;Ende Komm. Auftrag um;Ende Komm. Pos. um;Batch;Reihenfolge der Komm.;Wagen Nr;Artikel;Kistennummer;Erstellt am;Erstellt um;


### `Order`
Should hold all picks, ie pick objects, that make up an order:
- `picks`: list of Pick objects

### `Batch`
Should hold which order(s), that should be collect for each batch trip:
- `picks`: list of Pick objects

### `Warehouse`
Should hold all warehouse distance that is essential:
- `dist`: a np array where dist[i][j] is the distance between node i and node j

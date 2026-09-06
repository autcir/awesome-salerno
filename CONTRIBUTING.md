# Contributing to Awesome Salerno

Grazie per il tuo interesse nel contribuire a questa lista! Le contribuzioni sono fondamentali per mantenere questa risorsa aggiornata e utile.

## Come aggiungere una risorsa

1. **Fork** questo repository
2. **Crea un branch** per la tua modifica: `git checkout -b add-mio-link`
3. **Aggiungi il link** nella sezione giusta della README
4. **Segui il formato** esatto:
   ```markdown
   - [Nome della risorsa](https://url-esempio.it) - Breve descrizione di una riga.
   ```
5. **Apri un PR** con il titolo descrittivo: `Add: Nome della risorsa`

## Regole per le entry

- **Una riga per entry.** Niente paragrafi multipli, niente elenchi puntati interni.
- **Descrizione chiara e concisa.** Cosa è, perché è utile, dove si trova (se applicabile).
- **Link funzionante.** Verifica che il link sia attivo prima di aprire il PR.
- **Niente spam.** Non aggiungere servizi a pagamento non trasparenti, affiliate non dichiarati, o link promozionali.
- **Niente duplicati.** Controlla che la risorsa non sia già presente.
- **Ordine alfabetico** all'interno di ogni sottosezione (se applicabile).

## Formato delle entry

### Link a sito web
```markdown
- [Nome Sito](https://www.esempio.it) - Breve descrizione del sito.
```

### Link a luogo (OpenStreetMap)
```markdown
- [Nome Luogo](https://www.openstreetmap.org/#map=16/LAT/LNG) - Breve descrizione del luogo.
```

Sono ammessi solo link verificati: voci generate da `data/*.json` via
`scripts/gen_pois_md.py` (nome + comune + mappa OSM) e domini ufficiali
e istituzionali. Niente ID numerici OSM/TripAdvisor, niente indirizzi
o domini non presenti in fonti certe, niente superlativi non provati.

## Categorie

La README è organizzata in queste sezioni principali:

1. **Salerno** - Panoramica e Storia
2. **Spiagge** - Spiagge e lidi dai dati del progetto
3. **Attrazioni** - Chiese, monumenti, musei dai dati del progetto
4. **Food & Drink** - Locali dai dati del progetto
5. **Stay** - Strutture dai dati del progetto
6. **Trasporti** - Gestori ufficiali
7. **Servizi ed Emergenze** - Numeri di emergenza e servizi di base
8. **Eventi** - Manifestazioni ricorrenti documentate dal Comune
9. **Open Data e API** - Dataset pubblici e servizi tecnici
10. **Link utili** - Siti ufficiali e turismo
11. **Contributing** - Come aggiungere una risorsa (questa sezione)

## Issue

Se vuoi segnalare un link morto, un errore, o suggerire una nuova sezione, apri un [Issue](https://github.com/autcir/awesome-salerno/issues).

## Code of Conduct

Sii rispettoso, costruttivo e inclusivo. Non tolleriamo spam, hate speech, o comportamenti tossici.

## License

Contribuendo a questo progetto, accetti che i tuoi contributi siano rilasciati sotto la [CC0 1.0 Universal](LICENSE) license.

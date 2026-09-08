# Criteri editoriali

Cosa entra in Awesome Salerno, cosa no, e come si verifica. Chi apre una PR o una
issue accetta questi criteri; chi mantiene il repo li applica in modo uniforme.

## Ambito

Il territorio coperto e' **Salerno citta', Costiera Amalfitana e Cilento**.
Fuori ambito: il resto della Campania, salvo POI direttamente collegati (es. un
sentiero che parte dal Cilento e finisce altrove).

Il progetto e' una guida **aperta e verificabile** a luoghi ed eventi, non una
directory commerciale.

## Cosa entra

Una voce e' ammessa se soddisfa **tutti** questi punti:

1. **Esiste ed e' localizzabile** — coordinate GPS valide, all'interno dei
   confini geografici del progetto (lat 39-42, lng 14-16).
2. **E' di interesse pubblico** — sentieri, monumenti, spiagge, panorami,
   parchi, eventi ricorrenti o di rilievo.
3. **E' verificabile** — esiste una fonte pubblica consultabile (OpenStreetMap,
   Wikidata, Wikipedia, sito istituzionale, sito ufficiale dell'organizzatore).
4. **E' descrivibile in una riga** — se serve un paragrafo per spiegare perche'
   dovrebbe stare in lista, probabilmente non ci sta.

## Cosa non entra

- **Attivita' commerciali** (ristoranti, hotel, B&B, negozi, servizi
  professionali). Non abbiamo modo di curarle in modo equo e diventerebbero
  richieste di inserimento a pagamento.
- **Contenuti promozionali** — inserimenti richiesti dal proprietario a scopo
  pubblicitario, in qualunque forma.
- **Dati personali** — contatti privati, numeri di telefono personali,
  indirizzi di abitazioni.
- **Proprieta' private non visitabili** o luoghi il cui accesso e' vietato.
- **Informazioni non verificabili** — "si dice che", passaparola senza fonte.
- **Duplicati** — stessa voce entro 100 m con nome equivalente (vedi
  `scripts/merge_data.py`).
- **Eventi conclusi e non ricorrenti** — vengono rimossi, non archiviati.

## Verifica e freschezza

Ogni voce porta il campo `last_verified` (`YYYY-MM-DD`).

- I link OpenStreetMap sono generati dalle coordinate: si considerano validi e
  vengono ristampati senza chiamata di rete.
- Gli altri link esterni vengono controllati da
  `.github/workflows/link-check.yml`, ogni lunedi, tramite
  `scripts/verify_links.py`.
- I link rotti finiscono in `data/broken_links.json` e in una issue aperta
  automaticamente con label `needs-verification`.
- Un link morto viene sostituito a mano (`python3 scripts/verify_links.py --fix`)
  con il link OpenStreetMap generato dalle coordinate della voce; l'URL
  originale resta nel campo `link_rotto` per poterlo ripristinare se torna
  online. Il workflow settimanale non lo fa da solo: segnala e basta.
- Una voce non verificata da oltre **180 giorni** e' candidata alla rimozione.

Sul sito, una voce verificata da oltre 180 giorni mostra il badge
"da verificare" invece della data.

## Come si contesta una decisione

Apri una issue con label `needs-verification` indicando l'`id` della voce e la
fonte che sostiene la tua posizione. Le decisioni si prendono sulle fonti, non
sulle preferenze.

## Licenza dei contributi

I dati sono rilasciati in **CC0-1.0** (vedi `LICENSE`). Contribuendo accetti
che il tuo contributo sia distribuito con la stessa licenza. Non inserire
contenuti coperti da copyright altrui.

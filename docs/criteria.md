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
   limiti GPS del progetto (lat 39-42, lng 14-16, fonte unica
   `schema/limits.json`). Il rettangolo e' largo: ciò che sta fuori da Salerno,
   Costiera e Cilento resta nei dati con `in_ambito: false`.
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
- **Eventi conclusi e non ricorrenti** — non si mostrano in calendario e nel
  README. Nei file dati non si spostano e non si cancellano: `data/eventi.json`
  e `data/eventi_scraped.json` sono letti da altri sistemi (vedi
  `docs/CONTRACT.md`) e non devono mai diventare vuoti.

## Verifica e freschezza

`last_verified` (`YYYY-MM-DD`) dice quando una richiesta HTTP vera al link
esterno della voce e' riuscita. `last_checked` e `last_status` dicono quando e
con che esito e' stata fatta l'ultima richiesta, anche se fallita.

- I link OpenStreetMap sono generati dalle coordinate: non si richiedono, non
  ricevono `last_verified` e sono marcati `link_type: osm_generated`.
- Gli altri link esterni vengono controllati da
  `.github/workflows/link-check.yml`, ogni lunedi, tramite
  `scripts/verify_links.py` (HEAD poi GET, retry con backoff, limite per host).
- I link rotti finiscono in `data/broken_links.json` e in una issue aperta
  automaticamente con label `needs-verification`. Un server che risponde
  401/403/429 e' vivo ma non verificato.
- Un link morto viene sostituito (`python3 scripts/verify_links.py --fix`, che
  il workflow settimanale esegue) con il link OpenStreetMap generato dalle
  coordinate della voce; l'URL originale resta nel campo `link_rotto` e viene
  riesaminato a ogni controllo, per poterlo ripristinare se torna online.
- Una voce non verificata da oltre **180 giorni** e' candidata alla rimozione.

Sul sito, una voce verificata da oltre 180 giorni mostra il badge
"da verificare" invece della data.

## Come si contesta una decisione

Apri una issue con label `needs-verification` indicando l'`id` della voce e la
fonte che sostiene la tua posizione. Le decisioni si prendono sulle fonti, non
sulle preferenze.

## Licenza dei contributi

Le licenze dipendono dalla fonte (vedi `DATA-LICENSES.md`): i dati OpenStreetMap
sono ODbL, non CC0. La licenza del dataset composto la conferma il titolare.
Non inserire contenuti coperti da copyright altrui.

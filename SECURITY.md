# Sicurezza

## Cosa e' in ambito

- gli script in `scripts/`, `api/` e `mcp/` e i workflow in `.github/workflows/`;
- i dati in `data/`, se contengono dati personali o link a contenuti dannosi;
- le pagine statiche in `docs/` e `map.html`.

Non e' un servizio con account o pagamenti: non contiene segreti e non deve
contenerne. Se ne trovi uno nel repo, segnalalo come sotto.

## Come segnalare una vulnerabilita'

Non aprire una issue pubblica con i dettagli tecnici.

1. Usa la segnalazione privata di GitHub: scheda **Security** del repository,
   **Report a vulnerability**.
2. Se la scheda non e' disponibile, apri una issue che dica solo "vorrei
   segnalare un problema di sicurezza, serve un canale privato", senza dettagli:
   il titolare ti risponde con un contatto.

Indica cosa hai trovato, come riprodurlo e quale effetto ha. E' un progetto
volontario: il titolare risponde appena possibile, senza tempi garantiti.

## Versioni

Si corregge solo `main`: non ci sono rilasci mantenuti in parallelo.

## Come si evitano i problemi noti

- le action dei workflow sono fissate a SHA di commit e aggiornate da Dependabot
  con un periodo di attesa di 7 giorni;
- i job hanno permessi minimi (`permissions` per job) e, dove non si spinge,
  `persist-credentials: false`;

## Rischio aperto

I workflow girano su un runner self-hosted e il repo e' pubblico. `ci.yml` parte
su `pull_request`: una PR da fork puo' quindi far eseguire codice sul runner, a
meno che le impostazioni del repo (Settings > Actions > General, approvazione
dei workflow dei collaboratori esterni) non lo impediscano. Questa
configurazione non e' nel repo e va verificata dal titolare.

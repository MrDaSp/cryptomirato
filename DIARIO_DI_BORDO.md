# Diario di Bordo - CryptoMirato

## 1 Aprile 2026 - Inizio Progetto
Oggi abbiamo iniziato un nuovo progetto denominato **CryptoMirato**, chiaramente ispirato all'architettura e all'obiettivo di BetMirato.
Invece di analizzare asimmetrie ("edge") nelle quote sportive, CryptoMirato punta ad essere un vero e proprio "consulente automatico" per il trading di criptovalute.

### Obiettivi architetturali fissati:
- **Nessun login/auth richiesto**: La pagina sarà un cruscotto statico e accessibile da chiunque. Le analisi sono univoche, pubbliche e non personalizzate (non c'è un "bankroll" da mantenere).
- **Backend a "motore passivo"**: Uno script in Python (`scanner.py`) analizza i mercati regolarmente sfruttando l'API v3 (Tier Demo Gratuito) di CoinGecko. Lo script estrae i prezzi, il trend (1h, 24h, 7d) e i volumi, ed esegue un'analisi tecnica di base (es. RSI) per definire l'ipervenduto e le opportunità di investimento.
- **Frontend stile BetMirato**: Pagina web molto reattiva con design dark (Glassmorphism), divisa a colonne (Kanban) che mostrano a colpo d'occhio cosa compare (Verde), a cosa stare attenti (Giallo) e cosa lasciar perdere o vendere (Rosso).

### Il "Consulente Automatico"
A differenza di un semplice grafico, il software genererà veri e propri "segnali":
1.  **Cosa comprare**: Algoritmo di screening sulle top monete alla ricerca di anomalie.
2.  **A quanto vendere (Target)**: Generazione di una stima di profitto.
3.  **Calcolo Fee Reali**: Quando si indica l'edge o il potenziale profitto di un trade, verranno lette/stimate (es. 0.1% a transazione su Binance) le fee, così da mostrare all'analista che sta valutando il trade un valore più realistico di "Profitto Netto".
4.  **Take Profit / Stop Loss**: Suggerimenti dinamici basati sull'intensità e la rapidità dei movimenti di mercato registrati.

Abbiamo richiesto con successo la API Key di CoinGecko (versione Demo Free).
I prossimi step consisteranno nella creazione dello scanner Python.

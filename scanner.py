import os
import json
import time
import sys
from datetime import datetime
import requests

# Fix per console Windows
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# CONFIGURAZIONE STRATEGIA E API
# ==========================================

# Chiave API Demo di CoinGecko (sostituibile con variabile d'ambiente per prod)
COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY', 'CG-2ruTGdH5iXMMP6n3kgTYaYQW')
HEADERS = {'x-cg-demo-api-key': COINGECKO_API_KEY}

# Per rispettare il Rate Limit del piano gratuito (30 chiamate/minuto):
# 1 chiamata per i mercati + N chiamate storiche
# Preleviamo più monete dai mercati (es. 40) per filtrare le stablecoin, ma ne analizziamo max 15
TOP_N_MARKETS = 40
MAX_ANALISI = 15 

# Monete da IGNORARE (Stablecoin, Token di specifici Exchange o Wrapped tokens non sempre tradabili)
IGNORE_SYMBOLS = [
    'USDT', 'USDC', 'USDS', 'DAI', 'FDUSD', 'USDD', 'TUSD', 'BUSD', 'USDE', # Stablecoins
    'STETH', 'WETH', 'WBTC', 'RETH', 'CBETH', # Wrapped/Staked
    'WBT', 'LEO', 'OKB', 'GT', 'HT', 'KCS' # Exchange tokens (Spesso non su Nexo/Binance base)
]

# Fee di Binance ipotizzate
FEE_TAKER = 0.001   # 0.1% fee acquisto
FEE_MAKER = 0.001   # 0.1% fee vendita

def calcola_rsi(prices, window=14):
    """Calcola il (Relative Strength Index) per una serie di prezzi."""
    if len(prices) < window + 1:
        return 50  # Neutro se mancano dati
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))
            
    avg_gain = sum(gains[:window]) / window
    avg_loss = sum(losses[:window]) / window
    
    # Primo valore RSI
    if avg_loss == 0:
        return 100
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Calcolo lisciato Wilder per i giorni successivi
    for i in range(window, len(prices) - 1):
        diff = prices[i+1] - prices[i]
        gain = diff if diff > 0 else 0
        loss = abs(diff) if diff < 0 else 0
        
        avg_gain = (avg_gain * (window - 1) + gain) / window
        avg_loss = (avg_loss * (window - 1) + loss) / window
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
    return round(rsi, 2)

def genera_sistema_esperto(coin, current_price, rsi):
    """
    Simula l'intelligenza di un consulente.
    Esalta profitti netti e target/stop basati sulla situazione tecnica.
    """
    # 1. Analizza la situazione per generare Segnale (COMPRA / VENDI / ATTENDI)
    segnale = "ATTENDI"
    semaforo = "gialla"  # gialla, verde, rossa
    
    # Volatilità grezza - stimata approssimativamente in % 
    # Meno capitalizzazione = più volatilità. Prendo il Market Cap Rank come indizio grossolano.
    volatility_factor = min(0.15, max(0.05, (coin.get('market_cap_rank', 10) / 100.0) + 0.05))
    
    # Costruiamo il target e stop loss
    # Se Ipervenduto -> Segnale COMPRA
    if rsi < 35:
        segnale = "COMPRA"
        semaforo = "verde"
        # Ci aspettiamo un rimbalzo tecnico (es. pari alla volatilità)
        target_price = current_price * (1 + volatility_factor) 
        stop_price = current_price * (1 - (volatility_factor * 0.5)) # Stop stretto
        
    # Se Ipercomprato -> Segnale VENDI / NON COMPRARE
    elif rsi > 70:
        segnale = "VENDI"
        semaforo = "rossa"
        # Ci aspettiamo una correzione
        target_price = current_price * (1 - volatility_factor)
        stop_price = current_price * (1 + (volatility_factor * 0.5))
        
    # Neutro
    else:
        target_price = current_price * (1 + (volatility_factor * 0.5))
        stop_price = current_price * (1 - (volatility_factor * 0.5))
        
    # Calcolo PROFITTO NETTO in caso di acquisto
    # Sottraiamo le fee di acquisto e vendita future
    gross_profit_pct = ((target_price - current_price) / current_price) * 100
    fees_pct = (FEE_TAKER + FEE_MAKER) * 100
    net_profit_pct = gross_profit_pct - fees_pct
    
    # Se fosse un segnale di vendita, chiariamo che il profitto mancato è il calo.
    if segnale == "VENDI":
        net_profit_pct = ((current_price - target_price) / current_price) * 100 - fees_pct # Guadagno short / perdita evitata
        
    return {
        "segnale": segnale,
        "semaforo": semaforo,
        "prezzo_attuale": current_price,
        "target_price": round(target_price, 4),
        "stop_loss": round(stop_price, 4),
        "profitto_netto_stimato_pct": round(net_profit_pct, 2),
        "fee_stimate_pct": round(fees_pct, 3),
        "rischio": "ALTO" if volatility_factor > 0.1 else "MEDIO"
    }

def fetch_data():
    print("=" * 60)
    print("--- CryptoMirato Scanner in esecuzione ---")
    print("=" * 60)
    
    # 1. Ottieni le top Crypto via /coins/markets
    print(f"[1/3] Scaricamento mercati delle Top {TOP_N_MARKETS} Crypto...")
    url_markets = "https://api.coingecko.com/api/v3/coins/markets"
    params_markets = {
        'vs_currency': 'eur',
        'order': 'market_cap_desc',
        'per_page': TOP_N_MARKETS,
        'page': 1,
        'sparkline': False,
        'price_change_percentage': '1h,24h,7d'
    }
    
    res = requests.get(url_markets, headers=HEADERS, params=params_markets)
    if res.status_code != 200:
        print(f"Errore API CoinGecko: HTTP {res.status_code} - {res.text}")
        return
        
    top_coins = res.json()
    
    # Filtriamo le monete inutili per il trading (Stablecoins, WBT ecc.)
    monete_valide = [c for c in top_coins if c['symbol'].upper() not in IGNORE_SYMBOLS]
    
    # Prendiamo solo le prime N monete valide
    monete_valide = monete_valide[:MAX_ANALISI]
    
    print(f"Trovate {len(top_coins)} monete, di cui {len(monete_valide)} scambiabili (escluse stablecoin).")
    
    risultati = []
    
    # 2. Ottieni lo storico per il calcolo RSI
    print(f"\n[2/3] Analisi tecnica e calcolo RSI...")
    for i, coin in enumerate(monete_valide):
        coin_id = coin['id']
        symbol = coin['symbol'].upper()
        current_price = coin['current_price']
        
        # Pausa di 500ms tra richieste per non stressare il rate limit (30r/min)
        time.sleep(0.5) 
        
        # Storico 14 giorni (intervallo giornaliero)
        url_history = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params_history = {
            'vs_currency': 'eur',
            'days': '14',
            'interval': 'daily'
        }
        
        try:
            h_res = requests.get(url_history, headers=HEADERS, params=params_history)
            if h_res.status_code == 200:
                h_data = h_res.json()
                prices = [p[1] for p in h_data.get('prices', [])]
                
                # Calcola RSI
                rsi = calcola_rsi(prices)
            else:
                print(f"  Errore fetch storico per {symbol} ({h_res.status_code})")
                rsi = 50.0 # Valore neutro di fallback
        except Exception as e:
            print(f"  Errore interno su {symbol}: {e}")
            rsi = 50.0
            
        # 3. Consulto intelligenza (Sistema Esperto)
        consiglio = genera_sistema_esperto(coin, current_price, rsi)
        
        print(f"  ➜ {symbol}: Prezzo €{current_price} | RSI: {rsi} | Segnale: {consiglio['segnale']}")
        
        risultati.append({
            "id": coin_id,
            "nome": coin['name'],
            "simbolo": symbol,
            "logo": coin['image'],
            "rank": coin['market_cap_rank'],
            "prezzo": current_price,
            "variazione_1h": round(coin.get('price_change_percentage_1h_in_currency') or 0.0, 2),
            "variazione_24h": round(coin.get('price_change_percentage_24h_in_currency') or 0.0, 2),
            "variazione_7d": round(coin.get('price_change_percentage_7d_in_currency') or 0.0, 2),
            "volume_24h": coin.get('total_volume', 0),
            "rsi_14d": rsi,
            "analisi_tecnica": consiglio
        })
        
    # Ordinamento: Prima i COMPRA, poi ATTENDI, poi VENDI (ma per RSI, ascendente)
    risultati = sorted(risultati, key=lambda x: x['rsi_14d'])
    
    # 4. Salvataggio su JSON
    print("\n[3/3] Generazione file di output crypto_data.json...")
    
    # Creazione della stringa di statistiche globali (quanti compra/vendi)
    compra = sum(1 for r in risultati if r['analisi_tecnica']['segnale'] == 'COMPRA')
    attendi = sum(1 for r in risultati if r['analisi_tecnica']['segnale'] == 'ATTENDI')
    vendi = sum(1 for r in risultati if r['analisi_tecnica']['segnale'] == 'VENDI')
    
    output = {
        "ultimo_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fonti": "CoinGecko API (Free Tier)",
        "riepilogo": {
            "segnali_compra": compra,
            "segnali_attendi": attendi,
            "segnali_vendi": vendi
        },
        "crypto": risultati
    }
    
    with open('crypto_data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4, ensure_ascii=False)
        
    print(f"Fatto! File generato con successo.")

if __name__ == "__main__":
    fetch_data()

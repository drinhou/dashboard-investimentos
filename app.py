import streamlit as st
import pandas as pd
import yfinance as yf
import os
import datetime
import pytz

# ========== 1. CONFIGURAÇÃO ==========
st.set_page_config(
    page_title="Dinheiro Data | Onyx",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== 2. CSS "ONYX" (VISUAL + MOBILE CORRIGIDO) ==========
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

        :root {
            --bg-deep: #050505;
            --glass-bg: rgba(20, 20, 20, 0.6);
            --glass-border: rgba(255, 255, 255, 0.1);
            --neon-green: #00ff9d;
            --text-main: #ffffff;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-deep);
            color: var(--text-main);
            scroll-behavior: smooth !important;
        }
        
        #MainMenu, footer, header { visibility: hidden; }
        [data-testid="stElementToolbar"] { display: none !important; }
        .stMarkdown a.anchor-link { display: none !important; }
        .block-container { padding-top: 1rem; padding-bottom: 3rem; }

        /* HERO HEADER */
        .hero-container {
            text-align: center;
            padding: 60px 20px 40px 20px;
            background: radial-gradient(circle at center, rgba(0, 255, 157, 0.05) 0%, transparent 70%);
            margin-bottom: 30px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .hero-title {
            font-size: 4rem;
            font-weight: 800;
            letter-spacing: -2px;
            background: linear-gradient(180deg, #ffffff 0%, #666666 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            line-height: 1.1;
        }
        
        .hero-subtitle {
            font-size: 0.9rem;
            color: var(--neon-green);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .live-indicator {
            width: 8px; height: 8px;
            background-color: var(--neon-green);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--neon-green);
            animation: pulse 2s infinite;
        }

        /* CARDS */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            text-decoration: none !important;
            display: block;
            height: 100%;
            position: relative;
            overflow: hidden;
        }
        
        .glass-card:hover {
            border-color: rgba(0, 255, 157, 0.4);
            transform: translateY(-4px);
        }
        
        .card-icon { font-size: 1.8rem; margin-bottom: 10px; display: block; }
        .card-title { font-size: 1.1rem; font-weight: 700; color: #fff; display: block; margin-bottom: 4px; }
        .card-desc { font-size: 0.8rem; color: #777; display: block; }

        /* SEÇÕES */
        .section-box {
            margin-top: 50px;
            margin-bottom: 20px;
            padding-left: 15px;
            border-left: 4px solid var(--neon-green);
            background: linear-gradient(90deg, rgba(0, 255, 157, 0.05) 0%, transparent 100%);
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-radius: 0 12px 12px 0;
            padding-top: 12px;
            padding-bottom: 12px;
            padding-right: 15px;
        }
        .section-title { font-size: 1.4rem; font-weight: 800; color: #fff; text-transform: uppercase; }
        .section-badge { 
            background: rgba(0, 255, 157, 0.1); 
            color: var(--neon-green); 
            padding: 4px 10px; 
            border-radius: 6px; 
            font-size: 0.75rem; 
            font-weight: 700; 
            border: 1px solid rgba(0, 255, 157, 0.2);
            white-space: nowrap;
        }
        .section-desc-text {
            margin-left: 20px; margin-bottom: 20px; color:#666; font-size:0.85rem; max-width:800px;
        }

        /* TABELAS */
        div[data-testid="stDataFrame"] {
            background-color: #080808 !important;
            border: 1px solid #1f1f1f !important;
            border-radius: 12px;
        }
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #0f0f0f !important;
            color: #666 !important;
            font-size: 11px !important;
            font-weight: 800 !important;
            text-transform: uppercase;
            border-bottom: 1px solid #222 !important;
            text-align: center !important;
            justify-content: center !important;
            display: flex;
        }
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            background-color: #080808 !important;
            color: #e0e0e0 !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            border-bottom: 1px solid #161616 !important;
            display: flex;
            justify-content: center !important;
            align-items: center !important;
            pointer-events: none !important;
        }
        div[data-testid="stDataFrame"] div[role="gridcell"] > div {
            display: flex;
            justify-content: center !important;
            align-items: center !important;
            width: 100%;
            text-align: center !important;
        }
        div[data-testid="stDataFrame"] img {
            border-radius: 50%;
            width: 26px !important;
            height: 26px !important;
            object-fit: cover;
            border: 1px solid #333;
            background: #fff;
            padding: 1px;
            display: block;
            margin: 0 auto;
        }

        /* INPUTS */
        div[data-baseweb="base-input"] {
            background-color: #0a0a0a !important;
            border: 1px solid #333 !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="base-input"]:focus-within {
            border-color: var(--neon-green) !important;
        }
        input { color: white !important; }

        /* FAQ STYLE (CSS ESPECÍFICO) */
        .streamlit-expanderHeader {
            background-color: rgba(20, 20, 20, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #e0e0e0 !important;
            font-family: 'Inter', sans-serif !important;
            border-radius: 8px !important;
        }
        .streamlit-expanderHeader:hover {
            border-color: var(--neon-green) !important;
            color: var(--neon-green) !important;
        }
        .streamlit-expanderContent {
            background-color: transparent !important;
            color: #9ca3af !important;
            border: none !important;
            padding-left: 20px !important;
            font-size: 0.9rem !important;
        }
        .streamlit-expanderHeader svg {
            fill: #666 !important;
        }

        /* FOOTER */
        .legal-footer {
            margin-top: 60px;
            padding: 30px 20px;
            border-top: 1px solid #222;
            text-align: center;
            font-size: 0.7rem;
            color: #444;
            background: #050505;
            line-height: 1.5;
        }

        /* MOBILE FIXES */
        @media (max-width: 768px) {
            .hero-container { padding: 40px 15px 20px 15px; }
            .hero-title { font-size: 2.2rem; }
            .hero-subtitle { font-size: 0.7rem; flex-wrap: wrap; }
            
            .glass-card { padding: 15px; margin-bottom: 8px; min-height: 90px; }
            .card-icon { font-size: 1.4rem; margin-bottom: 5px; }
            .card-title { font-size: 0.9rem; }
            .card-desc { display: none; }
            
            .section-box { 
                flex-direction: column !important;
                align-items: flex-start !important;
                gap: 8px;
                padding-bottom: 15px;
                height: auto;
            }
            .section-title { font-size: 1.2rem; }
            .section-badge { align-self: flex-start; font-size: 0.65rem; padding: 4px 8px; }
            .section-desc-text { margin-left: 10px; font-size: 0.8rem; margin-bottom: 15px; }
            
            div[data-testid="stDataFrame"] div[role="columnheader"] { font-size: 10px !important; padding: 8px 2px !important; }
            div[data-testid="stDataFrame"] div[role="gridcell"] { font-size: 11px !important; padding: 8px 2px !important; }
            div[data-testid="stDataFrame"] img { width: 20px !important; height: 20px !important; }
            
            .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
        }
        
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }
    </style>
""", unsafe_allow_html=True)

# ========== 3. LÓGICA DE DADOS ==========

def get_time_greeting():
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(tz)
    h = now.hour
    greeting = "BOA NOITE"
    if 5 <= h < 12: greeting = "BOM DIA"
    elif 12 <= h < 18: greeting = "BOA TARDE"
    return greeting, now.strftime("%H:%M")

def clean_currency(x):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        try: return float(x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip())
        except: return 0.0
    return 0.0

def clean_dy_percentage(x):
    val = clean_currency(x)
    return val * 100 if 0 < val < 1.0 else val

def get_logo_url(ticker):
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip().upper()
    sites = {
        'CXSE3': 'caixaseguradora.com.br', 'BBSE3': 'bbseguros.com.br', 'ODPV3': 'odontoprev.com.br',
        'BBAS3': 'bb.com.br', 'ABCB4': 'abcbrasil.com.br', 'ITUB4': 'itau.com.br',
        'ISAE4': 'isaenergiabrasil.com.br', 'TRPL4': 'isaenergiabrasil.com.br',
        'CMIG4': 'cemig.com.br', 'SAPR4': 'sanepar.com.br', 'SAPR11': 'sanepar.com.br',
        'PETR4': 'petrobras.com.br', 'RANI3': 'irani.com.br', 'KLBN11': 'klabin.com.br',
        'KLBN4': 'klabin.com.br', 'IRBR3': 'ri.irbre.com', 'FLRY3': 'fleury.com.br',
        'PSSA3': 'portoseguro.com.br', 'WEGE3': 'weg.net', 'VALE3': 'vale.com',
        'ABEV3': 'ambev.com.br', 'B3SA3': 'b3.com.br', 'EGIE3': 'engie.com.br'
    }
    if clean in sites: return f"https://www.google.com/s2/favicons?domain={sites[clean]}&sz=128"
    if clean in ['BTC','BITCOIN']: return "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    if clean in ['ETH','ETHEREUM']: return "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
    if clean in ['SOL','SOLANA']: return "https://assets.coingecko.com/coins/images/4128/small/solana.png"
    return f"https://cdn.jsdelivr.net/gh/thefintz/icon-project@master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_market_data():
    groups = {
        'USA': { 'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'DOW JONES': '^DJI', 'VIX': '^VIX' },
        'BRASIL': { 'IBOVESPA': '^BVSP', 'IFIX': 'IFIX.SA', 'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA' },
        'MOEDAS': { 'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X', 'LIBRA': 'GBPBRL=X', 'DXY': 'DX-Y.NYB' },
        'COMMODITIES': { 'OURO': 'GC=F', 'PRATA': 'SI=F', 'COBRE': 'HG=F', 'PETRÓLEO': 'BZ=F' },
        'CRIPTO': { 'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD', 'SOLANA': 'SOL-USD', 'BNB': 'BNB-USD' }
    }
    final_dfs = {}
    for cat, items in groups.items():
        rows = []
        try:
            tickers = list(items.values())
            data = yf.download(tickers, period="5d", progress=False)['Close']
            for name, ticker in items.items():
                try:
                    series = pd.Series()
                    if len(tickers) > 1 and ticker in data.columns: series = data[ticker].dropna()
                    elif isinstance(data, pd.Series): series = data.dropna()
                    
                    if len(series) >= 2:
                        curr, prev = series.iloc[-1], series.iloc[-2]
                        pct = ((curr - prev) / prev) * 100
                        rows.append([name, curr, pct])
                    else: rows.append([name, 0.0, 0.0])
                except: rows.append([name, 0.0, 0.0])
        except: pass
        while len(rows) < 4: rows.append(["-", 0.0, 0.0])
        final_dfs[cat] = pd.DataFrame(rows[:4], columns=["Ativo", "Preço", "Var%"])
    return final_dfs

@st.cache_data(ttl=300)
def get_br_prices(ticker_list):
    if not ticker_list: return {}
    sa_tickers = [f"{t}.SA" for t in ticker_list]
    try:
        data = yf.download(sa_tickers, period="1d", progress=False)['Close'].iloc[-1]
        if isinstance(data, float): return {ticker_list[0]: data}
        prices = {}
        for t in ticker_list:
            if f"{t}.SA" in data: prices[t] = data[f"{t}.SA"]
        return prices
    except: return {}

def load_data():
    df_radar, df_div = pd.DataFrame(), pd.DataFrame()
    file_data = None
    if os.path.exists("PEC.xlsx"): file_data = pd.ExcelFile("PEC.xlsx")
    elif os.path.exists("PEC - Página1.csv"): file_data = pd.read_csv("PEC - Página1.csv")
    
    if file_data is not None:
        try:
            target_df = pd.DataFrame()
            if isinstance(file_data, pd.ExcelFile):
                for sheet in file_data.sheet_names:
                    temp = pd.read_excel(file_data, sheet)
                    if any("BAZIN" in str(c).upper() for c in temp.columns):
                        target_df = temp; break
            else: target_df = file_data

            if not target_df.empty:
                target_df.columns = [str(c).strip().upper() for c in target_df.columns]
                cols = target_df.columns
                c_tick = next((c for c in cols if 'TICKER' in c), None)
                c_baz = next((c for c in cols if 'BAZIN' in c), None)
                c_dy = next((c for c in cols if 'DY' in c), None)
                c_dpa = next((c for c in cols if 'DPA' in c), None)
                c_emp = next((c for c in cols if 'EMPRESA' in c), None)

                if c_tick and c_baz:
                    target_df['T
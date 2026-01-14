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

# ========== 2. DESIGN SYSTEM "ONYX" (CSS AVANÇADO) ==========
st.markdown("""
    <style>
        /* IMPORTAR FONTE MODERNA */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

        /* --- VARIÁVEIS DE COR (PALETA NEON DARK) --- */
        :root {
            --bg-deep: #050505;
            --glass-bg: rgba(20, 20, 20, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
            --neon-green: #00ff9d;
            --deep-green: #064e3b;
            --text-main: #ffffff;
            --text-dim: #888888;
        }

        /* --- RESET GLOBAL --- */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-deep);
            color: var(--text-main);
            scroll-behavior: smooth !important;
        }
        
        /* Remove excessos do Streamlit */
        #MainMenu, footer, header { visibility: hidden; }
        [data-testid="stElementToolbar"] { display: none !important; }
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }

        /* --- HEADER HERO --- */
        .hero-container {
            text-align: center;
            padding: 60px 20px;
            background: radial-gradient(circle at center, rgba(0, 255, 157, 0.08) 0%, transparent 60%);
            margin-bottom: 40px;
            border-bottom: 1px solid var(--glass-border);
        }
        
        .hero-title {
            font-size: 4rem;
            font-weight: 800;
            letter-spacing: -2px;
            background: linear-gradient(180deg, #fff 0%, #aaa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            text-shadow: 0 0 30px rgba(0, 255, 157, 0.2);
        }
        
        .hero-subtitle {
            font-size: 1.1rem;
            color: var(--neon-green);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .live-dot {
            width: 8px;
            height: 8px;
            background-color: var(--neon-green);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--neon-green);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.4; } 100% { opacity: 1; } }

        /* --- CARDS DE NAVEGAÇÃO (GLASSMORPHISM) --- */
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            position: relative;
            overflow: hidden;
            text-decoration: none !important;
            display: block;
            height: 100%;
        }
        
        .glass-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, var(--neon-green), transparent);
            opacity: 0;
            transition: 0.3s;
        }
        
        .glass-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px -10px rgba(0, 255, 157, 0.15);
            border-color: rgba(0, 255, 157, 0.3);
        }
        
        .glass-card:hover::before { opacity: 1; }
        
        .card-icon { font-size: 1.8rem; margin-bottom: 10px; display: block; }
        .card-title { font-size: 1.2rem; font-weight: 700; color: #fff !important; display: block; }
        .card-desc { font-size: 0.85rem; color: #888 !important; margin-top: 5px; display: block; }

        /* --- CONTAINER DE SEÇÃO (FUTURISTA) --- */
        .section-box {
            margin-top: 60px;
            margin-bottom: 20px;
            padding: 20px;
            border-left: 4px solid var(--neon-green);
            background: linear-gradient(90deg, rgba(0, 255, 157, 0.05) 0%, transparent 100%);
            border-radius: 0 12px 12px 0;
        }
        .section-title { font-size: 1.8rem; font-weight: 700; color: #fff; margin: 0; }
        .section-meta { font-size: 0.9rem; color: var(--neon-green); font-family: 'Courier New', monospace; margin-top: 5px; }

        /* --- TABELAS REESTILIZADAS (CLEAN & CENTER) --- */
        div[data-testid="stDataFrame"] {
            background-color: #0a0a0a !important;
            border: 1px solid #222 !important;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }

        /* Header Tabela */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #111 !important;
            color: #888 !important;
            font-size: 11px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid #333 !important;
            text-align: center !important;
            justify-content: center !important;
            display: flex;
        }

        /* Células Tabela */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            background-color: #0a0a0a !important;
            color: #eee !important;
            font-size: 13px !important;
            font-weight: 500 !important;
            border-bottom: 1px solid #1a1a1a !important;
            display: flex;
            justify-content: center !important;
            align-items: center !important;
            pointer-events: none !important; /* BLOQUEIA SELEÇÃO */
        }
        
        /* Centralização Interna */
        div[data-testid="stDataFrame"] div[role="gridcell"] > div {
            display: flex;
            justify-content: center !important;
            align-items: center !important;
            width: 100%;
            text-align: center !important;
        }

        /* Logos Circulares */
        div[data-testid="stDataFrame"] img {
            border-radius: 50%;
            width: 28px !important;
            height: 28px !important;
            object-fit: cover;
            border: 1px solid #333;
            background: #fff;
            padding: 1px;
            display: block;
            margin: 0 auto;
        }

        /* INPUTS DE PESQUISA (GLOW) */
        div[data-baseweb="base-input"] {
            background-color: #0a0a0a !important;
            border-color: #333 !important;
            border-radius: 8px !important;
            color: white !important;
        }
        div[data-baseweb="base-input"]:focus-within {
            border-color: var(--neon-green) !important;
            box-shadow: 0 0 15px rgba(0, 255, 157, 0.1) !important;
        }
        input { color: white !important; }

        /* FOOTER */
        .legal-footer {
            margin-top: 80px;
            padding: 40px;
            border-top: 1px solid #222;
            text-align: center;
            font-size: 0.75rem;
            color: #555;
            background: #080808;
        }
    </style>
""", unsafe_allow_html=True)

# ========== 3. LÓGICA ROBUSTA ==========

def get_time_greeting():
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(tz)
    h = now.hour
    greeting = "Boa noite"
    if 5 <= h < 12: greeting = "Bom dia"
    elif 12 <= h < 18: greeting = "Boa tarde"
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

# Função para carregar dados
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
                    target_df['TICKER_F'] = target_df[c_tick].astype(str).str.strip().str.upper()
                    target_df['BAZIN_F'] = target_df[c_baz].apply(clean_currency)
                    target_df['DY_F'] = target_df[c_dy].apply(clean_dy_percentage) if c_dy else 0.0
                    target_df['DPA_F'] = target_df[c_dpa].apply(clean_currency) if c_dpa else 0.0
                    
                    prices = get_br_prices(target_df['TICKER_F'].unique().tolist())
                    target_df['PRECO_F'] = target_df['TICKER_F'].map(prices).fillna(0)
                    target_df['MARGEM_VAL'] = target_df.apply(lambda x: ((x['BAZIN_F'] - x['PRECO_F']) / x['PRECO_F'] * 100) if x['PRECO_F'] > 0 else -999, axis=1)
                    target_df['Logo'] = target_df['TICKER_F'].apply(get_logo_url)
                    target_df['Ativo'] = target_df[c_emp] if c_emp else target_df['TICKER_F']
                    
                    df_radar = target_df[target_df['BAZIN_F'] > 0][['Logo', 'Ativo', 'TICKER_F', 'BAZIN_F', 'PRECO_F', 'MARGEM_VAL']].sort_values('MARGEM_VAL', ascending=False)
                    df_div = target_df[target_df['DY_F'] > 0][['Logo', 'Ativo', 'TICKER_F', 'DPA_F', 'DY_F']].sort_values('DY_F', ascending=False)
        except: pass
    return df_radar, df_div

# ========== 4. LAYOUT / UI ==========

greeting, time_now = get_time_greeting()

# Hero Section
st.markdown(f"""
    <div class='hero-container'>
        <h1 class='hero-title'>DINHEIRO DATA</h1>
        <div class='hero-subtitle'>
            <div class='live-dot'></div>
            {greeting} • MERCADO EM TEMPO REAL • {time_now}
        </div>
    </div>
""", unsafe_allow_html=True)

# Navigation Cards (Glassmorphism)
n1, n2, n3 = st.columns(3)
with n1:
    st.markdown("""
    <a href='#panorama' class='glass-card'>
        <span class='card-icon'>🌍</span>
        <span class='card-title'>Panorama Global</span>
        <span class='card-desc'>Índices, Moedas e Commodities</span>
    </a>
    """, unsafe_allow_html=True)
with n2:
    st.markdown("""
    <a href='#radar-bazin' class='glass-card'>
        <span class='card-icon'>🎯</span>
        <span class='card-title'>Radar Bazin</span>
        <span class='card-desc'>Preço Teto & Margem de Segurança</span>
    </a>
    """, unsafe_allow_html=True)
with n3:
    st.markdown("""
    <a href='#dividendos' class='glass-card'>
        <span class='card-icon'>💰</span>
        <span class='card-title'>Dividendos</span>
        <span class='card-desc'>Projeções de Yield 2026</span>
    </a>
    """, unsafe_allow_html=True)

# Carrega dados
M = get_market_data()
df_radar, df_div = load_data()

# --- PANORAMA ---
st.markdown("<div id='panorama'></div>", unsafe_allow_html=True)
st.markdown("""
<div class='section-box'>
    <div class='section-title'>Panorama Global</div>
    <div class='section-meta'>// MONITORAMENTO DE ATIVOS</div>
</div>
""", unsafe_allow_html=True)

def render_market_table(col, title, df):
    col.markdown(f"<div style='margin-bottom:10px; font-weight:700; color:#fff;'>{title}</div>", unsafe_allow_html=True)
    if not df.empty:
        # Styles
        def color_var(val):
            if val > 0: return 'color: #00ff9d; font-weight: 600;'
            if val < 0: return 'color: #ff4d4d; font-weight: 600;'
            return 'color: #666;'
        
        def fmt_price(val): return "-" if val == 0 else f"{val:.2f}"

        styled = df.style.format({'Preço': fmt_price, 'Var%': '{:+.2f}%'}).map(color_var, subset=['Var%'])
        
        col.dataframe(
            styled,
            column_config={
                'Ativo': st.column_config.TextColumn("Ativo"),
                'Preço': st.column_config.TextColumn("Cotação"),
                'Var%': st.column_config.TextColumn("Var %")
            },
            hide_index=True,
            use_container_width=True
        )

r1, r2, r3 = st.columns(3)
render_market_table(r1, "🇺🇸 ÍNDICES EUA", M['USA'])
render_market_table(r2, "🇧🇷 ÍNDICES BRASIL", M['BRASIL'])
render_market_table(r3, "💱 MOEDAS", M['MOEDAS'])

st.write("") 

r4, r5 = st.columns(2)
render_market_table(r4, "🛢️ COMMODITIES", M['COMMODITIES'])
render_market_table(r5, "💎 CRIPTOATIVOS", M['CRIPTO'])

# --- RADAR BAZIN ---
st.markdown("<div id='radar-bazin'></div>", unsafe_allow_html=True)
count_bazin = len(df_radar[df_radar['MARGEM_VAL'] > 10]) if not df_radar.empty else 0

st.markdown(f"""
<div class='section-box'>
    <div style='display:flex; justify-content:space-between; align-items:center;'>
        <div class='section-title'>Radar Bazin</div>
        <div style='background:#064e3b; color:#00ff9d; padding:5px 15px; border-radius:20px; font-size:0.8rem; font-weight:700;'>
            {count_bazin} OPORTUNIDADES (>10%)
        </div>
    </div>
    <div style='margin-top:10px; color:#888; font-size:0.9rem;'>
        O Preço Teto é calculado utilizando a metodologia de Décio Bazin (adaptado à nossa visão), visando identificar ativos que pagam bons dividendos a preços descontados.
    </div>
</div>
""", unsafe_allow_html=True)

if not df_radar.empty:
    search1 = st.text_input("", placeholder="🔍 Ex: BB Seguridade (Bazin)...", key="s1")
    
    data_show = df_radar.copy()
    if search1:
        data_show = data_show[data_show['Ativo'].str.contains(search1, case=False) | data_show['TICKER_F'].str.contains(search1, case=False)]

    def style_bazin(v):
        if v > 10: return 'color: #00ff9d; font-weight: 700;'
        if v < 0: return 'color: #ff4d4d; font-weight: 700;'
        return 'color: #666;'

    st.dataframe(
        data_show.style.format({
            'BAZIN_F': 'R$ {:.2f}', 'PRECO_F': 'R$ {:.2f}', 'MARGEM_VAL': '{:+.1f}%'
        }).map(style_bazin, subset=['MARGEM_VAL']),
        column_config={
            "Logo": st.column_config.ImageColumn(""),
            "Ativo": st.column_config.TextColumn("Ativo"),
            "TICKER_F": None,
            "BAZIN_F": st.column_config.TextColumn("Preço Teto"),
            "PRECO_F": st.column_config.TextColumn("Cotação"),
            "MARGEM_VAL": st.column_config.TextColumn("Margem")
        },
        hide_index=True,
        use_container_width=True
    )

# --- DIVIDENDOS ---
st.markdown("<div id='dividendos'></div>", unsafe_allow_html=True)
count_div = len(df_div[df_div['DY_F'] > 8]) if not df_div.empty else 0

st.markdown(f"""
<div class='section-box'>
    <div style='display:flex; justify-content:space-between; align-items:center;'>
        <div class='section-title'>Dividendos</div>
        <div style='background:#064e3b; color:#00ff9d; padding:5px 15px; border-radius:20px; font-size:0.8rem; font-weight:700;'>
            {count_div} ATIVOS PAGADORES (>8%)
        </div>
    </div>
    <div style='margin-top:10px; color:#888; font-size:0.9rem;'>
        Estimativas de rendimento anual (Dividend Yield) para o exercício de 2026, baseadas em projeções de mercado e histórico de pagamentos.
    </div>
</div>
""", unsafe_allow_html=True)

if not df_div.empty:
    search2 = st.text_input("", placeholder="🔍 Ex: BB Seguridade (Dividendos)...", key="s2")
    
    div_show = df_div.copy()
    if search2:
        div_show = div_show[div_show['Ativo'].str.contains(search2, case=False) | div_show['TICKER_F'].str.contains(search2, case=False)]

    def style_dy(v):
        return 'color: #00ff9d; font-weight: 700;' if v > 8 else 'color: #666;'

    st.dataframe(
        div_show.style.format({
            'DPA_F': 'R$ {:.2f}', 'DY_F': '{:.2f}%'
        }).map(style_dy, subset=['DY_F']),
        column_config={
            "Logo": st.column_config.ImageColumn(""),
            "Ativo": st.column_config.TextColumn("Ativo"),
            "TICKER_F": None,
            "DPA_F": st.column_config.TextColumn("Div. / Ação"),
            "DY_F": st.column_config.TextColumn("Yield Projetado")
        },
        hide_index=True,
        use_container_width=True
    )

# --- FOOTER ---
st.markdown("""
<div class='legal-footer'>
    <strong>⚠️ ISENÇÃO DE RESPONSABILIDADE</strong><br><br>
    Este dashboard tem caráter estritamente educativo e informativo. Nenhuma informação aqui apresentada constitui recomendação de compra ou venda de ativos.
    Os dados são obtidos de fontes públicas e podem conter atrasos.
</div>
""", unsafe_allow_html=True)
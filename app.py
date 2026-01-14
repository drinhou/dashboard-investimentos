import streamlit as st
import pandas as pd
import yfinance as yf
import os
import datetime

# --- 1. CONFIGURAÇÃO (WIDE & DARK) ---
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS PREMIUM (UX CENTRALIZADO E NAVEGAÇÃO) ---
st.markdown("""
    <style>
        /* Fundo e Fonte */
        .stApp { background-color: #0e1117; color: #e0e0e0; scroll-behavior: smooth; }
        * { font-family: 'Segoe UI', 'Roboto', sans-serif; }
        
        /* HEADER DE NAVEGAÇÃO (BOTÕES) */
        .nav-card {
            background-color: #1f2937;
            border: 1px solid #374151;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: white;
            display: block;
            margin-bottom: 20px;
        }
        .nav-card:hover {
            background-color: #374151;
            border-color: #60a5fa;
            transform: translateY(-2px);
        }
        .nav-title { font-weight: bold; font-size: 1.1rem; display: block; }
        .nav-desc { font-size: 0.8rem; color: #9ca3af; display: block; margin-top: 5px;}

        /* TABELAS - CENTRALIZAÇÃO TOTAL */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #111827;
            color: #9ca3af;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            border-bottom: 2px solid #374151;
            text-align: center !important;
            justify-content: center !important;
            display: flex;
        }

        /* CÉLULAS - CENTRALIZAÇÃO TOTAL */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            display: flex;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            font-size: 14px;
            font-weight: 500;
            height: 100%;
        }
        
        /* LOGOS CIRCULARES NO MEIO */
        div[data-testid="stDataFrame"] div[role="gridcell"] img {
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid #4b5563;
            padding: 2px;
            background-color: white;
            width: 32px;
            height: 32px;
            display: block;
            margin: 0 auto; /* Garante centro */
        }

        /* TÍTULOS DE SEÇÃO COM ÂNCORA */
        .section-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f3f4f6;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 5px solid #3b82f6;
            padding-left: 15px;
            background: linear-gradient(90deg, #1f2937 0%, transparent 100%);
            padding-top: 8px;
            padding-bottom: 8px;
            border-radius: 0 8px 8px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .kpi-badge {
            background-color: #064e3b;
            color: #4ade80;
            font-size: 0.9rem;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: 600;
            border: 1px solid #059669;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES AUXILIARES ---

def get_greeting():
    h = datetime.datetime.now().hour
    if 5 <= h < 12: return "Bom dia"
    elif 12 <= h < 18: return "Boa tarde"
    return "Boa noite"

def clean_currency(x):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

def clean_dy_percentage(x):
    val = clean_currency(x)
    if val > 0 and val < 1.0: return val * 100
    return val

def get_logo_url(ticker):
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip().upper()
    
    # LISTA MANUAL DE SITES
    meus_sites = {
        'CXSE3': 'caixaseguradora.com.br', 'BBSE3': 'bbseguros.com.br', 'ODPV3': 'odontoprev.com.br',
        'BBAS3': 'bb.com.br', 'ABCB4': 'abcbrasil.com.br', 'ITUB4': 'itau.com.br',
        'ISAE4': 'isaenergiabrasil.com.br', 'TRPL4': 'isaenergiabrasil.com.br',
        'CMIG4': 'cemig.com.br', 'SAPR4': 'sanepar.com.br', 'SAPR11': 'sanepar.com.br',
        'PETR4': 'petrobras.com.br', 'RANI3': 'irani.com.br', 'KLBN11': 'klabin.com.br',
        'KLBN4': 'klabin.com.br', 'IRBR3': 'ri.irbre.com', 'FLRY3': 'fleury.com.br',
        'PSSA3': 'portoseguro.com.br', 'WEGE3': 'weg.net', 'VALE3': 'vale.com',
        'ABEV3': 'ambev.com.br', 'B3SA3': 'b3.com.br', 'EGIE3': 'engie.com.br'
    }

    if clean in meus_sites:
        return f"https://www.google.com/s2/favicons?domain={meus_sites[clean]}&sz=128"
    
    if clean in ['BTC', 'BITCOIN']: return "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    if clean in ['ETH', 'ETHEREUM']: return "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
    if clean in ['SOL', 'SOLANA']: return "https://assets.coingecko.com/coins/images/4128/small/solana.png"

    return f"https://cdn.jsdelivr.net/gh/thefintz/icon-project@master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_market_data_distributed():
    groups = {
        'USA': { 'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'DOW JONES': '^DJI', 'VIX (Medo)': '^VIX' },
        'BRASIL': { 'IBOVESPA': '^BVSP', 'IFIX (FIIs)': 'IFIX.SA', 'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA' },
        'MOEDAS': { 'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X', 'DXY Global': 'DX-Y.NYB', 'LIBRA': 'GBPBRL=X' },
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
                    series = data[ticker].dropna() if len(tickers) > 1 and ticker in data.columns else data.dropna()
                    if len(series) >= 2:
                        curr, prev = series.iloc[-1], series.iloc[-2]
                        delta = curr - prev
                        pct = (delta / prev) * 100
                        rows.append([name, curr, pct])
                    else: rows.append([name, 0.0, 0.0])
                except: rows.append([name, 0.0, 0.0])
        except: pass
        # Garante 4 linhas fixas para simetria perfeita
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

# --- 4. APP LAYOUT ---

# Topo: Saudação
st.markdown(f"<h2 style='text-align: center; color: white; margin-bottom: 30px;'>🦅 {get_greeting()}, Investidor</h2>", unsafe_allow_html=True)

# NAVEGAÇÃO (BOTÕES CLICÁVEIS)
# Usamos HTML anchors para navegar na mesma página
nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.markdown("""<a href='#panorama' class='nav-card'>
        <span class='nav-title'>🌍 Panorama</span>
        <span class='nav-desc'>Mercado Global em Tempo Real</span>
    </a>""", unsafe_allow_html=True)
with nav2:
    st.markdown("""<a href='#radar-bazin' class='nav-card'>
        <span class='nav-title'>🎯 Radar Bazin</span>
        <span class='nav-desc'>Preço Teto e Margem</span>
    </a>""", unsafe_allow_html=True)
with nav3:
    st.markdown("""<a href='#dividendos' class='nav-card'>
        <span class='nav-title'>💰 Dividendos</span>
        <span class='nav-desc'>Yield Projetado 2026</span>
    </a>""", unsafe_allow_html=True)

M = get_market_data_distributed()

# --- ANCHOR: PANORAMA ---
st.markdown("<div id='panorama'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>🌍 Panorama de Mercado</div>", unsafe_allow_html=True)

def show_mini_table(col, title, df):
    col.write(f"**{title}**")
    if not df.empty:
        # APENAS VERDE OU VERMELHO
        def color_var(val):
            color = '#4ade80' if val > 0 else '#f87171' if val < 0 else '#6b7280'
            return f'color: {color}; font-weight: bold;'

        styled_df = df.style.format({ "Preço": "{:.2f}", "Var%": "{:+.2f}%" }).map(color_var, subset=['Var%'])
        
        col.dataframe(
            styled_df,
            column_config={
                "Ativo": st.column_config.TextColumn("Ativo"),
                "Preço": st.column_config.NumberColumn("Cotação"),
                "Var%": st.column_config.TextColumn("Var %")
            },
            hide_index=True,
            use_container_width=True
        )

# Layout Panorama (Simétrico)
row1_1, row1_2, row1_3 = st.columns(3)
with row1_1: show_mini_table(row1_1, "🇺🇸 Índices EUA", M['USA'])
with row1_2: show_mini_table(row1_2, "🇧🇷 Brasil", M['BRASIL'])
with row1_3: show_mini_table(row1_3, "💱 Moedas", M['MOEDAS'])

st.write("") 

row2_1, row2_2 = st.columns([1,1]) # Centralizado em 2 colunas
with row2_1: show_mini_table(row2_1, "🛢️ Commodities", M['COMMODITIES'])
with row2_2: show_mini_table(row2_2, "💎 Criptoativos", M['CRIPTO'])


# --- LÓGICA DE DADOS ---
df_radar, df_div = pd.DataFrame(), pd.DataFrame()
uploaded = st.sidebar.file_uploader("📂 Carregar Dados", type=['xlsx', 'csv'])
file_data = None

if uploaded: file_data = pd.read_csv(uploaded) if uploaded.name.endswith('.csv') else pd.ExcelFile(uploaded)
elif os.path.exists("PEC.xlsx"): file_data = pd.ExcelFile("PEC.xlsx")
elif os.path.exists("PEC - Página1.csv"): file_data = pd.read_csv("PEC - Página1.csv")

if file_data is not None:
    try:
        target_df = pd.DataFrame()
        if isinstance(file_data, pd.ExcelFile):
            for sheet in file_data.sheet_names:
                temp = pd.read_excel(file_data, sheet)
                if any("BAZIN" in str(c).upper() for c in temp.columns):
                    target_df = temp
                    break
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
                
                df_radar = target_df[target_df['BAZIN_F'] > 0][['Logo', 'Ativo', 'BAZIN_F', 'PRECO_F', 'MARGEM_VAL']].sort_values('MARGEM_VAL', ascending=False)
                df_div = target_df[target_df['DY_F'] > 0][['Logo', 'Ativo', 'DPA_F', 'DY_F']].sort_values('DY_F', ascending=False)
    except: pass

# --- ANCHOR: RADAR BAZIN ---
st.markdown("<div id='radar-bazin'></div>", unsafe_allow_html=True)

# KPI Count
count_opp = len(df_radar[df_radar['MARGEM_VAL'] > 10]) if not df_radar.empty else 0
html_header_bazin = f"""
<div class='section-header'>
    <span>🎯 Radar Preço Teto</span>
    <span class='kpi-badge'>{count_opp} Oportunidades (>10%)</span>
</div>
"""
st.markdown(html_header_bazin, unsafe_allow_html=True)

if not df_radar.empty:
    # CORES RÍGIDAS: Verde (>10), Vermelho (<0), Cinza (Resto)
    def style_margin(v):
        if v > 10: return 'color: #4ade80; font-weight: bold;' # Verde Forte
        if v < 0: return 'color: #f87171; font-weight: bold;' # Vermelho
        return 'color: #9ca3af;' # Cinza Neutro

    styled_radar = df_radar.style.format({
        "BAZIN_F": "R$ {:.2f}", "PRECO_F": "R$ {:.2f}", "MARGEM_VAL": "{:+.1f}%"
    }).map(style_margin, subset=['MARGEM_VAL'])

    st.dataframe(
        styled_radar,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"),
            "Ativo": st.column_config.TextColumn("Ativo"),
            "BAZIN_F": st.column_config.NumberColumn("Preço Teto"),
            "PRECO_F": st.column_config.NumberColumn("Cotação"),
            "MARGEM_VAL": st.column_config.TextColumn("Margem"),
        },
        hide_index=True,
        use_container_width=True
    )

# --- ANCHOR: DIVIDENDOS ---
st.markdown("<div id='dividendos'></div>", unsafe_allow_html=True)

# KPI Count
count_dy = len(df_div[df_div['DY_F'] > 8]) if not df_div.empty else 0
html_header_div = f"""
<div class='section-header'>
    <span>💰 Projeção Dividendos</span>
    <span class='kpi-badge'>{count_dy} Ativos Pagadores (>8%)</span>
</div>
"""
st.markdown(html_header_div, unsafe_allow_html=True)

if not df_div.empty:
    # CORES RÍGIDAS: Verde (>8), Cinza (Resto)
    def style_dy(v):
        if v > 8: return 'color: #4ade80; font-weight: bold;'
        return 'color: #9ca3af;'

    styled_div = df_div.style.format({
        "DPA_F": "R$ {:.2f}", "DY_F": "{:.2f}%"
    }).map(style_dy, subset=['DY_F'])

    st.dataframe(
        styled_div,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"),
            "Ativo": st.column_config.TextColumn("Ativo"),
            "DPA_F": st.column_config.NumberColumn("Div. / Ação"),
            "DY_F": st.column_config.TextColumn("Yield 2026"),
        },
        hide_index=True,
        use_container_width=True
    )
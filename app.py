import streamlit as st
import pandas as pd
import yfinance as yf
import os
import datetime
import pytz

# --- 1. CONFIGURAÇÃO (WIDE & DARK) ---
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS CORRIGIDO - CENTRALIZAÇÃO TOTAL ---
st.markdown("""
    <style>
        /* SCROLL SUAVE */
        html { scroll-behavior: smooth !important; }

        /* FUNDO */
        .stApp { background-color: #0c120f; color: #e0e0e0; }
        * { font-family: 'Segoe UI', 'Roboto', sans-serif; }
        
        /* OCULTAR ITENS PADRÃO */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stElementToolbar"] { display: none !important; }
        
        /* CORES PRIMÁRIAS */
        :root {
            --primary-color: #10b981;
        }

        /* Input de Texto (Busca) - Foco Verde */
        div[data-baseweb="base-input"] {
            border-color: #374151;
        }
        div[data-baseweb="base-input"]:focus-within {
            border-color: #10b981 !important;
            box-shadow: 0 0 0 1px #10b981 !important;
        }
        
        /* --- TABELAS: CENTRALIZAÇÃO COMPLETA --- */
        
        div[data-testid="stDataFrame"] {
            border: 1px solid #1f2937;
            border-radius: 10px;
            background-color: #0c120f;
        }
        
        /* Cabeçalho - Centralizado */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #141f1b !important;
            color: #6ee7b7 !important;
            font-size: 12px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            border-bottom: 1px solid #064e3b;
            text-align: center !important;
        }
        
        div[data-testid="stDataFrame"] div[role="columnheader"] > div {
            justify-content: center !important;
            text-align: center !important;
            width: 100%;
        }
        
        /* Células - Centralização Vertical e Horizontal TOTAL */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            background-color: #0c120f;
            text-align: center !important;
            vertical-align: middle !important;
            pointer-events: none !important; 
            user-select: none !important;
        }
        
        /* Força centralização em TODOS os elementos internos */
        div[data-testid="stDataFrame"] div[role="gridcell"] > div,
        div[data-testid="stDataFrame"] div[role="gridcell"] > div > div,
        div[data-testid="stDataFrame"] div[role="gridcell"] p,
        div[data-testid="stDataFrame"] div[role="gridcell"] span {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            width: 100% !important;
            margin: 0 auto !important;
        }
        
        /* Logos - Centralizadas */
        div[data-testid="stDataFrame"] div[role="gridcell"] img {
            border-radius: 50%;
            border: 1px solid #374151;
            padding: 2px;
            background-color: #fff;
            width: 30px !important;
            height: 30px !important;
            object-fit: contain;
            display: block !important;
            margin: 0 auto !important;
        }

        /* --- DESIGN GERAL --- */

        /* Header */
        .main-header {
            text-align: center;
            padding: 40px 0 10px 0;
            margin-bottom: 40px;
            border-bottom: 1px solid #1f2937;
            background: radial-gradient(circle at center, #132e25 0%, #0c120f 100%);
        }
        .main-title {
            font-size: 3rem;
            font-weight: 800;
            background: -webkit-linear-gradient(45deg, #10b981, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
            letter-spacing: -1px;
        }
        .main-greeting {
            font-size: 1rem;
            color: #9ca3af;
            font-weight: 400;
            margin-top: 5px;
        }

        /* Botões Navegação */
        .nav-card {
            background-color: #111a16;
            border: 1px solid #1f2937;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            text-decoration: none !important;
            display: block;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        .nav-card span, .nav-card div { text-decoration: none !important; }
        .nav-title { font-weight: 700; font-size: 1.1rem; display: block; color: #e5e7eb !important; }
        .nav-desc { font-size: 0.8rem; color: #6b7280 !important; display: block; margin-top: 5px; }
        .nav-card:hover {
            border-color: #10b981;
            transform: translateY(-3px);
            box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.1);
        }
        .nav-card:hover .nav-title { color: #10b981 !important; }

        /* Seções */
        .section-wrapper { margin-top: 60px; margin-bottom: 20px; }
        .section-header {
            font-size: 1.6rem;
            font-weight: 700;
            color: #f3f4f6;
            border-left: 6px solid #10b981;
            padding-left: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .section-desc {
            font-size: 0.9rem;
            color: #9ca3af;
            margin-top: 8px;
            margin-left: 21px;
            max-width: 800px;
            line-height: 1.4;
        }
        .status-badge {
            background-color: #064e3b;
            color: #34d399;
            font-size: 0.8rem;
            padding: 5px 12px;
            border-radius: 99px;
            border: 1px solid #059669;
            font-weight: 600;
            letter-spacing: 0.5px;
        }
        
        /* Footer */
        .footer-disclaimer {
            margin-top: 100px;
            padding: 40px;
            border-top: 1px solid #1f2937;
            text-align: center;
            color: #4b5563;
            font-size: 0.8rem;
            background-color: #0c120f;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES ---

def get_time_greeting():
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(tz)
    h = now.hour
    greeting = "Boa noite"
    if 5 <= h < 12: greeting = "Bom dia"
    elif 12 <= h < 18: greeting = "Boa tarde"
    time_str = now.strftime("%H:%M")
    return greeting, time_str

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
def get_market_data_distributed():
    groups = {
        'USA': { 'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'DOW JONES': '^DJI', 'VIX (Medo)': '^VIX' },
        'BRASIL': { 'IBOVESPA': '^BVSP', 'IFIX (FIIs)': 'IFIX.SA', 'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA' },
        'MOEDAS': { 'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X', 'LIBRA': 'GBPBRL=X', 'DXY Global': 'DX-Y.NYB' },
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
                    if len(tickers) > 1 and ticker in data.columns:
                        series = data[ticker].dropna()
                    elif isinstance(data, pd.Series):
                        series = data.dropna()
                    
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

# --- 4. APP PRINCIPAL ---

greeting_text, time_text = get_time_greeting()

# HEADER
st.markdown(f"""
    <div class='main-header'>
        <h1 class='main-title'>Dinheiro Data</h1>
        <p class='main-greeting'>{greeting_text}, Investidor. <span style='font-size: 0.8em; opacity: 0.6;'>| Dados: {time_text}</span></p>
    </div>
""", unsafe_allow_html=True)

# NAVEGAÇÃO
nav1, nav2, nav3 = st.columns(3)
with nav1:
    st.markdown("""
    <a href='#panorama' class='nav-card'>
        <span class='nav-title'>🌍 Panorama Global</span>
        <span class='nav-desc'>Visão Macro</span>
    </a>
    """, unsafe_allow_html=True)
with nav2:
    st.markdown("""
    <a href='#radar-bazin' class='nav-card'>
        <span class='nav-title'>🎯 Radar Bazin</span>
        <span class='nav-desc'>Análise de Preço Teto</span>
    </a>
    """, unsafe_allow_html=True)
with nav3:
    st.markdown("""
    <a href='#dividendos' class='nav-card'>
        <span class='nav-title'>💰 Dividendos</span>
        <span class='nav-desc'>Projeção de Renda</span>
    </a>
    """, unsafe_allow_html=True)

M = get_market_data_distributed()

# --- 1. PANORAMA ---
st.markdown("<div id='panorama'></div>", unsafe_allow_html=True)
st.markdown("""
<div class='section-wrapper'>
    <div class='section-header'>
        <span>🌍 Panorama Global</span>
    </div>
</div>
""", unsafe_allow_html=True)

def show_mini_table(col, title, df):
    col.write(f"**{title}**")
    if not df.empty:
        def format_price(val):
            if val == 0: return "-"
            return "{:.2f}".format(val)

        def color_var(val):
            if val > 0: return 'color: #34d399; font-weight: bold;'
            if val < 0: return 'color: #f87171; font-weight: bold;'
            return 'color: #6b7280;'
            
        styled_df = df.style.format({ 
            "Preço": format_price, 
            "Var%": "{:+.2f}%" 
        }).map(color_var, subset=['Var%'])
        
        col.dataframe(
            styled_df,
            column_config={
                "Ativo": st.column_config.TextColumn("Ativo"),
                "Preço": st.column_config.TextColumn("Cotação"),
                "Var%": st.column_config.TextColumn("Var %")
            },
            hide_index=True,
            use_container_width=True
        )

r1c1, r1c2, r1c3 = st.columns(3)
with r1c1: show_mini_table(r1c1, "🇺🇸 Índices EUA", M['USA'])
with r1c2: show_mini_table(r1c2, "🇧🇷 Índices Brasil", M['BRASIL'])
with r1c3: show_mini_table(r1c3, "💱 Moedas", M['MOEDAS'])

st.write("") 

r2c1, r2c2 = st.columns(2)
with r2c1: show_mini_table(r2c1, "🛢️ Commodities", M['COMMODITIES'])
with r2c2: show_mini_table(r2c2, "💎 Criptoativos", M['CRIPTO'])


# --- CARGA DADOS (AUTO) ---
df_radar, df_div = pd.DataFrame(), pd.DataFrame()
if os.path.exists("PEC.xlsx"): file_data = pd.ExcelFile("PEC.xlsx")
elif os.path.exists("PEC - Página1.csv"): file_data = pd.read_csv("PEC - Página1.csv")
else: file_data = None

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
                
                df_radar = target_df[target_df['BAZIN_F'] > 0][['Logo', 'Ativo', 'TICKER_F', 'BAZIN_F', 'PRECO_F', 'MARGEM_VAL']].sort_values('MARGEM_VAL', ascending=False)
                df_div = target_df[target_df['DY_F'] > 0][['Logo', 'Ativo', 'TICKER_F', 'DPA_F', 'DY_F']].sort_values('DY_F', ascending=False)
    except: pass

# --- 2. RADAR BAZIN ---
st.markdown("<div id='radar-bazin'></div>", unsafe_allow_html=True)
count_opp = len(df_radar[df_radar['MARGEM_VAL'] > 10]) if not df_radar.empty else 0

st.markdown(f"""
<div class='section-wrapper'>
    <div class='section-header'>
        <span>🎯 Radar Bazin</span>
        <span class='status-badge'>{count_opp} Ativos com desconto (>10%)</span>
    </div>
    <div class='section-desc'>
        O Preço Teto é calculado utilizando a metodologia de Décio Bazin (adaptado à nossa visão), visando identificar ativos que pagam bons dividendos a preços descontados.
    </div>
</div>
""", unsafe_allow_html=True)

if not df_radar.empty:
    search_bazin = st.text_input("🔍 Pesquisar Ativo (Bazin)", placeholder="Ex: BB Seguridade", key="sbazin")
    
    df_show = df_radar.copy()
    if search_bazin:
        df_show = df_show[
            df_show['Ativo'].str.contains(search_bazin, case=False) | 
            df_show['TICKER_F'].str.contains(search_bazin, case=False)
        ]

    def style_margin(v):
        if v > 10: return 'color: #34d399; font-weight: bold;'
        if v < 0: return 'color: #f87171; font-weight: bold;'
        return 'color: #9ca3af;'

    styled_radar = df_show.style.format({
        "BAZIN_F": "R$ {:.2f}", "PRECO_F": "R$ {:.2f}", "MARGEM_VAL": "{:+.1f}%"
    }).map(style_margin, subset=['MARGEM_VAL'])

    st.dataframe(
        styled_radar,
        column_config={
            "Logo": st.column_config.ImageColumn(""),
            "Ativo": st.column_config.TextColumn("Ativo"),
            "TICKER_F": None,
            "BAZIN_F": st.column_config.NumberColumn("Preço Teto"),
            "PRECO_F": st.column_config.NumberColumn("Cotação"),
            "MARGEM_VAL": st.column_config.TextColumn("Margem"),
        },
        hide_index=True,
        use_container_width=True
    )

# --- 3. DIVIDENDOS ---
st.markdown("<div id='dividendos'></div>", unsafe_allow_html=True)
count_dy = len(df_div[df_div['DY_F'] > 8]) if not df_div.empty else 0

st.markdown(f"""
<div class='section-wrapper'>
    <div class='section-header'>
        <span>💰 Dividendos</span>
        <span class='status-badge'>{count_dy} Ativos com Yield > 8%</span>
    </div>
    <div class='section-desc'>
        Estimativas de rendimento anual (Dividend Yield) para o exercício de 2026, baseadas em projeções de mercado e histórico de pagamentos das companhias.
    </div>
</div>
""", unsafe_allow_html=True)

if not df_div.empty:
    search_div = st.text_input("🔍 Pesquisar Ativo (Dividendos)", placeholder="Ex: BB Seguridade", key="sdiv")
    
    df_div_show = df_div.copy()
    if search_div:
        df_div_show = df_div_show[
            df_div_show['Ativo'].str.contains(search_div, case=False) | 
            df_div_show['TICKER_F'].str.contains(search_div, case=False)
        ]

    def style_dy(v):
        if v > 8: return 'color: #34d399; font-weight: bold;'
        return 'color: #9ca3af;'

    styled_div = df_div_show.style.format({
        "DPA_F": "R$ {:.2f}", "DY_F": "{:.2f}%"
    }).map(style_dy, subset=['DY_F'])

    st.dataframe(
        styled_div,
        column_config={
            "Logo": st.column_config.ImageColumn(""),
            "Ativo": st.column_config.TextColumn("Ativo"),
            "TICKER_F": None,
            "DPA_F": st.column_config.NumberColumn("Div. / Ação"),
            "DY_F": st.column_config.TextColumn("Yield Projetado"),
        },
        hide_index=True,
        use_container_width=True
    )

# --- FOOTER ---
st.markdown("""
    <div class='footer-disclaimer'>
        <strong>⚠️ ISENÇÃO DE RESPONSABILIDADE</strong><br><br>
        As informações, dados e indicadores apresentados nesta plataforma são obtidos de fontes públicas e cálculos automatizados. 
        Este dashboard tem caráter estritamente educativo e informativo.<br>
        <strong>Nenhum conteúdo aqui deve ser interpretado como recomendação de compra, venda ou manutenção de ativos mobiliários.</strong><br>
        Investimentos em renda variável estão sujeitos a riscos de mercado e perda de capital. 
        Realize sua própria análise ou consulte um profissional certificado antes de tomar decisões financeiras.
    </div>
""", unsafe_allow_html=True)
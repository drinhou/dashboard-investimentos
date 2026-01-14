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
    initial_sidebar_state="collapsed" # Menu recolhido para focar no conteúdo
)

# --- 2. CSS PREMIUM (UI/UX ESTILO BLOOMBERG) ---
st.markdown("""
    <style>
        /* Fundo e Fonte */
        .stApp { background-color: #0e1117; color: #e0e0e0; }
        * { font-family: 'Segoe UI', 'Roboto', sans-serif; }
        
        /* Remove padding excessivo do topo */
        .block-container { padding-top: 2rem; padding-bottom: 5rem; }

        /* HEADER DAS TABELAS (Centralizado) */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #111827;
            color: #9ca3af;
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #374151;
            text-align: center !important;
            justify-content: center !important;
        }

        /* CÉLULAS DAS TABELAS (Centralizadas) */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            display: flex;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            font-size: 14px;
            font-weight: 500;
        }

        /* LOGOS CIRCULARES */
        div[data-testid="stDataFrame"] div[role="gridcell"] img {
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid #4b5563;
            padding: 2px;
            background-color: white;
            width: 30px;
            height: 30px;
        }

        /* TÍTULOS DE SEÇÃO */
        .section-header {
            font-size: 1.4rem;
            font-weight: 700;
            color: #f3f4f6;
            margin-top: 30px;
            margin-bottom: 15px;
            border-left: 5px solid #3b82f6; /* Barra Azul */
            padding-left: 15px;
            background: linear-gradient(90deg, #1f2937 0%, transparent 100%);
            padding-top: 5px;
            padding-bottom: 5px;
            border-radius: 0 8px 8px 0;
        }
        
        /* SAUDAÇÃO */
        .greeting-card {
            text-align: center;
            padding: 20px;
            background: #1f2937;
            border-radius: 12px;
            border: 1px solid #374151;
            margin-bottom: 20px;
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
    """Busca Logo via Site Oficial (Coluna A)"""
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
    """
    5 PILARES DE MERCADO
    """
    groups = {
        'USA': {
            'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'DOW JONES': '^DJI', 'VIX (Medo)': '^VIX'
        },
        'BRASIL': {
            'IBOVESPA': '^BVSP', 'IFIX (FIIs)': 'IFIX.SA', 
            'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA', 'ITAU': 'ITUB4.SA', 'BB': 'BBAS3.SA'
        },
        'MOEDAS': {
            'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X', 'DXY (Global)': 'DX-Y.NYB', 'LIBRA': 'GBPBRL=X'
        },
        'COMMODITIES': {
            'OURO': 'GC=F', 'PRATA': 'SI=F', 'COBRE': 'HG=F', # Sequencia solicitada
            'BRENT OIL': 'BZ=F', 'GÁS NAT.': 'NG=F', 'SOJA': 'ZS=F'
        },
        'CRIPTO': {
            'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD', 'SOLANA': 'SOL-USD', 'BNB': 'BNB-USD'
        }
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
                    else:
                        rows.append([name, 0.0, 0.0])
                except: rows.append([name, 0.0, 0.0])
        except: pass
        
        # DataFrame (Sem Var R$, apenas %)
        df = pd.DataFrame(rows, columns=["Ativo", "Preço", "Var%"])
        final_dfs[cat] = df
        
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

# Saudação
st.markdown(f"""
    <div class='greeting-card'>
        <h1 style='margin:0; font-size: 2rem;'>🦅 {get_greeting()}, Investidor</h1>
        <p style='color: #9ca3af; margin-top: 5px;'>Sua central de inteligência financeira em tempo real.</p>
    </div>
""", unsafe_allow_html=True)

# Carregamento de Dados
M = get_market_data_distributed()

# --- SEÇÃO 1: PANORAMA (5 COLUNAS DISTRIBUÍDAS) ---
st.markdown("<div class='section-header'>🌍 Panorama de Mercado</div>", unsafe_allow_html=True)

# Estilo para as tabelas de mercado (Verde/Vermelho na porcentagem)
def show_mini_table(col, title, df):
    col.write(f"**{title}**")
    if not df.empty:
        def color_var(val):
            color = '#4ade80' if val > 0 else '#f87171' if val < 0 else '#6b7280'
            return f'color: {color}; font-weight: bold;'

        styled_df = df.style.format({
            "Preço": "{:.2f}",
            "Var%": "{:+.2f}%"
        }).map(color_var, subset=['Var%'])
        
        col.dataframe(
            styled_df,
            column_config={
                "Ativo": st.column_config.TextColumn("Ativo"), # Width auto
                "Preço": st.column_config.NumberColumn("Cotação"), # Width auto
                "Var%": st.column_config.TextColumn("Var %") # Width auto
            },
            hide_index=True,
            use_container_width=True
        )

# Layout: 3 Colunas em Cima, 2 Em Baixo (Para melhor leitura)
row1_1, row1_2, row1_3 = st.columns(3)
with row1_1: show_mini_table(row1_1, "🇺🇸 Índices EUA", M['USA'])
with row1_2: show_mini_table(row1_2, "🇧🇷 Índices Brasil", M['BRASIL'])
with row1_3: show_mini_table(row1_3, "💱 Moedas Fortes", M['MOEDAS'])

st.write("") # Espaçamento

row2_1, row2_2 = st.columns(2)
with row2_1: show_mini_table(row2_1, "🛢️ Commodities", M['COMMODITIES'])
with row2_2: show_mini_table(row2_2, "💎 Criptoativos", M['CRIPTO'])

# --- PROCESSAMENTO EXCEL ---
df_radar, df_div = pd.DataFrame(), pd.DataFrame()
uploaded = st.sidebar.file_uploader("📂 Atualizar Planilha", type=['xlsx', 'csv'])
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

# --- SEÇÃO 2: RADAR BAZIN ---
st.markdown("<div class='section-header'>🎯 Radar de Preço Justo (Bazin)</div>", unsafe_allow_html=True)

if not df_radar.empty:
    # Função de Estilo da Margem (Fundo Colorido Suave)
    def style_margin(v):
        if v > 10: return 'background-color: #064e3b; color: #4ade80; font-weight: bold;'
        if v > 0: return 'background-color: #422006; color: #facc15; font-weight: bold;'
        return 'background-color: #450a0a; color: #f87171; font-weight: bold;'

    styled_radar = df_radar.style.format({
        "BAZIN_F": "R$ {:.2f}", "PRECO_F": "R$ {:.2f}", "MARGEM_VAL": "{:+.1f}%"
    }).map(style_margin, subset=['MARGEM_VAL'])

    st.dataframe(
        styled_radar,
        column_config={
            "Logo": st.column_config.ImageColumn(""), # Logo sem nome
            "Ativo": st.column_config.TextColumn("Ativo"),
            "BAZIN_F": st.column_config.NumberColumn("Preço Teto"),
            "PRECO_F": st.column_config.NumberColumn("Cotação"),
            "MARGEM_VAL": st.column_config.TextColumn("Margem"),
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Carregando inteligência de dados...")

# --- SEÇÃO 3: DIVIDENDOS ---
st.markdown("<div class='section-header'>💰 Projeção de Renda Passiva</div>", unsafe_allow_html=True)

if not df_div.empty:
    def style_dy(v):
        return 'background-color: #064e3b; color: #4ade80; font-weight: bold;' if v > 6 else ''

    styled_div = df_div.style.format({
        "DPA_F": "R$ {:.2f}", "DY_F": "{:.2f}%"
    }).map(style_dy, subset=['DY_F'])

    st.dataframe(
        styled_div,
        column_config={
            "Logo": st.column_config.ImageColumn(""),
            "Ativo": st.column_config.TextColumn("Ativo"),
            "DPA_F": st.column_config.NumberColumn("Div. / Ação"),
            "DY_F": st.column_config.TextColumn("Yield Projetado"),
        },
        hide_index=True,
        use_container_width=True
    )
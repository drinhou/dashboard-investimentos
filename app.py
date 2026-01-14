import streamlit as st
import pandas as pd
import yfinance as yf
import os
import datetime

# --- 1. CONFIGURAÇÃO DA PÁGINA (WIDE & DARK) ---
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS AVANÇADO (UX PREMIUM) ---
st.markdown("""
    <style>
        /* Fundo Geral */
        .stApp { background-color: #0e1117; color: #e0e0e0; }
        
        /* Fontes */
        * { font-family: 'Segoe UI', 'Roboto', sans-serif; }
        
        /* HEADER DAS TABELAS (Centralizado) */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #1f2937;
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
            justify-content: center !important; /* Centraliza Horizontalmente */
            align-items: center !important;    /* Centraliza Verticalmente */
            text-align: center !important;
            font-size: 14px;
            font-weight: 500;
        }

        /* LOGOS CIRCULARES */
        div[data-testid="stDataFrame"] div[role="gridcell"] img {
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #374151; /* Borda sutil */
            padding: 2px;
            background-color: white;
        }

        /* KPI Cards (Métricas no topo) */
        div[data-testid="stMetric"] {
            background-color: #111827;
            border: 1px solid #374151;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        /* Títulos com destaque */
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f3f4f6;
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-left: 5px solid #3b82f6;
            padding-left: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES ---

def get_greeting():
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12: return "Bom dia"
    elif 12 <= hour < 18: return "Boa tarde"
    else: return "Boa noite"

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
    """Busca Favicon (Lista VIP + Google)"""
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip().upper()
    
    # LISTA VIP (Seus Sites + Ajustes)
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
    
    # Cripto
    if clean in ['BTC', 'BITCOIN']: return "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    if clean in ['ETH', 'ETHEREUM']: return "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
    if clean in ['SOL', 'SOLANA']: return "https://assets.coingecko.com/coins/images/4128/small/solana.png"

    # Fallback
    return f"https://cdn.jsdelivr.net/gh/thefintz/icon-project@master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_market_data_styled():
    """Busca dados de mercado"""
    lists = {
        'INDICES': {'IBOVESPA': '^BVSP', 'IFIX': 'IFIX.SA', 'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X'},
        'CRIPTO': {'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD', 'SOLANA': 'SOL-USD', 'OURO': 'GC=F', 'PETRÓLEO': 'BZ=F', 'PRATA': 'SI=F'},
        'TOP': {'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA', 'ITAU': 'ITUB4.SA', 'BB': 'BBAS3.SA', 'WEG': 'WEGE3.SA', 'AMBEV': 'ABEV3.SA'}
    }
    
    final_dfs = {}
    for cat, items in lists.items():
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
                        rows.append([name, curr, pct, delta])
                    else: rows.append([name, 0.0, 0.0, 0.0])
                except: rows.append([name, 0.0, 0.0, 0.0])
        except: pass
        while len(rows) < 6: rows.append(["-", 0.0, 0.0, 0.0])
        final_dfs[cat] = pd.DataFrame(rows, columns=["Ativo", "Preço", "Var%", "Var$"])
        
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

# Título Dinâmico
st.markdown(f"<h1 style='text-align: center; color: #fff; margin-bottom: 30px;'>🦅 {get_greeting()}, Investidor</h1>", unsafe_allow_html=True)

M = get_market_data_styled()

# --- SEÇÃO 1: PANORAMA ---
st.markdown("<div class='section-title'>🌍 Panorama Global</div>", unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)

def show_styled_table(col, df):
    if not df.empty:
        # Função para pintar o fundo da célula (Melhor visualização)
        def color_bg(val):
            if isinstance(val, (int, float)):
                if val > 0: return 'background-color: #064e3b; color: #4ade80;' # Verde escuro fundo, verde claro texto
                if val < 0: return 'background-color: #450a0a; color: #f87171;' # Vermelho escuro fundo, vermelho claro texto
            return ''
            
        styled_df = df.style.format({
            "Preço": "{:.2f}",
            "Var%": "{:+.2f}%",
            "Var$": "{:+.2f}"
        }).map(color_bg, subset=['Var%', 'Var$'])
        
        col.dataframe(
            styled_df,
            column_config={
                "Ativo": st.column_config.TextColumn("Ativo", width="small"),
                "Preço": st.column_config.NumberColumn("Cotação", width="small"),
                "Var%": st.column_config.TextColumn("Var %", width="small"),
                "Var$": st.column_config.TextColumn("Var R$", width="small")
            },
            hide_index=True,
            use_container_width=True
        )

with c1: st.write("📊 **Índices & Moedas**"); show_styled_table(c1, M['INDICES'])
with c2: st.write("💎 **Cripto & Commodities**"); show_styled_table(c2, M['CRIPTO'])
with c3: st.write("🏭 **Top Brasil**"); show_styled_table(c3, M['TOP'])

st.divider()

# --- 5. LÓGICA DO ARQUIVO ---
uploaded = st.sidebar.file_uploader("📂 Atualizar Dados", type=['xlsx', 'csv'])
file_data = None
if uploaded: 
    file_data = pd.read_csv(uploaded) if uploaded.name.endswith('.csv') else pd.ExcelFile(uploaded)
elif os.path.exists("PEC.xlsx"): file_data = pd.ExcelFile("PEC.xlsx")
elif os.path.exists("PEC - Página1.csv"): file_data = pd.read_csv("PEC - Página1.csv")

df_radar, df_div = pd.DataFrame(), pd.DataFrame()

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

# --- 6. VISUALIZAÇÃO COM STYLING ---

# KPI RÁPIDO
if not df_radar.empty:
    oportunidades = len(df_radar[df_radar['MARGEM_VAL'] > 10])
    st.markdown(f"<div class='section-title'>🎯 Radar de Oportunidades <span style='font-size: 0.8em; color: #4ade80; margin-left: 10px;'>({oportunidades} Ativos com Margem > 10%)</span></div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='section-title'>🎯 Radar de Oportunidades</div>", unsafe_allow_html=True)

if not df_radar.empty:
    # Cores Texto Margem
    def style_margin(v):
        color = '#4ade80' if v > 10 else '#facc15' if v > 0 else '#f87171'
        return f'color: {color}; font-weight: bold;'

    styled_radar = df_radar.style.format({
        "BAZIN_F": "R$ {:.2f}", "PRECO_F": "R$ {:.2f}", "MARGEM_VAL": "{:+.1f}%"
    }).map(style_margin, subset=['MARGEM_VAL'])

    st.dataframe(
        styled_radar,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"), 
            "Ativo": st.column_config.TextColumn("Ativo", width="large"), # Large para nome
            "BAZIN_F": st.column_config.NumberColumn("Preço Teto", width="small"), # Small para números
            "PRECO_F": st.column_config.NumberColumn("Cotação", width="small"),
            "MARGEM_VAL": st.column_config.TextColumn("Margem", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

st.markdown("<div class='section-title'>💰 Projeção de Renda Passiva</div>", unsafe_allow_html=True)

if not df_div.empty:
    def style_dy(v):
        return 'color: #4ade80; font-weight: bold;' if v > 8 else '' # Destaque DY > 8%

    styled_div = df_div.style.format({
        "DPA_F": "R$ {:.2f}", "DY_F": "{:.2f}%"
    }).map(style_dy, subset=['DY_F'])

    st.dataframe(
        styled_div,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"), # Simetria mantida
            "Ativo": st.column_config.TextColumn("Ativo", width="large"),
            "DPA_F": st.column_config.NumberColumn("Div. / Ação", width="small"),
            "DY_F": st.column_config.TextColumn("Yield Projetado", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )
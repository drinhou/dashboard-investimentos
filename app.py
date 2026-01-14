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

# --- 2. CSS PREMIUM (UI/UX) ---
st.markdown("""
    <style>
        /* Fundo e Fonte */
        .stApp { background-color: #0e1117; color: #e0e0e0; }
        * { font-family: 'Segoe UI', 'Roboto', sans-serif; }
        
        /* Título Pequeno e Elegante */
        .brand-header {
            font-size: 1.2rem;
            font-weight: 700;
            color: #60a5fa; /* Azul claro */
            margin-bottom: 0px;
            padding-bottom: 0px;
            border-bottom: 1px solid #1f2937;
        }

        /* ABAS (MENU SUPERIOR) */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            background-color: #0e1117;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #1f2937;
            border-radius: 8px;
            color: #9ca3af;
            font-weight: 600;
            padding: 0 20px; 
            border: 1px solid #374151;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #2563eb; /* Azul Selecionado */
            color: white;
            border-color: #3b82f6;
        }

        /* TABELAS CENTRAIS */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #111827;
            color: #9ca3af;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            text-align: center !important;
            justify-content: center !important;
            border-bottom: 2px solid #374151;
        }
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            display: flex;
            justify-content: center !important;
            align-items: center !important;
            text-align: center !important;
            font-size: 13px;
            font-weight: 500;
        }

        /* LOGOS CIRCULARES */
        div[data-testid="stDataFrame"] div[role="gridcell"] img {
            border-radius: 50%;
            object-fit: cover;
            border: 1px solid #4b5563;
            padding: 2px;
            background-color: white;
            width: 28px;
            height: 28px;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES ---

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
    
    # SUA LISTA DE SITES
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
    Separação: EUA | BRASIL | COMMODITIES | CRIPTO
    """
    groups = {
        'USA': {'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'DOW JONES': '^DJI', 'VIX': '^VIX', 'TESLA': 'TSLA', 'APPLE': 'AAPL'},
        'BRASIL': {'IBOVESPA': '^BVSP', 'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X', 'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA', 'ITAU': 'ITUB4.SA'},
        'COMMODITIES': {'OURO': 'GC=F', 'PRATA': 'SI=F', 'PETRÓLEO WTI': 'CL=F', 'PETRÓLEO BRENT': 'BZ=F', 'GÁS NAT.': 'NG=F', 'COBRE': 'HG=F'},
        'CRIPTO': {'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD', 'SOLANA': 'SOL-USD', 'BNB': 'BNB-USD', 'XRP': 'XRP-USD', 'DOGE': 'DOGE-USD'}
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
        
        # Garante 6 linhas para alinhamento
        while len(rows) < 6: rows.append(["-", 0.0, 0.0])
        
        # DataFrame SEM Var R$
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

# --- 4. APP ---

# Header Discreto
st.markdown("<div class='brand-header'>🦅 Dinheiro Data</div>", unsafe_allow_html=True)

# Menu Superior (ABAS)
tab_pano, tab_radar, tab_div = st.tabs(["🌍 Panorama de Mercado", "🎯 Radar Bazin", "💰 Dividendos"])

# --- ABA 1: PANORAMA ---
with tab_pano:
    M = get_market_data_distributed()
    
    # Função para Estilizar Tabela (Sem Var R$)
    def show_table(col, title, df):
        col.markdown(f"**{title}**")
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
                    "Ativo": st.column_config.TextColumn("Ativo", width="small"),
                    "Preço": st.column_config.NumberColumn("Cotação", width="small"),
                    "Var%": st.column_config.TextColumn("Var %", width="small")
                },
                hide_index=True,
                use_container_width=True
            )

    # 4 Colunas
    c1, c2, c3, c4 = st.columns(4)
    show_table(c1, "🇺🇸 Estados Unidos", M['USA'])
    show_table(c2, "🇧🇷 Brasil", M['BRASIL'])
    show_table(c3, "🛢️ Commodities", M['COMMODITIES'])
    show_table(c4, "💎 Criptoativos", M['CRIPTO'])


# --- CARREGAMENTO DE DADOS (COMUM AS ABAS 2 E 3) ---
df_radar, df_div = pd.DataFrame(), pd.DataFrame()
uploaded = st.sidebar.file_uploader("📂 Carregar PEC", type=['xlsx', 'csv'])
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

# --- ABA 2: RADAR BAZIN ---
with tab_radar:
    st.caption("Ações ordenadas pela margem de segurança em relação ao Preço Teto Bazin.")
    if not df_radar.empty:
        # Estilo Margem
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
                "Ativo": st.column_config.TextColumn("Ativo", width="medium"),
                "BAZIN_F": st.column_config.NumberColumn("Preço Teto", width="small"),
                "PRECO_F": st.column_config.NumberColumn("Cotação", width="small"),
                "MARGEM_VAL": st.column_config.TextColumn("Margem", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Carregando dados da planilha...")

# --- ABA 3: DIVIDENDOS ---
with tab_div:
    st.caption("Ranking de maiores pagadoras de dividendos projetadas.")
    if not df_div.empty:
        # Estilo DY
        def style_dy(v):
            return 'color: #4ade80; font-weight: bold;' if v > 6 else ''

        styled_div = df_div.style.format({
            "DPA_F": "R$ {:.2f}", "DY_F": "{:.2f}%"
        }).map(style_dy, subset=['DY_F'])

        st.dataframe(
            styled_div,
            column_config={
                "Logo": st.column_config.ImageColumn("", width="small"), # Largura igual ao Bazin
                "Ativo": st.column_config.TextColumn("Ativo", width="medium"),
                "DPA_F": st.column_config.NumberColumn("Div. / Ação", width="small"),
                "DY_F": st.column_config.TextColumn("Yield Projetado", width="small"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Carregando dados da planilha...")
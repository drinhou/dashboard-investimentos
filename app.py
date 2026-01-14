import streamlit as st
import pandas as pd
import yfinance as yf
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA (WIDE & DARK) ---
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS AVANÇADO (UX FINANCEIRO) ---
st.markdown("""
    <style>
        /* Fundo Geral */
        .stApp { background-color: #0e1117; color: #e0e0e0; }
        
        /* Fontes */
        * { font-family: 'Segoe UI', 'Roboto', sans-serif; }
        
        /* Remove padding excessivo do topo */
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }

        /* HEADER DAS TABELAS */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #1f2937;
            color: #9ca3af; /* Cinza claro */
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #374151;
        }

        /* LINHAS DAS TABELAS */
        div[data-testid="stDataFrame"] div[role="row"] {
            background-color: #111827; /* Fundo quase preto */
            color: #e5e7eb;
            font-size: 14px;
            border-bottom: 1px solid #1f2937;
        }
        
        /* Hover nas linhas */
        div[data-testid="stDataFrame"] div[role="row"]:hover {
            background-color: #1f2937;
        }

        /* Títulos de Seção */
        h3 {
            border-left: 4px solid #3b82f6; /* Barra azul ao lado do título */
            padding-left: 10px;
            margin-top: 20px;
            margin-bottom: 20px;
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES AUXILIARES ---

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
    """Busca Favicon baseada na lista VIP"""
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip().upper()
    
    # LISTA VIP (Seus Sites)
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
        return f"https://www.google.com/s2/favicons?domain={meus_sites[clean]}&sz=64"
    
    # Cripto
    if clean in ['BTC', 'BITCOIN']: return "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    if clean in ['ETH', 'ETHEREUM']: return "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
    if clean in ['SOL', 'SOLANA']: return "https://assets.coingecko.com/coins/images/4128/small/solana.png"

    # Genérico
    return f"https://cdn.jsdelivr.net/gh/thefintz/icon-project@master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_market_data_styled():
    """Busca dados e prepara DataFrame com cores"""
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
                    else:
                        rows.append([name, 0.0, 0.0, 0.0])
                except: rows.append([name, 0.0, 0.0, 0.0])
        except: pass
        
        while len(rows) < 6: rows.append(["-", 0.0, 0.0, 0.0])
        
        df = pd.DataFrame(rows, columns=["Ativo", "Preço", "Var%", "Var$"])
        final_dfs[cat] = df
        
    return final_dfs

# Função de Estilo (Cores Condicionais)
def color_surprises(val):
    if isinstance(val, (int, float)):
        color = '#4ade80' if val > 0 else '#f87171' if val < 0 else '#9ca3af'
        return f'color: {color}; font-weight: bold;'
    return ''

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

st.title("💸 Dinheiro Data")

M = get_market_data_styled()

# --- SEÇÃO 1: PANORAMA (COM STYLING PANDAS) ---
st.subheader("🌍 Panorama de Mercado")
c1, c2, c3 = st.columns(3)

def show_styled_table(col, title, df):
    col.write(f"**{title}**")
    if not df.empty:
        # Aplica cores nas colunas de variação
        styled_df = df.style.format({
            "Preço": "{:.2f}",
            "Var%": "{:+.2f}%",
            "Var$": "{:+.2f}"
        }).map(color_surprises, subset=['Var%', 'Var$'])
        
        col.dataframe(
            styled_df,
            column_config={
                "Ativo": st.column_config.TextColumn("Ativo", width="medium"),
                "Preço": st.column_config.NumberColumn("Cotação", width="small"),
                "Var%": st.column_config.TextColumn("Var %", width="small"), # TextColumn para aceitar cor
                "Var$": st.column_config.TextColumn("Var R$", width="small")
            },
            hide_index=True,
            use_container_width=True
        )

show_styled_table(c1, "📊 Índices & Moedas", M['INDICES'])
show_styled_table(c2, "💎 Cripto & Commodities", M['CRIPTO'])
show_styled_table(c3, "🏭 Top Brasil", M['TOP'])

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
                
                # Preços e Margem
                prices = get_br_prices(target_df['TICKER_F'].unique().tolist())
                target_df['PRECO_F'] = target_df['TICKER_F'].map(prices).fillna(0)
                
                target_df['MARGEM_VAL'] = target_df.apply(lambda x: ((x['BAZIN_F'] - x['PRECO_F']) / x['PRECO_F'] * 100) if x['PRECO_F'] > 0 else -999, axis=1)
                
                # Logo e Nome
                target_df['Logo'] = target_df['TICKER_F'].apply(get_logo_url)
                target_df['Ativo'] = target_df[c_emp] if c_emp else target_df['TICKER_F']
                
                # --- PREPARAÇÃO DO RADAR ---
                df_radar = target_df[target_df['BAZIN_F'] > 0].copy()
                df_radar = df_radar[['Logo', 'Ativo', 'BAZIN_F', 'PRECO_F', 'MARGEM_VAL']]
                df_radar = df_radar.sort_values('MARGEM_VAL', ascending=False)

                # --- PREPARAÇÃO DIVIDENDOS ---
                df_div = target_df[target_df['DY_F'] > 0].copy()
                df_div = df_div[['Logo', 'Ativo', 'DPA_F', 'DY_F']]
                df_div = df_div.sort_values('DY_F', ascending=False)
                
    except Exception as e: st.error(f"Erro: {e}")

# --- 6. VISUALIZAÇÃO COM PANDAS STYLING (VERDE/VERMELHO) ---

st.subheader("🎯 Radar de Preço Justo (Bazin)")

if not df_radar.empty:
    # Formatação Visual da Margem
    def style_margin(v):
        color = '#4ade80' if v > 10 else '#facc15' if v > 0 else '#f87171'
        weight = 'bold' if v > 10 else 'normal'
        return f'color: {color}; font-weight: {weight};'

    # Aplica estilo
    styled_radar = df_radar.style.format({
        "BAZIN_F": "R$ {:.2f}",
        "PRECO_F": "R$ {:.2f}",
        "MARGEM_VAL": "{:+.1f}%"
    }).map(style_margin, subset=['MARGEM_VAL'])

    st.dataframe(
        styled_radar,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"), # Sem título para "colar"
            "Ativo": st.column_config.TextColumn("Ativo", width="large"),
            "BAZIN_F": st.column_config.NumberColumn("Preço Teto", width="medium"),
            "PRECO_F": st.column_config.NumberColumn("Cotação", width="medium"),
            "MARGEM_VAL": st.column_config.TextColumn("Margem", width="medium"), # TextColumn aceita cor
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

st.subheader("💰 Projeção de Renda Passiva")

if not df_div.empty:
    # Estilo DY
    def style_dy(v):
        return 'color: #4ade80; font-weight: bold;' if v > 6 else ''

    styled_div = df_div.style.format({
        "DPA_F": "R$ {:.2f}",
        "DY_F": "{:.2f}%"
    }).map(style_dy, subset=['DY_F'])

    st.dataframe(
        styled_div,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"),
            "Ativo": st.column_config.TextColumn("Ativo", width="large"),
            "DPA_F": st.column_config.NumberColumn("Div. / Ação", width="medium"),
            "DY_F": st.column_config.TextColumn("Yield Projetado", width="medium"),
        },
        hide_index=True,
        use_container_width=True
    )
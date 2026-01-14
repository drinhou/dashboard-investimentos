import streamlit as st
import pandas as pd
import yfinance as yf
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS DARK MODE & DESIGN ---
st.markdown("""
    <style>
        /* Fundo Totalmente Escuro */
        .stApp {
            background-color: #0e1117;
            color: #e0e0e0;
        }
        h1, h2, h3, h4, p, div, span, label, li {
            font-family: 'Segoe UI', Helvetica, sans-serif;
            color: #e0e0e0 !important;
        }

        /* CARDS DE DESTAQUE (Topo) */
        div[data-testid="stMetric"] {
            background-color: #1e2129 !important;
            border: 1px solid #2d333b !important;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: 600; font-size: 0.9rem; }
        div[data-testid="stMetricValue"] div { color: #ffffff !important; font-weight: 700; font-size: 1.6rem; }

        /* TABELAS (Design Limpo) */
        div[data-testid="stDataFrame"] {
            background-color: #1e2129 !important;
            border: 1px solid #2d333b;
            border-radius: 8px;
        }
        
        /* Cabeçalhos */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #262730;
            color: #cbd5e1;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85rem;
            border-bottom: 1px solid #444;
        }
        
        /* Células */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            color: #e0e0e0;
            font-size: 0.95rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---

def clean_currency(x):
    """Limpa formatação financeira (R$, %, pontos)"""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        # Tira R$, tira pontos de milhar, troca virgula por ponto
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

def get_logo_url(ticker):
    """Busca logo baseada no Ticker"""
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip().upper()
    return f"https://raw.githubusercontent.com/thefintz/icon-project/master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_full_market_data():
    """Dados de mercado para as listas"""
    lists = {
        'INDICES': {
            'IBOVESPA': '^BVSP', 'IFIX (FIIs)': 'IFIX.SA', 
            'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'DOW JONES': '^DJI', 'VIX': '^VIX'
        },
        'COMMODITIES_CAMBIO': {
            'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X', 
            'OURO': 'GC=F', 'PETRÓLEO': 'BZ=F', 
            'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD'
        },
        'TOP_BRASIL': {
            'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA', 'ITAU': 'ITUB4.SA', 
            'WEG': 'WEGE3.SA', 'BANCO BRASIL': 'BBAS3.SA'
        }
    }
    
    results = {}
    for category, items in lists.items():
        rows = []
        try:
            tickers = list(items.values())
            data = yf.download(tickers, period="5d", progress=False)['Close']
            for name, ticker in items.items():
                price, delta, pct = 0, 0, 0
                try:
                    if len(tickers) == 1: series = data.dropna()
                    else: series = data[ticker].dropna() if ticker in data.columns else []

                    if len(series) >= 2:
                        curr = series.iloc[-1]
                        prev = series.iloc[-2]
                        delta = curr - prev
                        pct = (delta / prev) * 100
                        price = curr
                except: pass
                
                rows.append({"Nome": name, "Preço": price, "Var %": pct, "Var R$": delta})
        except: pass
        results[category] = pd.DataFrame(rows)
    return results

@st.cache_data(ttl=300)
def get_br_prices(ticker_list):
    """Busca cotação atual das ações da planilha"""
    if not ticker_list: return {}
    sa_tickers = [f"{t}.SA" for t in ticker_list]
    prices = {}
    try:
        data = yf.download(sa_tickers, period="1d", progress=False)['Close'].iloc[-1]
        if isinstance(data, float): prices[ticker_list[0]] = data
        else:
            for t in ticker_list:
                sa = f"{t}.SA"
                if sa in data: prices[t] = data[sa]
    except: pass
    return prices

# --- 4. APP PRINCIPAL ---

st.title("💸 Dinheiro Data")
st.markdown("---")

# Coletar dados de mercado
M = get_full_market_data()

# --- SEÇÃO 1: PANORAMA (3 COLUNAS) ---
st.subheader("🌍 Panorama de Mercado")
col1, col2, col3 = st.columns(3)

def show_market_list(col, title, df):
    col.markdown(f"**{title}**")
    if not df.empty:
        col.dataframe(
            df,
            column_config={
                "Nome": st.column_config.TextColumn("Ativo"),
                "Preço": st.column_config.NumberColumn("Cotação", format="%.2f"),
                "Var %": st.column_config.NumberColumn("Var %", format="%.2f %%"),
                "Var R$": st.column_config.NumberColumn("Var $", format="%.2f"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        col.info("Carregando...")

show_market_list(col1, "📊 Índices Globais", M.get('INDICES', pd.DataFrame()))
show_market_list(col2, "🛢️ Câmbio & Cripto", M.get('COMMODITIES_CAMBIO', pd.DataFrame()))
show_market_list(col3, "🏭 Top Brasil", M.get('TOP_BRASIL', pd.DataFrame()))

st.divider()

# --- 5. PROCESSAMENTO DE DADOS (CSV ou EXCEL) ---

def load_user_file():
    # 1. Upload Manual (Prioridade)
    uploaded = st.sidebar.file_uploader("📂 Atualizar Dados (.xlsx ou .csv)", type=['xlsx', 'csv'])
    if uploaded:
        if uploaded.name.endswith('.csv'):
            return pd.read_csv(uploaded)
        return pd.ExcelFile(uploaded)
    
    # 2. Arquivos no GitHub (Persistência)
    if os.path.exists("PEC.xlsx"): return pd.ExcelFile("PEC.xlsx")
    if os.path.exists("PEC - Página1.csv"): return pd.read_csv("PEC - Página1.csv") 
    
    return None

file_data = load_user_file()
df_radar = pd.DataFrame()
df_div = pd.DataFrame()

if file_data is not None:
    try:
        # Lógica para tratar Excel ou CSV
        if isinstance(file_data, pd.ExcelFile):
            target_df = pd.DataFrame()
            for sheet in file_data.sheet_names:
                temp = pd.read_excel(file_data, sheet)
                cols_upper = [str(c).upper() for c in temp.columns]
                if any("BAZIN" in c for c in cols_upper):
                    target_df = temp
                    break
        else:
            target_df = file_data # Já é o CSV

        if not target_df.empty:
            target_df.columns = [str(c).strip().upper() for c in target_df.columns]
            cols = target_df.columns
            
            # Mapeamento Inteligente
            col_ticker = next((c for c in cols if 'TICKER' in c), None)
            col_empresa = next((c for c in cols if 'EMPRESA' in c), None)
            col_bazin = next((c for c in cols if 'BAZIN' in c), None)
            col_dy = next((c for c in cols if 'DY' in c), None)
            col_dpa = next((c for c in cols if 'DPA' in c), None)

            if col_ticker and col_bazin:
                # Tratamento
                target_df['TICKER_F'] = target_df[col_ticker].astype(str).str.strip().str.upper()
                target_df['BAZIN_F'] = target_df[col_bazin].apply(clean_currency)
                
                if col_dy: target_df['DY_F'] = target_df[col_dy].apply(clean_currency)
                else: target_df['DY_F'] = 0.0
                
                if col_dpa: target_df['DPA_F'] = target_df[col_dpa].apply(clean_currency)
                else: target_df['DPA_F'] = 0.0
                
                # Preços Online
                tickers = target_df['TICKER_F'].unique().tolist()
                live_prices = get_br_prices(tickers)
                target_df['PRECO_F'] = target_df['TICKER_F'].map(live_prices).fillna(0)
                
                # Margem
                target_df['MARGEM_F'] = target_df.apply(
                    lambda x: ((x['BAZIN_F'] - x['PRECO_F']) / x['PRECO_F'] * 100) if x['PRECO_F'] > 0 else -999, 
                    axis=1
                )
                
                # Visual
                target_df['LOGO_F'] = target_df['TICKER_F'].apply(get_logo_url)
                if col_empresa:
                    target_df['NOME_F'] = target_df[col_empresa]
                else:
                    target_df['NOME_F'] = target_df['TICKER_F']

                # Tabelas Finais
                df_radar = target_df[target_df['BAZIN_F'] > 0].copy()
                df_radar = df_radar[['LOGO_F', 'NOME_F', 'BAZIN_F', 'PRECO_F', 'MARGEM_F']]
                df_radar = df_radar.sort_values('MARGEM_F', ascending=False)
                
                df_div = target_df[target_df['DY_F'] > 0].copy()
                df_div = df_div[['LOGO_F', 'NOME_F', 'DPA_F', 'DY_F']]
                df_div = df_div.sort_values('DY_F', ascending=False)
            
            else:
                st.error("Erro: Colunas TICKER ou BAZIN não encontradas.")
                
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")

# --- 6. VISUALIZAÇÃO DO RADAR ---
st.subheader("🎯 Radar de Preço Justo (Bazin)")

if not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "LOGO_F": st.column_config.ImageColumn("Logo", width="small"),
            "NOME_F": st.column_config.TextColumn("Ativo", width="medium"),
            "BAZIN_F": st.column_config.NumberColumn("Preço Justo (Teto)", format="R$ %.2f"),
            "PRECO_F": st.column_config.NumberColumn("Cotação Atual", format="R$ %.2f"),
            "MARGEM_F": st.column_config.ProgressColumn(
                "Margem de Segurança",
                format="%.1f%%",
                min_value=-50, max_value=50,
                width="medium"
            )
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Aguardando arquivo... Carregue 'PEC.xlsx' ou 'PEC - Página1.csv'.")

st.divider()

# --- 7. VISUALIZAÇÃO DE DIVIDENDOS ---
st.subheader("💰 Projeção de Renda Passiva")

if not df_div.empty:
    st.dataframe(
        df_div,
        column_config={
            "LOGO_F": st.column_config.ImageColumn("Logo", width="small"),
            "NOME_F": st.column_config.TextColumn("Ativo", width="medium"),
            "DPA_F": st.column_config.NumberColumn("Dividendo por Ação", format="R$ %.2f"),
            "DY_F": st.column_config.NumberColumn("Dividend Yield", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True
    )
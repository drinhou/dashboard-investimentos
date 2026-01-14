\import streamlit as st
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
        /* Fundo Escuro Global */
        .stApp {
            background-color: #0e1117;
            color: #e0e0e0;
        }
        h1, h2, h3, h4, p, div, span, label, li {
            font-family: 'Segoe UI', Helvetica, sans-serif;
            color: #e0e0e0 !important;
        }

        /* CARDS DE DESTAQUE */
        div[data-testid="stMetric"] {
            background-color: #1e2129 !important;
            border: 1px solid #2d333b !important;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: 600; font-size: 0.9rem; }
        div[data-testid="stMetricValue"] div { color: #ffffff !important; font-weight: 700; font-size: 1.6rem; }

        /* TABELAS */
        div[data-testid="stDataFrame"] {
            background-color: #1e2129 !important;
            border: 1px solid #2d333b;
            border-radius: 8px;
        }
        
        /* Cabeçalhos Centralizados */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #262730;
            color: #cbd5e1;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 0.85rem;
            border-bottom: 1px solid #444;
            text-align: center; 
        }
        
        /* Células Centralizadas */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            color: #e0e0e0;
            font-size: 0.95rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES DE TRATAMENTO ---

def clean_currency(x):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

def clean_dy_percentage(x):
    val = clean_currency(x)
    if val > 0 and val < 1.0:
        return val * 100
    return val

def get_logo_url(ticker):
    """
    ESTRATÉGIA INFALÍVEL:
    Usa o serviço de Favicon do Google baseado no site oficial da empresa.
    """
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip().upper()
    
    # 1. Mapeamento Manual para Garantir (Principais da sua planilha)
    # Ticker -> Domínio Oficial
    domain_map = {
        'BBAS3': 'bb.com.br',
        'BBSE3': 'bbseguridaderi.com.br',
        'ITUB4': 'itau.com.br',
        'BBDC4': 'bradesco.com.br',
        'SANB11': 'santander.com.br',
        'PETR4': 'petrobras.com.br',
        'VALE3': 'vale.com',
        'WEGE3': 'weg.net',
        'CMIG4': 'cemig.com.br',
        'SAPR4': 'sanepar.com.br',
        'SAPR11': 'sanepar.com.br',
        'ISAE4': 'isacteep.com.br', # Nova TRPL4
        'TRPL4': 'isacteep.com.br',
        'CXSE3': 'caixaseguridade.com.br',
        'ODPV3': 'odontoprev.com.br',
        'TAEE11': 'taesa.com.br',
        'KLBN11': 'klabin.com.br',
        'SUZB3': 'suzano.com.br',
        'JBSS3': 'jbs.com.br',
        'ABEV3': 'ambev.com.br',
        'EGIE3': 'engie.com.br',
        'VIVT3': 'vivo.com.br',
        'TIMS3': 'tim.com.br',
        'B3SA3': 'b3.com.br',
        'XP': 'xp.com.br',
        'NU': 'nubank.com.br',
        'MXRF11': 'xp.com.br', # Gestora
        'HGLG11': 'cshg.com.br',
        'KNCA11': 'kinea.com.br',
        'KNIP11': 'kinea.com.br',
        'XPLG11': 'xp.com.br',
        'VISC11': 'vinci-partners.com'
    }

    # Cripto (CoinGecko é robusto)
    if clean in ['BTC', 'BITCOIN']: return "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    if clean in ['ETH', 'ETHEREUM']: return "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
    if clean in ['SOL', 'SOLANA']: return "https://assets.coingecko.com/coins/images/4128/small/solana.png"

    # Se estiver no mapa, usa o Google Favicon (Alta qualidade e confiabilidade)
    if clean in domain_map:
        return f"https://www.google.com/s2/favicons?domain={domain_map[clean]}&sz=128"

    # Fallback: Tenta repositório genérico se não estiver na lista VIP
    return f"https://cdn.jsdelivr.net/gh/thefintz/icon-project@master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_full_market_data():
    """Retorna 3 listas com EXATAMENTE 6 itens cada."""
    lists = {
        'INDICES_MOEDAS': {
            'IBOVESPA': '^BVSP', 'IFIX (FIIs)': 'IFIX.SA',
            'S&P 500': '^GSPC', 'NASDAQ': '^IXIC',
            'DÓLAR': 'BRL=X', 'EURO': 'EURBRL=X'
        },
        'CRIPTO_COMMODITIES': {
            'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD',
            'SOLANA': 'SOL-USD', 'OURO': 'GC=F',
            'PETRÓLEO': 'BZ=F', 'PRATA': 'SI=F'
        },
        'TOP_BRASIL': {
            'VALE': 'VALE3.SA', 'PETROBRAS': 'PETR4.SA',
            'ITAU': 'ITUB4.SA', 'BANCO BRASIL': 'BBAS3.SA',
            'WEG': 'WEGE3.SA', 'AMBEV': 'ABEV3.SA'
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
        
        while len(rows) < 6:
            rows.append({"Nome": "-", "Preço": 0, "Var %": 0, "Var R$": 0})
            
        results[category] = pd.DataFrame(rows)
    return results

@st.cache_data(ttl=300)
def get_br_prices(ticker_list):
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

M = get_full_market_data()

# --- SEÇÃO 1: PANORAMA ---
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
                "Var R$": st.column_config.NumberColumn("Var R$", format="%.2f"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        col.info("Carregando...")

show_market_list(col1, "📊 Índices & Moedas", M.get('INDICES_MOEDAS', pd.DataFrame()))
show_market_list(col2, "💎 Cripto & Commodities", M.get('CRIPTO_COMMODITIES', pd.DataFrame()))
show_market_list(col3, "🏭 Top Brasil", M.get('TOP_BRASIL', pd.DataFrame()))

st.divider()

# --- 5. LEITURA DE ARQUIVO ---
def load_user_file():
    uploaded = st.sidebar.file_uploader("📂 Atualizar Dados (.xlsx ou .csv)", type=['xlsx', 'csv'])
    if uploaded:
        if uploaded.name.endswith('.csv'): return pd.read_csv(uploaded)
        return pd.ExcelFile(uploaded)
    if os.path.exists("PEC.xlsx"): return pd.ExcelFile("PEC.xlsx")
    if os.path.exists("PEC - Página1.csv"): return pd.read_csv("PEC - Página1.csv")
    return None

file_data = load_user_file()
df_radar = pd.DataFrame()
df_div = pd.DataFrame()

if file_data is not None:
    try:
        if isinstance(file_data, pd.ExcelFile):
            target_df = pd.DataFrame()
            for sheet in file_data.sheet_names:
                temp = pd.read_excel(file_data, sheet)
                cols_upper = [str(c).upper() for c in temp.columns]
                if any("BAZIN" in c for c in cols_upper):
                    target_df = temp
                    break
        else:
            target_df = file_data

        if not target_df.empty:
            target_df.columns = [str(c).strip().upper() for c in target_df.columns]
            cols = target_df.columns
            
            col_ticker = next((c for c in cols if 'TICKER' in c), None)
            col_empresa = next((c for c in cols if 'EMPRESA' in c), None)
            col_bazin = next((c for c in cols if 'BAZIN' in c), None)
            col_dy = next((c for c in cols if 'DY' in c), None)
            col_dpa = next((c for c in cols if 'DPA' in c), None)

            if col_ticker and col_bazin:
                target_df['TICKER_F'] = target_df[col_ticker].astype(str).str.strip().str.upper()
                target_df['BAZIN_F'] = target_df[col_bazin].apply(clean_currency)
                
                if col_dy: target_df['DY_F'] = target_df[col_dy].apply(clean_dy_percentage)
                else: target_df['DY_F'] = 0.0
                
                if col_dpa: target_df['DPA_F'] = target_df[col_dpa].apply(clean_currency)
                else: target_df['DPA_F'] = 0.0
                
                tickers = target_df['TICKER_F'].unique().tolist()
                live_prices = get_br_prices(tickers)
                target_df['PRECO_F'] = target_df['TICKER_F'].map(live_prices).fillna(0)
                
                target_df['MARGEM_F'] = target_df.apply(
                    lambda x: ((x['BAZIN_F'] - x['PRECO_F']) / x['PRECO_F'] * 100) if x['PRECO_F'] > 0 else -999, 
                    axis=1
                )
                
                target_df['LOGO_F'] = target_df['TICKER_F'].apply(get_logo_url)
                target_df['NOME_F'] = target_df[col_empresa] if col_empresa else target_df['TICKER_F']

                df_radar = target_df[target_df['BAZIN_F'] > 0].copy()
                df_radar = df_radar[['LOGO_F', 'NOME_F', 'BAZIN_F', 'PRECO_F', 'MARGEM_F']]
                df_radar = df_radar.sort_values('MARGEM_F', ascending=False)
                
                df_div = target_df[target_df['DY_F'] > 0].copy()
                df_div = df_div[['LOGO_F', 'NOME_F', 'DPA_F', 'DY_F']]
                df_div = df_div.sort_values('DY_F', ascending=False)
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")

# --- 6. RADAR BAZIN ---
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
    st.info("Aguardando carregamento de dados...")

st.divider()

# --- 7. DIVIDENDOS ---
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
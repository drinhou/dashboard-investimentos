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

# --- 2. CSS DARK MODE & ALINHAMENTO ---
st.markdown("""
    <style>
        /* Fundo Totalmente Escuro e Fonte */
        .stApp {
            background-color: #0e1117;
            color: #e0e0e0;
        }
        h1, h2, h3, h4, p, div, span, label {
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
        div[data-testid="stMetricLabel"] p { color: #9ca3af !important; font-weight: 600; }
        div[data-testid="stMetricValue"] div { color: #ffffff !important; font-weight: 700; }

        /* TABELAS (Design Limpo e Centralizado) */
        div[data-testid="stDataFrame"] {
            background-color: #1e2129 !important;
            border: 1px solid #2d333b;
            border-radius: 8px;
        }
        
        /* Centralizar Cabeçalhos */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #262730;
            color: white;
            justify-content: center;
            font-weight: bold;
            border-bottom: 1px solid #444;
        }
        
        /* Centralizar Células */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            justify-content: center;
            color: #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES DE DADOS ---

def clean_currency(x):
    """Limpa formatação financeira"""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

def get_logo_url(ticker):
    """
    Busca logo. Tenta repositório brasileiro confiável.
    Se não achar, retorna URL vazia (o Streamlit lida bem com isso).
    """
    if not isinstance(ticker, str): return ""
    # Limpa o ticker (remove .SA e espaços)
    clean = ticker.replace('.SA', '').strip().upper()
    
    # Repositório de ícones financeiros
    return f"https://raw.githubusercontent.com/thefintz/icon-project/master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_full_market_data():
    """
    Busca dados para as listas extensas de mercado.
    Retorna DataFrames prontos para exibição.
    """
    # Dicionário de Listas
    lists = {
        'INDICES': {
            'IBOVESPA': '^BVSP',
            'IFIX (FIIs)': 'IFIX.SA', # Tentativa via Yahoo
            'S&P 500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DOW JONES': '^DJI',
            'VIX (Medo)': '^VIX'
        },
        'COMMODITIES_CAMBIO': {
            'DÓLAR': 'BRL=X',
            'EURO': 'EURBRL=X',
            'OURO': 'GC=F',
            'PETRÓLEO BRENT': 'BZ=F',
            'BITCOIN': 'BTC-USD',
            'ETHEREUM': 'ETH-USD'
        },
        'TOP_BRASIL': {
            'VALE': 'VALE3.SA',
            'PETROBRAS': 'PETR4.SA',
            'ITAU': 'ITUB4.SA',
            'WEG': 'WEGE3.SA',
            'AMBEV': 'ABEV3.SA',
            'BANCO BRASIL': 'BBAS3.SA'
        }
    }
    
    results = {}
    
    for category, items in lists.items():
        rows = []
        try:
            # Baixa em lote para ser rápido
            tickers = list(items.values())
            data = yf.download(tickers, period="5d", progress=False)['Close']
            
            for name, ticker in items.items():
                price, delta, pct = 0, 0, 0
                try:
                    # Verifica se veio como Series (1 ativo) ou DataFrame (vários)
                    if len(tickers) == 1:
                        series = data.dropna()
                    else:
                        if ticker in data.columns:
                            series = data[ticker].dropna()
                        else:
                            series = []

                    if len(series) >= 2:
                        curr = series.iloc[-1]
                        prev = series.iloc[-2]
                        delta = curr - prev
                        pct = (delta / prev) * 100
                        price = curr
                except:
                    pass
                
                # Formatação visual da variação
                arrow = "▲" if delta >= 0 else "▼"
                rows.append({
                    "Nome": name,
                    "Preço": price,
                    "Var %": pct, # Mantém numérico para config
                    "Var R$": delta
                })
        except:
            pass
        
        results[category] = pd.DataFrame(rows)

    return results

@st.cache_data(ttl=300)
def get_br_prices(ticker_list):
    """Preços atuais para a planilha"""
    if not ticker_list: return {}
    sa_tickers = [f"{t}.SA" for t in ticker_list]
    prices = {}
    try:
        data = yf.download(sa_tickers, period="1d", progress=False)['Close'].iloc[-1]
        if isinstance(data, float):
             prices[ticker_list[0]] = data
        else:
            for t in ticker_list:
                sa = f"{t}.SA"
                if sa in data:
                    prices[t] = data[sa]
    except:
        pass
    return prices

# --- 4. APP PRINCIPAL ---

st.title("💸 Dinheiro Data")
st.markdown("---")

# Coletar dados
M = get_full_market_data()

# --- SEÇÃO 1: PANORAMA DE MERCADO (LISTAS EXTENSAS) ---
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
show_market_list(col2, "🛢️ Câmbio & Commodities", M.get('COMMODITIES_CAMBIO', pd.DataFrame()))
show_market_list(col3, "🏭 Top Brasil", M.get('TOP_BRASIL', pd.DataFrame()))

st.divider()

# --- 5. PROCESSAMENTO PLANILHA (PERSISTENTE) ---
def load_data():
    uploaded = st.sidebar.file_uploader("📂 Atualizar PEC.xlsx", type=['xlsx'])
    if uploaded: return pd.ExcelFile(uploaded)
    if os.path.exists("PEC.xlsx"): return pd.ExcelFile("PEC.xlsx")
    return None

xls = load_data()
df_radar = pd.DataFrame()
df_div = pd.DataFrame()

if xls:
    target_sheet = None
    for sheet in xls.sheet_names:
        df_chk = pd.read_excel(xls, sheet).head(2)
        cols_up = [str(c).upper() for c in df_chk.columns]
        if any("BAZIN" in c for c in cols_up):
            target_sheet = sheet
            break
            
    if target_sheet:
        try:
            df_main = pd.read_excel(xls, target_sheet).fillna(0)
            cols = df_main.columns
            
            # Mapeamento
            c_tick = [c for c in cols if 'TICKER' in c.upper()][0]
            c_emp = [c for c in cols if 'EMPRESA' in c.upper()][0]
            c_bazin = [c for c in cols if 'BAZIN' in c.upper()][0]
            c_dy = [c for c in cols if 'DY' in c.upper()][0]
            
            c_dpa_l = [c for c in cols if 'DPA' in c.upper()]
            c_dpa = c_dpa_l[0] if c_dpa_l else None

            # Tratamento
            df_main['TICKER_CLEAN'] = df_main[c_tick].astype(str).str.strip().str.upper()
            df_main['BAZIN_NUM'] = df_main[c_bazin].apply(clean_currency)
            df_main['DY_NUM'] = df_main[c_dy].apply(clean_currency)
            if c_dpa: df_main['DPA_NUM'] = df_main[c_dpa].apply(clean_currency)
            else: df_main['DPA_NUM'] = 0.0
            
            # Cotação Online e Radar
            tickers = df_main['TICKER_CLEAN'].unique().tolist()
            live_prices = get_br_prices(tickers)
            df_main['PRECO_LIVE'] = df_main['TICKER_CLEAN'].map(live_prices).fillna(0)
            
            df_main['MARGEM'] = df_main.apply(
                lambda x: ((x['BAZIN_NUM'] - x['PRECO_LIVE']) / x['PRECO_LIVE'] * 100) if x['PRECO_LIVE'] > 0 else -999, 
                axis=1
            )
            
            # Logo e Nome
            df_main['LOGO'] = df_main['TICKER_CLEAN'].apply(get_logo_url)
            df_main['ATIVO_DISPLAY'] = df_main[c_emp] # Apenas nome, ticker já está na logo ou separado se quiser
            
            # Dataframes Finais
            # Tabela 1: Valuation
            df_radar = df_main[df_main['BAZIN_NUM'] > 0][['LOGO', 'ATIVO_DISPLAY', 'BAZIN_NUM', 'PRECO_LIVE', 'MARGEM']].copy()
            df_radar = df_radar.sort_values('MARGEM', ascending=False)
            
            # Tabela 2: Dividendos
            df_div = df_main[df_main['DY_NUM'] > 0][['LOGO', 'ATIVO_DISPLAY', 'DPA_NUM', 'DY_NUM']].copy()
            df_div = df_div.sort_values('DY_NUM', ascending=False)
            
        except Exception as e:
            st.error(f"Erro na planilha: {e}")

# --- 6. TABELA: VALUATION ---
st.subheader("🎯 Radar de Preço-Teto (Bazin)")

if not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "LOGO": st.column_config.ImageColumn("Logo", width="small", alignment="center"),
            "ATIVO_DISPLAY": st.column_config.TextColumn("Ativo", width="medium", alignment="center"),
            "BAZIN_NUM": st.column_config.NumberColumn("Teto Bazin", format="R$ %.2f", alignment="center"),
            "PRECO_LIVE": st.column_config.NumberColumn("Cotação Atual", format="R$ %.2f", alignment="center"),
            "MARGEM": st.column_config.ProgressColumn(
                "Margem de Segurança",
                format="%.1f%%",
                min_value=-50, max_value=50,
                width="medium",
                alignment="center"
            )
        },
        hide_index=True,
        use_container_width=True
    )
elif not xls:
    st.info("⚠️ Arquivo 'PEC.xlsx' não encontrado. Faça o upload no GitHub.")

st.divider()

# --- 7. TABELA: DIVIDENDOS ---
st.subheader("💰 Dividendos Projetados")

if not df_div.empty:
    st.dataframe(
        df_div,
        column_config={
            "LOGO": st.column_config.ImageColumn("Logo", width="small", alignment="center"),
            "ATIVO_DISPLAY": st.column_config.TextColumn("Ativo", width="medium", alignment="center"),
            "DPA_NUM": st.column_config.NumberColumn("Dividendo por Ação", format="R$ %.2f", alignment="center"),
            "DY_NUM": st.column_config.NumberColumn("Dividend Yield", format="%.2f %%", alignment="center"),
        },
        hide_index=True,
        use_container_width=True
    )
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

# --- 2. CSS DARK MODE PROFISSIONAL ---
st.markdown("""
    <style>
        /* Fundo Totalmente Escuro */
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        
        /* Fontes e Textos */
        h1, h2, h3, p, div, span, label {
            font-family: 'Segoe UI', sans-serif;
            color: #e0e0e0 !important;
        }

        /* CARD DE ÍNDICE (SIMÉTRICO E ELEGANTE) */
        .index-card {
            background-color: #1e2129;
            border-radius: 8px;
            padding: 20px 10px; /* Mais espaçamento interno */
            margin-bottom: 15px;
            border: 1px solid #2d333b;
            text-align: center;
            height: 100%; /* Força altura igual */
            transition: transform 0.2s;
        }
        .index-card:hover {
            border-color: #4b5563;
        }
        .index-name {
            font-size: 0.85rem;
            color: #9ca3af !important;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }
        .index-price {
            font-size: 1.5rem;
            color: #ffffff !important;
            font-weight: 700;
        }
        .index-delta-pos { color: #4ade80 !important; font-size: 0.9rem; font-weight: 600; }
        .index-delta-neg { color: #f87171 !important; font-size: 0.9rem; font-weight: 600; }

        /* TABELAS DARK */
        div[data-testid="stDataFrame"] {
            background-color: #1e2129;
            border: 1px solid #2d333b;
            border-radius: 8px;
            text-align: center; /* Força alinhamento geral */
        }
        
        /* Cabeçalho da Tabela */
        div[data-testid="stDataFrame"] div[role="columnheader"] {
            background-color: #262730;
            color: white;
            font-weight: bold;
            justify-content: center; /* Centraliza Headers */
        }
        
        /* Células da Tabela */
        div[data-testid="stDataFrame"] div[role="gridcell"] {
            justify-content: center; /* Centraliza Conteúdo */
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #161920;
            border-right: 1px solid #2d333b;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. FUNÇÕES ---

def clean_currency(x):
    """Limpa formatação financeira R$ / %"""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

def get_logo_url(ticker):
    """Busca logo real no repositório"""
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip().upper()
    return f"https://raw.githubusercontent.com/thefintz/icon-project/master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_detailed_market_data():
    """Busca Cotação e Variação"""
    tickers_map = {
        'IBOV': '^BVSP', 'DÓLAR': 'BRL=X',
        'S&P 500': '^GSPC', 'NASDAQ': '^IXIC', 'VIX': '^VIX',
        'BITCOIN': 'BTC-USD', 'ETHEREUM': 'ETH-USD', 'SOLANA': 'SOL-USD'
    }
    results = {}
    try:
        data = yf.download(list(tickers_map.values()), period="5d", progress=False)['Close']
        for name, symbol in tickers_map.items():
            try:
                if symbol in data.columns:
                    series = data[symbol].dropna()
                    current = series.iloc[-1]
                    prev = series.iloc[-2]
                    delta = current - prev
                    pct = (delta / prev) * 100
                    results[name] = {'price': current, 'delta': delta, 'pct': pct}
                else:
                    results[name] = {'price': 0, 'delta': 0, 'pct': 0}
            except:
                results[name] = {'price': 0, 'delta': 0, 'pct': 0}
    except:
        pass
    return results

@st.cache_data(ttl=300)
def get_br_prices(ticker_list):
    """Cotação Atual das Ações da Planilha"""
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

# --- CARDS DE MERCADO ---
M = get_detailed_market_data()

def render_market_card(name, prefix=""):
    data = M.get(name, {'price': 0, 'delta': 0, 'pct': 0})
    price = data['price']
    delta = data['delta']
    pct = data['pct']
    
    color_class = "index-delta-pos" if delta >= 0 else "index-delta-neg"
    signal = "+" if delta >= 0 else ""
    arrow = "▲" if delta >= 0 else "▼"
    
    if price == 0:
        price_fmt = "---"
        delta_fmt = ""
    else:
        price_fmt = f"{prefix} {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        delta_fmt = f"{arrow} {pct:.2f}% ({signal}{delta:,.2f})"

    st.markdown(f"""
        <div class="index-card">
            <div class="index-name">{name}</div>
            <div class="index-price">{price_fmt}</div>
            <div class="{color_class}">{delta_fmt}</div>
        </div>
    """, unsafe_allow_html=True)

# Layout 3 Colunas
c_br, c_us, c_cr = st.columns(3)

with c_br:
    st.markdown("### 🇧🇷 Brasil")
    render_market_card('IBOV', "")
    render_market_card('DÓLAR', "R$")

with c_us:
    st.markdown("### 🇺🇸 Estados Unidos")
    render_market_card('S&P 500', "")
    render_market_card('NASDAQ', "")
    render_market_card('VIX', "")

with c_cr:
    st.markdown("### ₿ Cripto")
    render_market_card('BITCOIN', "US$")
    render_market_card('ETHEREUM', "US$")
    render_market_card('SOLANA', "US$")

st.divider()

# --- 5. LÓGICA DE DADOS ---
def load_data():
    uploaded = st.sidebar.file_uploader("📂 Atualizar Dados (.xlsx)", type=['xlsx'])
    if uploaded: return pd.ExcelFile(uploaded)
    if os.path.exists("PEC.xlsx"): return pd.ExcelFile("PEC.xlsx")
    return None

xls = load_data()
df_radar = pd.DataFrame()
df_div = pd.DataFrame()

if xls:
    target_sheet = None
    # Procura aba com BAZIN e DY
    for sheet in xls.sheet_names:
        df_chk = pd.read_excel(xls, sheet).head(2)
        cols_up = [str(c).upper() for c in df_chk.columns]
        if any("BAZIN" in c for c in cols_up) and any("DY" in c for c in cols_up):
            target_sheet = sheet
            break
            
    if target_sheet:
        try:
            df_main = pd.read_excel(xls, target_sheet).fillna(0)
            cols = df_main.columns
            
            # Mapeamento de Colunas
            c_tick = [c for c in cols if 'TICKER' in c.upper()][0]
            c_emp = [c for c in cols if 'EMPRESA' in c.upper()][0]
            c_bazin = [c for c in cols if 'BAZIN' in c.upper()][0]
            c_dy = [c for c in cols if 'DY' in c.upper()][0]
            # Tenta achar Dividendo Por Ação (DPA)
            c_dpa_list = [c for c in cols if 'DPA' in c.upper()]
            c_dpa = c_dpa_list[0] if c_dpa_list else None
            
            # Limpeza e Conversão
            df_main['TICKER_CLEAN'] = df_main[c_tick].astype(str).str.strip().str.upper()
            df_main['BAZIN_NUM'] = df_main[c_bazin].apply(clean_currency)
            df_main['DY_NUM'] = df_main[c_dy].apply(clean_currency)
            if c_dpa:
                df_main['DPA_NUM'] = df_main[c_dpa].apply(clean_currency)
            else:
                df_main['DPA_NUM'] = 0.0
            
            # Preço Online e Margem
            tickers_list = df_main['TICKER_CLEAN'].unique().tolist()
            live_prices = get_br_prices(tickers_list)
            df_main['PRECO_LIVE'] = df_main['TICKER_CLEAN'].map(live_prices).fillna(0)
            
            df_main['MARGEM'] = df_main.apply(
                lambda x: ((x['BAZIN_NUM'] - x['PRECO_LIVE']) / x['PRECO_LIVE'] * 100) if x['PRECO_LIVE'] > 0 else -999, 
                axis=1
            )
            
            # Visual
            df_main['LOGO'] = df_main['TICKER_CLEAN'].apply(get_logo_url)
            df_main['ATIVO_DISPLAY'] = df_main[c_emp] + " (" + df_main['TICKER_CLEAN'] + ")"
            
            # Tabelas Finais
            df_radar = df_main[df_main['BAZIN_NUM'] > 0][['LOGO', 'ATIVO_DISPLAY', 'BAZIN_NUM', 'PRECO_LIVE', 'MARGEM']].copy()
            df_radar = df_radar.sort_values('MARGEM', ascending=False)
            
            df_div = df_main[df_main['DY_NUM'] > 0][['LOGO', 'ATIVO_DISPLAY', 'DPA_NUM', 'DY_NUM']].copy()
            df_div = df_div.sort_values('DY_NUM', ascending=False)
            
        except Exception as e:
            st.error(f"Erro ao processar dados: {e}")

# --- 6. TABELA: PREÇO TETO (CENTRALIZADO) ---
st.subheader("🎯 Radar de Preço-Teto")

if not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "LOGO": st.column_config.ImageColumn("Log", width="small", alignment="center"), 
            "ATIVO_DISPLAY": st.column_config.TextColumn("Ativo", width="medium", alignment="center"), 
            "BAZIN_NUM": st.column_config.NumberColumn("Teto Bazin", format="R$ %.2f", width="small", alignment="center"),
            "PRECO_LIVE": st.column_config.NumberColumn("Cotação", format="R$ %.2f", width="small", alignment="center"),
            "MARGEM": st.column_config.ProgressColumn(
                "Margem Segurança", 
                format="%.1f%%", 
                min_value=-50, max_value=50,
                width="large",
                alignment="center"
            )
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("Carregue o arquivo PEC.xlsx no menu lateral ou no GitHub.")

st.divider()

# --- 7. TABELA: DIVIDENDOS (CENTRALIZADO) ---
st.subheader("💰 Dividendos Projetados")

if not df_div.empty:
    st.dataframe(
        df_div,
        column_config={
            "LOGO": st.column_config.ImageColumn("Log", width="small", alignment="center"),
            "ATIVO_DISPLAY": st.column_config.TextColumn("Ativo", width="large", alignment="center"),
            "DPA_NUM": st.column_config.NumberColumn("Dividendo por Ação", format="R$ %.2f", width="medium", alignment="center"),
            "DY_NUM": st.column_config.NumberColumn("Dividend Yield", format="%.2f %%", width="medium", alignment="center"),
        },
        hide_index=True,
        use_container_width=True
    )
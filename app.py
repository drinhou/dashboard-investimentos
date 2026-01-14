import streamlit as st
import pandas as pd
import yfinance as yf
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PRO (SIMETRIA E DESIGN) ---
st.markdown("""
    <style>
        .stApp {background-color: #f8fafc;}
        h1, h2, h3, p, div, span {font-family: 'Segoe UI', sans-serif; color: #1e293b !important;}
        
        /* CARD PADRÃO DE MERCADO */
        .market-card {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            text-align: center;
            margin-bottom: 10px;
        }
        .market-label {
            font-size: 0.85rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }
        .market-value {
            font-size: 1.5rem;
            color: #0f172a;
            font-weight: 700;
            margin-top: 5px;
        }
        
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

def make_avatar(name):
    if not isinstance(name, str): return ""
    initials = name[:2].upper()
    return f"https://ui-avatars.com/api/?name={initials}&background=0f172a&color=fff&size=64&font-size=0.5&rounded=true&bold=true"

@st.cache_data(ttl=60) # Atualiza a cada 60 segundos
def get_market_data():
    """Busca dados robustos do Yahoo Finance"""
    # Lista de Tickers
    tickers_map = {
        'IBOV': '^BVSP',
        'DOLAR': 'BRL=X',
        'SP500': '^GSPC',
        'NASDAQ': '^IXIC',
        'VIX': '^VIX',
        'BITCOIN': 'BTC-USD',
        'ETHEREUM': 'ETH-USD',
        'SOLANA': 'SOL-USD'
    }
    
    live_data = {}
    try:
        # Pega o último preço de fechamento ou preço atual
        for key, ticker in tickers_map.items():
            ticker_obj = yf.Ticker(ticker)
            hist = ticker_obj.history(period="1d")
            if not hist.empty:
                val = hist['Close'].iloc[-1]
                live_data[key] = val
            else:
                live_data[key] = 0.0
    except:
        pass
    return live_data

@st.cache_data(ttl=300)
def get_br_prices(ticker_list):
    """Preços de Ações BR"""
    if not ticker_list: return {}
    sa_tickers = [f"{t}.SA" for t in ticker_list]
    prices = {}
    try:
        data = yf.download(sa_tickers, period="1d", progress=False)['Close'].iloc[-1]
        # Se for apenas 1 ativo, o pandas retorna float, se for varios, retorna Series
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

# --- CARREGAMENTO DE DADOS (PERSISTÊNCIA) ---
def load_excel():
    # 1. Tenta carregar do Upload (Sidebar)
    uploaded = st.sidebar.file_uploader("Atualizar Planilha (.xlsx)", type=['xlsx'])
    if uploaded:
        return pd.ExcelFile(uploaded)
    
    # 2. Se não tiver upload, tenta carregar o arquivo 'PEC.xlsx' do repositório
    elif os.path.exists("PEC.xlsx"):
        return pd.ExcelFile("PEC.xlsx")
    
    return None

# --- APP START ---

st.title("💸 Dinheiro Data")

M = get_market_data()

# --- 1. DADOS DE MERCADO (SIMÉTRICO) ---
# Layout em 3 colunas iguais
col_br, col_us, col_cr = st.columns(3)

# Função para criar o Card HTML
def display_card(label, value, prefix="", suffix=""):
    val_fmt = f"{prefix} {value:,.2f} {suffix}".replace(",", "X").replace(".", ",").replace("X", ".")
    st.markdown(f"""
        <div class="market-card">
            <div class="market-label">{label}</div>
            <div class="market-value">{val_fmt}</div>
        </div>
    """, unsafe_allow_html=True)

with col_br:
    st.markdown("### 🇧🇷 Brasil")
    display_card("IBOVESPA", M.get('IBOV', 0), "", "pts")
    display_card("DÓLAR", M.get('DOLAR', 0), "R$")

with col_us:
    st.markdown("### 🇺🇸 Estados Unidos")
    display_card("S&P 500", M.get('SP500', 0), "", "pts")
    display_card("NASDAQ", M.get('NASDAQ', 0), "", "pts")
    display_card("VIX (Medo)", M.get('VIX', 0), "", "")

with col_cr:
    st.markdown("### ₿ Cripto")
    display_card("BITCOIN", M.get('BITCOIN', 0), "US$")
    display_card("ETHEREUM", M.get('ETHEREUM', 0), "US$")
    display_card("SOLANA", M.get('SOLANA', 0), "US$")

st.divider()

# --- PROCESSAMENTO DA PLANILHA ---
xls = load_excel()

df_radar = pd.DataFrame()
df_div = pd.DataFrame()

if xls:
    # Procura aba inteligente
    target_sheet = None
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
            
            # Mapeia colunas
            c_tick = [c for c in cols if 'TICKER' in c.upper()][0]
            c_emp = [c for c in cols if 'EMPRESA' in c.upper()][0]
            c_bazin = [c for c in cols if 'BAZIN' in c.upper()][0]
            c_dy = [c for c in cols if 'DY' in c.upper()][0]
            
            # Limpeza
            df_main['TICKER_CLEAN'] = df_main[c_tick].astype(str).str.strip().str.upper()
            df_main['BAZIN_NUM'] = df_main[c_bazin].apply(clean_currency)
            df_main['DY_NUM'] = df_main[c_dy].apply(clean_currency)
            
            # Busca Preço Online
            tickers_list = df_main['TICKER_CLEAN'].unique().tolist()
            live_prices = get_br_prices(tickers_list)
            df_main['PRECO_LIVE'] = df_main['TICKER_CLEAN'].map(live_prices).fillna(0)
            
            # Margem
            df_main['MARGEM'] = df_main.apply(
                lambda x: ((x['BAZIN_NUM'] - x['PRECO_LIVE']) / x['PRECO_LIVE'] * 100) if x['PRECO_LIVE'] > 0 else -999, 
                axis=1
            )
            
            # Visual
            df_main['LOGO'] = df_main['TICKER_CLEAN'].apply(make_avatar)
            df_main['NOME_FINAL'] = df_main[c_emp] + " (" + df_main['TICKER_CLEAN'] + ")"
            
            # Dataframes Finais
            df_radar = df_main[df_main['BAZIN_NUM'] > 0][['LOGO', 'NOME_FINAL', 'BAZIN_NUM', 'PRECO_LIVE', 'MARGEM']].sort_values('MARGEM', ascending=False)
            df_div = df_main[df_main['DY_NUM'] > 0][['LOGO', 'NOME_FINAL', 'DY_NUM']].sort_values('DY_NUM', ascending=False)
            
        except:
            st.error("Erro ao processar estrutura da planilha.")

# --- 2. PREÇO TETO ---
st.subheader("🎯 Preço-Teto (Valuation)")

if xls and not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "LOGO": st.column_config.ImageColumn("", width="small"),
            "NOME_FINAL": st.column_config.TextColumn("Ativo"),
            "BAZIN_NUM": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "PRECO_LIVE": st.column_config.NumberColumn("Cotação Atual", format="R$ %.2f"),
            "MARGEM": st.column_config.ProgressColumn(
                "Margem Segurança", 
                format="%.1f%%", 
                min_value=-50, max_value=50
            )
        },
        hide_index=True,
        use_container_width=True
    )
elif not xls:
    st.info("⚠️ Nenhuma planilha encontrada. Faça upload de 'PEC.xlsx' no GitHub ou arraste no menu lateral.")

st.divider()

# --- 3. DIVIDENDOS ---
st.subheader("💰 Dividendos Projetados")

if xls and not df_div.empty:
    st.dataframe(
        df_div,
        column_config={
            "LOGO": st.column_config.ImageColumn("", width="small"),
            "NOME_FINAL": "Ativo",
            "DY_NUM": st.column_config.NumberColumn("DY Projetado", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True
    )
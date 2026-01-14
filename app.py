import streamlit as st
import pandas as pd
import yfinance as yf

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILO VISUAL (CLEAN / PRO) ---
st.markdown("""
    <style>
        /* Fundo e Fonte Global */
        .stApp {background-color: #f8fafc;}
        h1, h2, h3, p, div, span {font-family: 'Segoe UI', Helvetica, sans-serif; color: #0f172a !important;}
        
        /* Cards de Destaque (Topo) */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetricLabel"] p {color: #64748b !important; font-size: 0.9rem;}
        div[data-testid="stMetricValue"] div {color: #0f172a !important; font-weight: 700;}
        
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 5px;
        }
        
        /* Status Badges (Semáforo) */
        .badge-verde {background-color: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: bold;}
        .badge-amarelo {background-color: #fef9c3; color: #854d0e; padding: 4px 8px; border-radius: 4px; font-weight: bold;}
        .badge-vermelho {background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES DE SUPORTE ---

def clean_currency(x):
    """Limpa textos financeiros (R$, %, pontos) para número."""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

def make_avatar(name):
    """Cria ícone com iniciais (Avatar)"""
    if not isinstance(name, str): return ""
    initials = name[:2].upper()
    return f"https://ui-avatars.com/api/?name={initials}&background=0f172a&color=fff&size=64&font-size=0.5&rounded=true&bold=true"

@st.cache_data(ttl=120)
def get_market_data():
    """Busca dados de mercado em tempo real."""
    tickers = {
        # Destaques
        'IBOV': '^BVSP', 'S&P 500': '^GSPC', 'DÓLAR': 'BRL=X', 'BITCOIN': 'BTC-USD',
        # Listas
        'IFIX': '^BVSP', # IFIX não tem no Yahoo, usando IBOV como placeholder ou remover
        'NASDAQ': '^IXIC', 'DOW JONES': '^DJI', 'VIX': '^VIX',
        'ETHEREUM': 'ETH-USD', 'SOLANA': 'SOL-USD'
    }
    
    # Busca em lote
    data = {'IBOV': 0, 'S&P 500': 0, 'DÓLAR': 0, 'BITCOIN': 0, 'NASDAQ': 0, 'DOW JONES': 0, 'VIX': 0, 'ETHEREUM': 0, 'SOLANA': 0}
    try:
        df = yf.download(list(tickers.values()), period="1d", progress=False)['Close'].iloc[-1]
        for name, ticker in tickers.items():
            if ticker in df:
                data[name] = df[ticker]
    except:
        pass
    return data

@st.cache_data(ttl=300)
def get_live_prices(ticker_list):
    """Busca preços atuais de uma lista de ações BR."""
    if not ticker_list: return {}
    # Adiciona .SA
    sa_tickers = [f"{t}.SA" for t in ticker_list]
    prices = {}
    try:
        df = yf.download(sa_tickers, period="1d", progress=False)['Close'].iloc[-1]
        # Mapeia de volta (TICKER.SA -> TICKER)
        for t in ticker_list:
            sa = f"{t}.SA"
            if sa in df:
                prices[t] = df[sa]
    except:
        pass
    return prices

# --- HEADER: DESTAQUES ---
st.title("💸 Dinheiro Data")

M = get_market_data()

# Cards de Destaque
c1, c2, c3, c4 = st.columns(4)
def card(col, label, val, prefix="", suffix=""):
    val_fmt = f"{prefix} {val:,.2f} {suffix}".replace(",", "X").replace(".", ",").replace("X", ".")
    col.metric(label, val_fmt)

card(c1, "🇺🇸 S&P 500", M['S&P 500'], "", "pts")
card(c2, "🇧🇷 IBOVESPA", M['IBOV'], "", "pts")
card(c3, "💵 DÓLAR", M['DÓLAR'], "R$")
card(c4, "₿ BITCOIN", M['BITCOIN'], "US$")

st.divider()

# --- SEÇÃO 1: PRINCIPAIS DADOS (LISTAS) ---
st.subheader("🌍 Visão de Mercado")

col_br, col_us, col_cr = st.columns(3)

with col_br:
    st.markdown("##### 🇧🇷 Brasil")
    # Simulação de tabela simples
    data_br = [
        {"Índice": "IBOVESPA", "Valor": M['IBOV']},
        {"Índice": "IFIX (FIIs)", "Valor": "---"}, # Yahoo não fornece IFIX
    ]
    st.dataframe(pd.DataFrame(data_br), hide_index=True, use_container_width=True)

with col_us:
    st.markdown("##### 🇺🇸 Estados Unidos")
    data_us = [
        {"Índice": "NASDAQ", "Valor": M['NASDAQ']},
        {"Índice": "DOW JONES", "Valor": M['DOW JONES']},
        {"Índice": "VIX (Medo)", "Valor": M['VIX']},
    ]
    st.dataframe(pd.DataFrame(data_us), hide_index=True, use_container_width=True)

with col_cr:
    st.markdown("##### ₿ Criptomoedas")
    data_cr = [
        {"Cripto": "Ethereum", "Valor ($)": M['ETHEREUM']},
        {"Cripto": "Solana", "Valor ($)": M['SOLANA']},
    ]
    st.dataframe(pd.DataFrame(data_cr), hide_index=True, use_container_width=True)

st.divider()

# --- UPLOAD E PROCESSAMENTO INTELIGENTE ---
uploaded_file = st.sidebar.file_uploader("📂 Carregar Planilha (.xlsx)", type=['xlsx'])

df_radar = pd.DataFrame()
df_div = pd.DataFrame()

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    
    # 1. Tenta achar a aba com Bazin e Dividendos (Página 1)
    target_sheet = None
    for sheet in xls.sheet_names:
        df_temp = pd.read_excel(xls, sheet).head(2)
        cols_upper = [str(c).upper() for c in df_temp.columns]
        # Se tiver BAZIN e DY, é essa a aba!
        if any("BAZIN" in c for c in cols_upper) and any("DY" in c for c in cols_upper):
            target_sheet = sheet
            break
            
    if target_sheet:
        try:
            df_main = pd.read_excel(xls, target_sheet).fillna(0)
            cols = df_main.columns
            
            # Mapeia colunas dinamicamente
            c_tick = [c for c in cols if 'TICKER' in c.upper()][0]
            c_emp = [c for c in cols if 'EMPRESA' in c.upper()][0]
            c_bazin = [c for c in cols if 'BAZIN' in c.upper()][0]
            c_dy = [c for c in cols if 'DY' in c.upper()][0]
            c_dpa = [c for c in cols if 'DPA' in c.upper()] # Pode não ter DPA explicito as vezes
            c_dpa = c_dpa[0] if c_dpa else None

            # Limpeza
            df_main['TICKER_CLEAN'] = df_main[c_tick].astype(str).str.strip().str.upper()
            df_main['BAZIN_NUM'] = df_main[c_bazin].apply(clean_currency)
            df_main['DY_NUM'] = df_main[c_dy].apply(clean_currency)
            if c_dpa: df_main['DPA_NUM'] = df_main[c_dpa].apply(clean_currency)
            else: df_main['DPA_NUM'] = 0
            
            # --- BUSCA COTAÇÕES ONLINE ---
            tickers_list = df_main['TICKER_CLEAN'].unique().tolist()
            live_prices = get_live_prices(tickers_list)
            
            df_main['PRECO_LIVE'] = df_main['TICKER_CLEAN'].map(live_prices).fillna(0)
            
            # --- PREPARAR RADAR (TETO) ---
            # Margem: ((Teto - Preço) / Preço) * 100
            df_main['MARGEM'] = df_main.apply(
                lambda x: ((x['BAZIN_NUM'] - x['PRECO_LIVE']) / x['PRECO_LIVE'] * 100) if x['PRECO_LIVE'] > 0 else -999, 
                axis=1
            )
            
            # Avatar
            df_main['LOGO'] = df_main['TICKER_CLEAN'].apply(make_avatar)
            df_main['NOME_DISPLAY'] = df_main[c_emp] + " (" + df_main['TICKER_CLEAN'] + ")"

            # Filtra e Ordena Radar
            # Apenas onde tem Teto definido
            df_radar = df_main[df_main['BAZIN_NUM'] > 0][['LOGO', 'NOME_DISPLAY', 'BAZIN_NUM', 'PRECO_LIVE', 'MARGEM']].copy()
            df_radar = df_radar.sort_values('MARGEM', ascending=False)
            
            # --- PREPARAR DIVIDENDOS ---
            # Ordena por Maior DY
            cols_div = ['LOGO', 'NOME_DISPLAY', 'DY_NUM']
            if c_dpa: cols_div.insert(2, 'DPA_NUM')
            
            df_div = df_main[df_main['DY_NUM'] > 0][cols_div].copy()
            df_div = df_div.sort_values('DY_NUM', ascending=False)
            
        except Exception as e:
            st.error(f"Erro ao processar planilha: {e}")
    else:
        st.warning("Não encontrei a aba com colunas 'BAZIN' e 'DY' no Excel.")

# --- SEÇÃO 2: PREÇO TETO (BAZIN) ---
st.subheader("🎯 Preço-Teto (Método Bazin)")
if uploaded_file and not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "LOGO": st.column_config.ImageColumn("", width="small"),
            "NOME_DISPLAY": st.column_config.TextColumn("Ativo"),
            "BAZIN_NUM": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "PRECO_LIVE": st.column_config.NumberColumn("Cotação Atual", format="R$ %.2f"),
            "MARGEM": st.column_config.ProgressColumn(
                "Margem de Segurança (%)",
                format="%.1f %%",
                min_value=-50,
                max_value=50
            ),
        },
        hide_index=True,
        use_container_width=True
    )
    st.caption("*Cotações atualizadas em tempo real via Yahoo Finance.")
elif not uploaded_file:
    st.info("👆 Carregue sua planilha no menu lateral para ver o Radar.")

st.divider()

# --- SEÇÃO 3: DIVIDENDOS ESPERADOS ---
st.subheader("💰 Dividendos Projetados (2026)")
if uploaded_file and not df_div.empty:
    st.dataframe(
        df_div,
        column_config={
            "LOGO": st.column_config.ImageColumn("", width="small"),
            "NOME_DISPLAY": "Ativo",
            "DPA_NUM": st.column_config.NumberColumn("Div. Projetado (R$)", format="R$ %.2f"),
            "DY_NUM": st.column_config.NumberColumn("Yield (DY%)", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True
    )
elif not uploaded_file:
    st.info("👆 Carregue sua planilha para ver as projeções.")
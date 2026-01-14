import streamlit as st
import pandas as pd
import yfinance as yf

# --- CONFIGURAÇÃO VISUAL (ALTO CONTRASTE) ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS FORÇADO PARA CORRIGIR "BRANCO NO BRANCO"
st.markdown("""
    <style>
        /* Força Fundo Claro Global */
        .stApp {background-color: #f4f7f6;}
        
        /* Força Textos Escuros (Preto/Cinza Escuro) em TUDO */
        h1, h2, h3, h4, h5, h6, p, div, span, label, li {
            color: #1e293b !important;
            font-family: 'Segoe UI', sans-serif;
        }
        
        /* Corrigir Métricas (Quadrados do Topo) */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #d1d5db !important;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        /* Texto do Label (Título do Card) */
        div[data-testid="stMetricLabel"] p {
            color: #64748b !important; /* Cinza médio */
            font-size: 0.9rem !important;
        }
        /* Texto do Valor (Número do Card) */
        div[data-testid="stMetricValue"] div {
            color: #0f172a !important; /* Preto forte */
        }
        
        /* Tabelas: Força fundo branco e texto preto */
        div[data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb;
        }
        div[data-testid="stDataFrame"] * {
            color: #333333 !important;
        }
        
        /* Abas (Tabs) */
        button[data-baseweb="tab"] {
            color: #333333 !important;
        }
        
        /* Barra Lateral */
        section[data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e5e7eb;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    """Limpa formatação e retorna float."""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=300)
def get_market_data():
    """Busca índices sem travar."""
    indices = {'IBOV': 0, 'S&P 500': 0, 'Dólar': 0, 'Bitcoin': 0}
    try:
        tickers = ['^BVSP', '^GSPC', 'BRL=X', 'BTC-USD']
        data = yf.download(tickers, period="1d", progress=False)['Close'].iloc[-1]
        indices['IBOV'] = data.get('^BVSP', 0)
        indices['S&P 500'] = data.get('^GSPC', 0)
        indices['Dólar'] = data.get('BRL=X', 0)
        indices['Bitcoin'] = data.get('BTC-USD', 0)
    except:
        pass
    return indices

@st.cache_data(ttl=86400) # Cache de 24h para nomes não ficarem lentos
def fetch_name_online(ticker):
    """Se não tiver nome no Excel, busca no Yahoo Finance."""
    try:
        # Tenta ticker direto ou com .SA
        t = ticker if str(ticker).endswith('.SA') else f"{ticker}.SA"
        info = yf.Ticker(t).info
        long_name = info.get('longName') or info.get('shortName')
        return long_name
    except:
        return None

def format_asset_name(nome_planilha, ticker, classe):
    """
    Formata inteligente:
    - Ações/FIIs: Nome Real (TICKER)
    - Cripto: Nome Real (SIGLA)
    - Renda Fixa: Nome Completo (Sem abreviação se não houver ticker)
    """
    ticker_clean = str(ticker).replace('.SA', '').strip().upper()
    nome_clean = str(nome_planilha).strip()
    
    # Se o nome na planilha for igual ao ticker ou vazio, tenta buscar online
    if (not nome_clean or nome_clean == 'nan' or nome_clean.upper() == ticker_clean):
        online_name = fetch_name_online(ticker_clean)
        if online_name:
            nome_clean = online_name
        else:
            nome_clean = ticker_clean # Fallback se não achar nada

    classe_str = str(classe).lower()

    if "cripto" in classe_str:
        # Ex: Bitcoin (BTC)
        # Se o nome já for BTC, tenta expandir (Difícil sem base, mantém BTC (BTC))
        if nome_clean == ticker_clean and ticker_clean == 'BTC': nome_clean = "Bitcoin"
        return f"{nome_clean} ({ticker_clean})"
    
    elif any(x in classe_str for x in ["renda fixa", "tesouro", "fixa"]):
        # Renda Fixa: Apenas nome completo. 
        # Se tiver um "ticker" que parece código (ex: LCA), põe em parenteses
        return nome_clean
    
    else:
        # Ações e FIIs: Kinea (KNCA11)
        # Remove S.A. do nome para ficar mais curto
        nome_clean = nome_clean.replace(" S.A.", "").replace(" S/A", "")
        return f"{nome_clean} ({ticker_clean})"

# --- HEADER ---
st.title("🦅 Aura Finance")

idx = get_market_data()
c1, c2, c3, c4 = st.columns(4)

def show_metric(col, label, val, prefix="", suffix=""):
    if val and val > 0:
        val_fmt = f"{prefix} {val:,.2f} {suffix}".replace(",", "X").replace(".", ",").replace("X", ".")
        col.metric(label, val_fmt)
    else:
        col.metric(label, "---")

show_metric(c1, "IBOVESPA", idx['IBOV'], "", "pts")
show_metric(c2, "S&P 500", idx['S&P 500'], "", "pts")
show_metric(c3, "DÓLAR", idx['Dólar'], "R$")
show_metric(c4, "BITCOIN", idx['Bitcoin'], "US$")

st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Upload")
    uploaded_file = st.file_uploader("Arquivo Excel (.xlsx)", type=['xlsx'])

if not uploaded_file:
    st.info("👆 Por favor, carregue sua planilha.")
    st.stop()

xls = pd.ExcelFile(uploaded_file)

# --- 1. PREPARAÇÃO DO VALUATION (Fonte de Nomes) ---
mapa_nomes = {}
df_radar = pd.DataFrame()

try:
    df_val = pd.read_excel(xls, 'Valuation').fillna(0)
    
    # Identificar colunas
    cols = df_val.columns
    c_ticker = [c for c in cols if 'TICKER' in c.upper()][0]
    c_empresa = [c for c in cols if 'EMPRESA' in c.upper()][0]
    c_cotacao = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
    c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]

    # Preencher dicionário de nomes
    for index, row in df_val.iterrows():
        t = str(row[c_ticker]).strip()
        n = str(row[c_empresa]).strip()
        if t and n and n != '0' and n != 'nan':
            mapa_nomes[t] = n

    df_val['TICKER_CLEAN'] = df_val[c_ticker].astype(str).str.strip()
    df_val['PRECO_NUM'] = df_val[c_cotacao].apply(clean_currency)
    df_val['TETO_NUM'] = df_val[c_teto].apply(clean_currency)
    
    # FÓRMULA: ((Teto - Preço) / Preço) * 100
    df_val['MARGEM_PCT'] = df_val.apply(
        lambda x: ((x['TETO_NUM'] - x['PRECO_NUM']) / x['PRECO_NUM']) * 100 if x['PRECO_NUM'] > 0 else 0, axis=1
    )
    
    # Formatar Nome para o Radar
    df_val['NOME_FINAL'] = df_val.apply(
        lambda x: format_asset_name(x[c_empresa], x['TICKER_CLEAN'], 'Ações'), axis=1
    )

    df_radar = df_val[['NOME_FINAL', 'PRECO_NUM', 'TETO_NUM', 'MARGEM_PCT']].copy()
    df_radar = df_radar.sort_values('MARGEM_PCT', ascending=False)
except Exception as e:
    # st.error(f"Erro Valuation: {e}") # Ocultar erro visual para o usuário
    pass

# --- 2. CARTEIRA ---
try:
    df_cart = pd.read_excel(xls, 'Carteira').fillna(0)
    c_ativo = [c for c in df_cart.columns if 'ATIVO' in c.upper()][0]
    c_qtd = [c for c in df_cart.columns if 'QUANTIDADE' in c.upper()][0]
    c_saldo = [c for c in df_cart.columns if 'SALDO' in c.upper() and 'TOTAL' not in c.upper()][0]
    
    # Tenta achar classe
    c_classe_list = [c for c in df_cart.columns if 'CLASSE' in c.upper()]
    c_classe = c_classe_list[0] if c_classe_list else None

    df_cart['TICKER_CLEAN'] = df_cart[c_ativo].astype(str).apply(lambda x: x.split('\n')[0].strip())
    df_cart['QTD_NUM'] = df_cart[c_qtd].apply(clean_currency)
    df_cart['SALDO_NUM'] = df_cart[c_saldo].apply(clean_currency)
    
    # Resolve nomes
    def resolver_nome_carteira(row):
        ticker = row['TICKER_CLEAN']
        classe = str(row[c_classe]) if c_classe else "Ações"
        
        # 1. Tenta pegar do mapa do valuation
        nome_base = mapa_nomes.get(ticker, ticker)
        
        # 2. Formata
        return format_asset_name(nome_base, ticker, classe)

    df_cart['NOME_EXIBICAO'] = df_cart.apply(resolver_nome_carteira, axis=1)

    df_carteira_show = df_cart[['NOME_EXIBICAO', 'QTD_NUM', 'SALDO_NUM']].copy()
    df_carteira_show = df_carteira_show[df_carteira_show['SALDO_NUM'] > 0] # Remove zerados
    df_carteira_show = df_carteira_show.sort_values('SALDO_NUM', ascending=False)
    
    total_patrimonio = df_cart['SALDO_NUM'].sum()
except Exception as e:
    st.error(f"Erro Carteira: {e}")
    total_patrimonio = 0
    df_carteira_show = pd.DataFrame()

# --- 3. PROVENTOS ---
dados_anos = {'2024': [0.0]*12, '2025': [0.0]*12, '2026': [0.0]*12}
try:
    df_prov = pd.read_excel(xls, 'Proventos').fillna(0)
    col_a = df_prov.iloc[:, 0].astype(str)
    for ano in ['2024', '2025', '2026']:
        linha = df_prov[col_a.str.contains(f"Proventos {ano}", na=False)]
        if not linha.empty:
            dados_anos[ano] = linha.iloc[0, 1:13].apply(clean_currency).values
except:
    pass

# --- LAYOUT DO DASHBOARD ---

# 1. CARTEIRA
st.subheader("🏦 Minha Carteira")
col_p1, col_p2 = st.columns([1, 3])
col_p1.metric("Patrimônio Total", f"R$ {total_patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

if not df_carteira_show.empty:
    with col_p2:
        st.dataframe(
            df_carteira_show,
            column_config={
                "NOME_EXIBICAO": st.column_config.TextColumn("Ativo / Empresa"),
                "QTD_NUM": st.column_config.NumberColumn("Quantidade", format="%.0f"),
                "SALDO_NUM": st.column_config.NumberColumn("Saldo Atual", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )

st.divider()

# 2. PROVENTOS
st.subheader("💰 Histórico de Proventos")
tab24, tab25, tab26 = st.tabs(["2024", "2025", "2026"])

def render_prov(ano):
    vals = dados_anos.get(ano, [0.0]*12)
    meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    df_t = pd.DataFrame([vals], columns=meses)
    total = sum(vals)
    
    st.dataframe(
        df_t,
        column_config={c: st.column_config.NumberColumn(format="R$ %.2f") for c in df_t.columns},
        hide_index=True,
        use_container_width=True
    )
    st.caption(f"Total {ano}: **R$ {total:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))

with tab24: render_prov('2024')
with tab25: render_prov('2025')
with tab26: render_prov('2026')

st.divider()

# 3. RADAR (VALUATION)
st.subheader("🎯 Radar de Oportunidades")
if not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "NOME_FINAL": st.column_config.TextColumn("Empresa (Ticker)"),
            "PRECO_NUM": st.column_config.NumberColumn("Cotação", format="R$ %.2f"),
            "TETO_NUM": st.column_config.NumberColumn("Preço Teto (Bazin)", format="R$ %.2f"),
            "MARGEM_PCT": st.column_config.NumberColumn(
                "Margem (%)",
                format="%.2f %%"
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
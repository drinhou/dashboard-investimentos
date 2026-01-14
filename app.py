import streamlit as st
import pandas as pd
import yfinance as yf

# --- CONFIGURAÇÃO VISUAL (CLEAN & ROBUST) ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para forçar visual "Investidor10" sem quebrar
st.markdown("""
    <style>
        /* Fundo limpo */
        .main {background-color: #f4f7f6;}
        
        /* Fontes */
        h1, h2, h3, p {font-family: 'Segoe UI', Helvetica, sans-serif; color: #333;}
        
        /* Cards de Índices (Topo) */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border-left: 5px solid #00C896; /* Verde Nubank */
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            border-radius: 5px;
        }
        
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    """Limpa textos de dinheiro e converte para número."""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        # Remove R$, espaços, pontos de milhar e converte vírgula
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=300)
def get_market_data():
    """Busca índices sem quebrar o site se falhar."""
    indices = {'IBOV': None, 'S&P 500': None, 'Dólar': None, 'Bitcoin': None}
    try:
        # Tenta buscar cotações
        tickers = ['^BVSP', '^GSPC', 'BRL=X', 'BTC-USD']
        data = yf.download(tickers, period="1d", progress=False)['Close'].iloc[-1]
        
        indices['IBOV'] = data.get('^BVSP', 0)
        indices['S&P 500'] = data.get('^GSPC', 0)
        indices['Dólar'] = data.get('BRL=X', 0)
        indices['Bitcoin'] = data.get('BTC-USD', 0)
    except:
        pass # Se der erro, mantemos None para tratar na exibição
    return indices

def make_avatar_url(ticker):
    """Gera um avatar colorido e elegante com as iniciais (Nunca quebra)."""
    if not isinstance(ticker, str): return ""
    clean = ticker.replace('.SA', '').strip()[:4] # Pega 4 letras
    # API ui-avatars gera imagem com iniciais
    return f"https://ui-avatars.com/api/?name={clean}&background=0D1117&color=fff&size=64&font-size=0.4&length=4&rounded=true&bold=true"

# --- HEADER (ÍNDICES) ---
st.title("🦅 Aura Finance")

idx = get_market_data()
c1, c2, c3, c4 = st.columns(4)

def show_metric(col, label, val, prefix="", suffix=""):
    if val and val > 0:
        col.metric(label, f"{prefix} {val:,.2f} {suffix}".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        col.metric(label, "---")

show_metric(c1, "IBOVESPA", idx['IBOV'], "", "pts")
show_metric(c2, "S&P 500", idx['S&P 500'], "", "pts")
show_metric(c3, "DÓLAR", idx['Dólar'], "R$")
show_metric(c4, "BITCOIN", idx['Bitcoin'], "US$")

st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Dados")
    uploaded_file = st.file_uploader("Arraste sua planilha aqui", type=['xlsx'])

if not uploaded_file:
    st.info("👆 Aguardando planilha...")
    st.stop()

# --- PROCESSAMENTO ---
xls = pd.ExcelFile(uploaded_file)

# 1. VALUATION (Fonte da Verdade para Nomes e Preços)
try:
    df_val = pd.read_excel(xls, 'Valuation')
    cols = df_val.columns
    c_ticker = [c for c in cols if 'TICKER' in c.upper()][0]
    c_empresa = [c for c in cols if 'EMPRESA' in c.upper()][0]
    c_cotacao = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
    c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]

    df_val['TICKER_CLEAN'] = df_val[c_ticker].astype(str).str.strip()
    df_val['PRECO_NUM'] = df_val[c_cotacao].apply(clean_currency)
    df_val['TETO_NUM'] = df_val[c_teto].apply(clean_currency)
    
    # FÓRMULA CORRIGIDA: ((Teto - Atual) / Atual)
    df_val['MARGEM_DECIMAL'] = (df_val['TETO_NUM'] - df_val['PRECO_NUM']) / df_val['PRECO_NUM']
    
    # Avatar
    df_val['LOGO'] = df_val['TICKER_CLEAN'].apply(make_avatar_url)

    df_radar = df_val[[c_empresa, 'LOGO', 'TICKER_CLEAN', 'PRECO_NUM', 'TETO_NUM', 'MARGEM_DECIMAL']].copy()
    df_radar = df_radar.sort_values('MARGEM_DECIMAL', ascending=False)
except:
    df_radar = pd.DataFrame()

# 2. CARTEIRA
try:
    df_cart = pd.read_excel(xls, 'Carteira')
    c_ativo = [c for c in df_cart.columns if 'ATIVO' in c.upper()][0]
    c_qtd = [c for c in df_cart.columns if 'QUANTIDADE' in c.upper()][0]
    c_saldo = [c for c in df_cart.columns if 'SALDO' in c.upper() and 'TOTAL' not in c.upper()][0]

    df_cart['TICKER_CLEAN'] = df_cart[c_ativo].astype(str).apply(lambda x: x.split('\n')[0].strip())
    df_cart['QTD_NUM'] = df_cart[c_qtd].apply(clean_currency)
    df_cart['SALDO_NUM'] = df_cart[c_saldo].apply(clean_currency)
    
    # Cruzamento de dados (VLOOKUP) para pegar nome da empresa e logo
    if not df_radar.empty:
        dict_nomes = pd.Series(df_val[c_empresa].values, index=df_val['TICKER_CLEAN']).to_dict()
        dict_logos = pd.Series(df_val['LOGO'].values, index=df_val['TICKER_CLEAN']).to_dict()
        
        df_cart['EMPRESA'] = df_cart['TICKER_CLEAN'].map(dict_nomes).fillna(df_cart['TICKER_CLEAN'])
        df_cart['LOGO'] = df_cart['TICKER_CLEAN'].map(dict_logos).fillna("")
    else:
        df_cart['EMPRESA'] = df_cart['TICKER_CLEAN']
        df_cart['LOGO'] = ""

    df_carteira_show = df_cart[['LOGO', 'EMPRESA', 'TICKER_CLEAN', 'QTD_NUM', 'SALDO_NUM']].copy()
    df_carteira_show = df_carteira_show.sort_values('SALDO_NUM', ascending=False)
    total_patrimonio = df_cart['SALDO_NUM'].sum()
except:
    total_patrimonio = 0
    df_carteira_show = pd.DataFrame()

# 3. PROVENTOS (ANOS COMPLETOS)
dados_anos = {'2024': [0.0]*12, '2025': [0.0]*12, '2026': [0.0]*12}

try:
    df_prov = pd.read_excel(xls, 'Proventos')
    col_a = df_prov.iloc[:, 0].astype(str)
    
    for ano in ['2024', '2025', '2026']:
        # Procura linha que contem "Proventos 20xx"
        linha = df_prov[col_a.str.contains(f"Proventos {ano}", na=False)]
        if not linha.empty:
            vals = linha.iloc[0, 1:13].apply(clean_currency).values
            dados_anos[ano] = vals
except:
    pass

# --- DASHBOARD LAYOUT ---

# 1. CARTEIRA
st.subheader("🏦 Minha Carteira")
col_p1, col_p2 = st.columns([1, 3])
col_p1.metric("Patrimônio Total", f"R$ {total_patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

if not df_carteira_show.empty:
    with col_p2:
        st.dataframe(
            df_carteira_show,
            column_config={
                "LOGO": st.column_config.ImageColumn("", width="small"),
                "EMPRESA": st.column_config.TextColumn("Empresa"),
                "TICKER_CLEAN": st.column_config.TextColumn("Ticker"),
                "QTD_NUM": st.column_config.NumberColumn("Qtd", format="%.0f"),
                "SALDO_NUM": st.column_config.NumberColumn("Saldo", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )

st.divider()

# 2. PROVENTOS (ABAS POR ANO)
st.subheader("💰 Proventos Recebidos")
tab24, tab25, tab26 = st.tabs(["2024", "2025", "2026"])

def render_prov_tab(ano):
    vals = dados_anos.get(ano, [0.0]*12)
    
    # LISTA CORRIGIDA (SEM QUEBRA DE LINHA)
    colunas_meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    
    df_tab = pd.DataFrame([vals], columns=colunas_meses)
    total = sum(vals)
    
    st.dataframe(
        df_tab,
        column_config={c: st.column_config.NumberColumn(format="R$ %.2f") for c in df_tab.columns},
        hide_index=True,
        use_container_width=True
    )
    st.caption(f"Total Acumulado em {ano}: **R$ {total:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))

with tab24: render_prov_tab('2024')
with tab25: render_prov_tab('2025')
with tab26: render_prov_tab('2026')

st.divider()

# 3. RADAR (VALUATION)
st.subheader("🎯 Radar de Oportunidades")
if not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "LOGO": st.column_config.ImageColumn("", width="small"),
            "EMPRESA": "Empresa",
            "TICKER_CLEAN": "Ticker",
            "PRECO_NUM": st.column_config.NumberColumn("Cotação", format="R$ %.2f"),
            "TETO_NUM": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "MARGEM_DECIMAL": st.column_config.ProgressColumn(
                "Margem de Segurança (%)",
                format="%.2f%%",
                min_value=-0.5,
                max_value=0.5,
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
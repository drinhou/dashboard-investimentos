import streamlit as st
import pandas as pd
import yfinance as yf

# --- CONFIGURAÇÃO VISUAL (PRETO NO BRANCO) ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS FORÇADO (HIGH CONTRAST)
st.markdown("""
    <style>
        .stApp {background-color: #f8fafc;}
        h1, h2, h3, h4, h5, h6, p, span, div, label {color: #0f172a !important; font-family: 'Segoe UI', sans-serif;}
        
        /* Cards do Topo */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
        }
        div[data-testid="stMetricLabel"] p {color: #64748b !important; font-size: 0.9rem !important;}
        div[data-testid="stMetricValue"] div {color: #0f172a !important; font-weight: 700 !important;}
        
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    """Limpa moeda para float"""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=300)
def get_market_data():
    """Busca índices"""
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

# --- LISTA VIP DE NOMES (CORREÇÃO MANUAL) ---
# Adicione aqui qualquer ativo que teime em ficar errado
KNOWN_FIXES = {
    'KNCA11': 'Kinea Rendimentos',
    'MXRF11': 'Maxi Renda',
    'HGLG11': 'CSHG Logística',
    'XPLG11': 'XP Log',
    'VISC11': 'Vinci Shopping',
    'KNIP11': 'Kinea Índices',
    'KNCR11': 'Kinea Rendimentos',
    'BBAS3': 'Banco do Brasil',
    'BBSE3': 'BB Seguridade',
    'ITUB4': 'Itaú Unibanco',
    'VALE3': 'Vale',
    'PETR4': 'Petrobras',
    'WEGE3': 'WEG',
    'TAEE11': 'Taesa'
}

@st.cache_data(ttl=86400)
def get_asset_name_online(ticker):
    """
    Tenta pegar o nome:
    1. Da lista manual (KNOWN_FIXES)
    2. Da API do Yahoo Finance
    """
    clean_ticker = str(ticker).replace('.SA', '').strip().upper()
    
    # 1. Verifica lista manual
    if clean_ticker in KNOWN_FIXES:
        return KNOWN_FIXES[clean_ticker]
        
    # 2. Tenta Online
    try:
        t_obj = yf.Ticker(f"{clean_ticker}.SA")
        info = t_obj.info
        # Tenta pegar nome curto ou longo
        name = info.get('shortName') or info.get('longName')
        if name:
            # Limpa "S.A." e nomes muito longos
            name = name.replace("Fundo De Investimento Imobiliario", "").replace("Fundo de Investimento Imobiliario", "")
            name = name.replace(" - FII", "").replace(" S.A.", "").replace(" S/A", "").strip()
            return name
    except:
        pass
    
    return None

def format_final_name(nome_planilha, ticker, classe):
    """Lógica final de formatação"""
    ticker_clean = str(ticker).replace('.SA', '').strip().upper()
    classe_str = str(classe).lower()
    
    # Renda Fixa: Não mexe, retorna nome da planilha
    if any(x in classe_str for x in ["renda fixa", "tesouro", "fixa"]):
        return str(nome_planilha)
    
    # Se for Cripto (Bitcoin, Ethereum)
    if "cripto" in classe_str:
        return f"{nome_planilha} ({ticker_clean})"

    # Ações e FIIs:
    # Se na planilha o nome for igual ao ticker ou vazio, busca o nome real
    nome_candidato = str(nome_planilha).strip()
    if not nome_candidato or nome_candidato == 'nan' or nome_candidato.upper() == ticker_clean:
        online = get_asset_name_online(ticker_clean)
        if online:
            nome_candidato = online
        else:
            nome_candidato = ticker_clean # Falhou tudo, usa ticker

    return f"{nome_candidato} ({ticker_clean})"

# --- APP ---
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

# --- UPLOAD ---
with st.sidebar:
    st.header("📂 Upload")
    uploaded_file = st.file_uploader("Arquivo Excel (.xlsx)", type=['xlsx'])

if not uploaded_file:
    st.info("👆 Por favor, carregue sua planilha.")
    st.stop()

xls = pd.ExcelFile(uploaded_file)

# --- 1. CARTEIRA E NOMES ---
# Vamos processar a Carteira primeiro e resolver os nomes
try:
    df_cart = pd.read_excel(xls, 'Carteira').fillna(0)
    c_ativo = [c for c in df_cart.columns if 'ATIVO' in c.upper()][0]
    c_qtd = [c for c in df_cart.columns if 'QUANTIDADE' in c.upper()][0]
    c_saldo = [c for c in df_cart.columns if 'SALDO' in c.upper() and 'TOTAL' not in c.upper()][0]
    c_classe_l = [c for c in df_cart.columns if 'CLASSE' in c.upper()]
    c_classe = c_classe_l[0] if c_classe_l else None

    # Limpeza
    df_cart['TICKER_CLEAN'] = df_cart[c_ativo].astype(str).apply(lambda x: x.split('\n')[0].strip())
    df_cart['QTD_NUM'] = df_cart[c_qtd].apply(clean_currency)
    df_cart['SALDO_NUM'] = df_cart[c_saldo].apply(clean_currency)
    
    # Processamento de Nomes
    def resolve_row_name(row):
        ticker = row['TICKER_CLEAN']
        classe = str(row[c_classe]) if c_classe else "Ações"
        # O nome na planilha Carteira geralmente é o próprio ticker ou vazio
        return format_final_name(ticker, ticker, classe)

    df_cart['NOME_EXIBICAO'] = df_cart.apply(resolve_row_name, axis=1)

    df_carteira_show = df_cart[['NOME_EXIBICAO', 'QTD_NUM', 'SALDO_NUM']].copy()
    df_carteira_show = df_carteira_show[df_carteira_show['SALDO_NUM'] > 0]
    df_carteira_show = df_carteira_show.sort_values('SALDO_NUM', ascending=False)
    
    total_patrimonio = df_cart['SALDO_NUM'].sum()
except Exception as e:
    st.error(f"Erro na Carteira: {e}")
    total_patrimonio = 0
    df_carteira_show = pd.DataFrame()

# --- 2. VALUATION (RADAR) ---
df_radar = pd.DataFrame()
try:
    df_val = pd.read_excel(xls, 'Valuation').fillna(0)
    cols = df_val.columns
    c_ticker = [c for c in cols if 'TICKER' in c.upper()][0]
    c_empresa = [c for c in cols if 'EMPRESA' in c.upper()][0]
    c_cotacao = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
    c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]

    df_val['TICKER_CLEAN'] = df_val[c_ticker].astype(str).str.strip()
    df_val['PRECO_NUM'] = df_val[c_cotacao].apply(clean_currency)
    df_val['TETO_NUM'] = df_val[c_teto].apply(clean_currency)
    
    # Margem: ((Teto - Preço) / Preço) * 100
    df_val['MARGEM_PCT'] = df_val.apply(
        lambda x: ((x['TETO_NUM'] - x['PRECO_NUM']) / x['PRECO_NUM']) * 100 if x['PRECO_NUM'] > 0 else 0, axis=1
    )
    
    # Usa a mesma lógica de nomes para consistência
    df_val['NOME_FINAL'] = df_val.apply(
        lambda x: format_final_name(x[c_empresa], x['TICKER_CLEAN'], 'Ações'), axis=1
    )

    df_radar = df_val[['NOME_FINAL', 'PRECO_NUM', 'TETO_NUM', 'MARGEM_PCT']].copy()
    df_radar = df_radar.sort_values('MARGEM_PCT', ascending=False)
except:
    pass

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

# --- DASHBOARD ---

# 1. CARTEIRA
st.subheader("🏦 Minha Carteira")
col_p1, col_p2 = st.columns([1, 3])
col_p1.metric("Patrimônio Total", f"R$ {total_patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

if not df_carteira_show.empty:
    with col_p2:
        st.dataframe(
            df_carteira_show,
            column_config={
                "NOME_EXIBICAO": st.column_config.TextColumn("Ativo"),
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
    df_t = pd.DataFrame([vals], columns=['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'])
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

# 3. RADAR
st.subheader("🎯 Radar de Oportunidades")
if not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "NOME_FINAL": st.column_config.TextColumn("Ativo"),
            "PRECO_NUM": st.column_config.NumberColumn("Cotação", format="R$ %.2f"),
            "TETO_NUM": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "MARGEM_PCT": st.column_config.NumberColumn("Margem (%)", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
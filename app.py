import streamlit as st
import pandas as pd
import yfinance as yf
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS REFINADO ---
st.markdown("""
    <style>
        .main {background-color: #f8fafc;}
        h1, h2, h3 {font-family: 'Helvetica Neue', sans-serif; color: #0f172a; font-weight: 600;}
        
        /* Cards de Métricas */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        /* Texto dos cards */
        div[data-testid="stMetricLabel"] p {color: #64748b !important; font-size: 0.85rem !important;}
        div[data-testid="stMetricValue"] div {color: #0f172a !important;}

        /* Tabelas Clean */
        div[data-testid="stDataFrame"] {
            background-color: white;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    """Limpa formatação de moeda R$"""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=600)
def get_market_indices():
    """Busca índices de mercado (com tratamento de erro individual)"""
    indices = {'IBOV': 0, 'S&P 500': 0, 'Dólar': 0, 'Bitcoin': 0}
    try:
        # Tenta pegar tudo de uma vez
        tickers = ['^BVSP', '^GSPC', 'BRL=X', 'BTC-USD']
        data = yf.download(tickers, period="1d", progress=False)['Close'].iloc[-1]
        indices['IBOV'] = data.get('^BVSP', 0)
        indices['S&P 500'] = data.get('^GSPC', 0)
        indices['Dólar'] = data.get('BRL=X', 0)
        indices['Bitcoin'] = data.get('BTC-USD', 0)
    except:
        pass
    return indices

def get_logo_url(ticker):
    """Tenta buscar a logo real da empresa baseada no Ticker"""
    if not isinstance(ticker, str): return ""
    clean_ticker = ticker.upper().replace('.SA', '').strip()
    # Repositório público de logos (Brasileiro e US)
    return f"https://raw.githubusercontent.com/thefintz/icon-project/master/stock_logos/{clean_ticker}.png"

# --- HEADER ---
st.title("✨ Aura Finance")

# Índices
idx = get_market_indices()
c1, c2, c3, c4 = st.columns(4)
c1.metric("🇧🇷 IBOVESPA", f"{idx['IBOV']:,.0f} pts")
c2.metric("🇺🇸 S&P 500", f"{idx['S&P 500']:,.0f} pts")
c3.metric("💵 DÓLAR", f"R$ {idx['Dólar']:.2f}")
c4.metric("₿ BITCOIN", f"US$ {idx['Bitcoin']:,.0f}")

st.divider()

# --- UPLOAD ---
with st.sidebar:
    st.header("Dados")
    uploaded_file = st.file_uploader("Arquivo Excel (.xlsx)", type=['xlsx'])

if not uploaded_file:
    st.info("👆 Por favor, carregue sua planilha para visualizar o dashboard.")
    st.stop()

# --- PROCESSAMENTO INTELIGENTE ---
xls = pd.ExcelFile(uploaded_file)

# 1. PREPARAÇÃO DO VALUATION (Necessário para nomes e logos)
try:
    df_val = pd.read_excel(xls, 'Valuation')
    
    # Identificar colunas
    cols = df_val.columns
    c_ticker = [c for c in cols if 'TICKER' in c.upper()][0]
    c_empresa = [c for c in cols if 'EMPRESA' in c.upper()][0]
    c_preco = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
    c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]

    # Processamento
    df_val['TICKER_CLEAN'] = df_val[c_ticker].astype(str).str.strip()
    df_val['PRECO_NUM'] = df_val[c_preco].apply(clean_currency)
    df_val['TETO_NUM'] = df_val[c_teto].apply(clean_currency)
    
    # FÓRMULA SOLICITADA: ((Teto - Preço) / Preço) * 100
    # O Streamlit Progress Bar aceita de 0.0 a 1.0 (então dividimos por 100 visualmente depois)
    df_val['MARGEM_REAL'] = (df_val['TETO_NUM'] - df_val['PRECO_NUM']) / df_val['PRECO_NUM']
    
    # Logo URL
    df_val['LOGO_URL'] = df_val['TICKER_CLEAN'].apply(get_logo_url)

    # Tabela Final Valuation
    df_radar = df_val[[c_empresa, 'LOGO_URL', 'PRECO_NUM', 'TETO_NUM', 'MARGEM_REAL']].copy()
    df_radar = df_radar.sort_values('MARGEM_REAL', ascending=False)

except Exception as e:
    st.error(f"Erro ao processar Valuation: {e}")
    df_radar = pd.DataFrame()

# 2. CARTEIRA (Com logo e nomes)
try:
    df_cart = pd.read_excel(xls, 'Carteira')
    c_ativo_c = [c for c in df_cart.columns if 'ATIVO' in c.upper()][0]
    c_qtd_c = [c for c in df_cart.columns if 'QUANTIDADE' in c.upper()][0]
    c_saldo_c = [c for c in df_cart.columns if 'SALDO' in c.upper() and 'TOTAL' not in c.upper()][0]
    
    # Limpeza básica
    df_cart['TICKER_C'] = df_cart[c_ativo_c].astype(str).apply(lambda x: x.split('\n')[0].strip())
    df_cart['SALDO_C'] = df_cart[c_saldo_c].apply(clean_currency)
    df_cart['QTD_C'] = df_cart[c_qtd_c].apply(clean_currency)
    
    # Cruzar com Valuation para pegar Nome Completo e Logo
    # Se não tiver no valuation, usa o próprio ticker
    if not df_radar.empty:
        # Cria dicionários de referência
        dict_nomes = pd.Series(df_val[c_empresa].values, index=df_val['TICKER_CLEAN']).to_dict()
        dict_logos = pd.Series(df_val['LOGO_URL'].values, index=df_val['TICKER_CLEAN']).to_dict()
        
        df_cart['NOME_FINAL'] = df_cart['TICKER_C'].map(dict_nomes).fillna(df_cart['TICKER_C'])
        df_cart['LOGO_FINAL'] = df_cart['TICKER_C'].map(dict_logos).fillna("")
    else:
        df_cart['NOME_FINAL'] = df_cart['TICKER_C']
        df_cart['LOGO_FINAL'] = ""

    df_cart_show = df_cart[['LOGO_FINAL', 'NOME_FINAL', 'QTD_C', 'SALDO_C']].sort_values('SALDO_C', ascending=False)
    patrimonio = df_cart['SALDO_C'].sum()

except Exception as e:
    st.error(f"Erro na Carteira: {e}")
    patrimonio = 0
    df_cart_show = pd.DataFrame()

# 3. PROVENTOS (Anos Dinâmicos)
try:
    df_prov = pd.read_excel(xls, 'Proventos')
    
    # Encontrar todas as linhas que começam com "Proventos 20.."
    col_ref = df_prov.iloc[:, 0].astype(str)
    linhas_anos = df_prov[col_ref.str.contains("Proventos 20", na=False)]
    
    dados_anos = {}
    anos_disponiveis = []

    # Processar cada ano encontrado
    for idx, row in linhas_anos.iterrows():
        nome_linha = row.iloc[0] # Ex: "Proventos 2025"
        ano = re.findall(r'20\d{2}', nome_linha) # Extrai "2025"
        if ano:
            ano_str = ano[0]
            anos_disponiveis.append(ano_str)
            valores = row.iloc[1:13].apply(clean_currency).values
            dados_anos[ano_str] = valores

    # Adicionar 2026 manualmente se não existir, para garantir
    if '2026' not in anos_disponiveis:
        anos_disponiveis.append('2026')
        dados_anos['2026'] = [0.0] * 12
        
    anos_disponiveis = sorted(list(set(anos_disponiveis))) # Remove duplicatas e ordena

except Exception as e:
    st.error(f"Erro nos Proventos: {e}")
    anos_disponiveis = ['2026']
    dados_anos = {'2026': [0.0]*12}


# --- VISUALIZAÇÃO ---

# SEÇÃO 1: PATRIMÔNIO E CARTEIRA
col_patr, col_sel_ano = st.columns([3, 1])
col_patr.metric("💰 Patrimônio Total Investido", f"R$ {patrimonio:,.2f}")

st.markdown("### 🏢 Minha Carteira")
if not df_cart_show.empty:
    st.dataframe(
        df_cart_show,
        column_config={
            "LOGO_FINAL": st.column_config.ImageColumn("", width="small"), # Título vazio para colar no nome
            "NOME_FINAL": st.column_config.TextColumn("Ativo"),
            "QTD_C": st.column_config.NumberColumn("Qtd", format="%.0f"),
            "SALDO_C": st.column_config.NumberColumn("Saldo Atual", format="R$ %.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

# SEÇÃO 2: PROVENTOS (SELETOR DE ANO)
c_head1, c_head2 = st.columns([3, 1])
c_head1.markdown("### 📅 Calendário de Recebimentos")

# Seletor de Ano
ano_selecionado = c_head2.selectbox("Ano", anos_disponiveis, index=len(anos_disponiveis)-1) # Seleciona o último por padrão

# Montar tabela do ano selecionado
vals_ano = dados_anos.get(ano_selecionado, [0.0]*12)
df_display_prov = pd.DataFrame([vals_ano], columns=['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'])
total_ano = sum(vals_ano)

st.dataframe(
    df_display_prov,
    column_config={k: st.column_config.NumberColumn(format="R$ %.2f") for k in df_display_prov.columns},
    hide_index=True,
    use_container_width=True
)
st.caption(f"Total acumulado em {ano_selecionado}: **R$ {total_ano:,.2f}**")

st.divider()

# SEÇÃO 3: RADAR (VALUATION)
st.markdown("### 🎯 Radar de Oportunidades")

if not df_radar.empty:
    st.dataframe(
        df_radar,
        column_config={
            "LOGO_URL": st.column_config.ImageColumn("", width="small"),
            "EMPRESA": st.column_config.TextColumn("Empresa"),
            "PRECO_NUM": st.column_config.NumberColumn("Cotação", format="R$ %.2f"),
            "TETO_NUM": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "MARGEM_REAL": st.column_config.ProgressColumn(
                "Margem (%)",
                format="%.1f%%",
                min_value=-0.5,
                max_value=1.0, # Ajuste conforme necessário
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=600
    )
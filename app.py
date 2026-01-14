import streamlit as st
import pandas as pd
import yfinance as yf

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS REFINADO (CONTRASTE E VISUAL) ---
st.markdown("""
    <style>
        /* Fundo Geral */
        .main {background-color: #f8fafc;}
        
        /* Ajuste de Fontes */
        h1, h2, h3 {font-family: 'Helvetica Neue', sans-serif; color: #0f172a; font-weight: 600;}
        p {color: #475569;}
        
        /* CARDS (Métricas de Mercado) */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        /* Forçar cor preta nos labels e valores (Correção do Bug) */
        div[data-testid="stMetricLabel"] p {color: #64748b !important; font-size: 0.9rem !important; font-weight: 600;}
        div[data-testid="stMetricValue"] div {color: #0f172a !important; font-size: 1.4rem !important;}

        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: white;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            padding: 10px;
        }
        
        /* Imagens/Logos nas tabelas */
        img {border-radius: 50%;}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=600)
def get_market_indices():
    # Busca segura e individual para não quebrar tudo se um falhar
    indices = {'IBOV': 0, 'S&P 500': 0, 'Dólar': 0, 'Bitcoin': 0}
    
    def get_single_ticker(ticker):
        try:
            return yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
        except:
            return 0

    indices['IBOV'] = get_single_ticker('^BVSP')
    indices['S&P 500'] = get_single_ticker('^GSPC')
    indices['Dólar'] = get_single_ticker('BRL=X')
    indices['Bitcoin'] = get_single_ticker('BTC-USD')
    
    return indices

def get_logo_url(ticker):
    # Tenta buscar logo num repositório público usando o ticker (sem o número final as vezes ajuda, mas vamos testar direto)
    # Fallback para um serviço de logos genérico
    clean_ticker = str(ticker).replace('.SA', '').strip()
    return f"https://raw.githubusercontent.com/thefintz/icon-project/master/stock_logos/{clean_ticker}.png"

# --- HEADER: ÍNDICES (AGORA VISÍVEIS) ---
st.title("✨ Aura Finance")
st.caption("Intelligence Dashboard")

indices = get_market_indices()

# Layout em 4 colunas fixas
c1, c2, c3, c4 = st.columns(4)
c1.metric("🇧🇷 IBOVESPA", f"{indices['IBOV']:,.0f} pts")
c2.metric("🇺🇸 S&P 500", f"{indices['S&P 500']:,.0f} pts")
c3.metric("💵 DÓLAR", f"R$ {indices['Dólar']:.2f}")
c4.metric("₿ BITCOIN", f"US$ {indices['Bitcoin']:,.0f}")

st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Upload de Dados")
    uploaded_file = st.file_uploader("Arquivo Excel (.xlsx)", type=['xlsx'])

if not uploaded_file:
    st.info("👆 Arraste sua planilha para começar.")
    st.stop()

# --- PROCESSAMENTO ---
xls = pd.ExcelFile(uploaded_file)

# 1. VALUATION (Precisamos dele primeiro para pegar os nomes das empresas)
try:
    df_val = pd.read_excel(xls, 'Valuation')
    
    # Mapeamento de Ticker -> Nome da Empresa
    # Procura colunas
    c_ticker_v = [c for c in df_val.columns if 'TICKER' in c.upper()][0]
    c_empresa_v = [c for c in df_val.columns if 'EMPRESA' in c.upper()][0]
    c_cotacao_v = [c for c in df_val.columns if 'COTAÇÃO' in c.upper()][0]
    c_bazin_v = [c for c in df_val.columns if 'BAZIN' in c.upper()][0]

    # Dicionário para traduzir ticker em nome
    mapa_nomes = pd.Series(df_val[c_empresa_v].values, index=df_val[c_ticker_v]).to_dict()

    # Processar Valuation
    df_val['PRECO'] = df_val[c_cotacao_v].apply(clean_currency)
    df_val['TETO'] = df_val[c_bazin_v].apply(clean_currency)
    
    # FÓRMULA CORRIGIDA: (Teto / Preço) - 1
    df_val['MARGEM'] = (df_val['TETO'] / df_val['PRECO']) - 1
    
    # Imagem (Logo)
    # Como não temos coluna de logo, vamos usar uma coluna de imagem gerada pelo Streamlit depois
    # mas aqui preparamos os dados
    df_val['LOGO'] = df_val[c_ticker_v].apply(lambda x: f"https://ui-avatars.com/api/?name={x}&background=0D8ABC&color=fff&size=128&bold=true") 
    
    val_final = df_val[[c_empresa_v, 'PRECO', 'TETO', 'MARGEM', 'LOGO']].copy()
    val_final = val_final.sort_values('MARGEM', ascending=False)
    
except Exception as e:
    st.error(f"Erro no Valuation: {e}")
    val_final = pd.DataFrame()
    mapa_nomes = {}

# 2. CARTEIRA
try:
    df_cart = pd.read_excel(xls, 'Carteira')
    c_ativo_c = [c for c in df_cart.columns if 'ATIVO' in c.upper()][0]
    c_qtd_c = [c for c in df_cart.columns if 'QUANTIDADE' in c.upper()][0]
    c_saldo_c = [c for c in df_cart.columns if 'SALDO' in c.upper() and 'TOTAL' not in c.upper()][0]

    # Limpeza
    df_cart['TICKER_LIMPO'] = df_cart[c_ativo_c].astype(str).apply(lambda x: x.split('\n')[0].strip())
    
    # Tenta pegar o nome completo do mapa. Se não tiver, usa o Ticker mesmo.
    df_cart['NOME_FINAL'] = df_cart['TICKER_LIMPO'].map(mapa_nomes).fillna(df_cart['TICKER_LIMPO'])
    
    df_cart['SALDO_REAL'] = df_cart[c_saldo_c].apply(clean_currency)
    df_cart['QTD_REAL'] = df_cart[c_qtd_c].apply(clean_currency)
    df_cart['PRECO_MEDIO'] = df_cart['SALDO_REAL'] / df_cart['QTD_REAL']
    
    cart_final = df_cart[['NOME_FINAL', 'QTD_REAL', 'PRECO_MEDIO', 'SALDO_REAL']].copy()
    cart_final = cart_final.sort_values('SALDO_REAL', ascending=False)
    
    patrimonio = df_cart['SALDO_REAL'].sum()
except Exception as e:
    st.error(f"Erro na Carteira: {e}")
    patrimonio = 0
    cart_final = pd.DataFrame()

# 3. PROVENTOS
try:
    df_prov = pd.read_excel(xls, 'Proventos')
    # Lógica para pegar 2025
    row_2025 = df_prov[df_prov.iloc[:, 0].astype(str).str.contains("2025", na=False)].iloc[0]
    vals = row_2025[1:13].apply(clean_currency).values
    total_prov = vals.sum()
    
    # Tabela formatada
    meses_nomes = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    df_prov_display = pd.DataFrame([vals], columns=meses_nomes)
    
except:
    total_prov = 0
    df_prov_display = pd.DataFrame()

# --- DASHBOARD VISUAL ---

# SEÇÃO 1: RESUMO
col_kpi1, col_kpi2 = st.columns(2)
col_kpi1.metric("💰 Patrimônio Total", f"R$ {patrimonio:,.2f}")
col_kpi2.metric("📅 Proventos 2025 (Estimado)", f"R$ {total_prov:,.2f}")

st.markdown("### 🏢 Minha Carteira")
if not cart_final.empty:
    st.dataframe(
        cart_final,
        column_config={
            "NOME_FINAL": st.column_config.TextColumn("Empresa / Ativo"),
            "QTD_REAL": st.column_config.NumberColumn("Qtd", format="%.0f"),
            "PRECO_MEDIO": st.column_config.NumberColumn("Preço Médio", format="R$ %.2f"),
            "SALDO_REAL": st.column_config.NumberColumn("Saldo Total", format="R$ %.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

# SEÇÃO 2: CALENDÁRIO DE DIVIDENDOS
st.markdown("### 🗓️ Calendário de Recebimentos")
if not df_prov_display.empty:
    # Mostra como uma tabela horizontal clean
    st.dataframe(
        df_prov_display,
        hide_index=True,
        use_container_width=True
    )

st.divider()

# SEÇÃO 3: RADAR (BAZIN)
st.markdown("### 🎯 Radar de Oportunidades")
st.caption("Margem calculada como: (Preço Teto / Cotação Atual) - 1")

if not val_final.empty:
    st.dataframe(
        val_final,
        column_config={
            "LOGO": st.column_config.ImageColumn("Logo", width="small"),
            "EMPRESA": st.column_config.TextColumn("Empresa"),
            "PRECO": st.column_config.NumberColumn("Preço Atual", format="R$ %.2f"),
            "TETO": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "MARGEM": st.column_config.ProgressColumn(
                "Margem de Segurança (%)",
                format="%.1f%%",
                min_value=-0.5, # Define limites para a barra ficar vermelha/verde
                max_value=1.0,
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=600 # Altura maior para ver tudo
    )
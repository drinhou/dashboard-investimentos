import streamlit as st
import pandas as pd
import yfinance as yf
import re

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Minimalista e Limpo
st.markdown("""
    <style>
        .main {background-color: #f8fafc;}
        h1, h2, h3, p {font-family: 'Segoe UI', Helvetica, sans-serif; color: #1e293b;}
        
        /* Cards de Índices */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: #ffffff;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    """Limpa formatação financeira e retorna float."""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        # Remove R$, espaços e converte
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=300)
def get_market_data():
    """Busca índices (Falha silenciosa para não mostrar erro)."""
    indices = {'IBOV': None, 'S&P 500': None, 'Dólar': None, 'Bitcoin': None}
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

def format_asset_name(nome_planilha, ticker, classe):
    """Formata o nome conforme solicitado: Nome (TICKER)"""
    ticker_str = str(ticker).replace('.SA', '').strip()
    nome_str = str(nome_planilha).strip()
    
    # Se o nome estiver vazio, usa o ticker
    if not nome_str or nome_str == 'nan':
        return ticker_str

    # Lógica de formatação
    classe_str = str(classe).lower()
    
    if "cripto" in classe_str:
        return f"{nome_str} ({ticker_str})"
    elif "renda fixa" in classe_str or "tesouro" in classe_str:
        return nome_str
    else:
        # Ações e FIIs
        return f"{nome_str} ({ticker_str})"

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
    st.header("📂 Dados")
    uploaded_file = st.file_uploader("Arraste sua planilha aqui", type=['xlsx'])

if not uploaded_file:
    st.info("👆 Aguardando planilha...")
    st.stop()

xls = pd.ExcelFile(uploaded_file)

# --- 1. PREPARAÇÃO DO VALUATION (Dicionário de Nomes) ---
mapa_nomes = {}
df_radar = pd.DataFrame()

try:
    df_val = pd.read_excel(xls, 'Valuation').fillna(0) # Preenche vazios com 0 para não quebrar
    
    # Identificar colunas
    cols = df_val.columns
    c_ticker = [c for c in cols if 'TICKER' in c.upper()][0]
    c_empresa = [c for c in cols if 'EMPRESA' in c.upper()][0]
    c_cotacao = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
    c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]

    # Criar dicionário {TICKER: NOME EMPRESA} para usar na carteira
    for index, row in df_val.iterrows():
        t = str(row[c_ticker]).strip()
        n = str(row[c_empresa]).strip()
        if t and n:
            mapa_nomes[t] = n

    # Cálculos Valuation
    df_val['TICKER_CLEAN'] = df_val[c_ticker].astype(str).str.strip()
    df_val['PRECO_NUM'] = df_val[c_cotacao].apply(clean_currency)
    df_val['TETO_NUM'] = df_val[c_teto].apply(clean_currency)
    
    # FÓRMULA CORRIGIDA: ((Teto - Preço) / Preço) * 100 -> Ex: 44.5
    # Evita divisão por zero
    df_val['MARGEM_PCT'] = df_val.apply(
        lambda x: ((x['TETO_NUM'] - x['PRECO_NUM']) / x['PRECO_NUM']) * 100 if x['PRECO_NUM'] > 0 else 0, axis=1
    )
    
    # Formatar Nome (Ticker) para o Valuation também
    df_val['NOME_FINAL'] = df_val.apply(lambda x: f"{x[c_empresa]} ({x['TICKER_CLEAN']})", axis=1)

    df_radar = df_val[['NOME_FINAL', 'PRECO_NUM', 'TETO_NUM', 'MARGEM_PCT']].copy()
    df_radar = df_radar.sort_values('MARGEM_PCT', ascending=False)
except Exception as e:
    st.error(f"Erro no processamento do Valuation: {e}")

# --- 2. CARTEIRA ---
try:
    df_cart = pd.read_excel(xls, 'Carteira').fillna(0)
    c_ativo = [c for c in df_cart.columns if 'ATIVO' in c.upper()][0]
    c_qtd = [c for c in df_cart.columns if 'QUANTIDADE' in c.upper()][0]
    c_saldo = [c for c in df_cart.columns if 'SALDO' in c.upper() and 'TOTAL' not in c.upper()][0]
    # Tenta achar classe, se não tiver, cria vazia
    c_classe_lista = [c for c in df_cart.columns if 'CLASSE' in c.upper()]
    c_classe = c_classe_lista[0] if c_classe_lista else None

    # Limpeza
    df_cart['TICKER_CLEAN'] = df_cart[c_ativo].astype(str).apply(lambda x: x.split('\n')[0].strip())
    df_cart['QTD_NUM'] = df_cart[c_qtd].apply(clean_currency)
    df_cart['SALDO_NUM'] = df_cart[c_saldo].apply(clean_currency)
    
    # Mapeamento de Nomes
    def resolver_nome(row):
        ticker = row['TICKER_CLEAN']
        # Tenta pegar a classe se existir
        classe = str(row[c_classe]) if c_classe else ""
        
        # Tenta achar o nome completo no dicionário do Valuation
        nome_empresa = mapa_nomes.get(ticker, "")
        
        # Se não achou no valuation, usa o próprio ticker como nome provisório
        if not nome_empresa:
            nome_empresa = ticker
            
        return format_asset_name(nome_empresa, ticker, classe)

    df_cart['NOME_EXIBICAO'] = df_cart.apply(resolver_nome, axis=1)

    df_carteira_show = df_cart[['NOME_EXIBICAO', 'QTD_NUM', 'SALDO_NUM']].copy()
    
    # Remove linhas onde o Saldo é 0 ou vazio (Opcional, se quiser ver tudo comente a linha abaixo)
    df_carteira_show = df_carteira_show[df_carteira_show['SALDO_NUM'] > 0]
    
    df_carteira_show = df_carteira_show.sort_values('SALDO_NUM', ascending=False)
    total_patrimonio = df_cart['SALDO_NUM'].sum()
except Exception as e:
    st.error(f"Erro na Carteira: {e}")
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
                "NOME_EXIBICAO": st.column_config.TextColumn("Ativo / Empresa"),
                "QTD_NUM": st.column_config.NumberColumn("Quantidade", format="%.0f"),
                "SALDO_NUM": st.column_config.NumberColumn("Saldo Atual", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )

st.divider()

# 2. PROVENTOS
st.subheader("💰 Proventos Recebidos")
tab24, tab25, tab26 = st.tabs(["2024", "2025", "2026"])

def render_prov_tab(ano):
    vals = dados_anos.get(ano, [0.0]*12)
    meses = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
    df_tab = pd.DataFrame([vals], columns=meses)
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
            "NOME_FINAL": st.column_config.TextColumn("Empresa (Ticker)"),
            "PRECO_NUM": st.column_config.NumberColumn("Cotação", format="R$ %.2f"),
            "TETO_NUM": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "MARGEM_PCT": st.column_config.NumberColumn(
                "Margem de Segurança (%)",
                format="%.2f %%" # Mostra 44.50 %
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
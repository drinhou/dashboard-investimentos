import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

# --- CONFIGURAÇÃO VISUAL (PRETO NO BRANCO / ALTO CONTRASTE) ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS FORÇADO (Sem Branco no Branco)
st.markdown("""
    <style>
        .stApp {background-color: #f8fafc;}
        h1, h2, h3, h4, h5, p, span, div, label, li {color: #0f172a !important; font-family: 'Segoe UI', sans-serif;}
        
        /* Cards */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-radius: 8px;
        }
        div[data-testid="stMetricLabel"] p {color: #64748b !important;}
        div[data-testid="stMetricValue"] div {color: #0f172a !important; font-weight: 700;}
        
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
        }
        
        /* Inputs */
        .stTextInput input {color: #000 !important;}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---

def clean_currency(x):
    """Limpa R$, % e converte para float."""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=300)
def get_market_data():
    """Busca índices de mercado (Yahoo Finance)."""
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

# --- LISTA DE NOMES CONHECIDOS (CORREÇÃO KNCA11 ETC) ---
KNOWN_NAMES = {
    'KNCA11': 'Kinea Rendimentos',
    'MXRF11': 'Maxi Renda',
    'HGLG11': 'CSHG Logística',
    'XPLG11': 'XP Log',
    'VISC11': 'Vinci Shopping',
    'BBAS3': 'Banco do Brasil',
    'BBSE3': 'BB Seguridade',
    'TAEE11': 'Taesa',
    'VALE3': 'Vale',
    'PETR4': 'Petrobras',
    'WEGE3': 'WEG',
    'ITUB4': 'Itaú Unibanco',
    'BTC': 'Bitcoin',
    'ETH': 'Ethereum',
    'USDT': 'Tether'
}

@st.cache_data(ttl=86400)
def get_name_online(ticker):
    """Busca nome se não estiver na lista VIP."""
    clean = str(ticker).replace('.SA', '').strip().upper()
    if clean in KNOWN_NAMES: return KNOWN_NAMES[clean]
    
    try:
        t = yf.Ticker(f"{clean}.SA")
        info = t.info
        name = info.get('shortName') or info.get('longName') or clean
        # Limpa sujeira do nome
        name = name.replace("Fundo De Investimento", "").replace("FII", "").replace("S.A.", "").replace(" - ", "").strip()
        return name
    except:
        return clean

def format_nice_name(ticker, nome_excel=None):
    """Retorna formato: Nome Bonito (TICKER)"""
    clean_ticker = str(ticker).strip().upper().replace(".SA", "")
    
    # 1. Tenta usar o nome que veio do Excel (Valuation)
    final_name = nome_excel
    
    # 2. Se não tiver, busca na lista VIP ou Online
    if not final_name or final_name == 'nan' or final_name == '0':
        final_name = get_name_online(clean_ticker)
        
    return f"{final_name} ({clean_ticker})"


# --- ROBÔ INVESTIDOR 10 ---
@st.cache_data(ttl=600)
def scrape_investidor10(url):
    """Acessa o site e extrai a tabela de ativos."""
    # Headers fingem ser um navegador real para não ser bloqueado
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None, f"Erro de conexão (Status {response.status_code})"
        
        # Tenta ler todas as tabelas da página
        tables = pd.read_html(response.content, decimal=',', thousands='.')
        
        df_final = pd.DataFrame()
        
        # Procura a tabela certa (que tem Ativo e Saldo)
        for table in tables:
            cols_upper = [str(c).upper() for c in table.columns]
            # Verifica colunas chaves
            if any("ATIVO" in c for c in cols_upper) and (any("SALDO" in c for c in cols_upper) or any("TOTAL" in c for c in cols_upper)):
                df_final = table
                break
        
        if df_final.empty:
            return None, "Tabela de ativos não encontrada no link."

        # Padronizar nomes das colunas
        rename_map = {}
        for c in df_final.columns:
            cup = c.upper()
            if "ATIVO" in cup: rename_map[c] = "TICKER"
            elif "QUANTIDADE" in cup: rename_map[c] = "QTD"
            elif "COTAÇÃO" in cup or "PREÇO ATUAL" in cup: rename_map[c] = "PRECO"
            elif "SALDO" in cup or "VALOR" in cup: rename_map[c] = "SALDO"
            
        df_final = df_final.rename(columns=rename_map)
        
        # Limpeza do Ticker (Site as vezes traz nome junto)
        if 'TICKER' in df_final.columns:
            df_final['TICKER'] = df_final['TICKER'].astype(str).apply(lambda x: x.split(' ')[0].split('\n')[0].strip())
            
        return df_final, None

    except Exception as e:
        return None, f"Erro ao ler site: {e}"

# --- APP ---
st.title("🦅 Aura Finance")

# Header
idx = get_market_data()
c1, c2, c3, c4 = st.columns(4)
def show_metric(col, label, val, prefix="", suffix=""):
    if val: col.metric(label, f"{prefix} {val:,.2f} {suffix}".replace(",", "X").replace(".", ",").replace("X", "."))
    else: col.metric(label, "---")

show_metric(c1, "IBOVESPA", idx['IBOV'], "", "pts")
show_metric(c2, "S&P 500", idx['S&P 500'], "", "pts")
show_metric(c3, "DÓLAR", idx['Dólar'], "R$")
show_metric(c4, "BITCOIN", idx['Bitcoin'], "US$")

st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔗 Conexão")
    st.caption("Puxando dados automaticamente de:")
    # URL Padrão Definida
    url_default = "https://investidor10.com.br/wallet/public/2194871"
    url_input = st.text_input("Link Investidor10", value=url_default)
    
    st.divider()
    st.header("📊 Valuation")
    uploaded_file = st.file_uploader("Preços Teto (.xlsx)", type=['xlsx'])
    st.caption("Envie o Excel se quiser calcular o Radar Bazin.")
    
    if st.button("🔄 Atualizar Agora"):
        st.cache_data.clear()
        st.rerun()

# --- LÓGICA PRINCIPAL ---

# 1. WEB SCRAPING
with st.spinner("Conectando ao Investidor10..."):
    df_web, erro = scrape_investidor10(url_input)

if erro:
    st.error(f"⚠️ {erro}")
    st.info("O site pode ter bloqueado o acesso temporariamente. Tente novamente em alguns minutos.")
    st.stop()

# 2. PROCESSAR DADOS DO EXCEL (SE TIVER)
mapa_teto = {}
mapa_nomes_excel = {}

if uploaded_file:
    try:
        df_excel = pd.read_excel(uploaded_file, 'Valuation').fillna(0)
        cols = df_excel.columns
        # Acha as colunas dinamicamente
        c_tick = [c for c in cols if 'TICKER' in c.upper()][0]
        c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]
        c_emp = [c for c in cols if 'EMPRESA' in c.upper()]
        
        col_nome_emp = c_emp[0] if c_emp else None
        
        for _, row in df_excel.iterrows():
            tk = str(row[c_tick]).strip().upper()
            mapa_teto[tk] = clean_currency(row[c_teto])
            if col_nome_emp:
                mapa_nomes_excel[tk] = str(row[col_nome_emp]).strip()
    except:
        pass # Se der erro no excel, segue sem valuation

# 3. UNIFICAR DADOS
master_list = []

try:
    # Garante que as colunas sejam numeros
    df_web['QTD_NUM'] = df_web['QTD'].apply(clean_currency)
    df_web['SALDO_NUM'] = df_web['SALDO'].apply(clean_currency)
    
    # Tenta pegar preço do site ou calcula
    if 'PRECO' in df_web.columns:
        df_web['PRECO_NUM'] = df_web['PRECO'].apply(clean_currency)
    else:
        df_web['PRECO_NUM'] = df_web['SALDO_NUM'] / df_web['QTD_NUM']

    for _, row in df_web.iterrows():
        ticker = str(row['TICKER']).strip().upper()
        
        # Pega dados do Excel
        teto = mapa_teto.get(ticker, 0.0)
        nome_excel = mapa_nomes_excel.get(ticker, None)
        
        # Gera nome bonito
        display_name = format_nice_name(ticker, nome_excel)
        
        # Calcula Margem: ((Teto - Preço) / Preço) * 100
        preco = row['PRECO_NUM']
        if preco > 0 and teto > 0:
            margem = ((teto - preco) / preco) * 100
        else:
            margem = -999 # Joga pro fim da fila
            
        master_list.append({
            'NOME': display_name,
            'TICKER': ticker,
            'QTD': row['QTD_NUM'],
            'SALDO': row['SALDO_NUM'],
            'PRECO': preco,
            'TETO': teto,
            'MARGEM': margem
        })

    df_master = pd.DataFrame(master_list)
    
    # Separação Views
    df_carteira = df_master[['NOME', 'QTD', 'SALDO']].copy()
    df_carteira = df_carteira.sort_values('SALDO', ascending=False)
    
    # Filtra Radar (Só o que tem teto > 0)
    df_radar = df_master[df_master['TETO'] > 0][['NOME', 'PRECO', 'TETO', 'MARGEM']].copy()
    df_radar = df_radar.sort_values('MARGEM', ascending=False)
    
    patrimonio = df_master['SALDO'].sum()

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")
    st.stop()


# --- DISPLAY ---

# 1. CARTEIRA (WEB)
st.subheader("🏦 Minha Carteira (Online)")
col_a, col_b = st.columns([1, 3])
col_a.metric("Patrimônio Total", f"R$ {patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col_b:
    st.dataframe(
        df_carteira,
        column_config={
            "NOME": st.column_config.TextColumn("Ativo"),
            "QTD": st.column_config.NumberColumn("Quantidade", format="%.0f"),
            "SALDO": st.column_config.NumberColumn("Saldo Atual", format="R$ %.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

# 2. RADAR (HÍBRIDO)
st.subheader("🎯 Radar de Oportunidades")

if uploaded_file is None:
    st.warning("⚠️ Faça upload do Excel 'Valuation' para habilitar o Radar.")
elif df_radar.empty:
    st.info("Nenhum ativo da carteira online foi encontrado na sua planilha de Valuation.")
else:
    st.dataframe(
        df_radar,
        column_config={
            "NOME": st.column_config.TextColumn("Ativo"),
            "PRECO": st.column_config.NumberColumn("Cotação", format="R$ %.2f"),
            "TETO": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
            "MARGEM": st.column_config.NumberColumn("Margem (%)", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

st.divider()
st.caption(f"Dados sincronizados de: {url_input}")
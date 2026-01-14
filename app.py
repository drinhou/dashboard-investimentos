import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

# --- CONFIGURAÇÃO VISUAL ---
st.set_page_config(
    page_title="Aura Finance",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS CLEAN (Alto Contraste)
st.markdown("""
    <style>
        .stApp {background-color: #f8fafc;}
        h1, h2, h3, h4, h5, p, span, div, label {color: #0f172a !important; font-family: 'Segoe UI', sans-serif;}
        
        /* Cards */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-radius: 8px;
        }
        div[data-testid="stMetricLabel"] p {color: #64748b !important;}
        
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
    """Limpa R$, pontos e vírgulas para número decimal"""
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try: return float(clean)
        except: return 0.0
    return 0.0

@st.cache_data(ttl=300)
def get_market_data():
    """Busca índices de mercado"""
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

# --- ROBÔ INVESTIDOR 10 ---
@st.cache_data(ttl=600) # Cache de 10 min para não bloquear o IP
def scrape_investidor10(url):
    """
    Acessa o link público e tenta extrair a tabela de ativos.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None, f"Erro ao acessar site (Status {response.status_code})"
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # O Investidor10 geralmente tem tabelas com classe 'table' ou dentro de divs específicas
        # Vamos tentar ler todas as tabelas da página
        tables = pd.read_html(response.content)
        
        # Procura a tabela que tem colunas de ativos (Ativo, Quantidade, etc)
        df_carteira = pd.DataFrame()
        
        for table in tables:
            # Verifica se tem colunas típicas de carteira
            cols = [c.upper() for c in table.columns]
            if any("ATIVO" in c for c in cols) and any("QUANTIDADE" in c for c in cols):
                df_carteira = table
                break
        
        if df_carteira.empty:
            return None, "Não encontrei a tabela de ativos no link. O layout do site pode ter mudado."
            
        # Padronizar colunas
        df_carteira.columns = [c.upper().strip() for c in df_carteira.columns]
        
        # Renomear para nosso padrão
        # O site geralmente retorna: Ativo, Cotação, Preço Médio, Rentabilidade, Quantidade, Saldo, %
        rename_map = {}
        for c in df_carteira.columns:
            if "ATIVO" in c: rename_map[c] = "TICKER"
            if "QUANTIDADE" in c: rename_map[c] = "QTD"
            if "SALDO" in c: rename_map[c] = "SALDO"
            if "MÉDIO" in c: rename_map[c] = "PM"
        
        df_carteira = df_carteira.rename(columns=rename_map)
        
        # Limpar dados
        if 'TICKER' in df_carteira.columns:
            # O site as vezes traz "WEGE3\nWEG", pegamos só a primeira parte
            df_carteira['TICKER'] = df_carteira['TICKER'].astype(str).apply(lambda x: x.split(' ')[0].split('\n')[0].strip())
            
        return df_carteira, None
        
    except Exception as e:
        return None, f"Erro no Robô: {e}"

# --- LISTA VIP DE NOMES (CORREÇÃO) ---
KNOWN_FIXES = {
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
    'ETH': 'Ethereum'
}

@st.cache_data(ttl=86400)
def get_name_online(ticker):
    t_clean = str(ticker).replace('.SA', '').strip().upper()
    if t_clean in KNOWN_FIXES: return KNOWN_FIXES[t_clean]
    try:
        t = yf.Ticker(f"{t_clean}.SA")
        return t.info.get('shortName') or t.info.get('longName') or t_clean
    except:
        return t_clean

def format_final_name(ticker, nome_valuation=None):
    """Garante o nome bonito: Nome (TICKER)"""
    ticker_clean = str(ticker).replace('.SA', '').strip().upper()
    
    # 1. Prioridade: Nome que veio do Excel Valuation
    nome = nome_valuation
    
    # 2. Se não tem no Excel, busca na lista VIP ou Online
    if not nome or nome == 'nan':
        nome = get_name_online(ticker_clean)
        
    # Limpeza estética
    nome = str(nome).replace('Fundo De Investimento', '').replace('FII', '').replace('S.A.', '').strip()
    
    return f"{nome} ({ticker_clean})"

# --- APP ---
st.title("🦅 Aura Finance")

# Índices
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

# --- SIDEBAR: ENTRADAS ---
with st.sidebar:
    st.header("⚙️ Configuração")
    
    st.subheader("1. Conexão Automática")
    url_investidor10 = st.text_input("Link Público Investidor10", value="https://investidor10.com.br/wallet/public/2194871")
    
    st.subheader("2. Inteligência (Excel)")
    uploaded_file = st.file_uploader("Arquivo Valuation (.xlsx)", type=['xlsx'])
    
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()

# --- LÓGICA PRINCIPAL ---

if not url_investidor10:
    st.info("👆 Cole o link da sua carteira pública no menu lateral.")
    st.stop()

# 1. ROBÔ: Puxar Carteira
with st.spinner("🤖 O robô está acessando o Investidor10..."):
    df_carteira_web, erro_web = scrape_investidor10(url_investidor10)

if erro_web:
    st.error(f"Falha na conexão: {erro_web}")
    st.stop()

# 2. EXCEL: Puxar Valuation (Se disponível)
df_radar = pd.DataFrame()
mapa_nomes_val = {}
mapa_teto = {}

if uploaded_file:
    try:
        df_val = pd.read_excel(uploaded_file, 'Valuation').fillna(0)
        
        # Mapear colunas
        cols = df_val.columns
        c_tick = [c for c in cols if 'TICKER' in c.upper()][0]
        c_emp = [c for c in cols if 'EMPRESA' in c.upper()][0]
        c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]
        
        # Criar mapas de referência
        for _, row in df_val.iterrows():
            t = str(row[c_tick]).strip().upper()
            mapa_nomes_val[t] = str(row[c_emp]).strip()
            mapa_teto[t] = clean_currency(row[c_teto])
            
    except Exception as e:
        st.warning(f"Erro ao ler Valuation: {e}. O Radar ficará incompleto.")

# --- PROCESSAMENTO DOS DADOS WEB ---
try:
    # Limpeza dos dados vindos do site
    df_carteira_web['QTD_NUM'] = df_carteira_web['QTD'].apply(clean_currency)
    df_carteira_web['SALDO_NUM'] = df_carteira_web['SALDO'].apply(clean_currency)
    
    # Preço Atual (Derivado do Saldo / Qtd para ser mais preciso, ou usar coluna do site se tiver)
    # Vamos tentar usar a coluna 'COTAÇÃO' do site se existir, senão calcula
    cols_web = [c.upper() for c in df_carteira_web.columns]
    if 'COTAÇÃO' in cols_web:
         df_carteira_web['PRECO_ATUAL'] = df_carteira_web['COTAÇÃO'].apply(clean_currency)
    else:
         df_carteira_web['PRECO_ATUAL'] = df_carteira_web['SALDO_NUM'] / df_carteira_web['QTD_NUM']

    # CRIAÇÃO DO DATAFRAME FINAL
    lista_final = []
    
    for _, row in df_carteira_web.iterrows():
        ticker = str(row['TICKER']).strip().upper()
        qtd = row['QTD_NUM']
        saldo = row['SALDO_NUM']
        preco = row['PRECO_ATUAL']
        
        # Pega dados do Excel (se houver)
        nome_val = mapa_nomes_val.get(ticker, None)
        teto_bazin = mapa_teto.get(ticker, 0.0)
        
        # Formata Nome
        nome_final = format_final_name(ticker, nome_val)
        
        # Calcula Margem
        margem = ((teto_bazin - preco) / preco) * 100 if preco > 0 and teto_bazin > 0 else -100 # -100 se não tiver teto
        
        lista_final.append({
            'ATIVO_NOME': nome_final,
            'TICKER': ticker,
            'QTD': qtd,
            'SALDO': saldo,
            'PRECO': preco,
            'TETO': teto_bazin,
            'MARGEM': margem
        })
        
    df_master = pd.DataFrame(lista_final)
    
    # Separação
    df_carteira_view = df_master[['ATIVO_NOME', 'QTD', 'SALDO']].sort_values('SALDO', ascending=False)
    patrimonio = df_master['SALDO'].sum()
    
    # Radar: Só mostra o que tem Preço Teto definido no Excel (> 0)
    df_radar_view = df_master[df_master['TETO'] > 0][['ATIVO_NOME', 'PRECO', 'TETO', 'MARGEM']].copy()
    df_radar_view = df_radar_view.sort_values('MARGEM', ascending=False)

except Exception as e:
    st.error(f"Erro ao processar dados do site: {e}")
    st.stop()

# --- DASHBOARD ---

# 1. CARTEIRA
st.subheader("🏦 Minha Carteira (Investidor10)")
col_p1, col_p2 = st.columns([1, 3])
col_p1.metric("Patrimônio Total", f"R$ {patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with col_p2:
    st.dataframe(
        df_carteira_view,
        column_config={
            "ATIVO_NOME": st.column_config.TextColumn("Ativo"),
            "QTD": st.column_config.NumberColumn("Quantidade", format="%.0f"),
            "SALDO": st.column_config.NumberColumn("Saldo Atual", format="R$ %.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

# 2. RADAR (CRUZAMENTO WEB + EXCEL)
st.subheader("🎯 Radar de Oportunidades")

if uploaded_file is None:
    st.warning("⚠️ Para ver o Radar Bazin, faça o upload da planilha 'Valuation' na barra lateral.")
elif df_radar_view.empty:
    st.info("Nenhum ativo da sua carteira online foi encontrado na planilha de Valuation com preço teto definido.")
else:
    st.dataframe(
        df_radar_view,
        column_config={
            "ATIVO_NOME": st.column_config.TextColumn("Ativo"),
            "PRECO": st.column_config.NumberColumn("Cotação (Web)", format="R$ %.2f"),
            "TETO": st.column_config.NumberColumn("Preço Teto (Excel)", format="R$ %.2f"),
            "MARGEM": st.column_config.NumberColumn("Margem (%)", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

st.divider()
st.caption("Dados obtidos via Investidor10. Preços Teto via Excel do Usuário.")
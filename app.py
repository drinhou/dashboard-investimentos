import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time

# --- CONFIGURAÇÃO VISUAL (CLEAN & ROBUST) ---
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
        # Remove caracteres invisíveis e R$
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
@st.cache_data(ttl=600) # Cache de 10 min para evitar bloqueio
def scrape_investidor10(url):
    """
    Acessa o link público e extrai a tabela de ativos.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return None, f"Erro ao acessar site (Status {response.status_code})"
        
        # Tenta ler tabelas HTML diretamente
        try:
            tables = pd.read_html(response.content)
        except:
            return None, "Não consegui ler as tabelas do site. O Investidor10 pode ter bloqueado robôs temporariamente."

        # Procura a tabela correta (a que tem 'ATIVO' e 'SALDO')
        df_carteira = pd.DataFrame()
        found = False
        
        for table in tables:
            # Normaliza colunas para maiúsculo para verificar
            cols_upper = [str(c).upper() for c in table.columns]
            if any("ATIVO" in c for c in cols_upper) and any("SALDO" in c for c in cols_upper):
                df_carteira = table
                # Renomeia colunas para nosso padrão
                rename_map = {}
                for idx, col in enumerate(table.columns):
                    c_up = str(col).upper()
                    if "ATIVO" in c_up: rename_map[col] = "TICKER"
                    elif "QUANTIDADE" in c_up: rename_map[col] = "QTD"
                    elif "SALDO" in c_up: rename_map[col] = "SALDO"
                    elif "PREÇO ATUAL" in c_up or "COTAÇÃO" in c_up: rename_map[col] = "PRECO"
                    
                df_carteira = df_carteira.rename(columns=rename_map)
                found = True
                break
        
        if not found or df_carteira.empty:
            return None, "A tabela de ativos não foi encontrada no link fornecido."
            
        # Limpeza básica do Ticker (Site às vezes manda 'WEGE3\nWEG')
        if 'TICKER' in df_carteira.columns:
            df_carteira['TICKER'] = df_carteira['TICKER'].astype(str).apply(lambda x: x.split(' ')[0].split('\n')[0].strip())
            
        return df_carteira, None
        
    except Exception as e:
        return None, f"Erro Técnico no Robô: {e}"

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

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Conexões")
    
    st.subheader("1. Carteira Online")
    url_investidor10 = st.text_input("Link Público Investidor10", value="https://investidor10.com.br/wallet/public/2194871")
    
    st.subheader("2. Preços Teto (Excel)")
    uploaded_file = st.file_uploader("Arquivo Valuation (.xlsx)", type=['xlsx'])
    st.caption("Apenas a aba 'Valuation' será usada.")
    
    if st.button("🔄 Forçar Atualização"):
        st.cache_data.clear()
        st.rerun()

# --- LÓGICA PRINCIPAL ---

if not url_investidor10:
    st.info("👆 Por favor, insira o link da carteira no menu lateral.")
    st.stop()

# 1. ROBÔ: Puxar Carteira
with st.spinner("🤖 Conectando ao Investidor10..."):
    df_web, erro_web = scrape_investidor10(url_investidor10)

if erro_web:
    st.error(f"⚠️ {erro_web}")
    st.info("Dica: Verifique se o link está correto e se a carteira está marcada como 'Pública' nas configurações do site.")
    st.stop()

# 2. EXCEL: Puxar Valuation (Se disponível)
mapa_nomes_val = {}
mapa_teto = {}

if uploaded_file:
    try:
        df_val = pd.read_excel(uploaded_file, 'Valuation').fillna(0)
        cols = df_val.columns
        c_tick = [c for c in cols if 'TICKER' in c.upper()][0]
        c_emp = [c for c in cols if 'EMPRESA' in c.upper()][0]
        c_teto = [c for c in cols if 'BAZIN' in c.upper()][0]
        
        for _, row in df_val.iterrows():
            t = str(row[c_tick]).strip().upper()
            mapa_nomes_val[t] = str(row[c_emp]).strip()
            mapa_teto[t] = clean_currency(row[c_teto])
    except:
        pass

# --- PROCESSAMENTO ---
try:
    # Converter colunas numéricas do site
    df_web['QTD_NUM'] = df_web['QTD'].apply(clean_currency)
    df_web['SALDO_NUM'] = df_web['SALDO'].apply(clean_currency)
    
    # Se o site não der o preço atual limpo, calculamos
    if 'PRECO' in df_web.columns:
        df_web['PRECO_NUM'] = df_web['PRECO'].apply(clean_currency)
    else:
        df_web['PRECO_NUM'] = df_web['SALDO_NUM'] / df_web['QTD_NUM']

    # Montar Lista Final
    lista_final = []
    for _, row in df_web.iterrows():
        ticker = str(row['TICKER']).strip().upper()
        
        # Pega do Excel
        teto = mapa_teto.get(ticker, 0.0)
        nome_val = mapa_nomes_val.get(ticker, None)
        
        # Formata Nome
        nome_display = format_final_name(ticker, nome_val)
        
        # Fórmula Margem: ((Teto - Preço) / Preço) * 100
        # Ex: ((30 - 20) / 20) * 100 = 50%
        if row['PRECO_NUM'] > 0 and teto > 0:
            margem = ((teto - row['PRECO_NUM']) / row['PRECO_NUM']) * 100
        else:
            margem = -999 # Valor simbólico para ordenar no final
            
        lista_final.append({
            'NOME': nome_display,
            'TICKER': ticker,
            'QTD': row['QTD_NUM'],
            'SALDO': row['SALDO_NUM'],
            'PRECO': row['PRECO_NUM'],
            'TETO': teto,
            'MARGEM': margem
        })
        
    df_master = pd.DataFrame(lista_final)
    
    # View 1: Carteira (Do Site)
    df_carteira = df_master[['NOME', 'QTD', 'SALDO']].copy()
    df_carteira = df_carteira.sort_values('SALDO', ascending=False)
    patrimonio = df_master['SALDO'].sum()
    
    # View 2: Radar (Site + Excel)
    # Mostra apenas o que tem Teto definido (maior que 0)
    df_radar = df_master[df_master['TETO'] > 0][['NOME', 'PRECO', 'TETO', 'MARGEM']].copy()
    df_radar = df_radar.sort_values('MARGEM', ascending=False)

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")
    st.stop()

# --- VISUALIZAÇÃO ---

# 1. CARTEIRA
st.subheader("🏦 Minha Carteira (Online)")
c_patr, c_table = st.columns([1, 3])
c_patr.metric("Patrimônio Total", f"R$ {patrimonio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

with c_table:
    st.dataframe(
        df_carteira,
        column_config={
            "NOME": st.column_config.TextColumn("Ativo"),
            "QTD": st.column_config.NumberColumn("Quantidade", format="%.0f"),
            "SALDO": st.column_config.NumberColumn("Saldo Total", format="R$ %.2f"),
        },
        hide_index=True,
        use_container_width=True
    )

st.divider()

# 2. RADAR
st.subheader("🎯 Radar de Oportunidades")

if uploaded_file is None:
    st.warning("⚠️ Envie a planilha 'Valuation' para ver o cálculo de margem.")
elif df_radar.empty:
    st.info("Nenhum ativo da carteira foi encontrado com Preço Teto no seu Excel.")
else:
    st.dataframe(
        df_radar,
        column_config={
            "NOME": st.column_config.TextColumn("Ativo"),
            "PRECO": st.column_config.NumberColumn("Cotação (Web)", format="R$ %.2f"),
            "TETO": st.column_config.NumberColumn("Preço Teto (Excel)", format="R$ %.2f"),
            "MARGEM": st.column_config.NumberColumn("Margem (%)", format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )

st.caption("Dados de Quantidade e Preço Atual extraídos do Investidor10. Preço Teto extraído do Excel.")
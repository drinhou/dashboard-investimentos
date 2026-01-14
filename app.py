import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Invest Pro",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PRO (ESTILO PANORAMA/INVESTIDOR10) ---
st.markdown("""
    <style>
        /* Fundo e Fontes */
        .main {background-color: #f4f6f9;}
        h1, h2, h3 {font-family: 'Roboto', sans-serif; color: #1e293b;}
        
        /* Cards de Métricas */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        div[data-testid="stMetricLabel"] {font-size: 0.85rem; color: #64748b; font-weight: 500;}
        div[data-testid="stMetricValue"] {font-size: 1.1rem; color: #0f172a; font-weight: 700;}
        
        /* Tabelas */
        div[data-testid="stDataFrame"] {
            background-color: white;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {background-color: #1e293b;}
        
        /* Status Badges */
        .compra-forte {color: #16a34a; font-weight: bold; padding: 4px; border-radius: 4px; background: #dcfce7;}
        .aguarde {color: #dc2626; font-weight: bold; padding: 4px; border-radius: 4px; background: #fee2e2;}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

def clean_currency(x):
    """Limpa strings de moeda (R$) e converte para float."""
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        # Remove quebras de linha e sujeira
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try:
            return float(clean)
        except:
            return 0.0
    return 0.0

@st.cache_data(ttl=300) # Atualiza a cada 5 min
def get_market_indices():
    """Busca índices reais do mercado."""
    tickers = {
        'IBOV': '^BVSP',
        'S&P 500': '^GSPC',
        'Dólar': 'BRL=X',
        'Bitcoin': 'BTC-USD'
    }
    try:
        data = yf.download(list(tickers.values()), period="1d", progress=False)['Close'].iloc[-1]
        return {
            'IBOV': data.get('^BVSP', 0),
            'S&P 500': data.get('^GSPC', 0),
            'Dólar': data.get('BRL=X', 0),
            'Bitcoin': data.get('BTC-USD', 0)
        }
    except:
        return {'IBOV': 0, 'S&P 500': 0, 'Dólar': 0, 'Bitcoin': 0}

def load_excel(file):
    """Carrega o Excel e trata erros."""
    try:
        xl = pd.ExcelFile(file)
        return xl
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

# --- HEADER: ÍNDICES DE MERCADO ---
indices = get_market_indices()
col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

with col1:
    st.title("🦅 Panorama Pro")
with col2:
    st.metric("🇧🇷 IBOV", f"{indices['IBOV']:,.0f} pts")
with col3:
    st.metric("🇺🇸 S&P 500", f"{indices['S&P 500']:,.0f} pts")
with col4:
    st.metric("💵 Dólar", f"R$ {indices['Dólar']:.2f}")
with col5:
    st.metric("₿ Bitcoin", f"US$ {indices['Bitcoin']:,.0f}")

st.divider()

# --- SIDEBAR (UPLOAD) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=50)
    st.header("Sua Carteira")
    uploaded_file = st.file_uploader("Atualizar Dados (.xlsx)", type=['xlsx'])
    st.caption("Certifique-se que o arquivo tem as abas: Carteira, Proventos e Valuation.")

# --- LÓGICA DE EXIBIÇÃO ---

if not uploaded_file:
    # TELA DE INÍCIO (SEM DADOS)
    c1, c2 = st.columns([1, 1])
    with c1:
        st.info("👋 **Bem-vindo ao seu painel.**")
        st.markdown("""
        Para visualizar seus investimentos, projeções e valuation, arraste sua planilha Excel no menu lateral.
        
        **O painel processa automaticamente:**
        * 📊 Sua posição atual e patrimônio.
        * 💰 Histórico e projeção de dividendos.
        * 🎯 Preço teto (Bazin) e margem de segurança.
        """)
    st.stop()

# --- PROCESSAMENTO DOS DADOS ---
xls = load_excel(uploaded_file)

# 1. CARTEIRA
try:
    df_carteira = pd.read_excel(xls, 'Carteira')
    # Identificar colunas dinamicamente
    col_ativo = [c for c in df_carteira.columns if 'ATIVO' in c.upper()][0]
    col_qtd = [c for c in df_carteira.columns if 'QUANTIDADE' in c.upper()][0]
    col_saldo = [c for c in df_carteira.columns if 'SALDO' in c.upper() and 'TOTAL' not in c.upper()][0] # Saldo individual
    
    # Limpeza
    df_carteira['C_ATIVO'] = df_carteira[col_ativo].astype(str).apply(lambda x: x.split('\n')[0]) # Tira o preço que vem junto no CSV
    df_carteira['C_SALDO'] = df_carteira[col_saldo].apply(clean_currency)
    df_carteira['C_QTD'] = df_carteira[col_qtd].apply(clean_currency)
    df_carteira['C_PRECO_MEDIO'] = df_carteira['C_SALDO'] / df_carteira['C_QTD']
    
    patrimonio_total = df_carteira['C_SALDO'].sum()
    
    # Tabela Final
    tabela_carteira = df_carteira[['C_ATIVO', 'C_QTD', 'C_PRECO_MEDIO', 'C_SALDO']].copy()
    tabela_carteira = tabela_carteira.sort_values('C_SALDO', ascending=False)
except Exception as e:
    st.error(f"Erro ao ler aba 'Carteira': {e}")
    patrimonio_total = 0
    tabela_carteira = pd.DataFrame()

# 2. PROVENTOS
try:
    df_prov = pd.read_excel(xls, 'Proventos')
    # Pegar linha de 2025
    row_2025 = df_prov[df_prov.iloc[:, 0].astype(str).str.contains("2025", na=False)].iloc[0]
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    valores = row_2025[1:13].apply(clean_currency).values
    
    tabela_proventos = pd.DataFrame({'Mês': meses, 'Valor (R$)': valores})
    total_prov_anual = tabela_proventos['Valor (R$)'].sum()
except:
    tabela_proventos = pd.DataFrame()
    total_prov_anual = 0

# 3. VALUATION (RADAR)
try:
    df_val = pd.read_excel(xls, 'Valuation')
    # Mapear colunas
    cols = df_val.columns
    c_ticker = [c for c in cols if 'TICKER' in c.upper()][0]
    c_cotacao = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
    c_bazin = [c for c in cols if 'BAZIN' in c.upper()][0]
    c_gordon = [c for c in cols if 'GORDON' in c.upper()][0]
    
    # Limpeza
    df_val['TICKER_F'] = df_val[c_ticker]
    df_val['PRECO_F'] = df_val[c_cotacao].apply(clean_currency)
    df_val['BAZIN_F'] = df_val[c_bazin].apply(clean_currency)
    df_val['GORDON_F'] = df_val[c_gordon].apply(clean_currency)
    
    # Cálculo Correto da Margem: (Teto - Preço) / Teto
    # Se preço for maior que teto, margem fica negativa
    df_val['MARGEM_BAZIN'] = (df_val['BAZIN_F'] - df_val['PRECO_F']) / df_val['BAZIN_F']
    
    # Status
    def get_status(margem):
        if margem > 0.15: return "COMPRAR" # > 15% margem
        if margem > 0: return "OBSERVAR"
        return "AGUARDAR"
    
    df_val['STATUS'] = df_val['MARGEM_BAZIN'].apply(get_status)
    
    tabela_valuation = df_val[['TICKER_F', 'PRECO_F', 'BAZIN_F', 'MARGEM_BAZIN', 'STATUS']].copy()
    # Ordenar: As melhores oportunidades (maior margem) primeiro
    tabela_valuation = tabela_valuation.sort_values('MARGEM_BAZIN', ascending=False)
except Exception as e:
    st.error(f"Erro no Valuation: {e}")
    tabela_valuation = pd.DataFrame()


# --- DASHBOARD VISUAL ---

# 1. CARTEIRA E ATIVOS
st.subheader("📊 Patrimônio e Ativos")
col_a, col_b = st.columns([1, 3])

with col_a:
    st.metric("Patrimônio Investido", f"R$ {patrimonio_total:,.2f}")
    st.metric("Total Proventos 2025", f"R$ {total_prov_anual:,.2f}")

with col_b:
    if not tabela_carteira.empty:
        st.dataframe(
            tabela_carteira,
            column_config={
                "C_ATIVO": "Ativo",
                "C_QTD": st.column_config.NumberColumn("Qtd", format="%.0f"),
                "C_PRECO_MEDIO": st.column_config.NumberColumn("Preço Médio", format="R$ %.2f"),
                "C_SALDO": st.column_config.NumberColumn("Saldo Atual", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True,
            height=300
        )

st.divider()

# 2. RADAR DE OPORTUNIDADES (VALUATION)
st.subheader("🎯 Radar de Oportunidades (Método Bazin)")
st.caption("Lista completa baseada no Preço Teto Bazin. Ordenado da maior margem para a menor.")

if not tabela_valuation.empty:
    st.dataframe(
        tabela_valuation,
        column_config={
            "TICKER_F": st.column_config.TextColumn("Ativo", width="small"),
            "PRECO_F": st.column_config.NumberColumn("Cotação Atual", format="R$ %.2f"),
            "BAZIN_F": st.column_config.NumberColumn("Preço Teto (Bazin)", format="R$ %.2f"),
            "MARGEM_BAZIN": st.column_config.NumberColumn(
                "Margem Segurança",
                format="%.1f%%", # Porcentagem com 1 casa decimal
            ),
            "STATUS": st.column_config.TextColumn("Recomendação"),
        },
        hide_index=True,
        use_container_width=True
    )
    # Dica de cor (não funciona nativo no dataframe simples, mas o sort ajuda)
    st.info("💡 **Dica:** Ativos no topo da lista possuem maior margem de segurança (estão mais 'baratos' em relação ao teto).")

st.divider()

# 3. PROVENTOS DETALHADOS
st.subheader("💰 Calendário de Proventos (2025)")

if not tabela_proventos.empty:
    # Transpor para ficar mais bonito se quiser, mas lista vertical é melhor para ler valores
    st.dataframe(
        tabela_proventos,
        column_config={
            "Mês": "Mês de Referência",
            "Valor (R$)": st.column_config.NumberColumn("Valor Recebido", format="R$ %.2f"),
        },
        hide_index=True,
        use_container_width=True
    )
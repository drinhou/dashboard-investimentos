import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf

# --- CONFIGURAÇÃO VISUAL (NUBANK/INVESTIDOR10 STYLE) ---
st.set_page_config(page_title="Minha Carteira", page_icon="💰", layout="wide")

# Remove margens excessivas
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 1rem;}
        .stMetric {background-color: #f0f2f6; border-radius: 10px; padding: 10px; border: 1px solid #e0e0e0;} 
        [data-testid="stMetricLabel"] {font-size: 0.9rem; color: #666;}
        [data-testid="stMetricValue"] {font-size: 1.2rem; font-weight: bold; color: #000;}
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---

# Cache para não ficar lento carregando cotações toda hora
@st.cache_data
def get_market_data():
    try:
        # Tickers: Dólar, IBOV, S&P500, IFIX
        tickers = ['BRL=X', '^BVSP', '^GSPC'] 
        data = yf.download(tickers, period="1d")['Close'].iloc[-1]
        
        # O Yahoo Finance retorna o Dólar invertido as vezes, ajuste básico
        dolar = data['BRL=X'] if 'BRL=X' in data else 0
        ibov = data['^BVSP'] if '^BVSP' in data else 0
        sp500 = data['^GSPC'] if '^GSPC' in data else 0
        
        return dolar, ibov, sp500
    except:
        return 0, 0, 0

def clean_currency(x):
    if isinstance(x, str):
        # Limpa R$, quebras de linha e converte para numero
        clean = x.split('\n')[0].replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try:
            return float(clean)
        except:
            return 0.0
    return x

def load_data(uploaded_file, sheet_name):
    try:
        return pd.read_excel(uploaded_file, sheet_name=sheet_name)
    except:
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Arquivo")
    uploaded_file = st.file_uploader("Arraste seu Excel aqui", type=['xlsx'])
    st.caption("Baseado no layout Investidor10")

# --- CABEÇALHO: ÍNDICES DE MERCADO (LIVE) ---
dolar, ibov, sp500 = get_market_data()

c1, c2, c3, c4 = st.columns(4)
c1.metric("💵 Dólar", f"R$ {dolar:.2f}")
c2.metric("🇧🇷 IBOV", f"{ibov:,.0f} pts")
c3.metric("🇺🇸 S&P 500", f"{sp500:,.0f} pts")
c4.metric("📊 IFIX", "Consultar") # IFIX é chato de pegar no Yahoo, deixei placeholder

st.markdown("---")

if not uploaded_file:
    st.info("👆 Para ver sua carteira, faça o upload da planilha na barra lateral.")
    st.stop()

# --- CARREGAMENTO DE DADOS ---
df_c = load_data(uploaded_file, "Carteira")
df_p = load_data(uploaded_file, "Proventos")
df_v = load_data(uploaded_file, "Valuation")

# --- PROCESSAMENTO INTELIGENTE ---

# 1. Carteira Limpa
if df_c is not None:
    # Identificar colunas
    col_saldo = [c for c in df_c.columns if 'SALDO' in c.upper()][0]
    col_ativo = [c for c in df_c.columns if 'ATIVO' in c.upper()][0]
    col_classe = [c for c in df_c.columns if 'CLASSE' in c.upper()]
    
    # Limpeza
    df_c['VALOR'] = df_c[col_saldo].apply(clean_currency)
    df_c['NOME'] = df_c[col_ativo].astype(str).apply(lambda x: x.split('\n')[0]) # Tira o preço que vem junto
    
    # Se tiver coluna CLASSE, usa ela. Se não, cria 'Geral'
    classe_col = col_classe[0] if col_classe else 'NOME'
    
    # Agrupamento para o gráfico não ficar confuso
    df_agrupado = df_c.groupby(classe_col)['VALOR'].sum().reset_index()
    patrimonio = df_c['VALOR'].sum()

# 2. Valuation (Oportunidades)
oportunidades = pd.DataFrame()
if df_v is not None:
    cols = df_v.columns
    # Busca colunas chave
    c_ticker = [c for c in cols if 'TICKER' in c.upper() or 'ATIVO' in c.upper()][0]
    c_cotacao = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
    c_bazin = [c for c in cols if 'BAZIN' in c.upper()][0]
    
    df_v['PRECO'] = df_v[c_cotacao].apply(clean_currency)
    df_v['TETO'] = df_v[c_bazin].apply(clean_currency)
    
    # Filtro Bazin
    df_v['MARGEM (%)'] = ((df_v['TETO'] - df_v['PRECO']) / df_v['TETO'])
    oportunidades = df_v[df_v['PRECO'] < df_v['TETO']].copy()
    oportunidades = oportunidades.sort_values('MARGEM (%)', ascending=False)
    # Seleciona só o necessário para exibir
    oportunidades = oportunidades[[c_ticker, 'PRECO', 'TETO', 'MARGEM (%)']]

# --- LAYOUT PRINCIPAL ---

tab1, tab2 = st.tabs(["🏠 Visão Geral", "🎯 Oportunidades & Valuation"])

with tab1:
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.subheader("Alocação")
        if df_c is not None:
            # GRÁFICO 1: PIZZA MAIS LIMPA (DONUT)
            # Dica UX: Usamos 'hole' para ficar mais leve e tiramos legendas poluídas
            fig_pie = px.pie(df_agrupado, values='VALOR', names=classe_col, hole=0.7, 
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            
            fig_pie.update_traces(textposition='outside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)
            
            st.metric("Patrimônio Total", f"R$ {patrimonio:,.2f}")

    with col_right:
        st.subheader("Histórico de Proventos")
        if df_p is not None:
            # Tenta pegar linha de 2025
            try:
                row_2025 = df_p[df_p.iloc[:, 0].astype(str).str.contains("2025", na=False)].iloc[0]
                valores = row_2025[1:13].apply(clean_currency).values
                meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
                
                df_bar = pd.DataFrame({'Mês': meses, 'Valor': valores})
                
                # GRÁFICO 2: BARRAS LIMPAS
                fig_bar = px.bar(df_bar, x='Mês', y='Valor', text_auto='.2s')
                
                # UX: Remove botões de zoom, grid lines chatas e fundo
                fig_bar.update_traces(marker_color='#1E3A8A', textposition='outside') # Cor Azul escuro "Financeiro"
                fig_bar.update_layout(
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='#eee'),
                    plot_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified", # Tooltip limpo
                    dragmode=False # Impede o usuário de dar zoom sem querer
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
            except:
                st.warning("Formato da aba Proventos não reconhecido.")

with tab2:
    st.subheader("Radar de Ações (Método Bazin)")
    st.caption("Ações negociadas abaixo do preço teto estipulado.")
    
    if not oportunidades.empty:
        # TABELA ESTILO INVESTIDOR10
        st.dataframe(
            oportunidades,
            column_config={
                c_ticker: "Ativo",
                "PRECO": st.column_config.NumberColumn("Preço Atual", format="R$ %.2f"),
                "TETO": st.column_config.NumberColumn("Preço Teto", format="R$ %.2f"),
                "MARGEM (%)": st.column_config.ProgressColumn(
                    "Margem de Segurança",
                    format="%.0f%%",
                    min_value=0,
                    max_value=1,
                ),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.success("Nenhuma oportunidade clara no momento.")
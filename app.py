import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Minha Carteira Pro", page_icon="📈", layout="wide")

# --- FUNÇÕES ---
def clean_currency(x):
    if isinstance(x, str):
        clean_str = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return x

def load_data(uploaded_file, sheet_name):
    if uploaded_file is None: return None
    try:
        return pd.read_excel(uploaded_file, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Erro ao ler a aba '{sheet_name}'. Verifique se o nome está correto no Excel.")
        return None

# --- CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    .stMetric {background-color: #262730; padding: 15px; border-radius: 10px;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (MENU LATERAL) ---
with st.sidebar:
    st.title("🚀 Painel do Investidor")
    st.markdown("Faça o upload da sua planilha Excel (.xlsx)")
    
    # AGORA É APENAS UM ARQUIVO
    uploaded_file = st.file_uploader("Arraste seu Excel aqui", type=['xlsx'])
    
    st.divider()
    st.info("Nota: Certifique-se que as abas do Excel se chamam: 'Carteira', 'Proventos' e 'Valuation'.")

# --- TELA PRINCIPAL ---
st.title("Visão Geral do Investidor")

if not uploaded_file:
    st.info("👋 Olá! Arraste seu arquivo Excel no menu lateral para começar.")
    st.stop()

# --- PROCESSAMENTO DOS DADOS (ARQUIVO ÚNICO) ---

# 1. CARTEIRA
df_carteira = load_data(uploaded_file, "Carteira")
patrimonio_total = 0
if df_carteira is not None:
    # Limpeza básica
    col_saldo = [c for c in df_carteira.columns if 'SALDO' in c.upper()][0] # Tenta achar coluna Saldo
    col_ativo = [c for c in df_carteira.columns if 'ATIVO' in c.upper()][0]
    
    df_carteira['SALDO_CLEAN'] = df_carteira[col_saldo].apply(clean_currency)
    df_carteira['ATIVO_CLEAN'] = df_carteira[col_ativo].astype(str).apply(lambda x: x.split('\n')[0])
    patrimonio_total = df_carteira['SALDO_CLEAN'].sum()

# 2. PROVENTOS
df_proventos = load_data(uploaded_file, "Proventos")
total_proventos_2025 = 0
media_mensal = 0
valores_2025 = []
if df_proventos is not None:
    try:
        # Tenta achar a linha de 2025
        row_2025 = df_proventos[df_proventos.iloc[:, 0].astype(str).str.contains("2025", na=False)].iloc[0]
        valores_2025 = row_2025[1:13].apply(clean_currency) # Jan a Dez
        total_proventos_2025 = valores_2025.sum()
        media_mensal = total_proventos_2025 / 12
    except:
        pass

# 3. VALUATION
df_valuation = load_data(uploaded_file, "Valuation")
oportunidades = pd.DataFrame()
if df_valuation is not None:
    try:
        cols = df_valuation.columns
        # Identifica colunas pelo nome aproximado
        c_cotacao = [c for c in cols if 'COTAÇÃO' in c.upper()][0]
        c_bazin = [c for c in cols if 'BAZIN' in c.upper()][0]
        
        df_valuation['COT_F'] = df_valuation[c_cotacao].apply(clean_currency)
        df_valuation['BAZ_F'] = df_valuation[c_bazin].apply(clean_currency)
        
        # Filtra onde Preço < Bazin
        oportunidades = df_valuation[df_valuation['COT_F'] < df_valuation['BAZ_F']].copy()
        oportunidades['DESCONTO'] = (oportunidades['BAZ_F'] - oportunidades['COT_F']) / oportunidades['BAZ_F'] * 100
        oportunidades = oportunidades.sort_values('DESCONTO', ascending=False)
    except:
        pass

# --- DASHBOARD ---

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Patrimônio Total", f"R$ {patrimonio_total:,.2f}")
c2.metric("Proventos 2025 (Proj)", f"R$ {total_proventos_2025:,.2f}")
c3.metric("Oportunidades (Bazin)", f"{len(oportunidades)} Ativos")

st.markdown("---")

# Gráficos
col_g1, col_g2 = st.columns([1, 2])

with col_g1:
    st.subheader("Sua Carteira")
    if df_carteira is not None:
        fig = px.pie(df_carteira, values='SALDO_CLEAN', names='ATIVO_CLEAN', hole=0.6)
        st.plotly_chart(fig, use_container_width=True)

with col_g2:
    st.subheader("Evolução de Dividendos")
    if total_proventos_2025 > 0:
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        df_chart = pd.DataFrame({'Mês': meses, 'Valor': valores_2025.values})
        st.plotly_chart(px.bar(df_chart, x='Mês', y='Valor', color='Valor'), use_container_width=True)

# Tabela Oportunidades
st.markdown("---")
st.subheader("🎯 Radar de Oportunidades")
if not oportunidades.empty:
    st.dataframe(oportunidades[[c_cotacao, c_bazin, 'DESCONTO']], use_container_width=True)
else:
    st.info("Nenhuma oportunidade óbvia pelo método Bazin no momento.")
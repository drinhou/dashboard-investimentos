import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA (ESTILO NUBANK/MINIMALISTA) ---
st.set_page_config(
    page_title="Minha Carteira Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNÇÕES DE LIMPEZA DE DADOS ---
def clean_currency(x):
    if isinstance(x, str):
        # Remove R$, espaços, pontos de milhar e troca vírgula por ponto
        clean_str = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return x

def load_data(uploaded_file, sheet_name):
    if uploaded_file is None:
        return None
    try:
        # Tenta ler como CSV ou Excel dependendo do arquivo
        if uploaded_file.name.endswith('.csv'):
            # Lendo CSV com tratamento específico para o formato brasileiro
            df = pd.read_csv(uploaded_file, encoding='utf-8', sep=',', quotechar='"')
        else:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
        return df
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        return None

# --- CSS CUSTOMIZADO PARA VISUAL CLEAN ---
st.markdown("""
    <style>
    .main {background-color: #0E1117;}
    .stMetric {background-color: #262730; padding: 15px; border-radius: 10px;}
    h1, h2, h3 {font-family: 'Sans-serif'; font-weight: 300;}
    .highlight {color: #00C896; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (MENU LATERAL) ---
with st.sidebar:
    st.title("🚀 Controle de Ativos")
    st.markdown("Faça o upload da sua planilha atualizada abaixo.")
    
    uploaded_file_1 = st.file_uploader("Upload Carteira (Página 1)", type=['csv', 'xlsx'])
    uploaded_file_2 = st.file_uploader("Upload Proventos (Página 2)", type=['csv', 'xlsx'])
    uploaded_file_3 = st.file_uploader("Upload Valuation (Página 3)", type=['csv', 'xlsx'])
    
    st.divider()
    st.caption("Desenvolvido para simplificar sua vida financeira.")

# --- TELA PRINCIPAL ---
st.title("Visão Geral do Investidor")

if not uploaded_file_1 or not uploaded_file_2 or not uploaded_file_3:
    st.info("👋 Olá! Para começar, arraste seus arquivos CSV/Excel no menu lateral.")
    st.stop()

# --- PROCESSAMENTO DOS DADOS ---

# 1. CARTEIRA
df_carteira = load_data(uploaded_file_1, "Carteira")
if df_carteira is not None:
    # Limpeza de colunas específicas baseada no seu arquivo
    # Assumindo colunas: ATIVO, TIPOLOGIA, SALDO, CLASSE, SALDO TOTAL
    # Ajuste fino para limpar nomes com quebra de linha (ex: BBSE3\nR$ 34,57)
    df_carteira['ATIVO_CLEAN'] = df_carteira['ATIVO'].astype(str).apply(lambda x: x.split('\n')[0])
    df_carteira['SALDO_CLEAN'] = df_carteira['SALDO'].apply(clean_currency)
    
    # KPIs Principais
    patrimonio_total = df_carteira['SALDO_CLEAN'].sum()
    
    # Top 3 Ativos
    top_ativos = df_carteira.sort_values(by='SALDO_CLEAN', ascending=False).head(3)

# 2. PROVENTOS
df_proventos = load_data(uploaded_file_2, "Proventos")
total_proventos_2025 = 0
if df_proventos is not None:
    # Focar na linha de totais ou soma das colunas
    # Lógica simplificada: procurar linha "Proventos 2025" e somar valores limpos
    try:
        row_2025 = df_proventos[df_proventos.iloc[:, 0].str.contains("Proventos 2025", na=False)].iloc[0]
        # Pega colunas de Jan a Dez (índices 1 a 12, ajustável)
        valores_2025 = row_2025[1:13].apply(clean_currency)
        total_proventos_2025 = valores_2025.sum()
        media_mensal = total_proventos_2025 / 12
    except:
        total_proventos_2025 = 0
        media_mensal = 0

# 3. VALUATION
df_valuation = load_data(uploaded_file_3, "Valuation")
oportunidades = []
if df_valuation is not None:
    # Limpar dados para comparação
    df_valuation['COTACAO_F'] = df_valuation['COTAÇÃO'].apply(clean_currency)
    df_valuation['BAZIN_F'] = df_valuation['BAZIN'].apply(clean_currency)
    df_valuation['GORDON_F'] = df_valuation['GORDON'].apply(clean_currency)
    
    # Lógica de Oportunidade: Preço Atual < Bazin
    df_valuation['DESCONTO_BAZIN'] = (df_valuation['BAZIN_F'] - df_valuation['COTACAO_F']) / df_valuation['BAZIN_F'] * 100
    oportunidades = df_valuation[df_valuation['COTACAO_F'] < df_valuation['BAZIN_F']].sort_values(by='DESCONTO_BAZIN', ascending=False)

# --- DASHBOARD LAYOUT ---

# Linha de KPIs (Indicadores)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Patrimônio Total", f"R$ {patrimonio_total:,.2f}")
with col2:
    st.metric("Dividendos 2025 (Proj)", f"R$ {total_proventos_2025:,.2f}", delta="Acumulado")
with col3:
    st.metric("Renda Mensal Média", f"R$ {media_mensal:,.2f}")
with col4:
    st.metric("Oportunidades no Radar", f"{len(oportunidades)} Ativos")

st.markdown("---")

# Seção Gráfica
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("Alocação por Ativo")
    # Gráfico de Rosca Minimalista
    fig_pizza = px.pie(df_carteira, values='SALDO_CLEAN', names='ATIVO_CLEAN', hole=0.6, color_discrete_sequence=px.colors.sequential.RdBu)
    fig_pizza.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pizza, use_container_width=True)

with c2:
    st.subheader("Evolução de Proventos (2025)")
    if total_proventos_2025 > 0:
        # Criar dataframe simples para o gráfico
        meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        df_chart_prov = pd.DataFrame({'Mês': meses, 'Valor': valores_2025.values})
        fig_bar = px.bar(df_chart_prov, x='Mês', y='Valor', color='Valor', color_continuous_scale='Greens')
        fig_bar.update_layout(xaxis_title=None, yaxis_title=None, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.caption("Dados de proventos insuficientes para gerar gráfico.")

st.markdown("---")

# Seção de Oportunidades (Estilo Loja/Shopping)
st.subheader("🎯 Radar de Oportunidades (Método Bazin)")
st.caption("Ativos que estão sendo negociados abaixo do Preço Justo de Bazin.")

if not oportunidades.empty:
    # Mostrar apenas colunas essenciais
    cols_show = ['EMPRESA', 'TICKER', 'COTAÇÃO', 'BAZIN', 'MARGEM', 'DY']
    st.dataframe(
        oportunidades[cols_show].style.format(precision=2),
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("Sua carteira parece estar precificada corretamente. Nenhuma oportunidade óbvia pelo método Bazin hoje.")

# Rodapé
st.markdown("---")
st.caption("Atualizado via Planilha Excel • Simples e Eficiente")
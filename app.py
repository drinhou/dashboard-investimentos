import streamlit as st
import pandas as pd
import yfinance as yf
import os
import datetime
import pytz

# =====================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# 2. CSS GLOBAL (CENTRALIZAÇÃO + UX)
# =====================================================
st.markdown("""
<style>

/* =========================
   SCROLL SUAVE + ANIMAÇÃO
   ========================= */
html {
    scroll-behavior: smooth;
}

:target {
    scroll-margin-top: 120px;
    animation: fadeSlide 0.6s ease-out;
}

@keyframes fadeSlide {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* =========================
   RESET VISUAL
   ========================= */
.stApp {
    background-color: #0c120f;
    color: #e0e0e0;
}

* {
    font-family: 'Segoe UI', 'Roboto', sans-serif;
}

#MainMenu, footer, header {
    visibility: hidden;
}

[data-testid="stElementToolbar"] {
    display: none !important;
}

/* =========================
   INPUTS
   ========================= */
div[data-baseweb="base-input"] {
    border-color: #374151;
}
div[data-baseweb="base-input"]:focus-within {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 1px #10b981 !important;
}

/* =====================================================
   TABELAS – CENTRALIZAÇÃO ABSOLUTA (DEFINITIVO)
   ===================================================== */

div[data-testid="stDataFrame"] {
    border: 1px solid #1f2937;
    border-radius: 12px;
    background-color: #0c120f;
    overflow: hidden;
}

/* Cabeçalhos */
div[data-testid="stDataFrame"] div[role="columnheader"] {
    display: grid !important;
    place-items: center !important;

    text-align: center !important;
    background-color: #141f1b;
    color: #6ee7b7;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    border-bottom: 1px solid #064e3b;
}

/* Células */
div[data-testid="stDataFrame"] div[role="gridcell"] {
    display: grid !important;
    place-items: center !important;

    text-align: center !important;
    min-height: 44px;
    background-color: #0c120f;

    pointer-events: none !important;
    user-select: none !important;
}

/* TODOS os níveis internos */
div[data-testid="stDataFrame"] div[role="gridcell"] *,
div[data-testid="stDataFrame"] div[role="columnheader"] * {
    display: grid !important;
    place-items: center !important;

    width: 100% !important;
    height: 100% !important;
    text-align: center !important;
    line-height: normal !important;
}

/* Neutraliza inline styles do Streamlit */
div[data-testid="stDataFrame"] div {
    align-items: center !important;
    justify-content: center !important;
}

/* Logos */
div[data-testid="stDataFrame"] img {
    width: 30px;
    height: 30px;
    object-fit: contain;
    border-radius: 50%;
    background: white;
    padding: 2px;
    border: 1px solid #374151;
}

/* =====================================================
   HEADER / SEÇÕES
   ===================================================== */

.main-header {
    text-align: center;
    padding: 40px 0 10px;
    margin-bottom: 40px;
    border-bottom: 1px solid #1f2937;
    background: radial-gradient(circle at center, #132e25 0%, #0c120f 100%);
}

.main-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(45deg, #10b981, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.main-greeting {
    font-size: 1rem;
    color: #9ca3af;
}

.section-wrapper {
    margin-top: 60px;
}

.section-header {
    font-size: 1.6rem;
    font-weight: 700;
    color: #f3f4f6;
    border-left: 6px solid #10b981;
    padding-left: 15px;
    display: flex;
    justify-content: space-between;
}

.section-desc {
    font-size: 0.9rem;
    color: #9ca3af;
    margin-left: 21px;
    margin-top: 8px;
    max-width: 800px;
}

.status-badge {
    background-color: #064e3b;
    color: #34d399;
    padding: 5px 12px;
    border-radius: 99px;
    border: 1px solid #059669;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Cards navegação */
.nav-card {
    background-color: #111a16;
    border: 1px solid #1f2937;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    cursor: pointer;
    text-decoration: none !important;
    display: block;
    transition: all 0.35s ease;
}

.nav-card:hover {
    border-color: #10b981;
    transform: translateY(-4px) scale(1.02);
    box-shadow: 0 12px 25px rgba(16, 185, 129, 0.15);
}

.nav-title {
    font-weight: 700;
    font-size: 1.1rem;
    color: #e5e7eb;
}

.nav-desc {
    font-size: 0.8rem;
    color: #6b7280;
}

/* Footer */
.footer-disclaimer {
    margin-top: 100px;
    padding: 40px;
    border-top: 1px solid #1f2937;
    text-align: center;
    color: #4b5563;
    font-size: 0.8rem;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# 3. FUNÇÕES
# =====================================================
def get_time_greeting():
    tz = pytz.timezone("America/Sao_Paulo")
    now = datetime.datetime.now(tz)
    if now.hour < 12:
        g = "Bom dia"
    elif now.hour < 18:
        g = "Boa tarde"
    else:
        g = "Boa noite"
    return g, now.strftime("%H:%M")

# =====================================================
# 4. HEADER
# =====================================================
greeting, time_now = get_time_greeting()

st.markdown(f"""
<div class="main-header">
    <h1 class="main-title">Dinheiro Data</h1>
    <p class="main-greeting">{greeting}, Investidor | {time_now}</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# 5. NAVEGAÇÃO
# =====================================================
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""
    <a href="#panorama" class="nav-card">
        <div class="nav-title">🌍 Panorama Global</div>
        <div class="nav-desc">Visão Macro</div>
    </a>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <a href="#radar-bazin" class="nav-card">
        <div class="nav-title">🎯 Radar Bazin</div>
        <div class="nav-desc">Preço Teto</div>
    </a>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <a href="#dividendos" class="nav-card">
        <div class="nav-title">💰 Dividendos</div>
        <div class="nav-desc">Renda Passiva</div>
    </a>
    """, unsafe_allow_html=True)

# =====================================================
# 6. SEÇÕES (EXEMPLO)
# =====================================================
st.markdown('<div id="panorama"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-wrapper"><div class="section-header">🌍 Panorama Global</div></div>', unsafe_allow_html=True)

df_demo = pd.DataFrame({
    "Logo": [
        "https://www.google.com/s2/favicons?domain=bb.com.br&sz=128",
        "https://www.google.com/s2/favicons?domain=itau.com.br&sz=128"
    ],
    "Ativo": ["BB Seguridade", "Banco Itaú"],
    "Valor": ["R$ 34,82", "R$ 39,60"],
    "Margem": ["+43.2%", "+12.4%"]
})

st.dataframe(
    df_demo,
    column_config={
        "Logo": st.column_config.ImageColumn(""),
        "Ativo": st.column_config.TextColumn("Ativo"),
        "Valor": st.column_config.TextColumn("Valor"),
        "Margem": st.column_config.TextColumn("Margem"),
    },
    hide_index=True,
    use_container_width=True
)

st.markdown('<div id="radar-bazin"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-wrapper"><div class="section-header">🎯 Radar Bazin</div></div>', unsafe_allow_html=True)

st.markdown('<div id="dividendos"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-wrapper"><div class="section-header">💰 Dividendos</div></div>', unsafe_allow_html=True)

# =====================================================
# 7. FOOTER
# =====================================================
st.markdown("""
<div class="footer-disclaimer">
<strong>⚠️ ISENÇÃO DE RESPONSABILIDADE</strong><br><br>
Este dashboard tem caráter educativo e não constitui recomendação de investimento.
</div>
""", unsafe_allow_html=True)

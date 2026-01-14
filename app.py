import streamlit as st
import pandas as pd
import yfinance as yf
import os
import datetime
import pytz

# ========== CONFIGURAÇÃO ==========
st.set_page_config(
    page_title="Dinheiro Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== CSS OTIMIZADO E MELHORADO ==========
st.markdown("""
    <style>
        /* ===== VARIÁVEIS GLOBAIS ===== */
        :root {
            --bg-primary: #0c120f;
            --bg-secondary: #111a16;
            --bg-tertiary: #141f1b;
            --border-color: #1f2937;
            --green-primary: #10b981;
            --green-secondary: #34d399;
            --green-dark: #064e3b;
            --green-emerald: #6ee7b7;
            --text-primary: #e0e0e0;
            --text-secondary: #9ca3af;
            --text-tertiary: #6b7280;
            --red-error: #f87171;
        }

        /* ===== SCROLL SUAVE GLOBAL ===== */
        * {
            scroll-behavior: smooth !important;
            font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
        }

        html {
            scroll-padding-top: 80px;
        }

        /* ===== BASE ===== */
        .stApp {
            background-color: var(--bg-primary);
            color: var(--text-primary);
        }
        
        /* Ocultar elementos padrão */
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        [data-testid="stElementToolbar"] {
            display: none !important;
        }

        /* ===== INPUTS COM ANIMAÇÃO ===== */
        div[data-baseweb="base-input"] {
            border-color: var(--border-color);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        div[data-baseweb="base-input"]:focus-within {
            border-color: var(--green-primary) !important;
            box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
            transform: translateY(-1px);
        }

        /* ===== HEADER PRINCIPAL ===== */
        .main-header {
            text-align: center;
            padding: 50px 0 20px 0;
            margin-bottom: 50px;
            border-bottom: 2px solid var(--border-color);
            background: radial-gradient(ellipse at center, rgba(16, 185, 129, 0.05) 0%, transparent 70%);
            animation: fadeInDown 0.8s ease-out;
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .main-title {
            font-size: 3.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--green-primary) 0%, var(--green-secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            letter-spacing: -2px;
            animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.9; }
        }

        .main-greeting {
            font-size: 1.1rem;
            color: var(--text-secondary);
            font-weight: 400;
            margin-top: 10px;
            animation: fadeIn 1s ease-out 0.3s both;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* ===== CARDS DE NAVEGAÇÃO COM ANIMAÇÃO ===== */
        .nav-card {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-tertiary) 100%);
            border: 2px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            cursor: pointer;
            text-decoration: none !important;
            display: block;
            margin-bottom: 20px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .nav-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.1), transparent);
            transition: left 0.5s;
        }

        .nav-card:hover::before {
            left: 100%;
        }

        .nav-card:hover {
            border-color: var(--green-primary);
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 20px 40px -10px rgba(16, 185, 129, 0.3);
        }

        .nav-title {
            font-weight: 700;
            font-size: 1.2rem;
            display: block;
            color: var(--text-primary) !important;
            transition: all 0.3s ease;
        }

        .nav-desc {
            font-size: 0.85rem;
            color: var(--text-tertiary) !important;
            display: block;
            margin-top: 8px;
            transition: all 0.3s ease;
        }

        .nav-card:hover .nav-title {
            color: var(--green-primary) !important;
            transform: scale(1.05);
        }

        .nav-card:hover .nav-desc {
            color: var(--green-secondary) !important;
        }

        /* ===== SEÇÕES COM ANIMAÇÃO ===== */
        .section-wrapper {
            margin-top: 80px;
            margin-bottom: 30px;
            animation: fadeInUp 0.6s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .section-header {
            font-size: 1.8rem;
            font-weight: 800;
            color: #f9fafb;
            border-left: 6px solid var(--green-primary);
            padding-left: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }

        .section-header:hover {
            border-left-width: 10px;
            padding-left: 24px;
        }

        .section-desc {
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-left: 26px;
            max-width: 900px;
            line-height: 1.6;
            margin-bottom: 30px;
        }

        .status-badge {
            background: linear-gradient(135deg, var(--green-dark) 0%, #047857 100%);
            color: var(--green-secondary);
            font-size: 0.85rem;
            padding: 8px 16px;
            border-radius: 50px;
            border: 2px solid #059669;
            font-weight: 700;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
            transition: all 0.3s ease;
        }

        .status-badge:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 15px rgba(16, 185, 129, 0.3);
        }

        /* ===== TABELAS - CENTRALIZAÇÃO FORÇADA ===== */
        div[data-testid="stDataFrame"] {
            border: 2px solid var(--border-color);
            border-radius: 12px;
            background-color: var(--bg-primary);
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }

        div[data-testid="stDataFrame"]:hover {
            box-shadow: 0 8px 30px rgba(16, 185, 129, 0.15);
            transform: translateY(-2px);
        }

        /* CABEÇALHO DA TABELA */
        div[data-testid="stDataFrame"] [role="columnheader"] {
            background: linear-gradient(180deg, var(--bg-tertiary) 0%, #0f1913 100%) !important;
            color: var(--green-emerald) !important;
            font-size: 13px !important;
            font-weight: 800 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid var(--green-dark) !important;
            padding: 12px 8px !important;
        }

        /* FORÇA CENTRALIZAÇÃO NO CABEÇALHO */
        div[data-testid="stDataFrame"] [role="columnheader"] * {
            text-align: center !important;
            justify-content: center !important;
            margin: 0 auto !important;
        }

        /* CÉLULAS DA TABELA - CENTRALIZAÇÃO ABSOLUTA */
        div[data-testid="stDataFrame"] [role="gridcell"] {
            background-color: var(--bg-primary) !important;
            padding: 10px 8px !important;
            border-bottom: 1px solid rgba(31, 41, 55, 0.5) !important;
            transition: background-color 0.2s ease;
        }

        div[data-testid="stDataFrame"] [role="gridcell"]:hover {
            background-color: rgba(16, 185, 129, 0.03) !important;
        }

        /* FORÇA CENTRALIZAÇÃO EM TODOS OS ELEMENTOS DAS CÉLULAS */
        div[data-testid="stDataFrame"] [role="gridcell"],
        div[data-testid="stDataFrame"] [role="gridcell"] > *,
        div[data-testid="stDataFrame"] [role="gridcell"] div,
        div[data-testid="stDataFrame"] [role="gridcell"] p,
        div[data-testid="stDataFrame"] [role="gridcell"] span {
            text-align: center !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }

        /* LOGOS */
        div[data-testid="stDataFrame"] img {
            border-radius: 50%;
            border: 2px solid var(--border-color);
            padding: 3px;
            background-color: #ffffff;
            width: 32px !important;
            height: 32px !important;
            object-fit: contain;
            display: block !important;
            margin: 0 auto !important;
            transition: all 0.3s ease;
        }

        div[data-testid="stDataFrame"] img:hover {
            transform: scale(1.15) rotate(5deg);
            border-color: var(--green-primary);
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }

        /* ===== FOOTER ===== */
        .footer-disclaimer {
            margin-top: 120px;
            padding: 50px 40px;
            border-top: 2px solid var(--border-color);
            text-align: center;
            color: var(--text-tertiary);
            font-size: 0.85rem;
            background: linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            line-height: 1.8;
        }

        .footer-disclaimer strong {
            color: var(--green-primary);
            font-size: 1rem;
        }

        /* ===== SCROLL SUAVE COM JAVASCRIPT ===== */
        a[href^="#"] {
            scroll-behavior: smooth;
        }
    </style>

    <script>
        // Script para scroll suave aprimorado
        document.addEventListener('DOMContentLoaded', function() {
            const links = document.querySelectorAll('a[href^="#"]');
            
            links.forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    const targetId = this.getAttribute('href').substring(1);
                    const targetElement = document.getElementById(targetId);
                    
                    if (targetElement) {
                        targetElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start',
                            inline: 'nearest'
                        });
                    }
                });
            });
        });

        // Observador de interseção para animações ao scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observa todas as seções
        setTimeout(() => {
            document.querySelectorAll('.section-wrapper').forEach(section => {
                section.style.opacity = '0';
                section.style.transform = 'translateY(30px)';
                section.style.transition = 'all 0.6s ease-out';
                observer.observe(section);
            });
        }, 100);
    </script>
""", unsafe_allow_html=True)

# ========== FUNÇÕES AUXILIARES ==========

def get_time_greeting():
    """Retorna saudação e horário formatado"""
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.datetime.now(tz)
    h = now.hour
    
    if 5 <= h < 12:
        greeting = "Bom dia"
    elif 12 <= h < 18:
        greeting = "Boa tarde"
    else:
        greeting = "Boa noite"
    
    time_str = now.strftime("%H:%M")
    return greeting, time_str

def clean_currency(x):
    """Limpa e converte valores monetários"""
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        clean = x.replace('R$', '').replace('.', '').replace(',', '.').replace('%', '').strip()
        try:
            return float(clean)
        except:
            return 0.0
    return 0.0

def clean_dy_percentage(x):
    """Limpa e normaliza percentuais de DY"""
    val = clean_currency(x)
    if 0 < val < 1.0:
        return val * 100
    return val

def get_logo_url(ticker):
    """Retorna URL do logo do ativo"""
    if not isinstance(ticker, str):
        return ""
    
    clean = ticker.replace('.SA', '').strip().upper()
    
    # Mapeamento de logos
    sites = {
        'CXSE3': 'caixaseguradora.com.br', 'BBSE3': 'bbseguros.com.br', 'ODPV3': 'odontoprev.com.br',
        'BBAS3': 'bb.com.br', 'ABCB4': 'abcbrasil.com.br', 'ITUB4': 'itau.com.br',
        'ISAE4': 'isaenergiabrasil.com.br', 'TRPL4': 'isaenergiabrasil.com.br',
        'CMIG4': 'cemig.com.br', 'SAPR4': 'sanepar.com.br', 'SAPR11': 'sanepar.com.br',
        'PETR4': 'petrobras.com.br', 'RANI3': 'irani.com.br', 'KLBN11': 'klabin.com.br',
        'KLBN4': 'klabin.com.br', 'IRBR3': 'ri.irbre.com', 'FLRY3': 'fleury.com.br',
        'PSSA3': 'portoseguro.com.br', 'WEGE3': 'weg.net', 'VALE3': 'vale.com',
        'ABEV3': 'ambev.com.br', 'B3SA3': 'b3.com.br', 'EGIE3': 'engie.com.br'
    }

    if clean in sites:
        return f"https://www.google.com/s2/favicons?domain={sites[clean]}&sz=128"
    
    # Criptomoedas
    if clean in ['BTC', 'BITCOIN']:
        return "https://assets.coingecko.com/coins/images/1/small/bitcoin.png"
    if clean in ['ETH', 'ETHEREUM']:
        return "https://assets.coingecko.com/coins/images/279/small/ethereum.png"
    if clean in ['SOL', 'SOLANA']:
        return "https://assets.coingecko.com/coins/images/4128/small/solana.png"
    
    return f"https://cdn.jsdelivr.net/gh/thefintz/icon-project@master/stock_logos/{clean}.png"

@st.cache_data(ttl=60)
def get_market_data_distributed():
    """Obtém dados do mercado distribuídos por categoria"""
    groups = {
        'USA': {
            'S&P 500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DOW JONES': '^DJI',
            'VIX (Medo)': '^VIX'
        },
        'BRASIL': {
            'IBOVESPA': '^BVSP',
            'IFIX (FIIs)': 'IFIX.SA',
            'VALE': 'VALE3.SA',
            'PETROBRAS': 'PETR4.SA'
        },
        'MOEDAS': {
            'DÓLAR': 'BRL=X',
            'EURO': 'EURBRL=X',
            'LIBRA': 'GBPBRL=X',
            'DXY Global': 'DX-Y.NYB'
        },
        'COMMODITIES': {
            'OURO': 'GC=F',
            'PRATA': 'SI=F',
            'COBRE': 'HG=F',
            'PETRÓLEO': 'BZ=F'
        },
        'CRIPTO': {
            'BITCOIN': 'BTC-USD',
            'ETHEREUM': 'ETH-USD',
            'SOLANA': 'SOL-USD',
            'BNB': 'BNB-USD'
        }
    }
    
    final_dfs = {}
    
    for cat, items in groups.items():
        rows = []
        try:
            tickers = list(items.values())
            data = yf.download(tickers, period="5d", progress=False)['Close']
            
            for name, ticker in items.items():
                try:
                    series = pd.Series()
                    if len(tickers) > 1 and ticker in data.columns:
                        series = data[ticker].dropna()
                    elif isinstance(data, pd.Series):
                        series = data.dropna()
                    
                    if len(series) >= 2:
                        curr, prev = series.iloc[-1], series.iloc[-2]
                        pct = ((curr - prev) / prev) * 100
                        rows.append([name, curr, pct])
                    else:
                        rows.append([name, 0.0, 0.0])
                except:
                    rows.append([name, 0.0, 0.0])
        except:
            pass
        
        # Garante 4 linhas
        while len(rows) < 4:
            rows.append(["-", 0.0, 0.0])
        
        final_dfs[cat] = pd.DataFrame(rows[:4], columns=["Ativo", "Preço", "Var%"])
    
    return final_dfs

@st.cache_data(ttl=300)
def get_br_prices(ticker_list):
    """Obtém preços atuais dos ativos brasileiros"""
    if not ticker_list:
        return {}
    
    sa_tickers = [f"{t}.SA" for t in ticker_list]
    
    try:
        data = yf.download(sa_tickers, period="1d", progress=False)['Close'].iloc[-1]
        
        if isinstance(data, float):
            return {ticker_list[0]: data}
        
        prices = {}
        for t in ticker_list:
            if f"{t}.SA" in data:
                prices[t] = data[f"{t}.SA"]
        
        return prices
    except:
        return {}

def show_mini_table(col, title, df):
    """Exibe tabela compacta formatada"""
    col.write(f"**{title}**")
    
    if not df.empty:
        def format_price(val):
            if val == 0:
                return "-"
            return "{:.2f}".format(val)

        def color_var(val):
            if val > 0:
                return 'color: #34d399; font-weight: bold;'
            if val < 0:
                return 'color: #f87171; font-weight: bold;'
            return 'color: #6b7280;'
        
        styled_df = df.style.format({
            "Preço": format_price,
            "Var%": "{:+.2f}%"
        }).map(color_var, subset=['Var%'])
        
        col.dataframe(
            styled_df,
            column_config={
                "Ativo": st.column_config.TextColumn("Ativo", width="medium"),
                "Preço": st.column_config.TextColumn("Cotação", width="medium"),
                "Var%": st.column_config.TextColumn("Var %", width="small")
            },
            hide_index=True,
            use_container_width=True,
            height=180
        )

# ========== APLICAÇÃO PRINCIPAL ==========

# Obter saudação
greeting_text, time_text = get_time_greeting()

# Header
st.markdown(f"""
    <div class='main-header'>
        <h1 class='main-title'>Dinheiro Data</h1>
        <p class='main-greeting'>{greeting_text}, Investidor. 
            <span style='font-size: 0.85em; opacity: 0.7;'>| Dados atualizados às {time_text}</span>
        </p>
    </div>
""", unsafe_allow_html=True)

# Navegação
nav1, nav2, nav3 = st.columns(3)

with nav1:
    st.markdown("""
    <a href='#panorama' class='nav-card'>
        <span class='nav-title'>🌍 Panorama Global</span>
        <span class='nav-desc'>Visão completa dos mercados</span>
    </a>
    """, unsafe_allow_html=True)

with nav2:
    st.markdown("""
    <a href='#radar-bazin' class='nav-card'>
        <span class='nav-title'>🎯 Radar Bazin</span>
        <span class='nav-desc'>Análise de Preço Teto</span>
    </a>
    """, unsafe_allow_html=True)

with nav3:
    st.markdown("""
    <a href='#dividendos' class='nav-card'>
        <span class='nav-title'>💰 Dividendos</span>
        <span class='nav-desc'>Projeção de Renda Passiva</span>
    </a>
    """, unsafe_allow_html=True)

# ========== 1. PANORAMA GLOBAL ==========

st.markdown("<div id='panorama'></div>", unsafe_allow_html=True)
st.markdown("""
<div class='section-wrapper'>
    <div class='section-header'>
        <span>🌍 Panorama Global</span>
    </div>
    <div class='section-desc'>
        Acompanhe os principais índices e ativos globais em tempo real. Dados atualizados automaticamente.
    </div>
</div>
""", unsafe_allow_html=True)

# Obter dados do mercado
M = get_market_data_distributed()

# Primeira linha
r1c1, r1c2, r1c3 = st.columns(3)
with r1c1:
    show_mini_table(r1c1, "🇺🇸 Índices EUA", M['USA'])
with r1c2:
    show_mini_table(r1c2, "🇧🇷 Índices Brasil", M['BRASIL'])
with r1c3:
    show_mini_table(r1c3, "💱 Moedas", M['MOEDAS'])

st.write("")

# Segunda linha
r2c1, r2c2 = st.columns(2)
with r2c1:
    show_mini_table(r2c1, "🛢️ Commodities", M['COMMODITIES'])
with r2c2:
    show_mini_table(r2c2, "💎 Criptoativos", M['CRIPTO'])

# ========== CARREGAMENTO DE DADOS ==========

df_radar = pd.DataFrame()
df_div = pd.DataFrame()

# Tenta carregar arquivo
file_data = None
if os.path.exists("PEC.xlsx"):
    file_data = pd.ExcelFile("PEC.xlsx")
elif os.path.exists("PEC - Página1.csv"):
    file_data = pd.read_csv("PEC - Página1.csv")

if file_data is not None:
    try:
        target_df = pd.DataFrame()
        
        # Identifica a planilha correta
        if isinstance(file_data, pd.ExcelFile):
            for sheet in file_data.sheet_names:
                temp = pd.read_excel(file_data, sheet)
                if any("BAZIN" in str(c).upper() for c in temp.columns):
                    target_df = temp
                    break
        else:
            target_df = file_data

        if not target_df.empty:
            # Normaliza colunas
            target_df.columns = [str(c).strip().upper() for c in target_df.columns]
            cols = target_df.columns
            
            # Identifica colunas
            c_tick = next((c for c in cols if 'TICKER' in c), None)
            c_baz = next((c for c in cols if 'BAZIN' in c), None)
            c_dy = next((c for c in cols if 'DY' in c), None)
            c_dpa = next((c for c in cols if 'DPA' in c), None)
            c_emp = next((c for c in cols if 'EMPRESA' in c), None)

            if c_tick and c_baz:
                # Processa dados
                target_df['TICKER_F'] = target_df[c_tick].astype(str).str.strip().str.upper()
                target_df['BAZIN_F'] = target_df[c_baz].apply(clean_currency)
                target_df['DY_F'] = target_df[c_dy].apply(clean_dy_percentage) if c_dy else 0.0
                target_df['DPA_F'] = target_df[c_dpa].apply(clean_currency) if c_dpa else 0.0
                
                # Obtém preços
                prices = get_br_prices(target_df['TICKER_F'].unique().tolist())
                target_df['PRECO_F'] = target_df['TICKER_F'].map(prices).fillna(0)
                
                # Calcula margem
                target_df['MARGEM_VAL'] = target_df.apply(
                    lambda x: ((x['BAZIN_F'] - x['PRECO_F']) / x['PRECO_F'] * 100) if x['PRECO_F'] > 0 else -999,
                    axis=1
                )
                
                # Adiciona logo e nome
                target_df['Logo'] = target_df['TICKER_F'].apply(get_logo_url)
                target_df['Ativo'] = target_df[c_emp] if c_emp else target_df['TICKER_F']
                
                # Cria DataFrames finais
                df_radar = target_df[target_df['BAZIN_F'] > 0][
                    ['Logo', 'Ativo', 'TICKER_F', 'BAZIN_F', 'PRECO_F', 'MARGEM_VAL']
                ].sort_values('MARGEM_VAL', ascending=False)
                
                df_div = target_df[target_df['DY_F'] > 0][
                    ['Logo', 'Ativo', 'TICKER_F', 'DPA_F', 'DY_F']
                ].sort_values('DY_F', ascending=False)
    except:
        pass

# ========== 2. RADAR BAZIN ==========

st.markdown("<div id='radar-bazin'></div>", unsafe_allow_html=True)

count_opp = len(df_radar[df_radar['MARGEM_VAL'] > 10]) if not df_radar.empty else 0

st.markdown(f"""
<div class='section-wrapper'>
    <div class='section-header'>
        <span>🎯 Radar Bazin</span>
        <span class='status-badge'>{count_opp} Ativos com desconto (>10%)</span>
    </div>
    <div class='section-desc'>
        O Preço Teto é calculado utilizando a metodologia de Décio Bazin, visando identificar 
        ativos que pagam bons dividendos a preços descontados.
    </div>
</div>
""", unsafe_allow_html=True)

if not df_radar.empty:
    # Campo de busca
    search_bazin = st.text_input(
        "🔍 Pesquisar Ativo",
        placeholder="Digite o nome da empresa ou ticker...",
        key="sbazin"
    )
    
    # Filtra dados
    df_show = df_radar.copy()
    if search_bazin:
        df_show = df_show[
            df_show['Ativo'].str.contains(search_bazin, case=False) |
            df_show['TICKER_F'].str.contains(search_bazin, case=False)
        ]

    # Estiliza
    def style_margin(v):
        if v > 10:
            return 'color: #34d399; font-weight: bold;'
        if v < 0:
            return 'color: #f87171; font-weight: bold;'
        return 'color: #9ca3af;'

    styled_radar = df_show.style.format({
        "BAZIN_F": "R$ {:.2f}",
        "PRECO_F": "R$ {:.2f}",
        "MARGEM_VAL": "{:+.1f}%"
    }).map(style_margin, subset=['MARGEM_VAL'])

    # Exibe tabela
    st.dataframe(
        styled_radar,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"),
            "Ativo": st.column_config.TextColumn("Ativo", width="large"),
            "TICKER_F": None,
            "BAZIN_F": st.column_config.NumberColumn("Preço Teto", width="medium"),
            "PRECO_F": st.column_config.NumberColumn("Cotação Atual", width="medium"),
            "MARGEM_VAL": st.column_config.TextColumn("Margem", width="small"),
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("📋 Nenhum dado disponível. Adicione o arquivo PEC.xlsx ou PEC - Página1.csv")

# ========== 3. DIVIDENDOS ==========

st.markdown("<div id='dividendos'></div>", unsafe_allow_html=True)

count_dy = len(df_div[df_div['DY_F'] > 8]) if not df_div.empty else 0

st.markdown(f"""
<div class='section-wrapper'>
    <div class='section-header'>
        <span>💰 Dividendos</span>
        <span class='status-badge'>{count_dy} Ativos com Yield > 8%</span>
    </div>
    <div class='section-desc'>
        Estimativas de rendimento anual (Dividend Yield) para 2026, baseadas em 
        projeções de mercado e histórico de pagamentos das companhias.
    </div>
</div>
""", unsafe_allow_html=True)

if not df_div.empty:
    # Campo de busca
    search_div = st.text_input(
        "🔍 Pesquisar Ativo",
        placeholder="Digite o nome da empresa ou ticker...",
        key="sdiv"
    )
    
    # Filtra dados
    df_div_show = df_div.copy()
    if search_div:
        df_div_show = df_div_show[
            df_div_show['Ativo'].str.contains(search_div, case=False) |
            df_div_show['TICKER_F'].str.contains(search_div, case=False)
        ]

    # Estiliza
    def style_dy(v):
        if v > 8:
            return 'color: #34d399; font-weight: bold;'
        return 'color: #9ca3af;'

    styled_div = df_div_show.style.format({
        "DPA_F": "R$ {:.2f}",
        "DY_F": "{:.2f}%"
    }).map(style_dy, subset=['DY_F'])

    # Exibe tabela
    st.dataframe(
        styled_div,
        column_config={
            "Logo": st.column_config.ImageColumn("", width="small"),
            "Ativo": st.column_config.TextColumn("Ativo", width="large"),
            "TICKER_F": None,
            "DPA_F": st.column_config.NumberColumn("Dividendo / Ação", width="medium"),
            "DY_F": st.column_config.TextColumn("Yield Projetado", width="medium"),
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("📋 Nenhum dado disponível. Adicione o arquivo PEC.xlsx ou PEC - Página1.csv")

# ========== FOOTER ==========

st.markdown("""
    <div class='footer-disclaimer'>
        <strong>⚠️ ISENÇÃO DE RESPONSABILIDADE</strong><br><br>
        As informações, dados e indicadores apresentados nesta plataforma são obtidos de fontes públicas 
        e cálculos automatizados. Este dashboard tem caráter estritamente educativo e informativo.<br>
        <strong>Nenhum conteúdo aqui deve ser interpretado como recomendação de compra, venda ou 
        manutenção de ativos mobiliários.</strong><br>
        Investimentos em renda variável estão sujeitos a riscos de mercado e perda de capital. 
        Realize sua própria análise ou consulte um profissional certificado antes de tomar decisões financeiras.
    </div>
""", unsafe_allow_html=True)
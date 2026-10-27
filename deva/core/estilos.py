"""Design System e estilos CSS globais para o Painel Deva.

Alinhado aos princípios de Taste-Skill (direção de arte sóbria, sem clichês de IA)
e UI/UX Pro Max (contraste WCAG AA, tipografia com números tabulares e densidade de dados).
"""
import streamlit as st

CSS_GLOBAL = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #0F172A;
}

/* Espaçamento do container principal */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 96% !important;
}

/* Tipografia de títulos */
h1 {
    font-size: 1.625rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #0F172A !important;
    margin-bottom: 0.25rem !important;
}

h2, h3 {
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    color: #1E293B !important;
}

h4 {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #1E293B !important;
}

/* Estilização moderna e sóbria de KPIs (Cartões de métrica) */
[data-testid="stMetric"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.03) !important;
    transition: border-color 0.15s ease !important;
}

[data-testid="stMetric"]:hover {
    border-color: #CBD5E1 !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.775rem !important;
    font-weight: 600 !important;
    color: #64748B !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    font-variant-numeric: tabular-nums !important;
    letter-spacing: -0.01em !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.8125rem !important;
    font-weight: 600 !important;
}

/* Botões com hierarquia sólida (sem gradientes ou brilhos) */
.stButton > button[kind="primary"] {
    background-color: #1A4B8C !important;
    border: 1px solid #1A4B8C !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    padding: 0.5rem 1rem !important;
    transition: background-color 0.15s ease, border-color 0.15s ease !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #123563 !important;
    border-color: #123563 !important;
}

.stButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    color: #334155 !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: #F8FAFC !important;
    border-color: #94A3B8 !important;
    color: #0F172A !important;
}

/* Tabs refinadas */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px !important;
    border-bottom: 1px solid #E2E8F0 !important;
}

.stTabs [data-baseweb="tab"] {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #64748B !important;
    padding: 8px 16px !important;
    border-radius: 6px 6px 0 0 !important;
}

.stTabs [aria-selected="true"] {
    color: #1A4B8C !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #1A4B8C !important;
}

/* Dataframe e tabelas */
[data-testid="stDataFrame"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    background: #FFFFFF !important;
}

/* Containers com borda */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #E2E8F0 !important;
    border-radius: 8px !important;
    background-color: #FFFFFF !important;
}

/* Classes utilitárias do Deva Design System */
.deva-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    line-height: 1.25;
    letter-spacing: 0.02em;
}

.deva-badge-fiel { background-color: #DCFCE7; color: #166534; border: 1px solid #BBF7D0; }
.deva-badge-recorrente { background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
.deva-badge-novo { background-color: #F0FDF4; color: #15803D; border: 1px solid #DCFCE7; }
.deva-badge-ocasional { background-color: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }
.deva-badge-risco { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
.deva-badge-perdido { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }

.deva-card {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 14px;
}

.deva-card-header {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0F172A;
    margin-bottom: 6px;
}

.deva-pitch-box {
    background-color: #F8FAFC;
    border-left: 4px solid #1A4B8C;
    border-radius: 0 6px 6px 0;
    padding: 12px 16px;
    margin: 10px 0 16px 0;
    font-size: 0.925rem;
    color: #1E293B;
}

.deva-insight-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 14px;
    margin-top: 12px;
}

.deva-insight-item {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px 16px;
}

.deva-insight-title {
    font-size: 0.8125rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #1A4B8C;
    margin-bottom: 6px;
}

.deva-insight-body {
    font-size: 0.875rem;
    line-height: 1.45;
    color: #334155;
}
</style>
"""


def aplicar():
    """Aplica o CSS global do Deva Design System na página ativa."""
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)

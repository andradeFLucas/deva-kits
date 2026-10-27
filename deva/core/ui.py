"""Componentes visuais compartilhados com Design System alinhado ao Taste-Skill e UI/UX Pro Max."""
import plotly.express as px
import streamlit as st

from deva.core import config, dados, navegacao

# Paleta Deva Industrial Tech (Alto Contraste WCAG AA)
AZUL = "#1A4B8C"
AZUL_HOVER = "#123563"

CORES_CATEGORIA = {
    "Fiel": "#0D6832",
    "Recorrente": "#15803D",
    "Novo": "#0284C7",
    "Ocasional": "#64748B",
    "Em risco": "#B45309",
    "Perdido": "#B91C1C",
}

CORES_GIRO = {
    "Alto": "#0D6832",
    "Médio": "#15803D",
    "Baixo": "#B45309",
    "Sem venda 12m": "#B91C1C",
}

CORES_SEGMENTO = {
    "Cliente": AZUL,
    "Mercado Livre": "#D97706",
    "Garantia": "#475569",
    "Interno": "#94A3B8",
    "Seguradora": "#7C3AED",
}


def badge_categoria_html(cat: str) -> str:
    """Retorna badge HTML estilizado para categorias."""
    classes = {
        "Fiel": "deva-badge deva-badge-fiel",
        "Recorrente": "deva-badge deva-badge-recorrente",
        "Novo": "deva-badge deva-badge-novo",
        "Ocasional": "deva-badge deva-badge-ocasional",
        "Em risco": "deva-badge deva-badge-risco",
        "Perdido": "deva-badge deva-badge-perdido",
    }
    cls = classes.get(cat, "deva-badge deva-badge-ocasional")
    return f'<span class="{cls}">{cat}</span>'


def filtro_canal(chave: str, padrao: str = "Todos") -> str:
    opcoes = ["Todos", "Balcão", "Oficina"]
    return st.segmented_control("Canal de Venda", opcoes, default=padrao, key=chave) or padrao


def kpis(itens: list[tuple[str, str, str | None]]) -> None:
    """Grid de métricas KPI com hierarquia visual e tipografia tabular."""
    cols = st.columns(len(itens))
    for col, (rotulo, valor, ajuda) in zip(cols, itens):
        col.metric(rotulo, valor, help=ajuda)


def grafico(fig, altura: int = 340):
    """Aplica o tema visual profissional Deva nos gráficos Plotly."""
    fig.update_layout(
        height=altura,
        font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#334155"),
        title=dict(
            font=dict(family="Inter, -apple-system, sans-serif", size=14, color="#0F172A", weight=600),
            x=0.01,
            xanchor="left",
            y=0.96,
        ),
        margin=dict(l=16, r=16, t=46, b=24),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            x=0,
            title=None,
            font=dict(size=11, color="#475569"),
        ),
        separators=",.",
        hovermode="x unified" if fig.layout.xaxis.type == "date" else "closest",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#CBD5E1",
            font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#0F172A"),
        ),
    )
    # Suaviza eixos e gridlines
    fig.update_xaxes(
        showline=True,
        linecolor="#E2E8F0",
        gridcolor="#F8FAFC",
        tickfont=dict(size=11, color="#64748B"),
        title=None,
    )
    fig.update_yaxes(
        showline=False,
        gridcolor="#F1F5F9",
        tickfont=dict(size=11, color="#64748B"),
        title=None,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def barras_mensais(df, x, y, cor=None, mapa_cores=None, titulo=None):
    fig = px.bar(
        df,
        x=x,
        y=y,
        color=cor,
        color_discrete_map=mapa_cores,
        title=titulo,
    )
    fig.update_yaxes(tickprefix="R$ ")
    return fig


def dinheiro(rotulo: str):
    """Separador de milhar no padrão brasileiro (R$ 1.234,56)."""
    return st.column_config.NumberColumn(f"{rotulo} (R$)", format="localized")


def inteiro(rotulo: str):
    return st.column_config.NumberColumn(rotulo, format="%d")


def percentual(rotulo: str):
    """Valores percentuais com uma casa decimal."""
    return st.column_config.NumberColumn(rotulo, format="%.1f%%")


def data(rotulo: str):
    return st.column_config.DateColumn(rotulo, format="DD/MM/YYYY")


def ordem_categorias():
    return {"categoria": config.CATEGORIAS}


def seletor_cliente(chave: str, segmento: str = "Cliente"):
    cli = dados.tabela("clientes")
    base = cli[(cli["segmento"] == segmento) & (cli["canal"] == "Todos")].sort_values("faturamento", ascending=False)
    rotulos = dict(zip(base["cliente_cod"], base["cliente_nome"] + " · " + base["cliente_cod"].astype(str)
                       + " · " + base["categoria"]))
    pendente = navegacao.cliente_pendente()
    if pendente in rotulos:
        st.session_state[chave] = pendente
    cod = st.selectbox(
        "Selecione ou busque o cliente",
        list(rotulos),
        format_func=rotulos.get,
        key=chave,
        index=None,
        placeholder="Digite o nome, código ou categoria do cliente...",
    )
    return cod, cli


def tabela(df, **kwargs):
    """st.dataframe com decimais arredondados e preenchimento de largura total."""
    numericas = df.select_dtypes("float").columns
    kwargs.setdefault("hide_index", True)
    kwargs.setdefault("use_container_width", True)
    return st.dataframe(df.assign(**{c: df[c].round(2) for c in numericas}), **kwargs)


def md(texto: str) -> None:
    """st.markdown com escape para evitar conflito com LaTeX em valores monetários."""
    st.markdown(texto.replace("$", r"\$"))

"""Componentes visuais compartilhados pelas páginas."""
import plotly.express as px
import streamlit as st

from deva.core import config, dados, navegacao

AZUL = "#1F4E9C"
CORES_CATEGORIA = {
    "Fiel": "#1F7A4D", "Recorrente": "#4FA36F", "Novo": "#2F6FD0",
    "Ocasional": "#9AA5B1", "Em risco": "#E08A1E", "Perdido": "#C2412D",
}
CORES_GIRO = {"Alto": "#1F7A4D", "Médio": "#4FA36F", "Baixo": "#E08A1E", "Sem venda 12m": "#C2412D"}
CORES_SEGMENTO = {
    "Cliente": AZUL, "Mercado Livre": "#F2B705", "Garantia": "#7A869A",
    "Interno": "#B4BCC8", "Seguradora": "#8E5BB5",
}


def filtro_canal(chave: str, padrao: str = "Todos") -> str:
    opcoes = ["Todos", "Balcão", "Oficina"]
    return st.segmented_control("Canal", opcoes, default=padrao, key=chave) or padrao


def kpis(itens: list[tuple[str, str, str | None]]) -> None:
    cols = st.columns(len(itens))
    for col, (rotulo, valor, ajuda) in zip(cols, itens):
        col.metric(rotulo, valor, help=ajuda)


def grafico(fig, altura: int = 360):
    fig.update_layout(
        height=altura, margin=dict(l=10, r=10, t=50, b=10),
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0, title=None),
        separators=",.", hovermode="x unified" if fig.layout.xaxis.type == "date" else "closest",
    )
    st.plotly_chart(fig, use_container_width=True)


def barras_mensais(df, x, y, cor=None, mapa_cores=None, titulo=None):
    fig = px.bar(df, x=x, y=y, color=cor, color_discrete_map=mapa_cores, title=titulo)
    fig.update_yaxes(tickprefix="R$ ", title=None)
    fig.update_xaxes(title=None)
    return fig


def dinheiro(rotulo: str):
    """Separador de milhar no padrão do navegador (pt-BR: 1.234,56)."""
    return st.column_config.NumberColumn(f"{rotulo} (R$)", format="localized")


def inteiro(rotulo: str):
    return st.column_config.NumberColumn(rotulo, format="%d")


def percentual(rotulo: str):
    """Use com valores já multiplicados por 100."""
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
    cod = st.selectbox("Cliente", list(rotulos), format_func=rotulos.get, key=chave, index=None,
                       placeholder="Digite o nome ou o código do cliente")
    return cod, cli


def tabela(df, **kwargs):
    """st.dataframe com decimais arredondados (o formato 'localized' não fixa casas)."""
    numericas = df.select_dtypes("float").columns
    kwargs.setdefault("hide_index", True)
    kwargs.setdefault("use_container_width", True)
    return st.dataframe(df.assign(**{c: df[c].round(2) for c in numericas}), **kwargs)


def md(texto: str) -> None:
    """st.markdown sem interpretar "R$ ... $" como fórmula LaTeX."""
    st.markdown(texto.replace("$", r"\$"))

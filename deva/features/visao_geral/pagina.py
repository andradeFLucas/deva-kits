import plotly.express as px
import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import brl_curto, data_br, num, pct


def render():
    st.title("Visão geral")
    canal = ui.filtro_canal("vg_canal")
    ref = dados.consulta("SELECT max(data) AS ref FROM vendas")["ref"].iloc[0]
    st.caption(f"Dados até {data_br(ref)}. Valores líquidos de devoluções.")

    filtro = "" if canal == "Todos" else "AND canal = ?"
    params = () if canal == "Todos" else (canal,)
    k = dados.consulta(f"""
        SELECT sum(valor) AS fat, sum(margem) AS margem, count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS nfs,
               count(DISTINCT cliente_cod) FILTER (WHERE sinal = 1) AS clientes,
               -sum(valor) FILTER (WHERE sinal = -1) AS devol
        FROM vendas WHERE data > (SELECT max(data) FROM vendas) - INTERVAL 365 DAY
          AND segmento = 'Cliente' {filtro}""", params).iloc[0]
    ui.kpis([
        ("Faturamento 12m (clientes)", brl_curto(k.fat), "Somente o segmento Cliente: sem garantia, interno, seguradoras e Mercado Livre"),
        ("Clientes ativos 12m", num(k.clientes), None),
        ("Ticket médio por nota", brl_curto(k.fat / max(k.nfs, 1)), None),
        ("Margem de contribuição", pct(k.margem / k.fat if k.fat else None), None),
        ("Devoluções 12m", brl_curto(k.devol), None),
    ])

    mensal = dados.consulta(f"""
        SELECT mes, segmento, sum(valor) AS faturamento FROM vendas WHERE 1=1 {filtro}
        GROUP BY ALL ORDER BY mes""", params)
    ui.grafico(ui.barras_mensais(mensal, "mes", "faturamento", "segmento", ui.CORES_SEGMENTO, "Faturamento mensal por segmento"))

    c1, c2 = st.columns(2)
    cli = dados.tabela("clientes")
    cli = cli[(cli["segmento"] == "Cliente") & (cli["canal"] == canal)]
    cat = cli.groupby("categoria").agg(clientes=("cliente_cod", "count"), faturamento_12m=("faturamento_12m", "sum")).reset_index()
    with c1:
        fig = px.bar(cat, x="categoria", y="clientes", color="categoria", color_discrete_map=ui.CORES_CATEGORIA,
                     category_orders=ui.ordem_categorias(), title="Clientes por categoria")
        fig.update_layout(showlegend=False)
        ui.grafico(fig, 320)
    with c2:
        fig = px.bar(cat, x="categoria", y="faturamento_12m", color="categoria", color_discrete_map=ui.CORES_CATEGORIA,
                     category_orders=ui.ordem_categorias(), title="Faturamento 12m por categoria")
        fig.update_layout(showlegend=False)
        fig.update_yaxes(tickprefix="R$ ", title=None)
        ui.grafico(fig, 320)

    lojas = dados.consulta(f"""
        SELECT loja, segmento, sum(valor) AS faturamento FROM vendas
        WHERE data > (SELECT max(data) FROM vendas) - INTERVAL 365 DAY {filtro} GROUP BY ALL""", params)
    fig = px.bar(lojas, y="loja", x="faturamento", color="segmento", orientation="h",
                 color_discrete_map=ui.CORES_SEGMENTO, title="Faturamento 12m por loja")
    fig.update_yaxes(categoryorder="total ascending", title=None)
    fig.update_xaxes(tickprefix="R$ ", title=None)
    ui.grafico(fig, 320)

    st.subheader("Leituras automáticas")
    ui.md(_leituras(cli))


def _leituras(cli) -> str:
    if cli.empty:
        return "Sem dados."
    ordem = cli.sort_values("faturamento", ascending=False)
    total = ordem["faturamento"].sum()
    top1 = ordem.head(max(1, len(ordem) // 100))["faturamento"].sum() / total
    top20 = ordem.head(max(1, len(ordem) // 5))["faturamento"].sum() / total
    unica = (cli["dias_compra"] == 1).mean()
    fieis = cli[cli["categoria"] == "Fiel"]
    risco = cli[cli["categoria"] == "Em risco"]
    linhas = [
        f"- **Concentração:** 1% dos clientes faz {pct(top1, 0)} do faturamento; 20% fazem {pct(top20, 0)}.",
        f"- **Compra única:** {pct(unica, 0)} dos clientes compraram em um único dia. Converter a segunda compra é a maior alavanca de base.",
        f"- **Fiéis:** {num(len(fieis))} clientes ({pct(len(fieis) / len(cli), 1)}) respondem por {pct(fieis['faturamento_12m'].sum() / max(cli['faturamento_12m'].sum(), 1), 0)} do faturamento dos últimos 12 meses.",
        f"- **Em risco:** {num(len(risco))} clientes que tinham hábito de compra sumiram além do normal. Eles faturaram {brl_curto(risco['faturamento_12m_anterior'].sum())} no período de 12 a 24 meses atrás.",
    ]
    return "\n".join(linhas)

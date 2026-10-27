import plotly.express as px
import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import brl_curto, data_br, num, pct


def render():
    st.title("Painel Executivo · Visão Geral")
    canal = ui.filtro_canal("vg_canal")
    ref = dados.consulta("SELECT max(data) AS ref FROM vendas")["ref"].iloc[0]
    st.caption(f"Posição consolidada com vendas até {data_br(ref)}. Valores líquidos de devoluções.")

    filtro = "" if canal == "Todos" else "AND canal = ?"
    params = () if canal == "Todos" else (canal,)
    k = dados.consulta(f"""
        SELECT sum(valor) AS fat, sum(margem) AS margem, count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS nfs,
               count(DISTINCT cliente_cod) FILTER (WHERE sinal = 1) AS clientes,
               -sum(valor) FILTER (WHERE sinal = -1) AS devol
        FROM vendas WHERE data > (SELECT max(data) FROM vendas) - INTERVAL 365 DAY
          AND segmento = 'Cliente' {filtro}""", params).iloc[0]

    ui.kpis([
        ("Faturamento 12m (Clientes)", brl_curto(k.fat), "Somente o segmento Cliente (exclui garantia, interno, seguradoras e Mercado Livre)"),
        ("Clientes Ativos 12m", num(k.clientes), "Clientes com ao menos uma nota fiscal nos últimos 12 meses"),
        ("Ticket Médio por Nota", brl_curto(k.fat / max(k.nfs, 1)), "Faturamento total dividido pelo número de notas emitidas"),
        ("Margem de Contribuição", pct(k.margem / k.fat if k.fat else None), "Margem bruta sobre o faturamento líquido"),
        ("Devoluções no Período", brl_curto(k.devol), "Total de mercadorias devolvidas nos últimos 12 meses"),
    ])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    mensal = dados.consulta(f"""
        SELECT mes, segmento, sum(valor) AS faturamento FROM vendas WHERE 1=1 {filtro}
        GROUP BY ALL ORDER BY mes""", params)
    ui.grafico(
        ui.barras_mensais(mensal, "mes", "faturamento", "segmento", ui.CORES_SEGMENTO, "Evolução do Faturamento Mensal por Segmento"),
        altura=320,
    )

    c1, c2 = st.columns(2)
    cli = dados.tabela("clientes")
    cli = cli[(cli["segmento"] == "Cliente") & (cli["canal"] == canal)]
    cat = cli.groupby("categoria").agg(
        clientes=("cliente_cod", "count"),
        faturamento_12m=("faturamento_12m", "sum"),
    ).reset_index()

    with c1:
        fig1 = px.bar(
            cat,
            x="categoria",
            y="clientes",
            color="categoria",
            color_discrete_map=ui.CORES_CATEGORIA,
            category_orders=ui.ordem_categorias(),
            title="Base de Clientes por Categoria",
        )
        fig1.update_layout(showlegend=False)
        ui.grafico(fig1, 300)

    with c2:
        fig2 = px.bar(
            cat,
            x="categoria",
            y="faturamento_12m",
            color="categoria",
            color_discrete_map=ui.CORES_CATEGORIA,
            category_orders=ui.ordem_categorias(),
            title="Faturamento 12m por Categoria",
        )
        fig2.update_layout(showlegend=False)
        fig2.update_yaxes(tickprefix="R$ ")
        ui.grafico(fig2, 300)

    lojas = dados.consulta(f"""
        SELECT loja, segmento, sum(valor) AS faturamento FROM vendas
        WHERE data > (SELECT max(data) FROM vendas) - INTERVAL 365 DAY {filtro} GROUP BY ALL""", params)
    fig_lojas = px.bar(
        lojas,
        y="loja",
        x="faturamento",
        color="segmento",
        orientation="h",
        color_discrete_map=ui.CORES_SEGMENTO,
        title="Faturamento 12m por Concessionária / Filial",
    )
    fig_lojas.update_yaxes(categoryorder="total ascending")
    fig_lojas.update_xaxes(tickprefix="R$ ")
    ui.grafico(fig_lojas, 280)

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.subheader("Leituras Estratégicas da Carteira")
    _render_leituras_cards(cli)


def _render_leituras_cards(cli):
    if cli.empty:
        st.info("Sem dados disponíveis para a seleção atual.")
        return

    ordem = cli.sort_values("faturamento", ascending=False)
    total = ordem["faturamento"].sum()
    top1 = ordem.head(max(1, len(ordem) // 100))["faturamento"].sum() / total if total else 0
    top20 = ordem.head(max(1, len(ordem) // 5))["faturamento"].sum() / total if total else 0
    unica = (cli["dias_compra"] == 1).mean()
    fieis = cli[cli["categoria"] == "Fiel"]
    risco = cli[cli["categoria"] == "Em risco"]
    fat_total_12m = max(cli["faturamento_12m"].sum(), 1)
    fat_fieis = fieis["faturamento_12m"].sum() / fat_total_12m

    st.markdown(
        f"""
        <div class="deva-insight-grid">
            <div class="deva-insight-item">
                <div class="deva-insight-title">Concentração de Receita</div>
                <div class="deva-insight-body">
                    <strong>1% dos clientes</strong> representa <strong>{pct(top1, 0)}</strong> do faturamento acumulado, enquanto o Top 20% responde por <strong>{pct(top20, 0)}</strong> da receita.
                </div>
            </div>
            <div class="deva-insight-item">
                <div class="deva-insight-title">Alavanca de Segunda Compra</div>
                <div class="deva-insight-body">
                    <strong>{pct(unica, 0)}</strong> dos clientes compraram apenas uma única vez. Converter a segunda compra é a principal alavanca de expansão da carteira ativa.
                </div>
            </div>
            <div class="deva-insight-item">
                <div class="deva-insight-title">Núcleo Fiel da Concessionária</div>
                <div class="deva-insight-body">
                    <strong>{num(len(fieis))} clientes fiéis</strong> ({pct(len(fieis) / len(cli), 1)} da base) geram <strong>{pct(fat_fieis, 0)}</strong> de todo o faturamento dos últimos 12 meses.
                </div>
            </div>
            <div class="deva-insight-item">
                <div class="deva-insight-title">Oportunidade em Risco</div>
                <div class="deva-insight-body">
                    <strong>{num(len(risco))} clientes</strong> com frequência histórica estão sumidos além do intervalo normal. Eles faturaram <strong>{brl_curto(risco['faturamento_12m_anterior'].sum())}</strong> no ciclo anterior.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

"""Garantia Iveco, consumo interno e seguradoras: canais operacionais analisados separadamente."""
import streamlit as st

from deva.core import config, dados, ui
from deva.core.formatacao import brl_curto, num, pct


def render():
    st.title("Segmentos Especiais · Garantia, Interno & Seguradoras")
    st.caption("Canais de demanda com dinâmicas operacionais específicas: garantia montadora (Iveco), consumo próprio de oficina/frota e sinistros de seguradoras.")

    seg = st.segmented_control("Segmento Específico", config.SEGMENTOS_ESPECIAIS, default="Seguradora") or "Seguradora"

    cli = dados.tabela("clientes")
    cli = cli[(cli["segmento"] == seg) & (cli["canal"] == "Todos")].sort_values("faturamento", ascending=False)

    ui.kpis([
        ("Faturamento Acumulado", brl_curto(cli["faturamento"].sum()), "Desde 2024"),
        ("Faturamento 12m", brl_curto(cli["faturamento_12m"].sum()), "Últimos 12 meses móveis"),
        ("Tendência Anual", pct(cli["faturamento_12m"].sum() / max(cli["faturamento_12m_anterior"].sum(), 1) - 1, 0, sinal=True), "Comparado aos 12 meses anteriores"),
        ("Total de Contas / Pagadores", num(len(cli)), "Entidades cadastradas no segmento"),
    ])

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    mensal = dados.consulta("SELECT mes, canal, sum(valor) AS faturamento FROM vendas WHERE segmento = ? GROUP BY ALL ORDER BY mes", (seg,))
    ui.grafico(
        ui.barras_mensais(mensal, "mes", "faturamento", "canal", {"Balcão": ui.AZUL, "Oficina": "#15803D"},
                         f"Evolução Mensal do Faturamento em {seg}"),
        altura=280,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Principais Entidades Pagadoras")
        t = cli.assign(tendencia_12m=cli["tendencia_12m"] * 100)
        ui.tabela(
            t[["cliente_nome", "faturamento", "faturamento_12m", "tendencia_12m", "nfs", "recencia_dias"]],
            column_config={
                "cliente_nome": st.column_config.TextColumn("Nome / Razão Social", width="medium"),
                "faturamento": ui.dinheiro("Total"),
                "faturamento_12m": ui.dinheiro("12 Meses"),
                "tendencia_12m": st.column_config.NumberColumn("Tendência", format="%+.0f%%"),
                "nfs": ui.inteiro("Notas"),
                "recencia_dias": ui.inteiro("Dias sem Faturar"),
            },
        )

    with c2:
        st.subheader("Peças Mais Requisitadas")
        itens = dados.consulta("""
            SELECT arg_max(produto_des, data) AS produto, arg_max(referencia, data) AS referencia,
                   sum(qtde) AS qtde, sum(valor) AS faturamento
            FROM vendas WHERE segmento = ? GROUP BY produto_cod ORDER BY faturamento DESC LIMIT 50""", (seg,))
        ui.tabela(
            itens,
            column_config={
                "produto": st.column_config.TextColumn("Descrição do Item", width="large"),
                "referencia": "Referência",
                "qtde": st.column_config.NumberColumn("Quantidade", format="%.0f"),
                "faturamento": ui.dinheiro("Faturamento"),
            },
        )

"""Garantia, venda interna e seguradoras: separados dos clientes para análise própria."""
import streamlit as st

from deva.core import config, dados, ui
from deva.core.formatacao import brl_curto, num, pct


def render():
    st.title("Garantia, interno e seguradoras")
    st.caption("Esses segmentos ficam fora das categorias de clientes, porque compram por outro motivo (garantia Iveco, "
               "uso interno, sinistro). Aqui dá para acompanhar cada um e trabalhar as seguradoras como canal comercial.")
    seg = st.segmented_control("Segmento", config.SEGMENTOS_ESPECIAIS, default="Seguradora") or "Seguradora"

    cli = dados.tabela("clientes")
    cli = cli[(cli["segmento"] == seg) & (cli["canal"] == "Todos")].sort_values("faturamento", ascending=False)
    ui.kpis([
        ("Faturamento total", brl_curto(cli["faturamento"].sum()), None),
        ("Faturamento 12m", brl_curto(cli["faturamento_12m"].sum()), None),
        ("Tendência 12m", pct(cli["faturamento_12m"].sum() / max(cli["faturamento_12m_anterior"].sum(), 1) - 1, 0, sinal=True), None),
        ("Pagadores", num(len(cli)), None),
    ])
    mensal = dados.consulta("SELECT mes, canal, sum(valor) AS faturamento FROM vendas WHERE segmento = ? GROUP BY ALL ORDER BY mes", (seg,))
    ui.grafico(ui.barras_mensais(mensal, "mes", "faturamento", "canal", {"Balcão": ui.AZUL, "Oficina": "#4FA36F"},
                                 "Faturamento mensal"), 300)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Quem paga")
        t = cli.assign(tendencia_12m=cli["tendencia_12m"] * 100)
        ui.tabela(t[["cliente_nome", "faturamento", "faturamento_12m", "tendencia_12m", "nfs", "recencia_dias"]],
                     column_config={
                         "cliente_nome": "Nome", "faturamento": ui.dinheiro("Faturamento"), "faturamento_12m": ui.dinheiro("Fat. 12m"),
                         "tendencia_12m": st.column_config.NumberColumn("Tendência", format="%+.0f%%"),
                         "nfs": ui.inteiro("Notas"), "recencia_dias": ui.inteiro("Dias sem comprar"),
                     })
    with c2:
        st.subheader("Itens mais usados")
        itens = dados.consulta("""
            SELECT arg_max(produto_des, data) AS produto, arg_max(referencia, data) AS referencia,
                   sum(qtde) AS qtde, sum(valor) AS faturamento
            FROM vendas WHERE segmento = ? GROUP BY produto_cod ORDER BY faturamento DESC LIMIT 50""", (seg,))
        ui.tabela(itens, column_config={
            "produto": "Produto", "referencia": "Referência", "qtde": st.column_config.NumberColumn("Qtde", format="%.0f"),
            "faturamento": ui.dinheiro("Faturamento"),
        })

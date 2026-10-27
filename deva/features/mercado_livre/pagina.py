"""Mercado Livre: análise separada + kits por produto para subir o ticket do pedido."""
import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import brl_curto, num, pct

SQL_KIT_PRODUTO = """
SELECT p.produto_des, p.referencia, p.faixa_giro, p.preco_ref, af.score,
       af.score * (0.35 + 0.65 * p.baixo_giro_score) AS prioridade
FROM afinidade af
JOIN produtos p ON p.canal = 'Todos' AND p.produto_cod = af.b
WHERE af.a = ?
ORDER BY prioridade DESC
LIMIT 6
"""


def render():
    st.title("Mercado Livre")
    k = dados.consulta("""
        WITH v AS (SELECT * FROM vendas WHERE segmento = 'Mercado Livre'),
        c AS (SELECT cliente_cod, count(DISTINCT CAST(data AS DATE)) AS dias FROM v WHERE sinal = 1 GROUP BY 1)
        SELECT (SELECT sum(valor) FROM v) AS fat,
               (SELECT count(DISTINCT nf_id) FROM v WHERE sinal = 1) AS pedidos,
               (SELECT count(*) FROM c) AS clientes,
               (SELECT avg((dias > 1)::INT) FROM c) AS recompra,
               (SELECT avg(n) FROM (SELECT count(*) AS n FROM v WHERE sinal = 1 GROUP BY nf_id)) AS itens_pedido
    """).iloc[0]
    ui.kpis([
        ("Faturamento", brl_curto(k.fat), None),
        ("Pedidos (NFs)", num(k.pedidos), None),
        ("Ticket médio", brl_curto(k.fat / max(k.pedidos, 1)), None),
        ("Itens por pedido", num(k.itens_pedido, 2), None),
        ("Clientes que recompraram", pct(k.recompra, 0), None),
    ])
    st.caption("Quase todo pedido do Mercado Livre tem um item só. O kit tem que estar no anúncio (\"compre junto\"), "
               "porque o cliente raramente volta.")

    mensal = dados.consulta("""
        SELECT mes, sum(valor) AS faturamento, count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS pedidos
        FROM vendas WHERE segmento = 'Mercado Livre' GROUP BY 1 ORDER BY 1""")
    ui.grafico(ui.barras_mensais(mensal, "mes", "faturamento", titulo="Faturamento mensal"), 300)

    top = dados.consulta("""
        SELECT produto_cod, arg_max(produto_des, data) AS produto_des, arg_max(referencia, data) AS referencia,
               count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS pedidos, sum(qtde) AS qtde, sum(valor) AS faturamento
        FROM vendas WHERE segmento = 'Mercado Livre' GROUP BY 1 ORDER BY pedidos DESC LIMIT 100""")
    st.subheader("Produtos mais vendidos e kit sugerido")
    st.caption("Clique num produto para ver o \"compre junto\" sugerido, que prioriza baixo giro compatível.")
    sel = ui.tabela(top, height=360, on_select="rerun",
                       selection_mode="single-row", column_config={
                           "produto_cod": None, "produto_des": "Produto", "referencia": "Referência",
                           "pedidos": ui.inteiro("Pedidos"), "qtde": st.column_config.NumberColumn("Qtde", format="%.0f"),
                           "faturamento": ui.dinheiro("Faturamento"),
                       })
    if top.empty:
        return
    i = sel.selection.rows[0] if sel.selection.rows else 0
    prod = top.iloc[i]
    kit = dados.consulta(SQL_KIT_PRODUTO, (int(prod["produto_cod"]),))
    ui.md(f"**Compre junto com {prod['produto_des']} ({prod['referencia']}):**")
    if kit.empty:
        st.info("Sem itens compatíveis com histórico suficiente.")
    else:
        ui.tabela(kit, column_config={
            "produto_des": "Produto", "referencia": "Referência", "faixa_giro": "Giro", "preco_ref": ui.dinheiro("Preço médio"),
            "score": st.column_config.ProgressColumn("Compatibilidade", min_value=0, max_value=1, format="%.2f"),
            "prioridade": None,
        })

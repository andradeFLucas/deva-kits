"""Mercado Livre: análise do canal digital e sugestão de combos 'compre junto' para expansão de ticket."""
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
    st.title("Canal Digital · Mercado Livre")
    st.caption("Acompanhamento das vendas no marketplace e inteligência para montagem de anúncios combinados ('Compre Junto').")

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
        ("Faturamento Acumulado", brl_curto(k.fat), "Receita total gerada no canal Mercado Livre"),
        ("Pedidos Concluídos (NFs)", num(k.pedidos), "Documentos fiscais emitidos"),
        ("Ticket Médio por Pedido", brl_curto(k.fat / max(k.pedidos, 1)), "Faturamento ÷ pedidos"),
        ("Itens por Pedido", num(k.itens_pedido, 2), "Média de peças por carrinho"),
        ("Taxa de Recompra", pct(k.recompra, 0), "Clientes que efetuaram mais de 1 compra no marketplace"),
    ])

    st.markdown(
        """
        <div style="background-color: #FFFBEB; border: 1px solid #FDE68A; border-radius: 6px; padding: 10px 14px; margin: 12px 0 16px 0; font-size: 0.85rem; color: #92400E;">
            <strong>Diagnóstico do Canal:</strong> O consumidor de marketplace tem perfil pontual e raramente retorna para recompra direta.
            Para elevar a margem e o ticket médio, monte <strong>anúncios com kits de produtos correlacionados</strong> ("Compre Junto"),
            incorporando peças de baixo giro antes do fechamento do carrinho.
        </div>
        """,
        unsafe_allow_html=True,
    )

    mensal = dados.consulta("""
        SELECT mes, sum(valor) AS faturamento, count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS pedidos
        FROM vendas WHERE segmento = 'Mercado Livre' GROUP BY 1 ORDER BY 1""")
    ui.grafico(
        ui.barras_mensais(mensal, "mes", "faturamento", mapa_cores={"Mercado Livre": "#D97706"}, titulo="Faturamento Mensal no Mercado Livre"),
        altura=280,
    )

    top = dados.consulta("""
        SELECT produto_cod, arg_max(produto_des, data) AS produto_des, arg_max(referencia, data) AS referencia,
               count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS pedidos, sum(qtde) AS qtde, sum(valor) AS faturamento
        FROM vendas WHERE segmento = 'Mercado Livre' GROUP BY 1 ORDER BY pedidos DESC LIMIT 100""")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.subheader("Produtos Mais Vendidos & Sugestão de Anúncios Combinados")
    st.caption("Clique sobre qualquer item na lista para ver os produtos recomendados para compor o anúncio combinado.")

    sel = ui.tabela(
        top,
        height=320,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "produto_cod": None,
            "produto_des": st.column_config.TextColumn("Produto Anunciado", width="large"),
            "referencia": "Referência",
            "pedidos": ui.inteiro("Pedidos"),
            "qtde": st.column_config.NumberColumn("Qtde Vendida", format="%.0f"),
            "faturamento": ui.dinheiro("Faturamento Gerado"),
        },
    )

    if top.empty:
        return

    i = sel.selection.rows[0] if sel.selection.rows else 0
    prod = top.iloc[i]
    kit = dados.consulta(SQL_KIT_PRODUTO, (int(prod["produto_cod"]),))

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #D97706; letter-spacing: 0.05em;">Oportunidade de Kit Digital</div>
            <h4 style="margin: 2px 0 8px 0; color: #0F172A;">Compre Junto: {prod['produto_des']} ({prod['referencia']})</h4>
            """,
            unsafe_allow_html=True,
        )
        if kit.empty:
            st.info("Sem itens com histórico de afinidade suficiente para este produto.")
        else:
            ui.tabela(
                kit,
                column_config={
                    "produto_des": st.column_config.TextColumn("Item Adicional Sugerido", width="large"),
                    "referencia": "Referência",
                    "faixa_giro": "Giro",
                    "preco_ref": ui.dinheiro("Preço Médio"),
                    "score": st.column_config.ProgressColumn("Compatibilidade Mecânica", min_value=0, max_value=1, format="%.2f"),
                    "prioridade": None,
                },
            )

import plotly.express as px
import streamlit as st

from deva.core import config, dados, ui
from deva.core.formatacao import num

COLUNAS = {
    "produto_des": "Produto", "referencia": "Referência", "classe_giro": "Classe estoque", "faixa_giro": "Giro",
    "nfs_12m": ui.inteiro("Notas 12m"), "qtde_12m": st.column_config.NumberColumn("Qtde 12m", format="%.0f"),
    "clientes_12m": ui.inteiro("Clientes 12m"), "faturamento_12m": ui.dinheiro("Fat. 12m"),
    "faturamento": ui.dinheiro("Fat. total"), "preco_ref": ui.dinheiro("Preço médio"),
    "margem_pct": ui.percentual("Margem"), "dias_sem_venda": ui.inteiro("Dias sem venda"),
    "ultima_venda": ui.data("Última venda"),
    "intervalo_reposicao_dias": st.column_config.NumberColumn("Reposição típica (dias)", format="%.0f"),
}


def render():
    st.title("Produtos")
    canal = ui.filtro_canal("pr_canal")
    df = dados.tabela("produtos")
    df = df[df["canal"] == canal].assign(margem_pct=lambda d: d["margem_pct"] * 100)

    contagem = df["faixa_giro"].value_counts()
    ui.kpis([
        ("Códigos vendidos", num(len(df)), "Desde jan/2024"),
        ("Giro alto (≥52 notas/ano)", num(contagem.get("Alto", 0)), None),
        ("Giro médio (12 a 51)", num(contagem.get("Médio", 0)), None),
        ("Giro baixo (1 a 11)", num(contagem.get("Baixo", 0)), None),
        ("Sem venda em 12m", num(contagem.get("Sem venda 12m", 0)), None),
    ])
    st.info("A base de estoque ainda não foi carregada: o giro aqui vem só das vendas. Quando o estoque entrar, "
            "esta página vai mostrar também a quantidade e o valor parado de cada código.", icon="📦")

    busca = st.text_input("Buscar por descrição ou referência")
    if busca:
        df = df[df["produto_des"].str.contains(busca, case=False, na=False) | df["referencia"].str.contains(busca, case=False, na=False)]

    mais, menos, giro = st.tabs(["Mais vendidos", "Menos vendidos", "Giro × classe de estoque"])
    with mais:
        criterio = st.radio("Ordenar por", ["Notas 12m", "Faturamento 12m", "Quantidade 12m"], horizontal=True)
        col = {"Notas 12m": "nfs_12m", "Faturamento 12m": "faturamento_12m", "Quantidade 12m": "qtde_12m"}[criterio]
        top = df.sort_values(col, ascending=False).head(200)
        # descrição + referência: códigos diferentes podem ter a mesma descrição
        top20 = top.head(20).assign(item=lambda d: d["produto_des"] + " · " + d["referencia"])
        fig = px.bar(top20, x=col, y="item", orientation="h",
                     title=f"Top 20 por {criterio.lower()}")
        fig.update_yaxes(categoryorder="total ascending", title=None)
        fig.update_xaxes(title=None)
        ui.grafico(fig, 520)
        ui.tabela(top[["produto_des", "referencia", "faixa_giro", "nfs_12m", "qtde_12m", "clientes_12m", "faturamento_12m",
                          "preco_ref", "margem_pct", "intervalo_reposicao_dias"]],
                     column_config=COLUNAS)
    with menos:
        faixas = st.multiselect("Faixas de giro", ["Baixo", "Sem venda 12m"], default=["Baixo", "Sem venda 12m"])
        baixo = df[df["faixa_giro"].isin(faixas)].sort_values(["baixo_giro_score", "faturamento"], ascending=[False, False])
        st.caption(f"{num(len(baixo))} códigos. Ordenados do que menos gira para o que mais gira; em caso de empate, "
                   "pelo que já faturou mais, porque provavelmente ainda tem estoque. Esses são os itens priorizados nos kits.")
        ui.tabela(baixo[["produto_des", "referencia", "classe_giro", "faixa_giro", "nfs_12m", "dias_sem_venda", "ultima_venda",
                            "faturamento", "preco_ref"]],
                     height=520, column_config=COLUNAS)
        st.download_button("Baixar CSV", baixo.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                           "itens_baixo_giro.csv", "text/csv")
    with giro:
        cruz = df.groupby(["classe_giro", "faixa_giro"]).size().reset_index(name="codigos")
        fig = px.bar(cruz, x="classe_giro", y="codigos", color="faixa_giro", color_discrete_map=ui.CORES_GIRO,
                     category_orders={"faixa_giro": config.FAIXAS_GIRO},
                     title="Classe de giro do estoque (ERP) × giro real de vendas")
        fig.update_xaxes(categoryorder="category ascending", title="Classe no ERP")
        fig.update_yaxes(title="Códigos")
        ui.grafico(fig, 400)
        st.caption("Itens com classe A no ERP mas giro baixo nas vendas merecem revisão da classificação de estoque.")

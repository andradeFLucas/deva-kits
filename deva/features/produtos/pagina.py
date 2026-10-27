import plotly.express as px
import streamlit as st

from deva.core import config, dados, ui
from deva.core.formatacao import num

COLUNAS = {
    "produto_des": st.column_config.TextColumn("Descrição do Produto", width="large"),
    "referencia": st.column_config.TextColumn("Referência", width="small"),
    "classe_giro": st.column_config.TextColumn("Classe ERP", width="small"),
    "faixa_giro": st.column_config.TextColumn("Giro Real", width="small"),
    "nfs_12m": ui.inteiro("Notas 12m"),
    "qtde_12m": st.column_config.NumberColumn("Qtde 12m", format="%.0f"),
    "clientes_12m": ui.inteiro("Clientes 12m"),
    "faturamento_12m": ui.dinheiro("Fat. 12m"),
    "faturamento": ui.dinheiro("Fat. Total"),
    "preco_ref": ui.dinheiro("Preço Médio"),
    "margem_pct": ui.percentual("Margem"),
    "dias_sem_venda": ui.inteiro("Dias sem Venda"),
    "ultima_venda": ui.data("Última Venda"),
    "intervalo_reposicao_dias": st.column_config.NumberColumn("Reposição Típica (dias)", format="%.0f"),
}


def render():
    st.title("Painel de Produtos & Giro de Estoque")
    st.caption("Visão da demanda real de peças, cruzamento de giro de vendas com classificação de estoque e itens prioritários para kits.")

    canal = ui.filtro_canal("pr_canal")
    df = dados.tabela("produtos")
    df = df[df["canal"] == canal].assign(margem_pct=lambda d: d["margem_pct"] * 100)

    contagem = df["faixa_giro"].value_counts()
    ui.kpis([
        ("Códigos Movimentados", num(len(df)), "Total de códigos com venda desde jan/2024"),
        ("Giro Alto (≥52 nfs/ano)", num(contagem.get("Alto", 0)), "Peças de saída semanal contínua"),
        ("Giro Médio (12 a 51)", num(contagem.get("Médio", 0)), "Peças de saída mensal regular"),
        ("Giro Baixo (1 a 11)", num(contagem.get("Baixo", 0)), "Peças com demanda espaçada"),
        ("Sem Venda em 12m", num(contagem.get("Sem venda 12m", 0)), "Estoque potencialmente estagnado"),
    ])

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.info("A base de saldo físico de estoque será integrada nas próximas versões. O giro atual reflete a demanda real medida pelo faturamento de balcão e oficina.", icon=":material/info:")

    busca = st.text_input("Buscar produto por descrição ou referência", placeholder="Ex: filtro, pastilha, óleo...")
    if busca:
        df = df[df["produto_des"].str.contains(busca, case=False, na=False) | df["referencia"].str.contains(busca, case=False, na=False)]

    mais, menos, giro = st.tabs(["Mais Vendidos", "Estoque Parado & Baixo Giro", "Giro Real × Classe ERP"])

    with mais:
        criterio = st.radio("Métrica de Ordenação:", ["Notas 12m", "Faturamento 12m", "Quantidade 12m"], horizontal=True)
        col = {"Notas 12m": "nfs_12m", "Faturamento 12m": "faturamento_12m", "Quantidade 12m": "qtde_12m"}[criterio]
        top = df.sort_values(col, ascending=False).head(200)
        top20 = top.head(20).assign(item=lambda d: d["produto_des"] + " (" + d["referencia"] + ")")
        fig = px.bar(
            top20,
            x=col,
            y="item",
            orientation="h",
            title=f"Top 20 Produtos por {criterio}",
            color_discrete_sequence=[ui.AZUL],
        )
        fig.update_yaxes(categoryorder="total ascending")
        ui.grafico(fig, 480)
        ui.tabela(
            top[["produto_des", "referencia", "faixa_giro", "nfs_12m", "qtde_12m", "clientes_12m", "faturamento_12m",
                 "preco_ref", "margem_pct", "intervalo_reposicao_dias"]],
            column_config=COLUNAS,
        )

    with menos:
        faixas = st.multiselect("Faixas de giro selecionadas:", ["Baixo", "Sem venda 12m"], default=["Baixo", "Sem venda 12m"])
        baixo = df[df["faixa_giro"].isin(faixas)].sort_values(["baixo_giro_score", "faturamento"], ascending=[False, False])
        st.caption(f"{num(len(baixo))} códigos encontrados. Ordenados pela urgência de desova para composição de kits de manutenção.")
        ui.tabela(
            baixo[["produto_des", "referencia", "classe_giro", "faixa_giro", "nfs_12m", "dias_sem_venda", "ultima_venda",
                   "faturamento", "preco_ref"]],
            height=480,
            column_config=COLUNAS,
        )
        st.download_button(
            "Exportar Itens Baixo Giro (CSV)",
            baixo.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            "itens_baixo_giro_deva.csv",
            "text/csv",
            type="secondary",
        )

    with giro:
        cruz = df.groupby(["classe_giro", "faixa_giro"]).size().reset_index(name="codigos")
        fig = px.bar(
            cruz,
            x="classe_giro",
            y="codigos",
            color="faixa_giro",
            color_discrete_map=ui.CORES_GIRO,
            category_orders={"faixa_giro": config.FAIXAS_GIRO},
            title="Classificação Teórica de Estoque (ERP) × Demanda Efetiva de Vendas",
        )
        fig.update_xaxes(categoryorder="category ascending", title="Classe de Estoque no ERP")
        fig.update_yaxes(title="Número de Códigos")
        ui.grafico(fig, 360)
        st.caption("Atenção: Itens classificados como A/B no ERP mas com giro baixo ou sem venda nas notas requerem revisão de parâmetros de compra.")

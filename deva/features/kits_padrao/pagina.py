import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import brl, num

METODO = """
**Como os kits foram montados (não existe plano de manutenção formal):**

1. **Mesmo veículo = mesma cesta.** Itens que saem juntos na mesma OS (oficina) ou na mesma NF (balcão) quase sempre
   vão para o mesmo caminhão. Medimos a força dessa ligação entre cada par de códigos.
2. **Kit padrão.** Para cada item muito presente (a âncora), juntamos os códigos com ligação forte com ele. Kits quase
   iguais são descartados.
3. **Periodicidade.** "Reposição típica" é a mediana do tempo que os clientes levam para recomprar o mesmo código.
   Itens do kit com periodicidade parecida formam uma revisão (ex.: ~120 dias = troca de óleo e filtros).
4. **Baixo giro agregado.** Para cada kit, listamos códigos de baixo giro compatíveis, para incluir na oferta e girar estoque.

Como o código exato importa (filtro de um caminhão não serve no outro), tudo é feito por código, nunca por família.
"""


def render():
    st.title("Kits e plano de manutenção")
    with st.expander("Como funciona", expanded=False):
        ui.md(METODO)

    kits = dados.tabela("kits_padrao")
    agregados = dados.tabela("kits_padrao_baixo_giro")
    if kits.empty:
        st.warning("Nenhum kit gerado. Rode o pipeline.")
        return

    resumo = kits.groupby(["kit_id", "kit_nome"]).agg(
        cestas=("cestas_ancora", "first"), itens=("produto_cod", "count"), valor=("preco_ref", "sum"),
        reposicao=("intervalo_reposicao_dias", "median"),
    ).reset_index().sort_values("cestas", ascending=False)

    busca = st.text_input("Buscar kit por item ou referência")
    if busca:
        ids = kits[kits["produto_des"].str.contains(busca, case=False, na=False)
                   | kits["referencia"].str.contains(busca, case=False, na=False)]["kit_id"].unique()
        resumo = resumo[resumo["kit_id"].isin(ids)]
        if resumo.empty:
            st.info("Nenhum kit contém esse item.")
            return

    st.caption(f"{num(len(resumo))} kits. Ordenados pela frequência da âncora em OS/NF.")
    sel = ui.tabela(resumo, height=320, on_select="rerun",
                       selection_mode="single-row", column_config={
                           "kit_id": None, "kit_nome": "Kit", "cestas": ui.inteiro("OS/NF com a âncora"),
                           "itens": ui.inteiro("Itens"), "valor": ui.dinheiro("Valor do kit (1 un. cada)"),
                           "reposicao": st.column_config.NumberColumn("Periodicidade típica (dias)", format="%.0f"),
                       })
    linhas = sel.selection.rows
    kit_id = resumo.iloc[linhas[0]]["kit_id"] if linhas else resumo.iloc[0]["kit_id"]
    k = kits[kits["kit_id"] == kit_id].sort_values("ordem")
    st.subheader(k["kit_nome"].iloc[0])
    ui.tabela(k[["produto_des", "referencia", "faixa_giro", "preco_ref", "intervalo_reposicao_dias", "forca_ligacao"]],
                 column_config={
                     "produto_des": "Produto", "referencia": "Referência", "faixa_giro": "Giro",
                     "preco_ref": ui.dinheiro("Preço médio"),
                     "intervalo_reposicao_dias": st.column_config.NumberColumn("Reposição típica (dias)", format="%.0f"),
                     "forca_ligacao": st.column_config.ProgressColumn("Força da ligação", min_value=0, max_value=1, format="%.2f"),
                 })
    a = agregados[agregados["kit_id"] == kit_id]
    ui.md(f"**Valor do kit:** {brl(k['preco_ref'].sum())}")
    if len(a):
        ui.md("**Itens de baixo giro compatíveis para agregar:**")
        ui.tabela(a[["produto_des", "referencia", "faixa_giro", "preco_ref", "dias_sem_venda"]],
                     use_container_width=True, column_config={
                         "produto_des": "Produto", "referencia": "Referência", "faixa_giro": "Giro",
                         "preco_ref": ui.dinheiro("Preço médio"), "dias_sem_venda": ui.inteiro("Dias sem venda"),
                     })

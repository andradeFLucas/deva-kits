import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import brl, num

METODO = """
**Engenharia de Composição dos Kits Inteligentes:**

1. **Mesmo Veículo = Mesma Cesta:** Peças que saem juntas na mesma Ordem de Serviço (Oficina) ou na mesma Nota Fiscal (Balcão) compartilham correlação mecânica para o mesmo veículo Iveco.
2. **Item Âncora:** Identifica-se a peça com maior frequência de demanda da família (a âncora) e agrupam-se as peças com forte associação estatística a ela.
3. **Periodicidade Típica:** Mediana do ciclo de recompra entre os clientes da casa, permitindo estruturar pacotes por quilometragem / tempo (ex.: revisões de 120 dias).
4. **Desova de Baixo Giro:** Incorporação de códigos de baixo giro compatíveis com desconto específico para girar estoque imobilizado.
"""


def render():
    st.title("Catálogo de Kits & Planos de Manutenção")
    st.caption("Kits de manutenção preventiva e corretiva derivados estatisticamente de ordens de serviço e notas fiscais.")

    with st.expander("Metodologia de formação dos kits", expanded=False):
        ui.md(METODO)

    kits = dados.tabela("kits_padrao")
    agregados = dados.tabela("kits_padrao_baixo_giro")
    if kits.empty:
        st.warning("Nenhum kit gerado. Execute o pipeline de processamento.")
        return

    resumo = kits.groupby(["kit_id", "kit_nome"]).agg(
        cestas=("cestas_ancora", "first"),
        itens=("produto_cod", "count"),
        valor=("preco_ref", "sum"),
        reposicao=("intervalo_reposicao_dias", "median"),
    ).reset_index().sort_values("cestas", ascending=False)

    busca = st.text_input("Buscar kit por peça ou número de referência", placeholder="Ex: filtro de ar, pastilha, correia...")
    if busca:
        ids = kits[kits["produto_des"].str.contains(busca, case=False, na=False)
                   | kits["referencia"].str.contains(busca, case=False, na=False)]["kit_id"].unique()
        resumo = resumo[resumo["kit_id"].isin(ids)]
        if resumo.empty:
            st.info("Nenhum kit padrão contém este item ou referência.")
            return

    st.caption(f"{num(len(resumo))} kits disponíveis no catálogo. Selecione uma linha abaixo para inspecionar os componentes.")
    sel = ui.tabela(
        resumo,
        height=320,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "kit_id": None,
            "kit_nome": st.column_config.TextColumn("Nome do Kit de Manutenção", width="large"),
            "cestas": ui.inteiro("OS / NFs com a Âncora"),
            "itens": ui.inteiro("Itens no Kit"),
            "valor": ui.dinheiro("Valor Médio (1 un. cada)"),
            "reposicao": st.column_config.NumberColumn("Periodicidade Sugerida (dias)", format="%.0f"),
        },
    )

    linhas = sel.selection.rows
    kit_id = resumo.iloc[linhas[0]]["kit_id"] if linhas else resumo.iloc[0]["kit_id"]
    k = kits[kits["kit_id"] == kit_id].sort_values("ordem")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #1A4B8C; letter-spacing: 0.05em;">Detalhes do Pacote</div>
            <h3 style="margin: 2px 0 10px 0; color: #0F172A;">{k['kit_nome'].iloc[0]}</h3>
            """,
            unsafe_allow_html=True,
        )
        ui.tabela(
            k[["produto_des", "referencia", "faixa_giro", "preco_ref", "intervalo_reposicao_dias", "forca_ligacao"]],
            column_config={
                "produto_des": st.column_config.TextColumn("Produto", width="large"),
                "referencia": st.column_config.TextColumn("Referência", width="small"),
                "faixa_giro": "Giro",
                "preco_ref": ui.dinheiro("Preço Médio Praticado"),
                "intervalo_reposicao_dias": st.column_config.NumberColumn("Ciclo Reposição (dias)", format="%.0f"),
                "forca_ligacao": st.column_config.ProgressColumn("Afinidade com a Âncora", min_value=0, max_value=1, format="%.2f"),
            },
        )
        st.markdown(f"**Valor total do pacote padrão:** `{brl(k['preco_ref'].sum())}`")

        a = agregados[agregados["kit_id"] == kit_id]
        if len(a):
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <strong style="color: #0F172A; font-size: 0.9rem;">
                    Itens de Baixo Giro Compatíveis para Agregar à Proposta Comercial:
                </strong>
                """,
                unsafe_allow_html=True,
            )
            ui.tabela(
                a[["produto_des", "referencia", "faixa_giro", "preco_ref", "dias_sem_venda"]],
                use_container_width=True,
                column_config={
                    "produto_des": st.column_config.TextColumn("Produto Oportunidade", width="large"),
                    "referencia": "Referência",
                    "faixa_giro": "Giro",
                    "preco_ref": ui.dinheiro("Preço Médio"),
                    "dias_sem_venda": ui.inteiro("Dias sem Venda"),
                },
            )

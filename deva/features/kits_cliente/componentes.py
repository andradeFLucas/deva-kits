import streamlit as st

from deva.core import config, ui
from deva.core.formatacao import brl, pct

ICONE = {"Âncora": "⚓ Âncora", "Mesmo serviço": "🔧 Mesmo serviço", "Baixo giro": "⭐ Baixo giro",
         "Reposição avulsa": "🔁 Reposição"}

COLUNAS = {
    "papel": "Papel", "produto_des": "Produto", "referencia": "Referência", "faixa_giro": "Giro",
    "qtde_sugerida": st.column_config.NumberColumn("Qtde", format="%.0f"),
    "preco_ref": ui.dinheiro("Preço un."), "valor": ui.dinheiro("Valor"),
    "desconto": st.column_config.NumberColumn("Desc.", format="%.0f%%"),
    "valor_kit": ui.dinheiro("Valor no kit"),
    "motivo": st.column_config.TextColumn("Por que está no kit", width="large"),
}


def _tabela(itens):
    t = itens.assign(papel=itens["papel"].map(ICONE), desconto=itens["desconto_pct"] * 100)
    ui.tabela(t[list(COLUNAS)], column_config=COLUNAS)


def mostrar_kits(kits):
    """Cartões de kit (âncora + mesmo serviço + baixo giro) e a reposição avulsa."""
    if kits.empty:
        st.info("Sem kit sugerido: o cliente ainda não comprou itens que costumam sair junto com outros no mesmo serviço.")
        return
    montados = kits[kits["kit_ordem"] > 0]
    n = montados["kit_ordem"].nunique()
    if n:
        st.caption(
            f"{n} kit(s) para este cliente. Cada kit parte de um item que ele já compra (⚓ âncora) e junta o que costuma "
            f"ser trocado no **mesmo serviço** (🔧, mesma OS/NF), mais itens de **baixo giro** compatíveis (⭐) com "
            f"{pct(config.KIT_DESCONTO_BAIXO_GIRO, 0)} de desconto sugerido para girar o estoque."
        )
    for ordem, itens in montados.groupby("kit_ordem", sort=True):
        with st.container(border=True):
            st.markdown(f"#### 🧰 {itens['kit_nome'].iloc[0]}")
            ui.md(f"**Por quê:** {itens['kit_motivo'].iloc[0]}")
            _tabela(itens)
            cheio, kit = itens["valor"].sum(), itens["valor_kit"].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Soma dos itens", brl(cheio))
            c2.metric("Preço do kit", brl(kit), help="Desconto aplicado só nos itens de baixo giro")
            c3.metric("Desconto do kit", brl(cheio - kit), f"-{pct((cheio - kit) / cheio if cheio else 0)}", delta_color="off")

    avulsa = kits[kits["kit_ordem"] == 0]
    if len(avulsa):
        with st.container(border=True):
            st.markdown("#### 🔁 Reposição avulsa")
            st.caption("Itens que ele já compra e estão no prazo de recompra, mas que não formam kit com outros.")
            _tabela(avulsa)
            ui.md(f"**Total:** {brl(avulsa['valor'].sum())}")
    st.caption("Preço un. = preço médio praticado nos últimos 12 meses. Confirme preço e estoque no sistema antes de fechar.")

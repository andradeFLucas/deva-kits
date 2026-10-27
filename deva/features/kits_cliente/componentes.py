import streamlit as st

from deva.core import config, ui
from deva.core.formatacao import brl, pct

PAPEL_ROTULOS = {
    "Âncora": "Âncora",
    "Mesmo serviço": "Mesmo serviço",
    "Baixo giro": "Baixo giro (oportunidade)",
    "Reposição avulsa": "Reposição habitual",
}

COLUNAS = {
    "papel": st.column_config.TextColumn("Papel no Kit", width="medium"),
    "produto_des": st.column_config.TextColumn("Produto", width="large"),
    "referencia": st.column_config.TextColumn("Referência", width="small"),
    "faixa_giro": st.column_config.TextColumn("Giro", width="small"),
    "qtde_sugerida": st.column_config.NumberColumn("Qtde", format="%.0f"),
    "preco_ref": ui.dinheiro("Preço un."),
    "valor": ui.dinheiro("Valor un."),
    "desconto": st.column_config.NumberColumn("Desconto", format="%.0f%%"),
    "valor_kit": ui.dinheiro("Valor no kit"),
    "motivo": st.column_config.TextColumn("Por que está no kit", width="large"),
}


def _tabela(itens):
    t = itens.assign(
        papel=itens["papel"].map(lambda p: PAPEL_ROTULOS.get(p, p)),
        desconto=itens["desconto_pct"] * 100,
    )
    ui.tabela(t[list(COLUNAS)], column_config=COLUNAS)


def mostrar_kits(kits):
    """Renderiza cartões de kits estruturados com identidade visual do Deva Design System."""
    if kits.empty:
        st.info("Nenhum kit sugerido para este cliente com base no histórico atual.")
        return

    montados = kits[kits["kit_ordem"] > 0]
    n = montados["kit_ordem"].nunique()
    if n:
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 10px 14px; margin-bottom: 14px; font-size: 0.85rem; color: #475569;">
                <strong>{n} kit(s) inteligente(s) identificado(s):</strong> Estruturados a partir do item <strong>Âncora</strong> (já habitual do cliente),
                reunindo peças trocadas no <strong>Mesmo Serviço</strong> (mesma OS/NF) e produtos de <strong>Baixo Giro</strong> compatíveis
                com <strong>{pct(config.KIT_DESCONTO_BAIXO_GIRO, 0)} de desconto sugerido</strong> para girar o estoque parado.
            </div>
            """,
            unsafe_allow_html=True,
        )

    for ordem, itens in montados.groupby("kit_ordem", sort=True):
        with st.container(border=True):
            nome = itens["kit_nome"].iloc[0]
            motivo = itens["kit_motivo"].iloc[0]
            st.markdown(
                f"""
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <div>
                        <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #1A4B8C; letter-spacing: 0.05em;">Kit Recomendado</div>
                        <h4 style="margin: 0; color: #0F172A;">{nome}</h4>
                    </div>
                </div>
                <div style="font-size: 0.875rem; color: #475569; margin-bottom: 12px; line-height: 1.4;">
                    <strong>Justificativa comercial:</strong> {motivo}
                </div>
                """,
                unsafe_allow_html=True,
            )
            _tabela(itens)
            cheio = itens["valor"].sum()
            kit = itens["valor_kit"].sum()
            economia = cheio - kit
            pct_economia = (economia / cheio) if cheio else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("Preço Avulso dos Itens", brl(cheio))
            c2.metric("Preço Fechado no Kit", brl(kit), help="Desconto promocional aplicado exclusivamente nos itens de baixo giro")
            c3.metric("Economia para o Cliente", brl(economia), f"-{pct(pct_economia, 0)} economia", delta_color="normal")

    avulsa = kits[kits["kit_ordem"] == 0]
    if len(avulsa):
        with st.container(border=True):
            st.markdown(
                """
                <div style="margin-bottom: 8px;">
                    <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #64748B; letter-spacing: 0.05em;">Reposição Periódica</div>
                    <h4 style="margin: 0; color: #0F172A;">Itens Avulsos no Prazo de Recompra</h4>
                </div>
                <div style="font-size: 0.85rem; color: #64748B; margin-bottom: 10px;">
                    Peças de compra habitual que já atingiram a periodicidade média de recompra deste cliente.
                </div>
                """,
                unsafe_allow_html=True,
            )
            _tabela(avulsa)
            st.caption(f"Valor total dos itens de reposição avulsa: **{brl(avulsa['valor'].sum())}**")

    st.caption("Preço un. = média praticada nos últimos 12 meses. Consulte preço atual e disponibilidade física antes de emitir a proposta.")

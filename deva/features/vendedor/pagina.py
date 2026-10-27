"""Tela do vendedor de balcão: identificação rápida, roteiro de abordagem e kits recomendados."""
import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import data_br, num
from deva.features.kits_cliente.componentes import mostrar_kits

ROTEIRO = {
    "Fiel": "Cliente prioritário e fiel da casa. O objetivo é aumentar o ticket médio: apresente o kit fechado com itens complementares aproveitando a visita de hoje.",
    "Recorrente": "Compra com frequência estável. Lembre os itens de reposição preventiva habitual e ofereça o kit completo com economia garantida.",
    "Novo": "Cliente novo. Apresente o kit da linha que ele veio buscar, questione o tamanho da frota e garanta o retorno da segunda compra.",
    "Ocasional": "Compra esporádica. Utilize a reposição dos itens de manutenção como argumento para fidelização.",
    "Em risco": "Atenção: cliente com atraso relevante em relação ao seu padrão habitual de compras. Pergunte se houve alguma insatisfação e apresente condição vantajosa no kit.",
    "Perdido": "Sem compras há mais de 12 meses. Oportunidade de reaproximação com kit de reposição e benefício nos itens de giro parado.",
}


def render():
    st.title("Terminal do Vendedor · Oferta de Kits")
    st.caption("Consulte o cliente no momento do atendimento para visualizar o perfil, o roteiro de abordagem e os kits ideais para fechar a venda.")

    cod, cli = ui.seletor_cliente("vend_cli")
    if cod is None:
        st.info("Digite o nome ou código do cliente acima para carregar o histórico e a recomendação de kits.")
        return

    c = cli[(cli["segmento"] == "Cliente") & (cli["canal"] == "Todos") & (cli["cliente_cod"] == cod)].iloc[0]

    badge = ui.badge_categoria_html(c["categoria"])
    dias = c.get("recencia_dias", 0)

    st.markdown(
        f"""
        <div class="deva-card" style="margin-top: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #64748B;">Cliente Selecionado</span>
                    <h3 style="margin: 2px 0 0 0; color: #0F172A;">{c['cliente_nome']} · Cód. {c['cliente_cod']}</h3>
                </div>
                <div>
                    {badge}
                </div>
            </div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 6px;">
                Última compra realizada em <strong>{data_br(c['ultima_compra'])}</strong> ({num(dias)} dias atrás).
            </div>
            <div class="deva-pitch-box">
                <strong style="color: #1A4B8C; font-size: 0.8125rem; text-transform: uppercase; letter-spacing: 0.04em; display: block; margin-bottom: 4px;">
                    Roteiro de Abordagem Sugerido
                </strong>
                {ROTEIRO.get(c['categoria'], 'Ofereça o kit de reposição e consulte as necessidades do cliente.')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    kits = dados.tabela("kits_cliente")
    kit = kits[kits["cliente_cod"] == cod]
    if kit.empty:
        st.warning("Não há kits mapeados para este cliente no histórico recente. Apresente os kits padrão de manutenção preventiva da linha que ele solicitar.")
        return

    mostrar_kits(kit)

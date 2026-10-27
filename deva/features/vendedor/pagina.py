"""Tela do vendedor de balcão: só o kit a oferecer e o roteiro, sem números da diretoria."""
import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import data_br
from deva.features.kits_cliente.componentes import mostrar_kits

ROTEIRO = {
    "Fiel": "Cliente da casa. Ofereça o kit completo como complemento do pedido de hoje.",
    "Recorrente": "Compra com frequência. Lembre a reposição e ofereça o kit fechado.",
    "Novo": "Cliente novo. Apresente o kit da linha que ele comprou e pergunte o tamanho da frota.",
    "Ocasional": "Compra de vez em quando. Use a reposição como gancho.",
    "Em risco": "Está comprando menos que o normal. Pergunte se está tudo certo e ofereça a reposição.",
    "Perdido": "Faz tempo que não compra. Boa hora para reconquistar com o kit.",
}


def render():
    st.title("Kits para oferecer")
    cod, cli = ui.seletor_cliente("vend_cli")
    if cod is None:
        st.info("Busque o cliente pelo nome ou código para ver o kit sugerido.")
        return
    c = cli[(cli["segmento"] == "Cliente") & (cli["canal"] == "Todos") & (cli["cliente_cod"] == cod)].iloc[0]
    ui.md(f"**{c['cliente_nome']}** · {c['categoria']} · última compra em {data_br(c['ultima_compra'])}")
    st.info(ROTEIRO.get(c["categoria"], ""), icon="💬")

    kits = dados.tabela("kits_cliente")
    kit = kits[kits["cliente_cod"] == cod]
    if kit.empty:
        st.warning("Ainda não há kit para este cliente. Ofereça os kits de manutenção da linha que ele comprar hoje.")
        return

    mostrar_kits(kit)

"""Escolha de perfil na entrada (uso local, sem senha)."""
import streamlit as st

PERFIS = {"diretoria": "Diretoria", "vendedor": "Vendedor de balcão"}
DESCRICOES = {
    "diretoria": "Painel completo: visão geral, clientes, perfis, produtos, kits e segmentos.",
    "vendedor": "Só os kits para oferecer a cada cliente no balcão.",
}


def perfil_atual() -> str | None:
    return st.session_state.get("perfil")


def tela_login() -> None:
    st.title("Deva · Inteligência de Clientes")
    st.write("Escolha a versão que você quer abrir:")
    colunas = st.columns(len(PERFIS))
    for col, (chave, nome) in zip(colunas, PERFIS.items()):
        with col.container(border=True):
            st.subheader(nome)
            st.caption(DESCRICOES[chave])
            if st.button(f"Entrar como {nome.lower()}", key=f"entrar_{chave}", type="primary", use_container_width=True):
                st.session_state["perfil"] = chave
                st.session_state["abrir_inicio"] = True
                st.rerun()


def sair() -> None:
    st.session_state.pop("perfil", None)
    st.rerun()


def abrir_inicio_pendente() -> bool:
    """True uma única vez logo após escolher a versão (para abrir a página inicial dela)."""
    return st.session_state.pop("abrir_inicio", False)

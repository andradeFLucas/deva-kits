"""Navegação entre páginas: app.py registra as páginas da sessão para as fatias poderem abrir umas às outras."""
import streamlit as st

CHAVE_CLIENTE = "cliente_aberto"


def registrar(nome: str, pagina):
    st.session_state.setdefault("_paginas", {})[nome] = pagina
    return pagina


def abrir_cliente(cliente_cod: int) -> None:
    st.session_state[CHAVE_CLIENTE] = int(cliente_cod)
    destino = st.session_state.get("_paginas", {}).get("perfil")
    if destino is not None:
        st.switch_page(destino)


def cliente_pendente() -> int | None:
    return st.session_state.pop(CHAVE_CLIENTE, None)

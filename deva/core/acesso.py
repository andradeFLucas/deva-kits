"""Escolha de perfil de acesso ao Painel Deva com design institucional refinado."""
import streamlit as st

PERFIS = {"diretoria": "Diretoria", "vendedor": "Vendedor de balcão"}
DESCRICOES = {
    "diretoria": "Painel completo e estratégico: visão geral, ranking de clientes, análise de produtos, kits e segmentos de mercado.",
    "vendedor": "Terminal rápido de balcão: consulta de clientes, roteiro de abordagem e kits recomendados para fechar vendas.",
}


def perfil_atual() -> str | None:
    return st.session_state.get("perfil")


def tela_login() -> None:
    st.markdown(
        """
        <div style="text-align: center; max-width: 680px; margin: 3rem auto 2.5rem auto;">
            <div style="font-size: 0.8125rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #1A4B8C; margin-bottom: 8px;">
                Deva Veículos · Concessionária Iveco
            </div>
            <h1 style="font-size: 2.1rem !important; font-weight: 800; color: #0F172A; margin-bottom: 10px; letter-spacing: -0.025em;">
                Inteligência de Clientes & Peças
            </h1>
            <p style="font-size: 1rem; color: #475569; margin: 0 auto; line-height: 1.5;">
                Selecione o ambiente de trabalho correspondente ao seu papel para iniciar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, c1, c2, _ = st.columns([1, 4, 4, 1], gap="medium")

    with c1:
        with st.container(border=True):
            st.markdown(
                """
                <div style="padding-bottom: 8px;">
                    <span style="background-color: #E0F2FE; color: #0369A1; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 4px;">
                        ESTRATÉGICO
                    </span>
                    <h3 style="margin-top: 10px; margin-bottom: 4px;">Diretoria</h3>
                    <p style="font-size: 0.875rem; color: #475569; line-height: 1.45; min-height: 58px;">
                        Visão consolidada da concessionária: margens, retenção, clientes em risco, estoque e canais.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Acessar Painel Executivo", key="entrar_diretoria", type="primary", use_container_width=True):
                st.session_state["perfil"] = "diretoria"
                st.session_state["abrir_inicio"] = True
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown(
                """
                <div style="padding-bottom: 8px;">
                    <span style="background-color: #DCFCE7; color: #166534; font-size: 0.75rem; font-weight: 600; padding: 2px 8px; border-radius: 4px;">
                        OPERACIONAL
                    </span>
                    <h3 style="margin-top: 10px; margin-bottom: 4px;">Vendedor de Balcão</h3>
                    <p style="font-size: 0.875rem; color: #475569; line-height: 1.45; min-height: 58px;">
                        Agilidade no atendimento: roteiro sob medida, kits de reposição e itens de baixo giro para oferta imediata.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Acessar Terminal de Vendas", key="entrar_vendedor", type="primary", use_container_width=True):
                st.session_state["perfil"] = "vendedor"
                st.session_state["abrir_inicio"] = True
                st.rerun()


def sair() -> None:
    st.session_state.pop("perfil", None)
    st.rerun()


def abrir_inicio_pendente() -> bool:
    """True uma única vez logo após escolher a versão (para abrir a página inicial dela)."""
    return st.session_state.pop("abrir_inicio", False)

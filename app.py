"""Painel Deva · Inteligência de Clientes e Peças. Rode com: streamlit run app.py"""
import streamlit as st

from deva.core import acesso, dados, estilos, navegacao
from deva.features.clientes import pagina as clientes
from deva.features.kits_padrao import pagina as kits_padrao
from deva.features.mercado_livre import pagina as mercado_livre
from deva.features.perfil_cliente import pagina as perfil_cliente
from deva.features.produtos import pagina as produtos
from deva.features.segmentos_especiais import pagina as segmentos_especiais
from deva.features.vendedor import pagina as vendedor
from deva.features.visao_geral import pagina as visao_geral

st.set_page_config(
    page_title="Deva · Inteligência de Clientes",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)
estilos.aplicar()

perfil = acesso.perfil_atual()
if perfil is None:
    acesso.tela_login()
    st.stop()

if not dados.existe("kits_cliente"):
    st.error("Base de dados não processada. Execute `python -m deva.pipeline` na pasta do projeto.")
    st.stop()

if perfil == "diretoria":
    paginas = {
        "Painel Executivo": [
            st.Page(visao_geral.render, title="Visão geral", icon=":material/monitoring:", url_path="visao-geral", default=True),
            st.Page(clientes.render, title="Clientes", icon=":material/group:", url_path="clientes"),
            navegacao.registrar("perfil", st.Page(perfil_cliente.render, title="Perfil do cliente", icon=":material/person_search:", url_path="perfil")),
            st.Page(produtos.render, title="Produtos", icon=":material/inventory_2:", url_path="produtos"),
        ],
        "Vendas & Operação": [
            st.Page(kits_padrao.render, title="Kits e manutenção", icon=":material/build:", url_path="kits"),
            st.Page(mercado_livre.render, title="Mercado Livre", icon=":material/shopping_cart:", url_path="mercado-livre"),
            st.Page(segmentos_especiais.render, title="Garantia e frotas", icon=":material/verified_user:", url_path="especiais"),
            st.Page(vendedor.render, title="Tela do vendedor", icon=":material/point_of_sale:", url_path="vendedor"),
        ],
    }
else:
    paginas = [
        st.Page(vendedor.render, title="Kits para oferecer", icon=":material/point_of_sale:", url_path="vendedor", default=True)
    ]

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px 0 16px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 14px;">
            <div style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #1A4B8C; letter-spacing: 0.05em;">Deva Veículos</div>
            <div style="font-size: 0.95rem; font-weight: 600; color: #0F172A;">Concessionária Iveco</div>
            <div style="margin-top: 6px;">
                <span style="font-size: 0.75rem; background-color: #F1F5F9; color: #334155; padding: 2px 8px; border-radius: 4px; font-weight: 500;">
                    Perfil: {acesso.PERFIS[perfil]}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Trocar perfil", type="secondary", use_container_width=True):
        acesso.sair()

pagina = st.navigation(paginas)
if acesso.abrir_inicio_pendente():
    inicio = paginas["Painel Executivo"][0] if isinstance(paginas, dict) else paginas[0]
    if pagina.url_path != inicio.url_path:
        st.switch_page(inicio)
pagina.run()

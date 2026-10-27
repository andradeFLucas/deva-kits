"""Painel Deva · Inteligência de Clientes. Rode com: streamlit run app.py"""
import streamlit as st

from deva.core import acesso, dados, navegacao
from deva.features.clientes import pagina as clientes
from deva.features.kits_padrao import pagina as kits_padrao
from deva.features.mercado_livre import pagina as mercado_livre
from deva.features.perfil_cliente import pagina as perfil_cliente
from deva.features.produtos import pagina as produtos
from deva.features.segmentos_especiais import pagina as segmentos_especiais
from deva.features.vendedor import pagina as vendedor
from deva.features.visao_geral import pagina as visao_geral

st.set_page_config(page_title="Deva · Inteligência de Clientes", page_icon="🚚", layout="wide")
# indicadores menores para caberem 5 por linha em telas médias
st.html("<style>[data-testid='stMetricValue']{font-size:1.5rem}</style>")

perfil = acesso.perfil_atual()
if perfil is None:
    acesso.tela_login()
    st.stop()

if not dados.existe("kits_cliente"):
    st.error("Dados ainda não processados. Rode `python -m deva.pipeline` na pasta do projeto.")
    st.stop()

if perfil == "diretoria":
    paginas = {
        "Painel": [
            st.Page(visao_geral.render, title="Visão geral", icon="📊", url_path="visao-geral", default=True),
            st.Page(clientes.render, title="Clientes", icon="👥", url_path="clientes"),
            navegacao.registrar("perfil", st.Page(perfil_cliente.render, title="Perfil do cliente", icon="🔎", url_path="perfil")),
            st.Page(produtos.render, title="Produtos", icon="📦", url_path="produtos"),
        ],
        "Vendas": [
            st.Page(kits_padrao.render, title="Kits e manutenção", icon="🧰", url_path="kits"),
            st.Page(mercado_livre.render, title="Mercado Livre", icon="🛒", url_path="mercado-livre"),
            st.Page(segmentos_especiais.render, title="Garantia, interno e seguradoras", icon="🛡️", url_path="especiais"),
            st.Page(vendedor.render, title="Tela do vendedor", icon="🧾", url_path="vendedor"),
        ],
    }
else:
    paginas = [st.Page(vendedor.render, title="Kits para oferecer", icon="🧾", url_path="vendedor", default=True)]

with st.sidebar:
    st.caption(f"Perfil: **{acesso.PERFIS[perfil]}**")
    if st.button("Trocar versão"):
        acesso.sair()

pagina = st.navigation(paginas)
if acesso.abrir_inicio_pendente():
    inicio = paginas["Painel"][0] if isinstance(paginas, dict) else paginas[0]
    if pagina.url_path != inicio.url_path:
        st.switch_page(inicio)
pagina.run()

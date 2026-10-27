import plotly.express as px
import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import brl_curto, num, pct
from deva.features.kits_cliente.componentes import mostrar_kits
from deva.features.perfil_cliente import analises_ia, insights


def render():
    st.title("Perfil do cliente")
    cod, cli = ui.seletor_cliente("perfil_cli")
    if cod is None:
        st.info("Escolha um cliente para ver o perfil, o que ele mais compra e o kit sugerido.")
        return

    todas = cli[(cli["segmento"] == "Cliente") & (cli["cliente_cod"] == cod)]
    c = todas[todas["canal"] == "Todos"].iloc[0]
    canais = todas[todas["canal"] != "Todos"]
    ref = insights.Referencia.de(cli[(cli["segmento"] == "Cliente") & (cli["canal"] == "Todos")])

    cp = dados.tabela("cliente_produtos")
    top = cp[(cp["cliente_cod"] == cod) & (cp["segmento"] == "Cliente") & (cp["canal"] == "Todos")].sort_values("valor", ascending=False)
    kits = dados.tabela("kits_cliente")
    kit = kits[kits["cliente_cod"] == cod]

    ui.kpis([
        ("Categoria", c["categoria"], None),
        ("Faturamento total", brl_curto(c["faturamento"]), None),
        ("Faturamento 12m", brl_curto(c["faturamento_12m"]),
         f"{pct(c['tendencia_12m'], 0, sinal=True)} contra os 12 meses anteriores" if c["faturamento_12m_anterior"] > 0 else None),
        ("Ticket médio", brl_curto(c["ticket_medio"]), None),
        ("Margem", pct(c["margem_pct"]), None),
    ])
    ui.kpis([
        ("Compra a cada", f"{num(c['intervalo_medio_dias'])} dias" if c["dias_compra"] > 1 else "—", None),
        ("Dias sem comprar", num(c["recencia_dias"]), "Comparado ao hábito do próprio cliente"),
        ("Situação", c["situacao"], f"{num(c['atraso_x'], 1)}× o intervalo habitual" if c["dias_compra"] > 1 else None),
        ("Desconto médio", pct(c["desconto_pct"]), f"Mediana dos clientes: {pct(ref.desconto_pct)}"),
        ("Notas emitidas", num(c["nfs"]), None),
    ])

    analise = analises_ia.carregar(cod)
    if analise:
        with st.container(border=True):
            st.subheader("🤖 Análise da IA")
            ui.md(analise)
            st.caption(f"Análise escrita pela IA (Claude) em {analises_ia.DATA_ANALISE}, com dados até {analises_ia.DADOS_ATE}. "
                       "Fixa até a próxima revisão; os números acima e os kits abaixo se atualizam todo mês.")
        abas = st.tabs(["Kits para vender", "Resumo automático", "Itens comprados", "Histórico"])
        aba_kit, aba_texto, aba_itens, aba_hist = abas
    else:
        abas = st.tabs(["Resumo automático", "Kits para vender", "Itens comprados", "Histórico"])
        aba_texto, aba_kit, aba_itens, aba_hist = abas
        st.caption("Análise da IA disponível só para os 10 maiores clientes. Este resumo é gerado por regras a partir dos números.")

    with aba_texto:
        ui.md(insights.gerar(c, canais, top, kit, ref))
    with aba_kit:
        mostrar_kits(kit)
    with aba_itens:
        t = top.assign(qtde_por_compra=top["qtde_por_compra"].round(1))
        ui.tabela(t[["produto_des", "referencia", "valor", "qtde", "dias_compra", "intervalo_medio_dias", "recencia_dias", "ultima"]],
                     height=480, column_config={
                         "produto_des": "Produto", "referencia": "Referência", "valor": ui.dinheiro("Valor"),
                         "qtde": st.column_config.NumberColumn("Qtde", format="%.0f"), "dias_compra": ui.inteiro("Compras"),
                         "intervalo_medio_dias": st.column_config.NumberColumn("Compra a cada (dias)", format="%.0f"),
                         "recencia_dias": ui.inteiro("Dias desde a última"), "ultima": ui.data("Última compra"),
                     })
    with aba_hist:
        hist = dados.consulta("""
            SELECT mes, canal, sum(valor) AS faturamento, count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS notas
            FROM vendas WHERE cliente_cod = ? AND segmento = 'Cliente' GROUP BY ALL ORDER BY mes""", (int(cod),))
        ui.grafico(ui.barras_mensais(hist, "mes", "faturamento", "canal", {"Balcão": ui.AZUL, "Oficina": "#4FA36F"},
                                     "Faturamento mensal"))
        lojas = dados.consulta("""
            SELECT loja, sum(valor) AS faturamento FROM vendas WHERE cliente_cod = ? AND segmento = 'Cliente' GROUP BY 1""", (int(cod),))
        if len(lojas) > 1:
            fig = px.pie(lojas, names="loja", values="faturamento", hole=0.5, title="Por loja")
            ui.grafico(fig, 300)

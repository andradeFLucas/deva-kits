import plotly.express as px
import streamlit as st

from deva.core import dados, ui
from deva.core.formatacao import brl_curto, num, pct
from deva.features.kits_cliente.componentes import mostrar_kits
from deva.features.perfil_cliente import analises_ia, insights


def render():
    st.title("Perfil 360° do Cliente")
    st.caption("Visão detalhada do cliente: indicadores de rentabilidade, hábito de compra, análise de IA e kits sugeridos.")

    cod, cli = ui.seletor_cliente("perfil_cli")
    if cod is None:
        st.info("Selecione um cliente no campo de busca acima para visualizar seu diagnóstico completo.")
        return

    todas = cli[(cli["segmento"] == "Cliente") & (cli["cliente_cod"] == cod)]
    c = todas[todas["canal"] == "Todos"].iloc[0]
    canais = todas[todas["canal"] != "Todos"]
    ref = insights.Referencia.de(cli[(cli["segmento"] == "Cliente") & (cli["canal"] == "Todos")])

    cp = dados.tabela("cliente_produtos")
    top = cp[(cp["cliente_cod"] == cod) & (cp["segmento"] == "Cliente") & (cp["canal"] == "Todos")].sort_values("valor", ascending=False)
    kits = dados.tabela("kits_cliente")
    kit = kits[kits["cliente_cod"] == cod]

    badge = ui.badge_categoria_html(c["categoria"])
    st.markdown(
        f"""
        <div class="deva-card" style="margin-top: 10px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <div>
                    <h3 style="margin: 0; color: #0F172A;">{c['cliente_nome']}</h3>
                    <div style="font-size: 0.85rem; color: #64748B; margin-top: 2px;">
                        Código: <strong>{c['cliente_cod']}</strong> · Filial Principal: <strong>{c.get('loja_principal', 'N/D')}</strong> · Curva: <strong>{c.get('curva', 'N/D')}</strong>
                    </div>
                </div>
                <div>{badge}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ui.kpis([
        ("Faturamento Acumulado", brl_curto(c["faturamento"]), "Histórico total desde 2024"),
        ("Faturamento 12m", brl_curto(c["faturamento_12m"]),
         f"{pct(c['tendencia_12m'], 0, sinal=True)} contra os 12 meses anteriores" if c["faturamento_12m_anterior"] > 0 else None),
        ("Ticket Médio por NF", brl_curto(c["ticket_medio"]), "Média por faturamento"),
        ("Margem de Contribuição", pct(c["margem_pct"]), "Margem líquida obtida"),
        ("Notas Emitidas", num(c["nfs"]), "Total de documentos fiscais"),
    ])

    ui.kpis([
        ("Frequência de Compra", f"A cada {num(c['intervalo_medio_dias'])} dias" if c["dias_compra"] > 1 else "Compra única", None),
        ("Dias sem Comprar", f"{num(c['recencia_dias'])} dias", "Dias decorridos desde a última nota fiscal"),
        ("Status de Recorrência", c["situacao"], f"{num(c['atraso_x'], 1)}× o intervalo habitual" if c["dias_compra"] > 1 else None),
        ("Desconto Praticado", pct(c["desconto_pct"]), f"Mediana da carteira geral: {pct(ref.desconto_pct)}"),
        ("Condição Principal", c.get("cond_pag_principal", "N/D"), None),
    ])

    analise = analises_ia.carregar(cod)
    if analise:
        with st.container(border=True):
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                    <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #1A4B8C; letter-spacing: 0.05em;">
                        Diagnóstico Analítico de IA
                    </span>
                    <span style="font-size: 0.75rem; color: #64748B;">
                        Atualizado em {analises_ia.DATA_ANALISE}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            ui.md(analise)
            st.caption(f"Análise estruturada via LLM com dados consolidados até {analises_ia.DADOS_ATE}.")
        abas = st.tabs(["Kits Recomendados", "Diagnóstico por Regras", "Itens Mais Comprados", "Histórico de Vendas"])
        aba_kit, aba_texto, aba_itens, aba_hist = abas
    else:
        abas = st.tabs(["Diagnóstico por Regras", "Kits Recomendados", "Itens Mais Comprados", "Histórico de Vendas"])
        aba_texto, aba_kit, aba_itens, aba_hist = abas
        st.caption("Diagnóstico gerado automaticamente por regras analíticas a partir do comportamento de compras.")

    with aba_texto:
        ui.md(insights.gerar(c, canais, top, kit, ref))

    with aba_kit:
        mostrar_kits(kit)

    with aba_itens:
        t = top.assign(qtde_por_compra=top["qtde_por_compra"].round(1))
        ui.tabela(
            t[["produto_des", "referencia", "valor", "qtde", "dias_compra", "intervalo_medio_dias", "recencia_dias", "ultima"]],
            height=460,
            column_config={
                "produto_des": st.column_config.TextColumn("Descrição do Produto", width="large"),
                "referencia": st.column_config.TextColumn("Referência", width="small"),
                "valor": ui.dinheiro("Faturamento"),
                "qtde": st.column_config.NumberColumn("Quantidade", format="%.0f"),
                "dias_compra": ui.inteiro("Nº Compras"),
                "intervalo_medio_dias": st.column_config.NumberColumn("Ciclo Médio (dias)", format="%.0f"),
                "recencia_dias": ui.inteiro("Dias sem Comprar"),
                "ultima": ui.data("Última Compra"),
            },
        )

    with aba_hist:
        hist = dados.consulta("""
            SELECT mes, canal, sum(valor) AS faturamento, count(DISTINCT nf_id) FILTER (WHERE sinal = 1) AS notas
            FROM vendas WHERE cliente_cod = ? AND segmento = 'Cliente' GROUP BY ALL ORDER BY mes""", (int(cod),))
        ui.grafico(
            ui.barras_mensais(hist, "mes", "faturamento", "canal", {"Balcão": ui.AZUL, "Oficina": "#15803D"},
                             "Faturamento Mensal por Canal de Atendimento"),
            altura=280,
        )

        lojas = dados.consulta("""
            SELECT loja, sum(valor) AS faturamento FROM vendas WHERE cliente_cod = ? AND segmento = 'Cliente' GROUP BY 1""", (int(cod),))
        if len(lojas) > 1:
            fig_l = px.bar(
                lojas,
                x="faturamento",
                y="loja",
                orientation="h",
                title="Distribuição de Compras por Filial Deva",
                color_discrete_sequence=[ui.AZUL],
            )
            fig_l.update_xaxes(tickprefix="R$ ")
            fig_l.update_yaxes(categoryorder="total ascending")
            ui.grafico(fig_l, 220)

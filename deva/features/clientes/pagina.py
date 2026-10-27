import streamlit as st

from deva.core import config, dados, navegacao, ui
from deva.core.formatacao import brl_curto, num

REGRAS = f"""
| Categoria | Critério Técnico de Enquadramento |
|---|---|
| **Novo** | Primeira compra realizada nos últimos {config.DIAS_NOVO} dias |
| **Perdido** | Sem compras registradas há mais de {config.DIAS_PERDIDO} dias |
| **Em risco** | Histórico de {config.COMPRAS_MIN_RISCO}+ dias de compra, sem compras há mais de {config.DIAS_MIN_RISCO} dias e com atraso > {config.FATOR_RISCO:g}× o seu intervalo habitual |
| **Fiel** | Compras registradas em {config.MESES_FIEL}+ dos últimos 12 meses |
| **Recorrente** | Compras registradas em {config.MESES_RECORRENTE} a {config.MESES_FIEL - 1} dos últimos 12 meses |
| **Ocasional** | Demais clientes com compras esporádicas |
"""


def render():
    st.title("Painel de Clientes · Carteira & Ranking")
    st.caption("Acompanhe a segmentação por comportamento de compra, saúde da carteira e ranking de faturamento.")

    c1, c2 = st.columns([2, 3])
    with c1:
        canal = ui.filtro_canal("cl_canal")
    with c2:
        segmento = st.segmented_control(
            "Segmento de Mercado",
            ["Cliente", "Mercado Livre", "Garantia", "Interno", "Seguradora"],
            default="Cliente",
            key="cl_seg",
        ) or "Cliente"

    df = dados.tabela("clientes")
    df = df[(df["canal"] == canal) & (df["segmento"] == segmento)]

    with st.container(border=True):
        f1, f2, f3, f4 = st.columns(4)
        cats = f1.multiselect("Categoria", config.CATEGORIAS, placeholder="Todas")
        lojas = f2.multiselect("Loja principal", sorted(df["loja_principal"].dropna().unique()), placeholder="Todas")
        curvas = f3.multiselect("Curva ABC", ["A", "B", "C"], placeholder="Todas")
        busca = f4.text_input("Buscar cliente por nome", placeholder="Digite parte do nome...")

    if cats:
        df = df[df["categoria"].isin(cats)]
    if lojas:
        df = df[df["loja_principal"].isin(lojas)]
    if curvas:
        df = df[df["curva"].isin(curvas)]
    if busca:
        df = df[df["cliente_nome"].str.contains(busca, case=False, na=False)]

    media_sem_comprar = df["recencia_dias"].mean() if not df.empty else 0
    ui.kpis([
        ("Total de Clientes", num(len(df)), "Base de clientes filtrada"),
        ("Faturamento Acumulado", brl_curto(df["faturamento"].sum()), "Desde o início do histórico (jan/2024)"),
        ("Faturamento 12m", brl_curto(df["faturamento_12m"].sum()), "Últimos 12 meses móveis"),
        ("Ticket Médio (Mediana)", brl_curto(df["ticket_medio"].median()), "Valor mediano por nota fiscal"),
        ("Média de Dias sem Comprar", f"{num(media_sem_comprar)} dias",
         f"Mediana: {num(df['recencia_dias'].median())} dias. Influenciada pelos clientes perdidos; filtre por categoria para comparar grupos homogêneos."),
    ])

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.subheader("Distribuição por Categoria")
    resumo = df.groupby("categoria").agg(
        clientes=("cliente_cod", "count"),
        faturamento_12m=("faturamento_12m", "sum"),
        ticket_mediano=("ticket_medio", "median"),
        intervalo_mediano=("intervalo_medio_dias", "median"),
    ).reindex(config.CATEGORIAS).dropna(how="all").reset_index()

    resumo["part_fat"] = resumo["faturamento_12m"] / max(resumo["faturamento_12m"].sum(), 1) * 100
    ui.tabela(
        resumo,
        column_config={
            "categoria": "Categoria",
            "clientes": ui.inteiro("Clientes"),
            "faturamento_12m": ui.dinheiro("Faturamento 12m"),
            "ticket_mediano": ui.dinheiro("Ticket Mediano"),
            "intervalo_mediano": st.column_config.NumberColumn("Intervalo Mediano (dias)", format="%.0f"),
            "part_fat": ui.percentual("Participação no Faturamento"),
        },
    )

    with st.expander("Regras e critérios das categorias"):
        ui.md(REGRAS)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    st.subheader("Ranking Detalhado de Clientes")
    if segmento == "Cliente":
        st.info("Dica: Clique sobre qualquer linha da tabela para abrir o Perfil 360° do Cliente com histórico de peças e kits sugeridos.", icon=":material/info:")

    tabela = df.sort_values("faturamento", ascending=False).assign(
        margem_pct=lambda d: d["margem_pct"] * 100,
        desconto_pct=lambda d: d["desconto_pct"] * 100,
        tendencia_12m=lambda d: d["tendencia_12m"] * 100,
        vs_media=lambda d: d["recencia_dias"] - media_sem_comprar,
    ).reset_index(drop=True)

    colunas = [
        "ranking", "cliente_nome", "cliente_cod", "categoria", "curva", "faturamento", "faturamento_12m",
        "tendencia_12m", "nfs", "ticket_medio", "intervalo_medio_dias", "recencia_dias", "situacao",
        "atraso_x", "vs_media", "meses_ativos_12m", "margem_pct", "desconto_pct", "loja_principal", "cond_pag_principal",
    ]

    sel = ui.tabela(
        tabela[colunas],
        height=520,
        on_select="rerun",
        selection_mode="single-row",
        key=f"cl_ranking_{st.session_state.get('cl_ranking_v', 0)}",
        column_config={
            "ranking": ui.inteiro("#"),
            "cliente_nome": st.column_config.TextColumn("Cliente", width="medium"),
            "cliente_cod": st.column_config.NumberColumn("Código", format="%d"),
            "categoria": "Categoria",
            "curva": "Curva",
            "faturamento": ui.dinheiro("Faturamento Total"),
            "faturamento_12m": ui.dinheiro("Fat. 12m"),
            "tendencia_12m": st.column_config.NumberColumn("Tendência 12m", format="%+.0f%%"),
            "nfs": ui.inteiro("Notas"),
            "ticket_medio": ui.dinheiro("Ticket Médio"),
            "intervalo_medio_dias": st.column_config.NumberColumn("Intervalo Médio (dias)", format="%.0f"),
            "recencia_dias": ui.inteiro("Dias sem Comprar"),
            "situacao": st.column_config.TextColumn("Situação", help="Comparado ao hábito do próprio cliente"),
            "atraso_x": st.column_config.NumberColumn("Atraso (× hábito)", format="%.1fx",
                                                      help="Dias sem comprar ÷ intervalo habitual. Acima de 1 = passou do prazo usual"),
            "vs_media": st.column_config.NumberColumn("vs Média Carteira (dias)", format="%+.0f",
                                                      help="Diferença para a média dos clientes filtrados"),
            "meses_ativos_12m": ui.inteiro("Meses Ativos 12m"),
            "margem_pct": ui.percentual("Margem"),
            "desconto_pct": ui.percentual("Desconto"),
            "loja_principal": "Filial",
            "cond_pag_principal": "Condição de Pagamento",
        },
    )

    st.download_button(
        "Exportar Tabela para CSV",
        tabela[colunas].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
        "clientes_deva.csv",
        "text/csv",
        type="secondary",
    )

    if sel.selection.rows and segmento == "Cliente":
        st.session_state["cl_ranking_v"] = st.session_state.get("cl_ranking_v", 0) + 1
        navegacao.abrir_cliente(tabela.iloc[sel.selection.rows[0]]["cliente_cod"])

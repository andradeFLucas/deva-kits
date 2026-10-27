import streamlit as st

from deva.core import config, dados, navegacao, ui
from deva.core.formatacao import brl_curto, num

REGRAS = f"""
| Categoria | Regra |
|---|---|
| **Novo** | primeira compra nos últimos {config.DIAS_NOVO} dias |
| **Perdido** | sem comprar há mais de {config.DIAS_PERDIDO} dias |
| **Em risco** | já comprou em {config.COMPRAS_MIN_RISCO}+ dias e está sem comprar há mais de {config.DIAS_MIN_RISCO} dias e de {config.FATOR_RISCO:g}× o seu intervalo habitual |
| **Fiel** | comprou em {config.MESES_FIEL}+ dos últimos 12 meses |
| **Recorrente** | comprou em {config.MESES_RECORRENTE} a {config.MESES_FIEL - 1} dos últimos 12 meses |
| **Ocasional** | demais |
"""


def render():
    st.title("Clientes")
    c1, c2 = st.columns([2, 3])
    with c1:
        canal = ui.filtro_canal("cl_canal")
    with c2:
        segmento = st.segmented_control("Segmento", ["Cliente", "Mercado Livre", "Garantia", "Interno", "Seguradora"],
                                        default="Cliente", key="cl_seg") or "Cliente"
    df = dados.tabela("clientes")
    df = df[(df["canal"] == canal) & (df["segmento"] == segmento)]

    f1, f2, f3, f4 = st.columns(4)
    cats = f1.multiselect("Categoria", config.CATEGORIAS, placeholder="Todas")
    lojas = f2.multiselect("Loja principal", sorted(df["loja_principal"].dropna().unique()), placeholder="Todas")
    curvas = f3.multiselect("Curva ABC", ["A", "B", "C"], placeholder="Todas")
    busca = f4.text_input("Buscar nome")
    if cats:
        df = df[df["categoria"].isin(cats)]
    if lojas:
        df = df[df["loja_principal"].isin(lojas)]
    if curvas:
        df = df[df["curva"].isin(curvas)]
    if busca:
        df = df[df["cliente_nome"].str.contains(busca, case=False, na=False)]

    media_sem_comprar = df["recencia_dias"].mean()
    ui.kpis([
        ("Clientes", num(len(df)), None),
        ("Faturamento total", brl_curto(df["faturamento"].sum()), None),
        ("Faturamento 12m", brl_curto(df["faturamento_12m"].sum()), None),
        ("Ticket médio (mediana)", brl_curto(df["ticket_medio"].median()), None),
        ("Média de dias sem comprar", f"{num(media_sem_comprar)} dias",
         f"Média dos clientes filtrados. Mediana: {num(df['recencia_dias'].median())} dias. "
         "A média sobe muito por causa dos clientes perdidos; filtre por categoria para comparar grupos parecidos."),
    ])

    st.subheader("Resumo por categoria")
    resumo = df.groupby("categoria").agg(
        clientes=("cliente_cod", "count"), faturamento_12m=("faturamento_12m", "sum"),
        ticket_mediano=("ticket_medio", "median"), intervalo_mediano=("intervalo_medio_dias", "median"),
    ).reindex(config.CATEGORIAS).dropna(how="all").reset_index()
    resumo["part_fat"] = resumo["faturamento_12m"] / max(resumo["faturamento_12m"].sum(), 1) * 100
    ui.tabela(resumo, column_config={
        "categoria": "Categoria", "clientes": ui.inteiro("Clientes"), "faturamento_12m": ui.dinheiro("Faturamento 12m"),
        "ticket_mediano": ui.dinheiro("Ticket mediano"), "intervalo_mediano": st.column_config.NumberColumn("Intervalo mediano (dias)", format="%.0f"),
        "part_fat": ui.percentual("% do faturamento 12m"),
    })
    with st.expander("Como as categorias são definidas"):
        ui.md(REGRAS)

    st.subheader("Ranking de clientes")
    tabela = df.sort_values("faturamento", ascending=False).assign(
        margem_pct=lambda d: d["margem_pct"] * 100, desconto_pct=lambda d: d["desconto_pct"] * 100,
        tendencia_12m=lambda d: d["tendencia_12m"] * 100,
        vs_media=lambda d: d["recencia_dias"] - media_sem_comprar,
    ).reset_index(drop=True)
    colunas = ["ranking", "cliente_nome", "cliente_cod", "categoria", "curva", "faturamento", "faturamento_12m", "tendencia_12m",
               "nfs", "ticket_medio", "intervalo_medio_dias", "recencia_dias", "situacao", "atraso_x", "vs_media",
               "meses_ativos_12m", "margem_pct", "desconto_pct", "loja_principal", "cond_pag_principal"]
    st.caption("Clique em um cliente para abrir o perfil completo com análise, números e kits." if segmento == "Cliente"
               else "O perfil completo está disponível para o segmento Cliente.")
    sel = ui.tabela(tabela[colunas], height=520, on_select="rerun", selection_mode="single-row",
                    key=f"cl_ranking_{st.session_state.get('cl_ranking_v', 0)}",
                    column_config={
        "ranking": ui.inteiro("#"), "cliente_nome": "Cliente", "cliente_cod": st.column_config.NumberColumn("Código", format="%d"),
        "categoria": "Categoria", "curva": "Curva", "faturamento": ui.dinheiro("Faturamento"),
        "faturamento_12m": ui.dinheiro("Fat. 12m"), "tendencia_12m": st.column_config.NumberColumn("Tendência", format="%+.0f%%"),
        "nfs": ui.inteiro("Notas"), "ticket_medio": ui.dinheiro("Ticket médio"),
        "intervalo_medio_dias": st.column_config.NumberColumn("Compra a cada (dias)", format="%.0f"),
        "recencia_dias": ui.inteiro("Dias sem comprar"),
        "situacao": st.column_config.TextColumn("Situação", help="Dias sem comprar comparado ao hábito do próprio cliente"),
        "atraso_x": st.column_config.NumberColumn("× o hábito", format="%.1fx",
                                                  help="Dias sem comprar ÷ intervalo habitual. Acima de 1 = passou do prazo dele"),
        "vs_media": st.column_config.NumberColumn("vs média (dias)", format="%+.0f",
                                                  help="Dias sem comprar menos a média dos clientes filtrados. Negativo = abaixo da média"),
        "meses_ativos_12m": ui.inteiro("Meses ativos 12m"),
        "margem_pct": ui.percentual("Margem"), "desconto_pct": ui.percentual("Desconto"),
        "loja_principal": "Loja", "cond_pag_principal": "Condição de pagamento",
    })
    st.download_button("Baixar CSV", tabela[colunas].to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       "clientes.csv", "text/csv")
    if sel.selection.rows and segmento == "Cliente":
        # nova chave = seleção limpa ao voltar para esta página
        st.session_state["cl_ranking_v"] = st.session_state.get("cl_ranking_v", 0) + 1
        navegacao.abrir_cliente(tabela.iloc[sel.selection.rows[0]]["cliente_cod"])

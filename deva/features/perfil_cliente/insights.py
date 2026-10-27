"""Texto automático sobre o cliente: quem é, como compra, o que vender e se vale negociar.

Regras explícitas (sem IA externa): cada frase vem de um número que a diretoria pode conferir.
"""
from dataclasses import dataclass

import pandas as pd

from deva.core.formatacao import brl, data_br, mes_ano, num, pct

ACOES_CATEGORIA = {
    "Fiel": [
        "Cliente fiel: o foco é **aumentar o ticket**, não reconquistar. Leve o kit em toda compra recorrente.",
        "Inclua 1 ou 2 itens de baixo giro compatíveis como \"adicional do pedido\", com condição só para o kit.",
        "Proponha um acordo de fornecimento (reposição programada) no intervalo em que ele já compra.",
    ],
    "Recorrente": [
        "Cliente recorrente: o objetivo é **levá-lo a fiel**, comprando todo mês.",
        "Antecipe-se ao intervalo de recompra dele com o kit de reposição montado.",
        "Desconto progressivo se fechar o kit completo (reposição + baixo giro) em vez de itens avulsos.",
    ],
    "Novo": [
        "Cliente novo: o objetivo é **garantir a segunda compra** nos próximos 30 a 60 dias.",
        "Ofereça o kit da linha que ele já comprou (mesmo veículo) e registre o tamanho e o modelo da frota.",
        "Evite desconto agressivo logo de início; prefira um brinde ou item de baixo giro no kit.",
    ],
    "Ocasional": [
        "Compra de vez em quando: use o kit de reposição como motivo de contato no intervalo dele.",
    ],
    "Em risco": [
        "**Sumiu além do habitual.** Faça contato agora para entender o motivo (preço, prazo, atendimento, concorrência).",
        "Leve uma oferta de retorno com o kit de reposição dos itens que ele comprava.",
    ],
    "Perdido": [
        "Sem compras há mais de um ano: vale uma campanha de reativação com kit de baixo giro em condição especial.",
    ],
}


@dataclass
class Referencia:
    """Medianas dos clientes do segmento, para comparação."""
    ticket: float
    desconto_pct: float
    margem_pct: float
    prazo: float

    @classmethod
    def de(cls, clientes: pd.DataFrame) -> "Referencia":
        ativos = clientes[clientes["nfs_12m"] > 0]
        return cls(
            ticket=ativos["ticket_medio_12m"].median(),
            desconto_pct=ativos["desconto_pct"].median(),
            margem_pct=ativos["margem_pct"].median(),
            prazo=ativos["prazo_dias"].median(),
        )


def _comparar(valor, referencia, mais="acima", menos="abaixo") -> str:
    if pd.isna(valor) or pd.isna(referencia) or referencia == 0:
        return ""
    dif = valor / referencia - 1
    if dif >= 1:
        return f"{num(valor / referencia, 1)} vezes a mediana dos clientes"
    if abs(dif) < 0.1:
        return "em linha com a média dos clientes"
    return f"{pct(abs(dif), 0)} {mais if dif > 0 else menos} da mediana dos clientes"


def avaliar_negociacao(c: pd.Series, ref: Referencia) -> tuple[str, list[str]]:
    pontos, motivos = 0, []
    if pd.notna(c["margem_pct"]) and pd.notna(ref.margem_pct):
        if c["margem_pct"] >= ref.margem_pct:
            pontos += 1
            motivos.append(f"margem de contribuição de {pct(c['margem_pct'])}, acima da mediana ({pct(ref.margem_pct)})")
        else:
            pontos -= 1
            motivos.append(f"margem de contribuição de {pct(c['margem_pct'])}, abaixo da mediana ({pct(ref.margem_pct)})")
    if pd.notna(c["desconto_pct"]) and pd.notna(ref.desconto_pct):
        if c["desconto_pct"] > 1.5 * max(ref.desconto_pct, 0.01):
            pontos -= 2
            motivos.append(f"já recebe desconto médio alto ({pct(c['desconto_pct'])} contra {pct(ref.desconto_pct)}): cliente sensível a preço")
        elif c["desconto_pct"] <= ref.desconto_pct:
            pontos += 1
            motivos.append(f"desconto médio baixo ({pct(c['desconto_pct'])}): há espaço para uma condição no kit")
    if pd.notna(c["devolucao_pct"]) and c["devolucao_pct"] > 0.05:
        pontos -= 1
        motivos.append(f"devolve {pct(c['devolucao_pct'])} do que compra")
    if pd.notna(c["prazo_dias"]):
        if c["prazo_dias"] == 0:
            pontos += 1
            motivos.append("paga à vista ou antecipado")
        elif c["prazo_dias"] > 90:
            pontos -= 1
            motivos.append(f"prazo longo de pagamento (até {num(c['prazo_dias'])} dias)")
    if pd.notna(c["tendencia_12m"]):
        if c["tendencia_12m"] > 0.1:
            pontos += 1
            motivos.append(f"compras em alta ({pct(c['tendencia_12m'], 0, sinal=True)} nos últimos 12 meses)")
        elif c["tendencia_12m"] < -0.2:
            pontos -= 1
            motivos.append(f"compras em queda ({pct(c['tendencia_12m'], 0, sinal=True)} nos últimos 12 meses)")

    if pontos >= 2:
        veredito = "🟢 **Bom para negociar.** Dá para oferecer condição especial no kit sem comprometer a rentabilidade."
    elif pontos >= 0:
        veredito = "🟡 **Negociação neutra.** Negocie pelo valor do kit, sem abrir desconto extra nos itens avulsos."
    else:
        veredito = "🔴 **Negocie com cautela.** Evite descontos adicionais; venda pela disponibilidade e pela compatibilidade."
    return veredito, motivos


def _plural(n, singular: str, plural: str) -> str:
    return f"{num(n)} {singular if n == 1 else plural}"


def _ha(dias) -> str:
    return "hoje" if dias == 0 else ("ontem" if dias == 1 else f"há {num(dias)} dias")


def gerar(c: pd.Series, canais: pd.DataFrame, top_itens: pd.DataFrame, kit: pd.DataFrame, ref: Referencia) -> str:
    """c: linha de `clientes` (canal Todos); canais: linhas do cliente por canal; kit: linhas de `kits_cliente`."""
    linhas = []

    # Quem é
    total = canais["faturamento"].clip(lower=0).sum()
    mix = ", ".join(
        f"{r.canal} {pct(r.faturamento / total, 0)}" for r in canais.sort_values("faturamento", ascending=False).itertuples()
        if total > 0 and r.faturamento > 0
    )
    lojas = f"em {c['qtd_lojas']} lojas (principal: {c['loja_principal']})" if c["qtd_lojas"] > 1 else f"na loja {c['loja_principal']}"
    linhas.append("#### Quem é")
    linhas.append(
        f"**{c['cliente_nome']}** é um cliente **{c['categoria']}**, curva **{c['curva']}** "
        f"(#{num(c['ranking'])} em faturamento). Compra desde {mes_ano(c['primeira_compra'])} {lojas}; "
        f"última compra em {data_br(c['ultima_compra'])} ({_ha(c['recencia_dias'])})."
    )
    linhas.append(
        f"Canal: {mix or '—'}. Paga normalmente em **{c['cond_pag_principal']}**. "
        f"Vendedor mais frequente: {c['vendedor_principal']}."
    )

    # Como compra
    linhas.append("#### Como compra")
    freq = (f"compra em média a cada **{num(c['intervalo_medio_dias'])} dias**" if pd.notna(c["intervalo_medio_dias"])
            else "fez uma única compra até agora")
    linhas.append(
        f"- Faturamento líquido: **{brl(c['faturamento'])}** no total, {brl(c['faturamento_12m'])} nos últimos 12 meses"
        + (f" ({pct(c['tendencia_12m'], 0, sinal=True)} contra os 12 meses anteriores)." if pd.notna(c["tendencia_12m"]) else ".")
    )
    linhas.append(f"- Frequência: {freq}, com compra em {c['meses_ativos_12m']} dos últimos 12 meses ({_plural(c['dias_compra'], 'dia', 'dias')} de compra no histórico).")
    ticket = c["ticket_medio_12m"] if pd.notna(c["ticket_medio_12m"]) else c["ticket_medio"]
    comp = _comparar(ticket, ref.ticket)
    linhas.append(f"- Ticket médio por nota: **{brl(ticket)}**" + (f", {comp}." if comp else "."))
    linhas.append(f"- Mix: {num(c['itens_distintos'])} códigos diferentes já comprados.")

    # O que mais compra
    if len(top_itens):
        linhas.append("#### O que mais compra")
        for r in top_itens.head(5).itertuples():
            rec = (f", a cada ~{num(r.intervalo_medio_dias)} dias" if pd.notna(r.intervalo_medio_dias) else "")
            linhas.append(f"- {r.produto_des} ({r.referencia}): {brl(r.valor)} em {_plural(r.dias_compra, 'compra', 'compras')}{rec}")
        conc = top_itens.head(5)["valor"].sum() / max(c["faturamento"], 1)
        if conc > 0.6:
            linhas.append(f"- Os 5 itens acima concentram {pct(conc, 0)} do que ele compra: mix estreito, com espaço para ampliar.")

    # O que vender
    linhas.append("#### O que é bom vender para ele")
    if len(kit):
        for ordem, k in kit[kit["kit_ordem"] > 0].groupby("kit_ordem"):
            baixo = (k["papel"] == "Baixo giro").sum()
            linhas.append(f"- **{k['kit_nome'].iloc[0]}**: {len(k)} itens ({baixo} de baixo giro), "
                          f"preço do kit {brl(k['valor_kit'].sum())}.")
        avulsa = kit[kit["kit_ordem"] == 0]
        if len(avulsa):
            itens = "; ".join(f"{r.produto_des} ({r.referencia})" for r in avulsa.itertuples())
            linhas.append(f"- **Reposição avulsa (no prazo):** {itens}.")
        medio = kit[kit["kit_ordem"] > 0].groupby("kit_ordem")["valor_kit"].sum().mean()
        if pd.notna(medio) and ticket and ticket > 0:
            linhas.append(f"- Cada kit vale em média **{brl(medio)}**, {pct(medio / ticket, 0)} do ticket médio dele.")
    else:
        linhas.append("- Ainda não há histórico suficiente para sugerir um kit compatível com segurança.")
    for acao in ACOES_CATEGORIA.get(c["categoria"], []):
        linhas.append(f"- {acao}")

    # Negociação
    veredito, motivos = avaliar_negociacao(c, ref)
    linhas.append("#### Vale negociar?")
    linhas.append(veredito)
    for m in motivos:
        linhas.append(f"- {m[0].upper() + m[1:]}")

    return "\n\n".join(linhas)

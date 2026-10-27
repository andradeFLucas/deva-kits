"""Kits por cliente (segmento Cliente, todos os canais).

Cada kit nasce de uma ÂNCORA: um item que o cliente já compra com frequência (de preferência no
prazo de recompra dele). Em volta dela entram:
- Mesmo serviço: itens que saem junto com a âncora na mesma OS/NF (mesmo veículo, mesmo serviço)
- Baixo giro: até 2 itens de baixo giro compatíveis com o kit, com desconto sugerido (girar estoque)

Itens no prazo de reposição que não formam kit (peças genéricas) viram "Reposição avulsa".
Gera a tabela `kits_cliente`, uma linha por item, com `kit_ordem` = 0 para a reposição avulsa.
"""
from collections import defaultdict

import numpy as np
import pandas as pd

from deva.core import armazenamento, config

FAIXAS_BAIXO = ("Baixo", "Sem venda 12m")


def _no_prazo(r) -> bool:
    i = r.intervalo_medio_dias
    return bool(r.dias_compra >= 2 and i >= 7 and 0.8 * i <= r.recencia_dias <= 4 * i)


def _qtde(r) -> float:
    return float(max(1, round(r.qtde_por_compra))) if r is not None else 1.0


def _vizinhos(af: pd.DataFrame, prod: pd.DataFrame):
    """servico[a] = [(b, co_cesta)] por força na cesta; baixo[a] = [(b, score)] só itens de baixo giro."""
    s = af[(af["co_cesta"] >= config.KIT_SERVICO_MIN_CO) & (af["cos_cesta"] >= config.KIT_SERVICO_MIN_COS)]
    s = s.sort_values(["a", "cos_cesta"], ascending=[True, False])
    servico = {a: list(zip(g["b"], g["co_cesta"])) for a, g in s.groupby("a")}
    baixos = set(prod.loc[prod["faixa_giro"].isin(FAIXAS_BAIXO), "produto_cod"])
    # baixo giro precisa ter saído ao menos 2x na mesma OS/NF de um item do kit (mesmo veículo)
    b = af[af["b"].isin(baixos) & (af["co_cesta"] >= config.KIT_BAIXO_GIRO_MIN_CO)]
    baixo = {a: list(zip(g["b"], g["score"])) for a, g in b.groupby("a")}
    return servico, baixo


def montar(cp: pd.DataFrame, prod: pd.DataFrame, af: pd.DataFrame) -> pd.DataFrame:
    info = prod.set_index("produto_cod")
    servico, baixo = _vizinhos(af, prod)
    linhas = []

    def item(cli, ordem, nome, motivo_kit, papel, cod, qtde, motivo, ja_compra):
        p = info.loc[cod]
        desconto = config.KIT_DESCONTO_BAIXO_GIRO if papel == "Baixo giro" else 0.0
        valor = qtde * p["preco_ref"]
        linhas.append({
            "cliente_cod": cli, "kit_ordem": ordem, "kit_nome": nome, "kit_motivo": motivo_kit, "papel": papel,
            "produto_cod": cod, "produto_des": p["produto_des"], "referencia": p["referencia"], "faixa_giro": p["faixa_giro"],
            "ja_compra": ja_compra, "qtde_sugerida": qtde, "preco_ref": p["preco_ref"], "valor": valor,
            "desconto_pct": desconto, "valor_kit": valor * (1 - desconto), "motivo": motivo,
        })

    for cli, itens_cli in cp.groupby("cliente_cod"):
        do_cliente = {r.produto_cod: r for r in itens_cli.itertuples()}
        cands = itens_cli.copy()
        cands["no_prazo"] = [_no_prazo(r) for r in cands.itertuples()]
        cands = cands[cands["produto_cod"].isin(servico.keys())]
        cands = cands.sort_values(["no_prazo", "dias_compra"], ascending=False).head(config.KIT_ANCORAS_AVALIADAS)

        kits, usados = [], set()
        for r in cands.itertuples():
            if len(kits) >= config.KIT_MAX_POR_CLIENTE or r.produto_cod in usados:
                continue
            membros = [(b, co) for b, co in servico[r.produto_cod] if b in info.index][: config.KIT_SERVICO_MAX_ITENS]
            if len(membros) < config.KIT_SERVICO_MIN_ITENS:
                continue
            conjunto = {r.produto_cod} | {b for b, _ in membros}
            if any(len(conjunto & k) / len(conjunto) > config.KIT_SOBREPOSICAO_MAX for k in kits):
                continue
            kits.append(conjunto)
            usados |= conjunto
            ordem = len(kits)

            a = info.loc[r.produto_cod]
            nome = f"Kit {a['produto_des'].title()} ({a['referencia']})"
            if r.no_prazo:
                motivo_kit = (f"{a['produto_des']} está no prazo de reposição (compra a cada ~{r.intervalo_medio_dias:.0f} dias; "
                              f"última há {r.recencia_dias} dias). Os itens abaixo costumam ser trocados no mesmo serviço.")
            elif r.dias_compra >= 2:
                motivo_kit = (f"{a['produto_des']} é um item que ele compra sempre ({r.dias_compra} compras). "
                              "Os itens abaixo costumam sair no mesmo serviço.")
            else:
                motivo_kit = (f"Ele já comprou {a['produto_des']}. Os itens abaixo costumam sair no mesmo serviço "
                              "e completam a manutenção.")
            motivo_ancora = (f"Compra a cada ~{r.intervalo_medio_dias:.0f} dias; última há {r.recencia_dias} dias"
                             if pd.notna(r.intervalo_medio_dias) else f"Comprou há {r.recencia_dias} dias")
            item(cli, ordem, nome, motivo_kit, "Âncora", r.produto_cod, _qtde(r), motivo_ancora, True)
            for b, co in membros:
                ja = b in do_cliente
                item(cli, ordem, nome, motivo_kit, "Mesmo serviço", b, _qtde(do_cliente.get(b)),
                     f"Sai junto com a âncora em {co} OS/NF" + (" · ele já compra" if ja else " · ele ainda não compra"), ja)

            # baixo giro compatível com qualquer item do kit
            soma, via = defaultdict(float), {}
            for x in conjunto:
                for b, s in baixo.get(x, []):
                    if b not in conjunto and b not in usados:
                        soma[b] += s
                        if s > via.get(b, (None, 0))[1]:
                            via[b] = (x, s)
            ranking = sorted(
                (b for b in soma if soma[b] >= config.KIT_BAIXO_GIRO_MIN_LIGACAO),
                key=lambda b: soma[b] * (0.35 + 0.65 * info.loc[b, "baixo_giro_score"]), reverse=True,
            )[: config.KIT_BAIXO_GIRO_MAX_ITENS]
            for b in ranking:
                v = info.loc[via[b][0]]
                usados.add(b)
                item(cli, ordem, nome, motivo_kit, "Baixo giro", b, 1.0,
                     f"Compatível com {v['produto_des']} ({v['referencia']}); giro baixo na Deva", b in do_cliente)

        avulsos = itens_cli[[_no_prazo(r) and r.produto_cod not in usados for r in itens_cli.itertuples()]]
        for r in avulsos.sort_values("dias_compra", ascending=False).head(config.REPOSICAO_AVULSA_MAX).itertuples():
            item(cli, 0, "Reposição avulsa", "Itens que ele já compra e estão no prazo, mas que não formam kit.",
                 "Reposição avulsa", r.produto_cod, _qtde(r),
                 f"Compra a cada ~{r.intervalo_medio_dias:.0f} dias; última há {r.recencia_dias} dias", True)

    df = pd.DataFrame(linhas)
    if not df.empty:
        df["item_ordem"] = df.groupby(["cliente_cod", "kit_ordem"]).cumcount() + 1
        df["ja_compra"] = df["ja_compra"].astype(bool)
        df["qtde_sugerida"] = df["qtde_sugerida"].astype(float)
        df["desconto_pct"] = df["desconto_pct"].astype(np.float64)
    return df


def executar(con) -> int:
    cp = con.execute("""
        SELECT cliente_cod, produto_cod, dias_compra, intervalo_medio_dias, recencia_dias, qtde_por_compra
        FROM cliente_produtos WHERE segmento = 'Cliente' AND canal = 'Todos' AND dias_compra > 0""").df()
    prod = con.execute("SELECT * FROM produtos WHERE canal = 'Todos'").df()
    af = con.execute("SELECT a, b, co_cesta, cos_cesta, score FROM afinidade").df()
    return armazenamento.salvar_df(con, "kits_cliente", montar(cp, prod, af))

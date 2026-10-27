"""Kits padrão = plano de manutenção inferido dos dados (não existe plano formal).

Para cada item "âncora" muito presente em OS/NF, juntamos os itens que saem com ele na mesma
cesta (mesmo veículo). Kits quase iguais são descartados. Para cada kit também listamos itens
de baixo giro compatíveis, para agregar na oferta e girar estoque.

Gera `kits_padrao` (composição) e `kits_padrao_baixo_giro` (agregados sugeridos).
"""
import pandas as pd

from deva.core import armazenamento, config


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / max(len(a | b), 1)


def montar(af: pd.DataFrame, prod: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    info = prod.set_index("produto_cod")
    forte = af[(af["cos_cesta"] >= config.KIT_PADRAO_MIN_COS) & (af["co_cesta"] >= config.KIT_PADRAO_MIN_CO)]
    ancoras = (
        af[af["na_cesta"] >= config.KIT_PADRAO_MIN_CESTAS]
        .groupby("a")["na_cesta"].first().sort_values(ascending=False)
    )

    kits, agregados, conjuntos = [], [], []
    for ancora, n_cestas in ancoras.items():
        membros = forte[forte["a"] == ancora].sort_values("cos_cesta", ascending=False)
        membros = membros.head(config.KIT_PADRAO_MAX_ITENS - 1)
        if len(membros) < 2:
            continue
        itens = [ancora] + membros["b"].tolist()
        if any(_jaccard(set(itens), c) > 0.6 for c in conjuntos):
            continue
        conjuntos.append(set(itens))
        kit_id = len(conjuntos)
        a = info.loc[ancora]
        nome = f"Kit {a['produto_des'].title()} ({a['referencia']})"
        cos = dict(zip(membros["b"], membros["cos_cesta"]))
        for ordem, cod in enumerate(itens, start=1):
            p = info.loc[cod]
            kits.append({
                "kit_id": kit_id, "kit_nome": nome, "ancora_cod": ancora, "cestas_ancora": int(n_cestas),
                "ordem": ordem, "produto_cod": cod, "produto_des": p["produto_des"], "referencia": p["referencia"],
                "faixa_giro": p["faixa_giro"], "preco_ref": p["preco_ref"],
                "intervalo_reposicao_dias": p["intervalo_reposicao_dias"],
                "forca_ligacao": 1.0 if cod == ancora else cos.get(cod),
            })

        viz = af[af["a"].isin(itens) & ~af["b"].isin(itens)]
        viz = viz.merge(prod[["produto_cod", "faixa_giro", "baixo_giro_score"]], left_on="b", right_on="produto_cod")
        viz = viz[viz["faixa_giro"].isin(["Baixo", "Sem venda 12m"])]
        viz = viz.groupby("b").agg(compat=("score", "sum"), giro=("baixo_giro_score", "first")).reset_index()
        viz["prioridade"] = viz["compat"] * (0.35 + 0.65 * viz["giro"])
        for _, v in viz.sort_values("prioridade", ascending=False).head(5).iterrows():
            p = info.loc[v["b"]]
            agregados.append({
                "kit_id": kit_id, "produto_cod": v["b"], "produto_des": p["produto_des"], "referencia": p["referencia"],
                "faixa_giro": p["faixa_giro"], "preco_ref": p["preco_ref"], "dias_sem_venda": p["dias_sem_venda"],
                "prioridade": v["prioridade"],
            })
    return pd.DataFrame(kits), pd.DataFrame(agregados)


def executar(con) -> int:
    af = con.execute("SELECT * FROM afinidade").df()
    prod = con.execute("SELECT * FROM produtos WHERE canal = 'Todos'").df()
    kits, agregados = montar(af, prod)
    armazenamento.salvar_df(con, "kits_padrao_baixo_giro", agregados)
    return armazenamento.salvar_df(con, "kits_padrao", kits)

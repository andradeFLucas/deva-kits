"""Métricas por cliente (por segmento e canal, com canal 'Todos') e categoria de frequência.

Gera:
- `clientes`: uma linha por (segmento, canal, cliente)
- `cliente_produtos`: o que cada cliente compra, com intervalo de recompra do item
"""
import numpy as np
import pandas as pd

from deva.core import armazenamento, regras

SQL_CLIENTES = """
WITH x AS (
    SELECT * FROM vendas
    UNION ALL SELECT * REPLACE ('Todos' AS canal) FROM vendas
),
r AS (SELECT max(data) AS ref FROM vendas)
SELECT
    segmento, canal, cliente_cod,
    arg_max(cliente_nome, data)                                   AS cliente_nome,
    mode(loja) FILTER (WHERE sinal = 1)                           AS loja_principal,
    count(DISTINCT loja)                                          AS qtd_lojas,
    mode(cond_pag) FILTER (WHERE sinal = 1)                       AS cond_pag_principal,
    mode(vendedor) FILTER (WHERE sinal = 1)                       AS vendedor_principal,
    min(data) FILTER (WHERE sinal = 1)                            AS primeira_compra,
    max(data) FILTER (WHERE sinal = 1)                            AS ultima_compra,
    count(DISTINCT CAST(data AS DATE)) FILTER (WHERE sinal = 1)   AS dias_compra,
    count(DISTINCT nf_id) FILTER (WHERE sinal = 1)                AS nfs,
    sum(valor)                                                    AS faturamento,
    -coalesce(sum(valor) FILTER (WHERE sinal = -1), 0)            AS devolucoes,
    sum(valor) FILTER (WHERE sinal = 1)                           AS vendas_brutas,
    sum(margem)                                                   AS margem,
    sum(desconto) FILTER (WHERE sinal = 1)                        AS desconto,
    sum(valor_tabela) FILTER (WHERE sinal = 1)                    AS valor_tabela,
    count(DISTINCT produto_cod)                                   AS itens_distintos,
    count(DISTINCT mes) FILTER (WHERE sinal = 1 AND mes > date_trunc('month', ref) - INTERVAL 12 MONTH) AS meses_ativos_12m,
    coalesce(sum(valor) FILTER (WHERE data > ref - INTERVAL 365 DAY), 0)           AS faturamento_12m,
    coalesce(sum(valor) FILTER (WHERE data <= ref - INTERVAL 365 DAY
                                  AND data > ref - INTERVAL 730 DAY), 0)          AS faturamento_12m_anterior,
    count(DISTINCT nf_id) FILTER (WHERE sinal = 1 AND data > ref - INTERVAL 365 DAY) AS nfs_12m,
    any_value(ref)                                                AS data_ref
FROM x, r
GROUP BY segmento, canal, cliente_cod
HAVING count(*) FILTER (WHERE sinal = 1) > 0
"""

SQL_CLIENTE_PRODUTOS = """
WITH x AS (
    SELECT * FROM vendas
    UNION ALL SELECT * REPLACE ('Todos' AS canal) FROM vendas
),
r AS (SELECT max(data) AS ref FROM vendas)
SELECT
    segmento, canal, cliente_cod, produto_cod,
    arg_max(produto_des, data)                                    AS produto_des,
    arg_max(referencia, data)                                     AS referencia,
    sum(qtde)                                                     AS qtde,
    sum(valor)                                                    AS valor,
    count(DISTINCT CAST(data AS DATE)) FILTER (WHERE sinal = 1)   AS dias_compra,
    min(data) FILTER (WHERE sinal = 1)                            AS primeira,
    max(data) FILTER (WHERE sinal = 1)                            AS ultima,
    date_diff('day', max(data) FILTER (WHERE sinal = 1), any_value(ref)) AS recencia_dias
FROM x, r
GROUP BY segmento, canal, cliente_cod, produto_cod
HAVING count(*) FILTER (WHERE sinal = 1) > 0
"""


def _derivar(df: pd.DataFrame) -> pd.DataFrame:
    ref = df["data_ref"]
    df["recencia_dias"] = (ref - df["ultima_compra"]).dt.days
    df["dias_desde_primeira"] = (ref - df["primeira_compra"]).dt.days
    vida = (df["ultima_compra"] - df["primeira_compra"]).dt.days
    df["intervalo_medio_dias"] = np.where(df["dias_compra"] > 1, vida / (df["dias_compra"] - 1).clip(lower=1), np.nan)
    df["ticket_medio"] = df["faturamento"] / df["nfs"].clip(lower=1)
    df["ticket_medio_12m"] = np.where(df["nfs_12m"] > 0, df["faturamento_12m"] / df["nfs_12m"].clip(lower=1), np.nan)
    df["margem_pct"] = df["margem"] / df["faturamento"].where(df["faturamento"] > 0)
    df["desconto_pct"] = df["desconto"] / df["valor_tabela"].where(df["valor_tabela"] > 0)
    df["devolucao_pct"] = df["devolucoes"] / df["vendas_brutas"].where(df["vendas_brutas"] > 0)
    df["tendencia_12m"] = np.where(
        df["faturamento_12m_anterior"] > 0,
        df["faturamento_12m"] / df["faturamento_12m_anterior"].where(df["faturamento_12m_anterior"] > 0) - 1,
        np.nan,
    )
    df["prazo_dias"] = df["cond_pag_principal"].map(regras.prazo_dias)
    df["categoria"] = regras.categorizar(df)
    df["atraso_x"], df["situacao"] = regras.situacao_compra(df)
    df["curva"] = df.groupby(["segmento", "canal"], group_keys=False)["faturamento"].apply(regras.curva_abc)
    df["ranking"] = df.groupby(["segmento", "canal"])["faturamento"].rank(ascending=False, method="first").astype(int)
    return df


def executar(con) -> int:
    df = _derivar(con.execute(SQL_CLIENTES).df())
    n = armazenamento.salvar_df(con, "clientes", df)

    cp = con.execute(SQL_CLIENTE_PRODUTOS).df()
    vida = (cp["ultima"] - cp["primeira"]).dt.days
    cp["intervalo_medio_dias"] = np.where(cp["dias_compra"] > 1, vida / (cp["dias_compra"] - 1).clip(lower=1), np.nan)
    cp["qtde_por_compra"] = cp["qtde"] / cp["dias_compra"].clip(lower=1)
    armazenamento.salvar_df(con, "cliente_produtos", cp)
    return n

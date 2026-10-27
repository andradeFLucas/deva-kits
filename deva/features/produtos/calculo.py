"""Métricas por produto (código exato) e por canal, giro de vendas e intervalo típico de reposição.

O intervalo de reposição é a mediana, entre clientes, do tempo que cada cliente leva para
recomprar o mesmo código. É a base do "plano de manutenção" inferido dos dados.
"""
from deva.core import armazenamento, regras

SQL_PRODUTOS = """
WITH x AS (
    SELECT * FROM vendas
    UNION ALL SELECT * REPLACE ('Todos' AS canal) FROM vendas
),
r AS (SELECT max(data) AS ref FROM vendas)
SELECT
    canal, produto_cod,
    arg_max(produto_des, data)                                       AS produto_des,
    arg_max(referencia, data)                                        AS referencia,
    arg_max(classe_giro, data)                                       AS classe_giro,
    arg_max(produto_tipo, data)                                      AS produto_tipo,
    sum(qtde)                                                        AS qtde,
    sum(valor)                                                       AS faturamento,
    sum(margem)                                                      AS margem,
    count(DISTINCT nf_id) FILTER (WHERE sinal = 1)                   AS nfs,
    count(DISTINCT cliente_cod) FILTER (WHERE sinal = 1)             AS clientes,
    coalesce(sum(qtde) FILTER (WHERE data > ref - INTERVAL 365 DAY), 0)                    AS qtde_12m,
    count(DISTINCT nf_id) FILTER (WHERE sinal = 1 AND data > ref - INTERVAL 365 DAY)       AS nfs_12m,
    count(DISTINCT cliente_cod) FILTER (WHERE sinal = 1 AND data > ref - INTERVAL 365 DAY) AS clientes_12m,
    coalesce(sum(valor) FILTER (WHERE data > ref - INTERVAL 365 DAY), 0)                   AS faturamento_12m,
    count(DISTINCT mes) FILTER (WHERE sinal = 1 AND mes > date_trunc('month', ref) - INTERVAL 12 MONTH) AS meses_venda_12m,
    min(data) FILTER (WHERE sinal = 1)                               AS primeira_venda,
    max(data) FILTER (WHERE sinal = 1)                               AS ultima_venda,
    sum(valor) FILTER (WHERE sinal = 1 AND data > ref - INTERVAL 365 DAY)
        / nullif(sum(qtde) FILTER (WHERE sinal = 1 AND data > ref - INTERVAL 365 DAY), 0) AS preco_12m,
    sum(valor) FILTER (WHERE sinal = 1) / nullif(sum(qtde) FILTER (WHERE sinal = 1), 0)    AS preco_hist,
    date_diff('day', max(data) FILTER (WHERE sinal = 1), any_value(ref))                   AS dias_sem_venda
FROM x, r
GROUP BY canal, produto_cod
HAVING count(*) FILTER (WHERE sinal = 1) > 0
"""

# Recompra do mesmo código pelo mesmo cliente (ignora intervalos < 7 dias: mesmo serviço)
SQL_REPOSICAO = """
WITH d AS (
    SELECT DISTINCT produto_cod, cliente_cod, CAST(data AS DATE) AS dia
    FROM vendas
    WHERE sinal = 1 AND segmento IN ('Cliente', 'Mercado Livre')
),
g AS (
    SELECT produto_cod, cliente_cod,
           dia - lag(dia) OVER (PARTITION BY produto_cod, cliente_cod ORDER BY dia) AS gap
    FROM d
),
por_cliente AS (
    SELECT produto_cod, cliente_cod, median(gap) AS gap_cliente
    FROM g WHERE gap >= 7
    GROUP BY 1, 2
)
SELECT produto_cod,
       median(gap_cliente)  AS intervalo_reposicao_dias,
       count(*)             AS clientes_recompra
FROM por_cliente
GROUP BY 1
HAVING count(*) >= 5
"""


def executar(con) -> int:
    df = con.execute(SQL_PRODUTOS).df()
    rep = con.execute(SQL_REPOSICAO).df()
    df = df.merge(rep, on="produto_cod", how="left")
    df["clientes_recompra"] = df["clientes_recompra"].fillna(0).astype(int)
    df["preco_ref"] = df["preco_12m"].fillna(df["preco_hist"])
    df["margem_pct"] = df["margem"] / df["faturamento"].where(df["faturamento"] > 0)
    df["faixa_giro"] = regras.faixa_giro(df["nfs_12m"])
    df["baixo_giro_score"] = regras.baixo_giro_score(df["nfs_12m"], df["classe_giro"])
    df["curva"] = df.groupby("canal", group_keys=False)["faturamento"].apply(regras.curva_abc)
    return armazenamento.salvar_df(con, "produtos", df)

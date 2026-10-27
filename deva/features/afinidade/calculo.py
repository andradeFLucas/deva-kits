"""Afinidade entre produtos = proxy de compatibilidade (mesmo caminhão/motor).

A base não traz o modelo do veículo, então inferimos pela compra conjunta:
- cesta: itens na mesma OS (oficina) ou NF (balcão) -> quase sempre o mesmo veículo
- cliente: itens comprados pelo mesmo cliente ao longo do tempo -> a mesma frota

score(a -> b) = PESO_CESTA * cosseno_cesta + PESO_CLIENTE * cosseno_cliente
Guardamos os VIZINHOS_POR_ITEM melhores vizinhos de cada produto.
"""
from deva.core import armazenamento, config

SQL = """
WITH ci0 AS (
    SELECT DISTINCT cesta_id, produto_cod FROM vendas WHERE sinal = 1
),
ci AS (
    SELECT ci0.* FROM ci0
    JOIN (SELECT cesta_id FROM ci0 GROUP BY 1 HAVING count(*) BETWEEN 2 AND {cesta_max}) t USING (cesta_id)
),
n_cesta AS (SELECT produto_cod, count(*) AS n FROM ci GROUP BY 1),
par_cesta AS (
    SELECT a.produto_cod AS a, b.produto_cod AS b, count(*) AS co_cesta
    FROM ci a JOIN ci b ON a.cesta_id = b.cesta_id AND a.produto_cod <> b.produto_cod
    GROUP BY 1, 2 HAVING count(*) >= {min_co_cesta}
),
cl0 AS (
    SELECT DISTINCT cliente_cod, produto_cod FROM vendas
    WHERE sinal = 1 AND segmento IN ('Cliente', 'Mercado Livre')
),
cl AS (
    SELECT cl0.* FROM cl0
    JOIN (SELECT cliente_cod FROM cl0 GROUP BY 1 HAVING count(*) BETWEEN 2 AND {cliente_max}) t USING (cliente_cod)
),
n_cli AS (SELECT produto_cod, count(*) AS n FROM cl GROUP BY 1),
par_cli AS (
    SELECT a.produto_cod AS a, b.produto_cod AS b, count(*) AS co_cliente
    FROM cl a JOIN cl b ON a.cliente_cod = b.cliente_cod AND a.produto_cod <> b.produto_cod
    GROUP BY 1, 2 HAVING count(*) >= {min_co_cliente}
),
pares AS (
    SELECT coalesce(pc.a, pl.a) AS a, coalesce(pc.b, pl.b) AS b,
           coalesce(pc.co_cesta, 0) AS co_cesta, coalesce(pl.co_cliente, 0) AS co_cliente
    FROM par_cesta pc FULL OUTER JOIN par_cli pl ON pc.a = pl.a AND pc.b = pl.b
),
s AS (
    SELECT p.*,
        na.n AS na_cesta, nb.n AS nb_cesta,
        coalesce(p.co_cesta / sqrt(na.n * nb.n), 0)       AS cos_cesta,
        coalesce(p.co_cliente / sqrt(ma.n * mb.n), 0)     AS cos_cliente
    FROM pares p
    LEFT JOIN n_cesta na ON na.produto_cod = p.a
    LEFT JOIN n_cesta nb ON nb.produto_cod = p.b
    LEFT JOIN n_cli ma ON ma.produto_cod = p.a
    LEFT JOIN n_cli mb ON mb.produto_cod = p.b
)
SELECT *, {peso_cesta} * cos_cesta + {peso_cliente} * cos_cliente AS score
FROM s
QUALIFY row_number() OVER (PARTITION BY a ORDER BY {peso_cesta} * cos_cesta + {peso_cliente} * cos_cliente DESC) <= {vizinhos}
"""


def executar(con) -> int:
    sql = SQL.format(
        cesta_max=config.CESTA_MAX_ITENS,
        cliente_max=config.CLIENTE_MAX_ITENS,
        min_co_cesta=config.MIN_CO_CESTA,
        min_co_cliente=config.MIN_CO_CLIENTE,
        peso_cesta=config.PESO_CESTA,
        peso_cliente=config.PESO_CLIENTE,
        vizinhos=config.VIZINHOS_POR_ITEM,
    )
    return armazenamento.salvar_sql(con, "afinidade", sql)

"""Ingestão: lê a exportação bruta do ERP e gera a tabela `vendas` padronizada.

- uma linha por item de nota; devoluções (Tipo D) entram com sinal negativo
- `segmento` separa Garantia, Interno, Seguradora e Mercado Livre dos clientes comuns
- `cesta_id` agrupa itens do mesmo veículo/atendimento (OS na oficina, NF no balcão)
"""
from pathlib import Path

from deva.core import armazenamento, config

SQL = """
WITH bruto AS (
    SELECT *,
        CASE WHEN Tipo = 'D' THEN -1 ELSE 1 END AS s,
        upper(trim(NF_PessoaNom)) AS nome_up,
        upper(trim(NF_CondPagDes)) AS cond_up
    FROM read_parquet('{fonte}')
    WHERE NF_Dataemis >= DATE '{inicio}'
)
SELECT
    NF_Dataemis                                        AS data,
    CAST(date_trunc('month', NF_Dataemis) AS DATE)     AS mes,
    EmpNome                                            AS loja,
    CASE WHEN NF_Origem = 'OFI' THEN 'Oficina' ELSE 'Balcão' END AS canal,
    CASE
        WHEN nome_up LIKE 'IVG BRASIL%' OR cond_up = 'GARANTIA'                   THEN 'Garantia'
        WHEN cond_up = 'VENDA INTERNA' OR nome_up LIKE 'DEVA VE%CULOS%'            THEN 'Interno'
        WHEN cond_up = 'SEGURADORA' OR nome_up LIKE '%SEGUROS%' OR nome_up LIKE '%SEGURADORA%' THEN 'Seguradora'
        WHEN cond_up LIKE 'MERCADO LIVRE%'                                         THEN 'Mercado Livre'
        ELSE 'Cliente'
    END                                                AS segmento,
    NF_Codigo                                          AS nf_id,
    NF_Numero                                          AS nf_numero,
    CAST(NF_OsCod AS BIGINT)                           AS os_id,
    NF_OsTipoDes                                       AS os_tipo,
    COALESCE('OS' || CAST(CAST(NF_OsCod AS BIGINT) AS VARCHAR), 'NF' || CAST(NF_Codigo AS VARCHAR)) AS cesta_id,
    NF_PessoaCod                                       AS cliente_cod,
    trim(NF_PessoaNom)                                 AS cliente_nome,
    trim(NF_CondPagDes)                                AS cond_pag,
    trim(NF_UsuNomVendedor)                            AS vendedor,
    NFItem_ProdutoCod                                  AS produto_cod,
    trim(NFItem_ProdutoDes)                            AS produto_des,
    trim(ProdMarcaReferencia)                          AS referencia,
    ProdTipoCod                                        AS produto_tipo,
    NULLIF(trim(ProdEstoqueClasABC), '')               AS classe_giro,
    Tipo                                               AS tipo_mov,
    s                                                  AS sinal,
    NFItem_Qtde * s                                    AS qtde,
    NFItem_VlTotal * s                                 AS valor,
    -- NFItem_VlBruto às vezes vem unitário; valor pago + desconto bate com NFItem_PercDesc
    (NFItem_VlTotal + NFItem_VlDesc - NFItem_VlAcres) * s AS valor_tabela,
    NFItem_VlDesc * s                                  AS desconto,
    NF_ProdCusto * s                                   AS custo,
    NFItem_VlMargemCont * s                            AS margem
FROM bruto
WHERE NF_Status = 'EMI'
"""


def executar(con, fonte: Path | None = None) -> int:
    fonte = Path(fonte or config.FONTE_VENDAS)
    if not fonte.exists():
        raise FileNotFoundError(f"Base de vendas não encontrada: {fonte}")
    return armazenamento.salvar_sql(con, "vendas", SQL.format(fonte=fonte.as_posix(), inicio=config.DATA_INICIO))

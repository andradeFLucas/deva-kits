"""Processamento mensal: `python -m deva.pipeline [caminho_da_base_de_vendas.parquet]`

Cada fatia expõe `executar(con)` e grava suas tabelas em data/processed.
A ordem importa: cada etapa lê o que as anteriores gravaram.
"""
import sys
import time

from deva.core import armazenamento
from deva.features.afinidade import calculo as afinidade
from deva.features.clientes import calculo as clientes
from deva.features.ingestao import calculo as ingestao
from deva.features.kits_cliente import calculo as kits_cliente
from deva.features.kits_padrao import calculo as kits_padrao
from deva.features.produtos import calculo as produtos

ETAPAS = [
    ("clientes", clientes.executar),
    ("produtos", produtos.executar),
    ("afinidade", afinidade.executar),
    ("kits_cliente", kits_cliente.executar),
    ("kits_padrao", kits_padrao.executar),
]


def rodar(fonte=None) -> None:
    con = armazenamento.conexao()
    t0 = time.time()
    print(f"vendas: {ingestao.executar(con, fonte):,} linhas")
    for nome, etapa in ETAPAS:
        t = time.time()
        n = etapa(con)
        print(f"{nome}: {n:,} linhas ({time.time() - t:.1f}s)")
    print(f"Concluído em {time.time() - t0:.1f}s")


if __name__ == "__main__":
    rodar(sys.argv[1] if len(sys.argv) > 1 else None)

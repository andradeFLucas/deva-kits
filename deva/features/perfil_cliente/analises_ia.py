"""Análises escritas pela IA (Claude) para os 10 maiores clientes, fixas no código.

Cada cliente tem um arquivo `analises_ia/<codigo>.md`. Para atualizar, reescreva o arquivo
com base nos dados novos e ajuste as datas abaixo.
"""
from pathlib import Path

PASTA = Path(__file__).parent / "analises_ia"
DATA_ANALISE = "19/10/2026"
DADOS_ATE = "14/10/2026"


def carregar(cliente_cod: int) -> str | None:
    arquivo = PASTA / f"{int(cliente_cod)}.md"
    return arquivo.read_text(encoding="utf-8") if arquivo.exists() else None

"""Camada de dados: hoje parquet + DuckDB; amanhã pode apontar para o banco sem mudar as fatias."""
import duckdb
import pandas as pd

from deva.core import config


def caminho(nome: str):
    return config.DADOS_PROC / f"{nome}.parquet"


def conexao() -> duckdb.DuckDBPyConnection:
    """Conexão em memória com uma view para cada tabela processada."""
    con = duckdb.connect()
    for p in sorted(config.DADOS_PROC.glob("*.parquet")):
        con.execute(f"CREATE OR REPLACE VIEW {p.stem} AS SELECT * FROM read_parquet('{p.as_posix()}')")
    return con


def salvar_sql(con, nome: str, sql: str) -> int:
    config.DADOS_PROC.mkdir(parents=True, exist_ok=True)
    destino = caminho(nome)
    temp = destino.with_suffix(".tmp")
    con.execute(f"COPY ({sql}) TO '{temp.as_posix()}' (FORMAT PARQUET)")
    temp.replace(destino)
    con.execute(f"CREATE OR REPLACE VIEW {nome} AS SELECT * FROM read_parquet('{destino.as_posix()}')")
    return con.execute(f"SELECT count(*) FROM {nome}").fetchone()[0]


def salvar_df(con, nome: str, df: pd.DataFrame) -> int:
    con.register("_df_salvar", df)
    try:
        return salvar_sql(con, nome, "SELECT * FROM _df_salvar")
    finally:
        con.unregister("_df_salvar")

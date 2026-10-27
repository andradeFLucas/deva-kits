"""Leitura com cache para as páginas (Streamlit). O cache invalida quando o pipeline regrava o arquivo."""
import pandas as pd
import streamlit as st

from deva.core import armazenamento


def _versao(nome: str) -> float:
    p = armazenamento.caminho(nome)
    return p.stat().st_mtime if p.exists() else 0.0


@st.cache_data(show_spinner=False)
def _ler(nome: str, versao: float) -> pd.DataFrame:
    return pd.read_parquet(armazenamento.caminho(nome))


def tabela(nome: str) -> pd.DataFrame:
    return _ler(nome, _versao(nome))


@st.cache_data(show_spinner=False)
def _consulta(sql: str, params: tuple, versao: float) -> pd.DataFrame:
    con = armazenamento.conexao()
    try:
        return con.execute(sql, list(params)).df()
    finally:
        con.close()


def consulta(sql: str, params: tuple = ()) -> pd.DataFrame:
    """SQL livre sobre as tabelas processadas (ex.: vendas filtradas por cliente)."""
    return _consulta(sql, params, _versao("vendas"))


def existe(nome: str) -> bool:
    return armazenamento.caminho(nome).exists()

"""Regras de negócio puras (sem I/O), reaproveitadas pelas fatias e testadas isoladamente."""
import re

import numpy as np
import pandas as pd

from deva.core import config


def prazo_dias(cond_pag: str | None) -> float:
    """Maior prazo, em dias, de uma condição de pagamento. À vista = 0; desconhecido = NaN."""
    if not cond_pag:
        return np.nan
    c = cond_pag.upper()
    if any(k in c for k in ("A VISTA", "PIX", "ANTECIPAD", "DINH", "CARTAO")):
        return 0.0
    parcelas = re.search(r"(\d+)\s*X\b", c)
    if parcelas:
        passo = re.search(r"DE\s*(\d+)\s*EM\s*\d+", c)  # "10X - VENCIMENTO DE 20 EM 20 DIAS"
        return float(int(parcelas.group(1)) * (int(passo.group(1)) if passo else 30))
    dias = [int(n) for n in re.findall(r"\d+", c)]
    if dias and ("DIA" in c or "/" in c or "DUPL" in c or "BOL" in c):
        return float(max(dias))
    return np.nan


def categorizar(df: pd.DataFrame) -> pd.Series:
    """Categoria de frequência. Espera colunas: dias_desde_primeira, recencia_dias,
    meses_ativos_12m, dias_compra, intervalo_medio_dias."""
    intervalo = df["intervalo_medio_dias"].fillna(np.inf)
    limite_risco = np.maximum(config.DIAS_MIN_RISCO, config.FATOR_RISCO * intervalo)
    condicoes = [
        df["dias_desde_primeira"] <= config.DIAS_NOVO,
        df["recencia_dias"] > config.DIAS_PERDIDO,
        (df["dias_compra"] >= config.COMPRAS_MIN_RISCO) & (df["recencia_dias"] > limite_risco),
        df["meses_ativos_12m"] >= config.MESES_FIEL,
        df["meses_ativos_12m"] >= config.MESES_RECORRENTE,
    ]
    escolhas = ["Novo", "Perdido", "Em risco", "Fiel", "Recorrente"]
    return pd.Series(np.select(condicoes, escolhas, default="Ocasional"), index=df.index)


def faixa_giro(nfs_12m: pd.Series) -> pd.Series:
    n = nfs_12m.fillna(0)
    return pd.Series(
        np.select(
            [n >= config.NFS_GIRO_ALTO, n >= config.NFS_GIRO_MEDIO, n >= 1],
            ["Alto", "Médio", "Baixo"],
            default="Sem venda 12m",
        ),
        index=nfs_12m.index,
    )


def baixo_giro_score(nfs_12m: pd.Series, classe_giro: pd.Series) -> pd.Series:
    """0 = gira muito, 1 = quase não gira. Classe de estoque C reforça o score."""
    n = nfs_12m.fillna(0).clip(lower=0)
    base = 1 - np.minimum(1, np.log1p(n) / np.log1p(config.NFS_GIRO_ALTO))
    reforco = classe_giro.fillna("").str.startswith("C") * 0.15
    return (base + reforco).clip(0, 1)


def curva_abc(valores: pd.Series) -> pd.Series:
    ordem = valores.sort_values(ascending=False).clip(lower=0)
    # participação acumulada ANTES do item: quem começa abaixo de 80% é A
    antes = (ordem.cumsum() - ordem) / max(ordem.sum(), 1e-9)
    curva = pd.Series(np.select([antes < 0.8, antes < 0.95], ["A", "B"], default="C"), index=ordem.index)
    return curva.reindex(valores.index)


def situacao_compra(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Dias sem comprar comparado ao hábito do próprio cliente.
    Retorna (atraso_x = recência / intervalo habitual, rótulo da situação)."""
    habito = df["intervalo_medio_dias"].where(df["dias_compra"] > 1)
    # quem compra quase todo dia não vira "atrasado" por poucos dias sem nota
    atraso = df["recencia_dias"] / habito.clip(lower=config.DIAS_MIN_HABITO)
    rotulo = np.select(
        [habito.isna(), atraso <= 1, atraso <= 2],
        ["Compra única", "No ritmo", "Atrasado"],
        default="Muito atrasado",
    )
    return atraso, pd.Series(rotulo, index=df.index)

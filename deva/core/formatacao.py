import math

import pandas as pd

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def _vazio(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x)) or x is pd.NaT


def brl(x, casas: int = 2) -> str:
    if _vazio(x):
        return "—"
    s = f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def brl_curto(x) -> str:
    if _vazio(x):
        return "—"
    for lim, suf in ((1e6, " mi"), (1e3, " mil")):
        if abs(x) >= lim:
            return f"R$ {x / lim:,.1f}{suf}".replace(".", ",")
    return brl(x, 0)


def num(x, casas: int = 0) -> str:
    if _vazio(x):
        return "—"
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, casas: int = 1, sinal: bool = False) -> str:
    if _vazio(x):
        return "—"
    s = f"{x * 100:+.{casas}f}%" if sinal else f"{x * 100:.{casas}f}%"
    return s.replace(".", ",")


def mes_ano(d) -> str:
    if _vazio(d):
        return "—"
    d = pd.Timestamp(d)
    return f"{MESES[d.month - 1]}/{d.year}"


def data_br(d) -> str:
    if _vazio(d):
        return "—"
    return pd.Timestamp(d).strftime("%d/%m/%Y")

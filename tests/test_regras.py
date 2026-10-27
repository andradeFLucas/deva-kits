import math

import pandas as pd

from deva.core import regras


def test_prazo_dias():
    assert regras.prazo_dias("BOL. 30 / 60 / 90 DIAS") == 90
    assert regras.prazo_dias("DUPL 30/60/90/120/150/180 DIAS") == 180
    assert regras.prazo_dias("PRIME 75DIAS") == 75
    assert regras.prazo_dias("BOLETO 8X") == 240
    assert regras.prazo_dias("PIX / DEPÓSITO / ANTECIPADO") == 0
    assert regras.prazo_dias("A VISTA - DINH / CARTAO") == 0
    assert math.isnan(regras.prazo_dias("GARANTIA"))


def test_categorizar():
    df = pd.DataFrame([
        # primeira, recência, meses 12m, dias compra, intervalo
        (30, 10, 1, 1, None),     # Novo
        (900, 400, 0, 10, 30),    # Perdido
        (700, 120, 3, 12, 20),    # Em risco: sumiu 120 > max(90, 40)
        (700, 10, 10, 40, 15),    # Fiel
        (700, 20, 5, 12, 50),     # Recorrente
        (700, 60, 2, 2, 300),     # Ocasional
        (700, 100, 2, 5, 80),     # Ocasional: 100 < 2 x 80
    ], columns=["dias_desde_primeira", "recencia_dias", "meses_ativos_12m", "dias_compra", "intervalo_medio_dias"])
    assert regras.categorizar(df).tolist() == ["Novo", "Perdido", "Em risco", "Fiel", "Recorrente", "Ocasional", "Ocasional"]


def test_faixa_e_score_giro():
    n = pd.Series([100, 20, 3, 0])
    assert regras.faixa_giro(n).tolist() == ["Alto", "Médio", "Baixo", "Sem venda 12m"]
    s = regras.baixo_giro_score(n, pd.Series(["A1", "B2", "C?", None]))
    assert s.is_monotonic_increasing and s.iloc[0] == 0 and s.iloc[-1] == 1


def test_curva_abc_primeiro_sempre_a():
    curva = regras.curva_abc(pd.Series([900, 50, 30, 20]))
    assert curva.tolist() == ["A", "B", "C", "C"]


def test_situacao_compra():
    df = pd.DataFrame({"recencia_dias": [6, 30, 90, 40, 20], "intervalo_medio_dias": [2.7, 20, 30, None, 3],
                       "dias_compra": [500, 5, 4, 1, 300]})
    atraso, rotulo = regras.situacao_compra(df)
    # 6 dias sem comprar para quem compra a cada 2,7 dias ainda é "no ritmo" (piso de 14 dias)
    assert rotulo.tolist() == ["No ritmo", "Atrasado", "Muito atrasado", "Compra única", "Atrasado"]
    assert atraso.iloc[1] == 1.5

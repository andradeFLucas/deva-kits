import pandas as pd

from deva.core import config
from deva.features.kits_cliente import calculo


def _prod(cod, faixa="Alto", bg=0.0):
    return dict(produto_cod=cod, produto_des=f"P{cod}", referencia=str(cod), faixa_giro=faixa,
                baixo_giro_score=bg, preco_ref=100.0)


def _af(a, b, co, cos, score):
    return dict(a=a, b=b, co_cesta=co, cos_cesta=cos, score=score)


def test_kit_com_ancora_mesmo_servico_e_baixo_giro():
    prod = pd.DataFrame([_prod(1), _prod(2), _prod(3), _prod(4), _prod(9, "Baixo", 0.9), _prod(7)])
    af = pd.DataFrame([
        _af(1, 2, 50, 0.5, 0.5), _af(1, 3, 40, 0.4, 0.4), _af(1, 4, 1, 0.01, 0.01),  # 4 fraco demais
        _af(2, 9, 3, 0.1, 0.2), _af(3, 7, 0, 0.0, 0.3),                             # 9 ok; 7 sem cesta
    ])
    cp = pd.DataFrame([
        # cliente 10 compra o item 1 a cada 30 dias e está há 30 sem comprar (no prazo)
        dict(cliente_cod=10, produto_cod=1, dias_compra=6, intervalo_medio_dias=30.0, recencia_dias=30, qtde_por_compra=2.2),
        dict(cliente_cod=10, produto_cod=2, dias_compra=3, intervalo_medio_dias=60.0, recencia_dias=10, qtde_por_compra=1.0),
        # item 7 genérico, no prazo, sem vizinhos de serviço -> reposição avulsa
        dict(cliente_cod=10, produto_cod=7, dias_compra=4, intervalo_medio_dias=20.0, recencia_dias=25, qtde_por_compra=1.0),
    ])
    k = calculo.montar(cp, prod, af)
    kit = k[k["kit_ordem"] == 1]
    assert kit["papel"].tolist() == ["Âncora", "Mesmo serviço", "Mesmo serviço", "Baixo giro"]
    assert kit["produto_cod"].tolist() == [1, 2, 3, 9]
    assert kit.iloc[0]["qtde_sugerida"] == 2
    assert kit.iloc[3]["valor_kit"] == 100 * (1 - config.KIT_DESCONTO_BAIXO_GIRO)
    assert kit["ja_compra"].tolist() == [True, True, False, False]
    avulsa = k[k["kit_ordem"] == 0]
    assert avulsa["produto_cod"].tolist() == [7]


def test_sem_itens_de_servico_nao_vira_kit():
    prod = pd.DataFrame([_prod(1), _prod(2)])
    af = pd.DataFrame([_af(1, 2, 50, 0.5, 0.5)])
    cp = pd.DataFrame([dict(cliente_cod=10, produto_cod=1, dias_compra=6, intervalo_medio_dias=30.0,
                            recencia_dias=5, qtde_por_compra=1.0)])
    assert calculo.montar(cp, prod, af).empty

"""Parâmetros do sistema. Ajuste aqui as regras de negócio sem mexer nas fatias."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DADOS_RAW = RAIZ / "data" / "raw"
DADOS_PROC = RAIZ / "data" / "processed"
FONTE_VENDAS = DADOS_RAW / "VendasPecas.parquet"

# Linhas anteriores a esta data são resíduos e ficam fora da análise
DATA_INICIO = "2024-01-01"

# --- Segmentos (regras aplicadas linha a linha na ingestão) ---
SEGMENTOS_ESPECIAIS = ["Garantia", "Interno", "Seguradora"]
SEGMENTO_CLIENTE = "Cliente"
SEGMENTO_ML = "Mercado Livre"

# --- Categorias de frequência ---
DIAS_NOVO = 90            # primeira compra há até N dias
DIAS_PERDIDO = 365        # sem comprar há mais de N dias
MESES_FIEL = 8            # meses com compra nos últimos 12
MESES_RECORRENTE = 4
DIAS_MIN_RISCO = 90       # em risco: sumiu há mais de N dias...
FATOR_RISCO = 2.0         # ...e há mais de FATOR x o seu intervalo habitual
COMPRAS_MIN_RISCO = 3     # só quem já tinha hábito (dias de compra)

DIAS_MIN_HABITO = 14      # piso do intervalo habitual ao medir atraso

CATEGORIAS = ["Fiel", "Recorrente", "Novo", "Ocasional", "Em risco", "Perdido"]

# --- Giro de produtos (notas com o item nos últimos 12 meses) ---
NFS_GIRO_ALTO = 52        # ~semanal
NFS_GIRO_MEDIO = 12       # ~mensal
FAIXAS_GIRO = ["Alto", "Médio", "Baixo", "Sem venda 12m"]

# --- Afinidade / compatibilidade ---
CESTA_MAX_ITENS = 40          # cestas maiores misturam veículos
CLIENTE_MAX_ITENS = 150       # clientes com mix enorme têm frota variada demais
MIN_CO_CESTA = 2
MIN_CO_CLIENTE = 3
PESO_CESTA = 0.65             # mesma NF/OS = mesmo veículo -> sinal mais forte
PESO_CLIENTE = 0.35
VIZINHOS_POR_ITEM = 40

# --- Kits por cliente (âncora + itens do mesmo serviço + baixo giro) ---
KIT_MAX_POR_CLIENTE = 5
KIT_ANCORAS_AVALIADAS = 20        # candidatas a âncora por cliente
KIT_SERVICO_MIN_CO = 5            # OS/NF em que âncora e item saíram juntos
KIT_SERVICO_MIN_COS = 0.08
KIT_SERVICO_MIN_ITENS = 2         # sem 2 itens do mesmo serviço, não vira kit
KIT_SERVICO_MAX_ITENS = 4
KIT_BAIXO_GIRO_MAX_ITENS = 2
KIT_BAIXO_GIRO_MIN_LIGACAO = 0.05
KIT_BAIXO_GIRO_MIN_CO = 2         # vezes na mesma OS/NF que algum item do kit
KIT_DESCONTO_BAIXO_GIRO = 0.10    # desconto sugerido só nos itens de baixo giro do kit
KIT_SOBREPOSICAO_MAX = 0.5        # kits com itens demais em comum são descartados
REPOSICAO_AVULSA_MAX = 5

# --- Kits padrão (plano de manutenção inferido) ---
KIT_PADRAO_MIN_CESTAS = 30
KIT_PADRAO_MIN_COS = 0.12
KIT_PADRAO_MIN_CO = 8
KIT_PADRAO_MAX_ITENS = 6

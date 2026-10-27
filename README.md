# Deva · Inteligência de Clientes

Painel local para entender os clientes de peças da Deva (Iveco), classificá-los por frequência e sugerir **kits**
que aumentam o ticket e **priorizam itens de baixo giro** compatíveis com o que cada cliente já compra.

- **Diretoria:** BI completo (visão geral, clientes, perfil com texto automático, produtos, kits/manutenção, Mercado Livre, segmentos especiais).
- **Vendedor de balcão:** só a tela "Kits para oferecer", sem margens nem números da diretoria.

## Como rodar

```bash
pip install -r requirements.txt
python -m deva.pipeline data/raw/VendasPecas.parquet   # processa a base (~10 s)
streamlit run app.py                                   # abre em http://localhost:8501
```

Na entrada, escolha a versão: **Diretoria** (painel completo) ou **Vendedor de balcão** (só os kits). Não há senha; para trocar de versão, use "Trocar versão" na barra lateral.

**Atualização mensal:** substitua `data/raw/VendasPecas.parquet` pela nova exportação e rode o pipeline de novo. O painel recarrega sozinho.

## Arquitetura (fatias verticais)

Cada funcionalidade é uma pasta em `deva/features/` com o próprio cálculo (`calculo.py`) e a própria tela (`pagina.py`).
Para adicionar uma funcionalidade, crie uma nova fatia sem mexer nas outras.

```
deva/
  core/            config (regras ajustáveis), armazenamento (parquet+DuckDB), regras puras, ui, acesso
  features/
    ingestao/            base bruta -> tabela `vendas` (devoluções negativas, segmentos, cesta por OS/NF)
    clientes/            métricas por cliente/canal, categoria de frequência, curva ABC
    produtos/            giro por código, intervalo típico de reposição
    afinidade/           compatibilidade entre códigos (mesma OS/NF e mesmo cliente)
    kits_cliente/        até 5 kits por cliente: âncora (item que ele compra) + itens do mesmo serviço + baixo giro c/ desconto
    kits_padrao/         plano de manutenção inferido (kits por item âncora)
    perfil_cliente/      texto automático "quem é / como compra / o que vender / vale negociar"
      analises_ia/       análise escrita pela IA para os 10 maiores clientes (um .md por código; fixa)
    visao_geral/  mercado_livre/  segmentos_especiais/  vendedor/   (telas)
  pipeline.py      ordem de execução das etapas
app.py             navegação e perfis
```

A camada `core/armazenamento.py` é o único ponto que sabe onde os dados estão. Quando a base vier de um banco,
basta trocar a ingestão (e, se for o caso, o armazenamento) sem mexer nas telas.

## Regras principais (ajustáveis em `deva/core/config.py`)

| Conceito | Regra |
|---|---|
| Segmentos | Garantia (IVG/cond. GARANTIA), Interno (Deva Veículos/VENDA INTERNA), Seguradora, Mercado Livre; o resto é Cliente |
| Novo | 1ª compra há até 90 dias |
| Perdido | sem comprar há mais de 365 dias |
| Em risco | tinha hábito (3+ dias de compra) e está sem comprar há mais de 90 dias e de 2× o seu intervalo |
| Fiel / Recorrente | compra em 8+ / 4–7 dos últimos 12 meses |
| Giro do item | Alto ≥52 notas/ano, Médio 12–51, Baixo 1–11, Sem venda 12m |
| Kit do cliente | âncora = item que ele já compra (no prazo primeiro); entram os itens que saem com ela na mesma OS/NF (5+ vezes) e até 2 de baixo giro com 10% de desconto sugerido |
| Compatibilidade | itens na mesma OS/NF (mesmo veículo, peso 65%) + mesmo cliente (mesma frota, peso 35%), sempre por código exato |

## Análise da IA (top 10)

Os 10 maiores clientes em faturamento total têm uma análise escrita pela IA (Claude) em
`deva/features/perfil_cliente/analises_ia/<codigo>.md`. Ela é **fixa**: não gasta tokens ao abrir o painel.
Para atualizar (ex.: a cada trimestre), reescreva os arquivos com os dados novos e ajuste as datas em `analises_ia.py`.
Os demais clientes usam o resumo automático por regras.

## Próximas fatias

- **estoque:** cruzar quantidade e valor parado com o giro, para priorizar nos kits o que tem estoque obsoleto.
- Ligação direta com o banco do ERP, no lugar do parquet mensal.

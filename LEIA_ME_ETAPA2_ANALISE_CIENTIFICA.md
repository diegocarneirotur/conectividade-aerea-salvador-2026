# Etapa 2 — Modelagem de grafos direcionados e reexame da hipótese

## 1. Escopo e proveniência

A comparação utiliza `ssa.csv`, com reconstrução em `etapa1_validacao_ssa/02_etapas_fisicas_reconstruidas.csv`. Semanas de movimentos reais em Salvador: **20 a 26 de outubro de 2025** e **12 a 18 de fevereiro de 2026**. Companhias domésticas de passageiros incluídas, entre elas LATAM/TAM (`JJ`); TAP (`TP`) excluída. `NÃO REGULAR` vem de `ds_grupo_di`, e não de `ds_tipo_empresa`. A unidade de voos físicos é a **etapa real de chegada ou saída de SSA**, reconstruída por chave composta (não identificador operacional nativo). Contagens ainda dependem de confrontação externa com etapas básicas da ANAC.

O indicador de passageiros é a soma dos embarques e desembarques reportados em SSA associados aos movimentos; os totais não equivalem a turistas únicos nem à lotação física das aeronaves.

## 2. Resultados comparativos

| Indicador | Outubro 2025 | Fevereiro 2026 | Diferença |
|---|---:|---:|---:|
| Etapas físicas reconstruídas | 993 | 1.167 | +174 (17,5%) |
| Movimentos com passageiros associados a SSA | 149.367 | 164.628 | +15.261 (10,2%) |
| Aeroportos diretos com passageiros | 27 | 29 | +2 |
| Arestas direcionadas com passageiros | 54 | 58 | +4 |
| Etapas regulares | 969 | 1.081 | +112 |
| Etapas não regulares | 24 | 86 | +62 |
| Passageiros em operações não regulares | 2.221 | 10.907 | +8.686 |
| Etapas LATAM/TAM (`JJ`) | 268 | 298 | +30 |
| Passageiros LATAM/TAM (`JJ`) | 44.221 | 49.254 | +5.033 |

## 3. Mudança nas arestas e componentes do crescimento

- **Retidas:** 54 de 54 arestas direcionadas com passageiros presentes em outubro permanecem em fevereiro.
- **Adicionadas:** quatro arestas direcionadas correspondentes aos pares de ida e volta com **Santos Dumont (SDU/SBRJ)** e **Cuiabá (CGB/SBCY)**.
- **Removidas:** nenhuma aresta dirigida com passageiro positivo no período de controle.
- Similaridade de Jaccard entre conjuntos de arestas dirigidas: 93,10%.
- **SDU:** 10 etapas e 1.237 movimentos de passageiros; categoria `REGULAR`.
- **CGB:** quatro etapas e 504 movimentos de passageiros; categoria `NÃO REGULAR`.
- Novos corredores responderam por apenas 14 de 174 etapas adicionais e 1.741 dos 15.261 movimentos de passageiros adicionais. A maior parte do crescimento ocorreu em corredores previamente existentes. Duas etapas de fevereiro para SSCE, sem passageiros, são mantidas no universo operacional, mas não representadas no grafo de ligações com passageiros.

## 4. Concentração e hipótese de desconcentração

Os cinco maiores aeroportos do período controle foram CGH, GRU, GIG, BSB e VCP. Sua participação conjunta subiu de **67,22%** para **68,85%**, variação de **+1.63 p.p.** O HHI por aeroporto adjacente, ponderado pelos movimentos de passageiros, aumentou de **0.11554** para **0.12035** (variação +0.00482). A ampliação da capilaridade não correspondeu a desconcentração de passageiros; na medida disponível, observou-se o contrário.

Os cinco corredores respondem por 12.947 dos 15.261 passageiros adicionais (84,8% do saldo líquido). Isso indica intensificação de corredores existentes, não a transferência comprovada de passageiros entre hubs.

## 5. Teste exploratório de diferenças diárias

Foram comparados 7 pares por dia da semana (segunda com segunda, etc.), enumerando todas as 128 possibilidades de inversão de sinais; teste **bicaudal**, com ajuste **Holm** para três desfechos principais. Esse procedimento **não estabelece causalidade** e possui poder estatístico reduzido em apenas 7 dias por período.

| Indicador | Valor-p bicaudal exato | Valor-p ajustado Holm |
|---|---:|---:|
| Etapas físicas/dia | 0.04688 | 0.14062 |
| Passageiros/dia | 0.15625 | 0.15625 |
| Etapas não regulares/dia | 0.06250 | 0.14062 |

**Interpretação:** as diferenças agregadas são observadas nas duas semanas escolhidas. Após o ajuste para três comparações exploratórias, nenhum teste atinge p < 0,05. Os números não permitem inferir efeito causal do Carnaval; podem refletir feriados, calendário comercial, alterações de oferta ou outros fatores.

## 6. Limites de inferência pela Teoria dos Grafos

Os grafos são uma **rede focal (ego-network) de SSA**: somente há arestas que ligam SSA a um aeroporto adjacente. Portanto, não representam ligações entre outros aeroportos brasileiros. Por construção, não é adequado calcular centralidade de intermediação dos hubs, caminhos mínimos da malha brasileira, centralidade de proximidade global ou alegar redução da dependência de conexões intermediárias. Esses indicadores dependem da malha nacional completa, com o mesmo recorte e a mesma unidade de etapas básicas.

**Síntese das hipóteses:** H1a (ampliação de conectividade direta) é corroborada na comparação descritiva; H1b (aumento da participação de não regulares) é corroborada descritivamente; H1c (desconcentração dos fluxos/redução de intermediação dos hubs) não é corroborada quanto à concentração observável e permanece sem teste válido quanto à intermediação de hubs.

## 7. Pendências para redação definitiva

1. Conferir amostra das etapas reconstruídas com os dados independentes de **etapas básicas ANAC/VRA** e registrar o dicionário e a origem da extração de `ssa.csv`.
2. Esclarecer o zero de passageiros nas cinco etapas de cada semana e os dois movimentos de SSCE em fevereiro.
3. Verificar a duplicidade de um passageiro em outubro; a sensibilidade é de no máximo um movimento de passageiro.
4. Para sustentar conclusões sobre rede nacional e hubs, obter dados de trajetos diretos entre **todos** os aeroportos comerciais do Brasil nas mesmas duas semanas.
5. Para atribuir efeito ao Carnaval, incluir semanas adicionais e, idealmente, períodos de fevereiro de outros anos, usando comparação ajustada a sazonalidade, dia da semana e tendências da aviação.

## 8. Entregáveis

- Dois grafos direcionados (.png e .svg), um por semana, com layout, símbolos e escala iguais.
- Gráfico de diferenças por corredor e gráfico da concentração dos cinco principais mercados.
- Matrizes de arestas com orientação, peso de etapas, passageiros e presença da LATAM.
- Tabelas de aeroportos, diferenças, indicadores diários e testes exatos.
- Script reproduzível e JSON com verificações.

*Resultados preliminares para elaboração de artigo científico. Dados derivados de reconstrução interna, não validados independentemente como etapa básica oficial.*

# Estudo SSA — Etapa 1: auditoria e reconstrução dos microdados

**Objetivo:** preparar uma base auditável de operações domésticas de passageiros associadas ao Aeroporto de Salvador (SSA), para a comparação entre 20–26/10/2025 e 12–18/02/2026. Inclui a LATAM/TAM (`JJ`) e exclui a TAP (`TP`).  
**Arquivo de entrada:** `ssa.csv` (mantido sem alterações).  
**Estado:** base reconstruída e validada por regras de consistência interna; a equivalência com registros independentes de etapas básicas e com o dicionário completo da fonte ainda deve ser confirmada.

## 1. Fonte, alcance e unidade de observação

A base fornecida possui **26.101 registros e 55 campos**. A data de referência cobre exclusivamente outubro de 2025 (31 dias) e fevereiro de 2026 (28 dias). Dois campos (`nr_linha`, `dt_sistema`) estão inteiramente vazios. Os dados parecem uma extração analítica de informações da ANAC; a procedência da consulta e seu procedimento de transformação precisam ser declarados pelo responsável pela extração.

**A linha original não equivale a um voo físico:** há registros de origem–destino de passageiros associados a uma mesma etapa da aeronave, com possibilidade de escalas intermediárias. O estudo requer duas unidades distintas:

- **Registro de origem–destino (OD)**: passageiros pagos + gratuitos atribuídos a uma origem e um destino no mesmo voo, potencialmente com escalas intermediárias.
- **Etapa física associada a SSA**: um movimento de chegada ou partida em Salvador, entre SSA e o aeroporto imediatamente anterior ou posterior, reconstruído a partir das sequências de escalas e do horário real da movimentação em SSA.

Na ANAC, a *etapa básica* equivale a decolagem → pouso seguinte, e a *etapa combinada* representa o par embarque/desembarque de pessoas ou carga com ou sem escalas. A reconstrução abaixo corresponde a essa distinção, mas o CSV não apresenta um identificador nativo da etapa básica.

## 2. Recorte principal e regras de inclusão

1. **Períodos por data real de movimentação em SSA:** chegadas pela coluna `dt_chegada_real`; partidas por `dt_partida_real`. Semanas: 20–26 de outubro de 2025 e 12–18 de fevereiro de 2026, sete dias cada. Os horários seguem as informações do próprio CSV; recomenda-se confirmar o fuso oficial da extração.
2. SSA deve ser uma e apenas uma ponta (`sg_iata_origem` ou `sg_iata_destino`).
3. Origem e destino devem estar no **Brasil** (`nm_pais_origem` e `nm_pais_destino`).
4. Serviço destinado a **passageiros** (`ds_servico_tipo_linha = PASSAGEIRO`).
5. Manter `ds_grupo_di = REGULAR` ou `NÃO REGULAR`; excluir `IMPRODUTIVO`. A distinção operacional utiliza **`ds_grupo_di`**, não `ds_tipo_empresa` — este último refere-se à habilitação/classificação empresarial e motivou confusão nos mapas anteriores.
6. Excluir a TAP (`sg_empresa_iata = TP`). Os registros TAP presentes nesta base são internacionais, portanto já ficam fora pelo recorte doméstico. A LATAM aparece como `JJ` / `TAM LINHAS AÉREAS S.A.` e foi mantida.
7. Remover apenas **duplicidades integralmente idênticas com zero passageiros** na seleção semanal, para que não inflacionem o número de registros. A contagem de etapas físicas já evita múltiplas contagens de uma mesma operação. Uma duplicidade positiva de **1 passageiro**, na madrugada de 20/10 (voo G3 2084, com referência em 19/10), foi **preservada** porque não existe chave de COTRAN/classificação de passageiros no CSV para afirmar que o registro é falso. A incerteza correspondente é de 1 movimento de passageiro.
8. Manter no arquivo de etapas os movimentos com zero passageiros, porém identificados por sinalizador. Eles **não** entram na contagem de aeroportos com passageiros registrados.

## 3. Como foi reconstruído o trecho físico

Os campos `nr_etapa` e `nr_escala_destino` representam sequências de escala presentes na extração. Uma linha com `nr_escala_destino = nr_etapa + 1` identifica o par sem aeroporto intermediário dentro daquele itinerário. Os demais pares correspondem a passageiros cujo trajeto no mesmo voo inclui ao menos uma etapa intermediária.

A chave operacional construída para SSA reúne companhia, número do voo, data de referência, movimento, data/hora real de chegada ou partida em SSA e posição da escala de SSA na operação. Cada chave reúne todas as linhas de passageiros correspondentes àquela movimentação de aeronave. A associação ao aeroporto imediatamente anterior ou posterior é retirada da linha adjacente.

**Exemplo verificável no arquivo:** voo Azul `AD 4330`, em 22/10/2025. O movimento de chegada é **AJU → SSA**, embora contenha passageiros registrados nos pares **REC → SSA** (18 passageiros) e **AJU → SSA** (40 passageiros). Assim, são **58 passageiros desembarcados naquele movimento em SSA**, mas **apenas uma etapa física de chegada**, não duas. Na partida do mesmo voo, o trecho físico de saída é **SSA → VDC**, embora haja registros de destinos SSA → VDC e SSA → CNF. Um grafo de voos diretos deve usar AJU → SSA e SSA → VDC, não representar REC → SSA e SSA → CNF como ligações diretas desse voo.

**Limite:** os totais de passageiros agregados por etapa representam os passageiros com embarque ou desembarque em SSA e não devem ser confundidos com a ocupação total da aeronave na etapa física (que pode incluir passageiros passantes), nem com indivíduos únicos ou turistas. Falta a tabela oficial de etapas básicas e o identificador nativo completo de operação para auditoria externa dos pares reconstruídos.

## 4. Indicadores validados para as duas semanas reais

| Indicador | 20–26/10/2025 | 12–18/02/2026 | Interpretação |
|---|---:|---:|---|
| Registros OD originais dentro dos filtros | 2.755 | 3.158 | **Não são voos** |
| Duplicados idênticos de zero passageiros retirados | 217 | 292 | Sem impacto nos totais de passageiros |
| Registros OD higienizados | 2.538 | 2.866 | Mantêm abertura OD original |
| **Etapas físicas reconstruídas em SSA** | **993** | **1.167** | +17,52% (chave operacional inferida) |
| Etapas de chegada | 497 | 585 | Movimentos chegando a SSA |
| Etapas de partida | 496 | 582 | Movimentos partindo de SSA |
| Etapas REGULAR | 969 | 1.081 | Por `ds_grupo_di` |
| Etapas NÃO REGULAR | 24 | 86 | Por `ds_grupo_di` |
| **Passageiros (pagos + gratuitos)** | **149.367** | **164.628** | **+10,22%** |
| Passageiros em chegadas | 74.253 | 82.251 | +10,77% |
| Passageiros em partidas | 75.114 | 82.377 | +9,67% |
| Passageiros de operações não regulares | 2.221 | 10.907 | Composição operacional distinta |
| Aeroportos diretamente adjacentes com passageiros | 27 | 29 | Dois aeroportos adicionais: CGB e SDU |
| Arestas dirigidas com passageiros positivos | 54 | 58 | 27/29 pares bidirecionais |
| Etapas sem passageiro reportado | 5 | 5 | Mantidas com alerta |
| Passageiros OD com etapa intermediária atribuídos à etapa física | 884 | 291 | Precisariam ser redistribuídos ao aeroporto imediatamente adjacente |

**Verificação:** todas as **2.160 etapas físicas** das duas semanas têm uma única ponta imediatamente adjacente identificada. Nenhuma chave teve conflito de companhia, classificação ou aeroporto adjacente. A soma dos passageiros por etapa confere com a soma dos registros OD higienizados (313.995 movimentos de passageiros nas duas semanas somadas).

## 5. Diferença importante entre data de referência e data real

Nos resultados exploratórios anteriores, as semanas foram filtradas por `dt_referencia`, isto é, a data de referência da operação. Agora, no recorte de movimentos efetivos de SSA, usei a data/hora real **em Salvador**. Voos que partem no dia anterior e chegam após a meia-noite passam a ser atribuídos ao dia em que efetivamente chegaram a Salvador.

| Critério de recorte | Outubro/2025 | Fevereiro/2026 |
|---|---:|---:|
| Passageiros por `dt_referencia` (análise anterior) | 149.450 | 164.154 |
| Passageiros por data real de chegada/partida em SSA (etapa 1) | **149.367** | **164.628** |
| Etapas por `dt_referencia` | 993 | 1.166 |
| Etapas por data real em SSA | **993** | **1.167** |

**Decisão metodológica recomendada:** para a comparação de fluxos efetivos nas semanas do evento, utilizar o recorte **pela data real de movimento em SSA**, e manter o recorte por `dt_referencia` como teste de sensibilidade. Se o estudo for reformulado como análise da programação de voos planejados, o critério terá de ser diferente e validado com documentação.

## 6. Alertas que permanecem abertos

- **Risco alto — confirmação externa da etapa física:** `nr_etapa` e `nr_escala_destino` oferecem um mapeamento interno consistente e cobrem todos os movimentos examinados, mas a base não fornece identificador nativo completo da aeronave/etapa nem informação explícita da categoria básica/combinada. Recomenda-se confrontar amostra de voos com os microdados oficiais de etapas básicas/VRA e o dicionário exato da extração.
- **Risco médio — duplicidade positiva não resolvida:** duas linhas integralmente iguais com `1` passageiro no voo G3 2084, chegada real em SSA em 20/10/2025, referência 19/10. Ambas permanecem. O total de outubro pode variar em um passageiro após verificação na origem.
- **Risco médio — registros sem passageiros:** há 5 etapas físicas com zero passageiros em cada semana. Em fevereiro, duas delas são saídas de SSA para o aeródromo **SSCE (Emival Caiado)**, sem código IATA no CSV (`...`) e sem passageiros. SSCE não integra a rede de passageiros positivos, mas permanece na base de movimentos com alerta.
- **Risco médio — atributos indisponíveis:** o arquivo não contém assentos ofertados, identificação de turista, motivo de viagem, conexões entre aeroportos que não SSA, identificação individual de passageiros ou condição explícita de cancelamento. Esses indicadores não podem ser inferidos dos campos disponíveis.
- **Risco médio — fonte transformada:** `nr_linha` e `dt_sistema` estão 100% vazios; `nm_arquivo` possui lacunas, embora `id_arquivo` esteja preenchido. A origem da transformação do CSV deve ser documentada antes da submissão científica.
- **Risco baixo — detalhe temporal:** as diferenças entre o filtro por referência e o filtro por movimento real afetam principalmente pousos após a meia-noite. Comparações que misturam os critérios deixam de ser válidas.

## 7. Consistência adicional com os mapas anteriores

Aplicando os filtros domésticos de passageiros às **bases mensais de referência** (`dt_referencia`), obtêm-se **637.978 passageiros em outubro** e **639.379 em fevereiro**, reproduzindo os totais anteriormente apresentados nos mapas consolidados. O subconjunto LATAM/TAM (`JJ`) soma **187.141** e **187.405**, respectivamente. Isso é compatível com o material gráfico; não constitui validação de registros individuais por uma fonte independente.

## 8. Uso dos arquivos

- `01_registros_od_higienizados.csv`: linhas de passageiros que compõem as semanas reais, sem duplicações exatas de zero, com sinalizadores e associação à etapa física.
- `02_etapas_fisicas_reconstruidas.csv`: tabela principal, **uma linha por movimento físico reconstruído** no aeroporto SSA; pronta para estudos de conectividade focal, com coluna de alertas de zero passageiros.
- `03_rotas_diretas_agrupadas.csv`: matriz de arestas físicas de SSA (origem/destino ICAO), frequência de etapas e passageiros embarcados/desembarcados em SSA.
- `04_resumo_comparativo_e_sensibilidade.csv`: métricas e comparação de regras temporais.
- `05_auditoria_filtros.csv`: volumes e razões de inclusão/exclusão nas janelas reais.
- `06_perfil_completude_dos_campos.csv`: 55 campos originais, quantidades e percentuais de valores ausentes.
- `07_exemplo_trajeto_com_escala.csv`: linhas e trajetos reais do exemplo AD 4330.
- `08_alertas_duplicados_com_pax.csv`: linha repetida positiva preservada, sujeita à verificação de origem.
- `reproduzir_etapa1_ssa.py`: script reproduzível, sem acesso remoto, somente depende de Python, pandas e numpy.
- `verificacoes_automaticas.json`: testes executados e avisos de interpretação.

## 9. Recomendação para a etapa 2

Usar a base **02** para calcular **graus de entrada e saída de SSA, frequência de etapas e pesos de passageiros por ligação direta**, e a base **01** para discutir mercados de origem–destino de passageiros. Manter separados os mapas topológicos da rede direta e os mapas de mercados OD.

**Não calcular intermediação de hubs, proximidade global ou caminhos mínimos da malha nacional com esse CSV**, pois ele contém apenas operações associadas a Salvador. Para esses indicadores, será necessário obter também as ligações domésticas entre todos os aeroportos brasileiros, sob a mesma unidade e janelas temporais.

## Referências metodológicas oficiais

- ANAC. [Metadados: Dados Estatísticos do Transporte Aéreo](https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/dados-estatisticos-do-transporte-aereo/48-dados-estatisticos-do-transporte-aereo) — definições de etapa básica e etapa combinada.
- ANAC. [Metadados: Voo Regular Ativo (VRA)](https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/voo-regular-ativo-vra/62-voo-regular-ativo-vra) — voos planejados e realizados e situação do voo.

*Documento técnico de auditoria; não é, ainda, uma seção de resultados revisada por pares.*

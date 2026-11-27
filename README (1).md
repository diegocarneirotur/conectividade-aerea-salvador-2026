# Conectividade aérea doméstica direta de Salvador (SSA)

**Uma análise comparativa entre outubro de 2025 e o período do Carnaval de 2026 pela Teoria dos Grafos**

Pesquisa de Trabalho de Conclusão de Curso — Bacharelado em Turismo, Instituto Federal de Goiás (IFG), Câmpus Goiânia.

**Autor:** Diego Carneiro Oliveira  
**Orientador:** Adriano de Carvalho Paranaiba  
**Ano:** 2026

## Objetivo e recorte

Comparar a rede doméstica de ligações diretas associadas a SSA nas semanas de 20 a 26 de outubro de 2025 e 12 a 18 de fevereiro de 2026, distinguindo capilaridade, intensidade operacional e concentração dos movimentos de passageiros. A análise é observacional e descritiva; não identifica efeito causal do Carnaval.

## Organização do material

| Pasta | Conteúdo |
| --- | --- |
| `01_dados_originais/` | Identificação da base original, links oficiais e pendências de proveniência. |
| `02_dados_processados/` | Registros origem–destino higienizados, etapas físicas reconstruídas e rotas agrupadas. |
| `03_scripts/` | Scripts originais de tratamento e análise. |
| `04_resultados/` | Matrizes de arestas e corredores, indicadores semanais, resumo diário e testes exploratórios. |
| `05_figuras/` | Grafos, comparação visual e gráficos em PNG e SVG. |
| `06_documentacao/` | Relatórios técnicos originais, verificações, auditoria e manifesto de integridade. |

## Resultados principais

| Indicador | Outubro/2025 | Fevereiro/2026 |
| --- | ---: | ---: |
| Etapas físicas reconstruídas | 993 | 1.167 |
| Movimentos de passageiros | 149.367 | 164.628 |
| Aeroportos adjacentes com passageiros | 27 | 29 |
| Arestas direcionadas com passageiros | 54 | 58 |
| Etapas não regulares | 24 | 86 |
| HHI ponderado por movimentos de passageiros | 0,11554 | 0,12035 |
| Número efetivo de aeroportos (Shannon) | 11,59 | 11,37 |
| Participação dos cinco corredores líderes de outubro | 67,22% | 68,85% |

Os movimentos não são turistas ou pessoas únicas. Os pesos de passageiros representam embarques/desembarques associados a SSA, não capacidade ou ocupação das aeronaves. Os grafos representam uma rede focal, não a malha nacional completa. A regularidade operacional é definida por `ds_grupo_di`, não por `ds_tipo_empresa`.

## Reproduzir as análises

Com Python 3 instalado, abra um terminal na raiz deste repositório e execute:

```bash
python -m pip install -r requirements.txt
python 03_scripts/reproduzir_etapa2_ssa.py 02_dados_processados execucao/etapa2
```

O segundo comando usa a base reconstruída já disponibilizada, sem modificar os resultados depositados. Os arquivos serão gerados em `execucao/etapa2`.

**Etapa 1: condicionada à recuperação do arquivo bruto.** Após obter o arquivo `ssa.csv` original e verificar seu SHA-256 conforme `01_dados_originais/README.md`, coloque-o em `01_dados_originais/` e execute:

```bash
python 03_scripts/reproduzir_etapa1_ssa.py 01_dados_originais/ssa.csv execucao/etapa1
python 03_scripts/reproduzir_etapa2_ssa.py execucao/etapa1 execucao/etapa2
```

Os scripts foram preservados como recebidos; os relatórios técnicos de cada etapa registram decisões, limitações e verificações. A nomenclatura histórica de "controle" em alguns arquivos significa período de referência, não grupo de controle experimental. O script de Etapa 1 contém um filtro explícito para TAP (TP); conforme a documentação, seus registros disponíveis estavam fora do recorte doméstico.

## Fontes e rastreabilidade

A base de trabalho `ssa.csv` foi descrita na pesquisa como uma extração da ANAC de 26.101 registros e 55 variáveis. A consulta original e os metadados específicos da extração ainda devem ser documentados. A base VRA (Voo Regular Ativo) não contém quantitativos de passageiros e deve ser utilizada apenas para eventual validação externa das etapas, não como fonte exclusiva dos indicadores de passageiros. Ver `01_dados_originais/README.md`.

**Situação da disponibilização:** este pacote inclui as bases derivadas, scripts, resultados e figuras recuperados da documentação do estudo. A base bruta `ssa.csv` e o arquivo histórico `execucao_log.txt` não foram localizados. A reprodução a partir da base derivada não equivale à reprodução integral desde a fonte primária. Os documentos originais foram preservados e o manifesto histórico não foi modificado.

Antes da publicação pública, os responsáveis devem confirmar os direitos de redistribuição da extração original e das bases derivadas, revisar o conteúdo e definir as condições de reutilização. Não foi atribuída licença ao material sem autorização dos autores. Os mapas mensais da fase exploratória não foram incluídos, por adotarem recorte e critérios diferentes dos resultados semanais do TCC.

## Citação

OLIVEIRA, Diego Carneiro. *Conectividade aérea doméstica direta de Salvador: uma análise comparativa entre outubro de 2025 e o período do Carnaval de 2026 pela Teoria dos Grafos*. Dados e códigos de pesquisa. Goiânia: Instituto Federal de Goiás, 2026. Orientador: Adriano de Carvalho Paranaiba. Repositório eletrônico (inserir URL e versão publicadas).

A citação deverá ser atualizada com o endereço definitivo e a versão publicada após a conferência pelos responsáveis.

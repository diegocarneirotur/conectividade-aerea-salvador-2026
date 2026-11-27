# Conectividade aérea doméstica direta de Salvador (SSA)

**Uma análise comparativa entre outubro de 2025 e o período do Carnaval de 2026 pela Teoria dos Grafos**

Pesquisa de Trabalho de Conclusão de Curso — Bacharelado em Turismo, Instituto Federal de Goiás (IFG), Câmpus Goiânia.

**Autor:** Diego Carneiro Oliveira  
**Orientador:** Adriano de Carvalho Paranaiba  
**Ano:** 2026

## Objetivo e recorte

Comparar a rede doméstica de ligações diretas associadas a SSA nas semanas de 20 a 26 de outubro de 2025 e 12 a 18 de fevereiro de 2026, distinguindo capilaridade, intensidade operacional e concentração dos movimentos de passageiros. A análise é observacional e descritiva; não identifica efeito causal do Carnaval.

## Organização do material

Os arquivos estão na raiz deste repositório:

| Grupo | Arquivos |
| --- | --- |
| Dados processados | `01_registros_od_higienizados.csv`, `02_etapas_fisicas_reconstruidas.csv`, `03_rotas_diretas_agrupadas.csv` |
| Scripts | `reproduzir_etapa1_ssa.py`, `reproduzir_etapa2_ssa.py` |
| Resultados | `01_arestas_direcionadas.csv`, `02_corredores_comparativos.csv`, `03_indicadores_semanas.csv`, `04_comparacao_arestas.csv`, `05_resumo_diario.csv`, `06_testes_exploratorios.csv` |
| Figuras | Grafos e gráficos em PNG e SVG |
| Documentação | `LEIA_ME_RELATORIO_TECNICO.md`, `LEIA_ME_ETAPA2_ANALISE_CIENTIFICA.md`, `CONFERENCIA_PACOTE.md`, relatórios de auditoria, arquivos JSON e manifesto histórico |
| Dependências e citação | `requirements.txt`, `CITATION.cff` |

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
python reproduzir_etapa2_ssa.py . execucao/etapa2
```

O segundo comando usa a base reconstruída já disponibilizada, sem modificar os resultados depositados. Os arquivos serão gerados em `execucao/etapa2`.

**Etapa 1: condicionada à recuperação do arquivo bruto.** Após obter o arquivo `ssa.csv` original e verificar o SHA-256 registrado abaixo, coloque-o na raiz do repositório e execute:

```bash
python reproduzir_etapa1_ssa.py ssa.csv execucao/etapa1
python reproduzir_etapa2_ssa.py execucao/etapa1 execucao/etapa2
```

Os scripts foram preservados como recebidos; os relatórios técnicos de cada etapa registram decisões, limitações e verificações. A nomenclatura histórica de "controle" em alguns arquivos significa período de referência, não grupo de controle experimental. O script de Etapa 1 contém um filtro explícito para TAP (TP); conforme a documentação, seus registros disponíveis estavam fora do recorte doméstico.

## Fontes e rastreabilidade

A base de trabalho `ssa.csv` foi descrita na pesquisa como uma extração da ANAC de 26.101 registros e 55 variáveis. A consulta original e os metadados específicos da extração ainda devem ser documentados. A base VRA (Voo Regular Ativo) não contém quantitativos de passageiros e deve ser utilizada apenas para eventual validação externa das etapas, não como fonte exclusiva dos indicadores de passageiros. Consulte os metadados oficiais e as informações de integridade abaixo.

**Situação da disponibilização:** este pacote inclui as bases derivadas, scripts, resultados e figuras recuperados da documentação do estudo. A base bruta `ssa.csv` e o arquivo histórico `execucao_log.txt` não foram localizados. A reprodução a partir da base derivada não equivale à reprodução integral desde a fonte primária. Os documentos originais foram preservados e o manifesto histórico não foi modificado.

Os responsáveis ainda devem confirmar os direitos de redistribuição da extração original e das bases derivadas, revisar o conteúdo e definir as condições de reutilização. Não foi atribuída licença ao material sem autorização dos autores. Os mapas mensais da fase exploratória não foram incluídos, por adotarem recorte e critérios diferentes dos resultados semanais do TCC.

## Dados originais e fontes oficiais

### Arquivo ainda pendente

- Nome: `ssa.csv`
- Tamanho esperado: 13.092.774 bytes
- Dimensão: 26.101 registros e 55 variáveis
- SHA-256 esperado: `dede0b5db5057fe6c05f6df7a8a64f60e63546e3018a28ebb177dd554f7e8198`

O arquivo não está incluído neste pacote. Solicitar ao responsável pela extração a versão original, o endereço da consulta, a data da extração, os filtros e o dicionário de variáveis. Confirmar o hash antes de executar a Etapa 1. A fonte específica dos quantitativos de passageiros ainda depende dessa documentação.

### Fontes complementares

- [ANAC — Metadados dos dados estatísticos do transporte aéreo](https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/dados-estatisticos-do-transporte-aereo/48-dados-estatisticos-do-transporte-aereo)
- [ANAC — Metadados do VRA](https://www.anac.gov.br/acesso-a-informacao/dados-abertos/areas-de-atuacao/voos-e-operacoes-aereas/voo-regular-ativo-vra/62-voo-regular-ativo-vra)
- [VRA outubro/2025](https://siros.anac.gov.br/siros/registros/diversos/vra/2025/VRA_2025_10.csv)
- [VRA fevereiro/2026](https://siros.anac.gov.br/siros/registros/diversos/vra/2026/VRA_2026_02.csv)

Os CSVs mensais do VRA não foram incluídos nem conciliados com as etapas físicas neste pacote. São fontes complementares para verificação operacional, não substitutos do `ssa.csv` original.


**Nota de integridade:** `manifest_hashes.json` registra os hashes históricos dos arquivos da Etapa 1; `SHA256SUMS.txt` preserva os caminhos da estrutura originalmente distribuída no ZIP, antes do upload dos arquivos na raiz.

## Citação

OLIVEIRA, Diego Carneiro. *Conectividade aérea doméstica direta de Salvador: uma análise comparativa entre outubro de 2025 e o período do Carnaval de 2026 pela Teoria dos Grafos*. Dados e códigos de pesquisa. Goiânia: Instituto Federal de Goiás, 2026. Orientador: Adriano de Carvalho Paranaiba. Disponível em: https://github.com/diegocarneirotur/conectividade-aerea-salvador-2026. Acesso em: 26 nov. 2026.

O repositório é público. Para maior estabilidade da citação, recomenda-se publicar uma versão numerada (release).

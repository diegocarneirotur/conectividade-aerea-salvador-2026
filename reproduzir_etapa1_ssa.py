#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria e reconstrução das etapas físicas associadas a SSA.

Uso: python reproduzir_etapa1_ssa.py /mnt/data/ssa.csv /mnt/data/etapa1_validacao_ssa
Não altera o arquivo original.
"""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd

SRC = Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/ssa.csv')
OUT = Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/etapa1_validacao_ssa')
OUT.mkdir(parents=True, exist_ok=True)
raw = pd.read_csv(SRC, sep=';', encoding='utf-8-sig', low_memory=False)
source_columns = raw.columns.to_list()
assert len(raw) == 26101 and len(source_columns) == 55, 'O arquivo original mudou: conferir perfil antes de processar.'
for c in ('dt_referencia', 'dt_partida_real', 'dt_chegada_real'):
    raw[c+'_parsed'] = pd.to_datetime(raw[c], format='%d/%m/%Y', errors='coerce')
raw['passageiros_total'] = pd.to_numeric(raw.nr_passag_pagos,errors='coerce') + pd.to_numeric(raw.nr_passag_gratis,errors='coerce')
raw['data_movimento_ssa'] = pd.to_datetime(np.where(raw.movimento.eq('CHEGADA'), raw.dt_chegada_real_parsed, raw.dt_partida_real_parsed))
raw['hora_movimento_ssa'] = np.where(raw.movimento.eq('CHEGADA'),raw.hr_chegada_real,raw.hr_partida_real)
raw['instante_movimento_ssa'] = raw.data_movimento_ssa.dt.strftime('%Y-%m-%d') + ' ' + raw.hora_movimento_ssa.astype(str)
raw['periodo_referencia'] = np.select([raw.dt_referencia_parsed.between('2025-10-20','2025-10-26'), raw.dt_referencia_parsed.between('2026-02-12','2026-02-18')],['outubro_2025','fevereiro_2026'],default='fora')
raw['periodo_real'] = np.select([raw.data_movimento_ssa.between('2025-10-20','2025-10-26'), raw.data_movimento_ssa.between('2026-02-12','2026-02-18')],['outubro_2025','fevereiro_2026'],default='fora')
raw['direcao'] = np.where(raw.movimento.eq('CHEGADA'),'chegada','partida')

base=(raw.sg_iata_origem.eq('SSA') ^ raw.sg_iata_destino.eq('SSA')) & raw.nm_pais_origem.eq('BRASIL') & raw.nm_pais_destino.eq('BRASIL') & raw.ds_servico_tipo_linha.eq('PASSAGEIRO') & raw.ds_grupo_di.isin(['REGULAR','NÃO REGULAR']) & raw.sg_empresa_iata.ne('TP')
selected_all = raw[base].copy()
selected = selected_all[selected_all.periodo_real.ne('fora')].copy()
# Auditoria de duplicados: comparar apenas colunas originais; as exatas ocorrem em linhas de 0 passageiro no recorte.
selected['duplicado_exato_alem_primeiro'] = selected.duplicated(subset=source_columns,keep='first')
duplicated_positive = selected[selected.duplicado_exato_alem_primeiro & selected.passageiros_total.gt(0)].copy()
duplicated = selected[selected.duplicado_exato_alem_primeiro & selected.passageiros_total.eq(0)].copy()
# Duplicidades exatas com passageiros positivos são preservadas e sinalizadas,
# pois a extração não disponibiliza o identificador de classe/COTRAN para decidir.
filtered = selected[~(selected.duplicado_exato_alem_primeiro & selected.passageiros_total.eq(0))].copy()
filtered['periodo'] = filtered['periodo_real']
filtered['par_direto'] = filtered.nr_escala_destino.eq(filtered.nr_etapa+1)
filtered['passageiro_via_escala'] = ~filtered['par_direto']
filtered['indice_etapa_fisica_ssa'] = np.where(filtered.movimento.eq('CHEGADA'),filtered.nr_escala_destino,filtered.nr_etapa)
filtered['aeroporto_outro_od_icao'] = np.where(filtered.movimento.eq('CHEGADA'),filtered.sg_icao_origem,filtered.sg_icao_destino)
filtered['aeroporto_outro_od_iata'] = np.where(filtered.movimento.eq('CHEGADA'),filtered.sg_iata_origem,filtered.sg_iata_destino)
filtered['outro_aerodromo_nome_od'] = np.where(filtered.movimento.eq('CHEGADA'),filtered.nm_aerodromo_origem,filtered.nm_aerodromo_destino)
keyfields=['sg_empresa_iata','nr_voo','dt_referencia_parsed','movimento','instante_movimento_ssa','indice_etapa_fisica_ssa']
# A chave preserva a data de referência de toda a operação e o horário real em SSA.
filtered['chave_etapa_ssa']=(filtered.sg_empresa_iata.astype(str)+'|'+filtered.nr_voo.astype(str)+'|'+filtered.dt_referencia_parsed.dt.strftime('%Y-%m-%d')+'|'+filtered.movimento.astype(str)+'|'+filtered.instante_movimento_ssa+'|'+filtered.indice_etapa_fisica_ssa.astype(str))

adjacent=filtered[filtered.par_direto].copy()
per_key_neighbor=adjacent.groupby('chave_etapa_ssa')['aeroporto_outro_od_icao'].nunique()
per_key_nature=filtered.groupby('chave_etapa_ssa')['ds_grupo_di'].nunique()
all_keys=set(filtered.chave_etapa_ssa)
assert all_keys==set(per_key_neighbor.index),f'Etapas sem registro de trecho adjacente: {len(all_keys-set(per_key_neighbor.index))}'
assert per_key_neighbor.eq(1).all(),'Um mesmo movimento SSA tem múltiplos aeroportos de origem/destino imediato.'
assert per_key_nature.eq(1).all(),'Naturezas operacionais diferentes na mesma etapa.'
assert filtered['passageiros_total'].ge(0).all(),'Passageiros negativos encontrados.'
assert filtered.sg_iata_origem.eq('SSA').eq(filtered.movimento.eq('PARTIDA')).all(),'Movimento não coincide com posição de SSA.'
assert filtered['data_movimento_ssa'].notna().all(),'Data real de movimentação inválida.'
assert filtered.nr_escala_destino.gt(filtered.nr_etapa).all(),'Sequência de escalas inválida.'

neighbor_cols = ['chave_etapa_ssa','aeroporto_outro_od_icao','aeroporto_outro_od_iata','outro_aerodromo_nome_od']
nearest = adjacent[neighbor_cols].drop_duplicates('chave_etapa_ssa').rename(columns={'aeroporto_outro_od_icao':'aeroporto_adjacent_icao','aeroporto_outro_od_iata':'aeroporto_adjacent_iata','outro_aerodromo_nome_od':'aeroporto_adjacent_nome'})
filtered = filtered.merge(nearest,on='chave_etapa_ssa',validate='many_to_one',how='left')
filtered['origem_fisica_icao'] = np.where(filtered.movimento.eq('CHEGADA'),filtered.aeroporto_adjacent_icao,'SBSV')
filtered['destino_fisico_icao'] = np.where(filtered.movimento.eq('PARTIDA'),filtered.aeroporto_adjacent_icao,'SBSV')
filtered['origem_fisica_iata'] = np.where(filtered.movimento.eq('CHEGADA'),filtered.aeroporto_adjacent_iata,'SSA')
filtered['destino_fisico_iata'] = np.where(filtered.movimento.eq('PARTIDA'),filtered.aeroporto_adjacent_iata,'SSA')

stage = filtered.groupby('chave_etapa_ssa',as_index=False).agg(
    periodo=('periodo','first'), data_referencia=('dt_referencia_parsed','first'),
    data_movimento_ssa=('data_movimento_ssa','first'),hora_movimento_ssa=('hora_movimento_ssa','first'),
    movimento=('movimento','first'), companhia_iata=('sg_empresa_iata','first'),companhia_nome=('nm_empresa','first'),
    voo_numero=('nr_voo','first'), categoria_operacional=('ds_grupo_di','first'),
    descricao_operacao=('ds_di','first'),indice_etapa_fisica_ssa=('indice_etapa_fisica_ssa','first'),
    origem_fisica_icao=('origem_fisica_icao','first'),destino_fisico_icao=('destino_fisico_icao','first'),
    origem_fisica_iata=('origem_fisica_iata','first'),destino_fisico_iata=('destino_fisico_iata','first'),
    aeroporto_adjacent_nome=('aeroporto_adjacent_nome','first'),
    passageiros_pagantes_movimento=('nr_passag_pagos','sum'),passageiros_gratuitos_movimento=('nr_passag_gratis','sum'),
    passageiros_total_movimento=('passageiros_total','sum'),
    passageiros_od_com_escala=('passageiros_total', lambda z:0),
    registros_od=('chave_etapa_ssa','size'))
passengers_through=filtered[~filtered.par_direto].groupby('chave_etapa_ssa').passageiros_total.sum()
stage['passageiros_od_com_escala'] = stage.chave_etapa_ssa.map(passengers_through).fillna(0).astype(int)
stage['passageiros_od_direto'] = stage.passageiros_total_movimento-stage.passageiros_od_com_escala
stage['tipo_fonte'] = 'etapa_fisica_ssa_reconstruida_de_etapas_combinadas'
stage['movimento_sem_passageiro_reportado'] = stage.passageiros_total_movimento.eq(0)
stage['iata_aeroporto_adjacente_ausente']=np.where(stage.movimento.eq('CHEGADA'),stage.origem_fisica_iata.eq('...'),stage.destino_fisico_iata.eq('...'))
stage['outra_ponta_icao'] = np.where(stage.movimento.eq('CHEGADA'),stage.origem_fisica_icao,stage.destino_fisico_icao)
stage['outra_ponta_iata'] = np.where(stage.movimento.eq('CHEGADA'),stage.origem_fisica_iata,stage.destino_fisico_iata)
stage['ligacao_com_pax']=stage.passageiros_total_movimento.gt(0)
assert stage.passageiros_total_movimento.sum()==filtered.passageiros_total.sum(),'Totais de passageiros não reconciliam.'
assert stage.groupby('periodo').passageiros_total_movimento.sum().equals(filtered.groupby('periodo').passageiros_total.sum())
assert stage.duplicated('chave_etapa_ssa').sum()==0

# Rotas reais em SSA; escala adjacente, não OD original dos passageiros.
route = stage.groupby(['periodo','origem_fisica_icao','destino_fisico_icao','origem_fisica_iata','destino_fisico_iata'],dropna=False).agg(
    etapas_fisicas=('chave_etapa_ssa','size'),etapas_com_pax=('ligacao_com_pax','sum'),
    passageiros_embarcados_ou_desembarcados_ssa=('passageiros_total_movimento','sum'),
    pax_reportados_od_com_escala=('passageiros_od_com_escala','sum'),
    etapas_regulares=('categoria_operacional',lambda z:int((z=='REGULAR').sum())),
    etapas_nao_regulares=('categoria_operacional',lambda z:int((z=='NÃO REGULAR').sum())),
    cias=('companhia_iata',lambda z:', '.join(sorted(set(z))))
).reset_index().sort_values(['periodo','passageiros_embarcados_ou_desembarcados_ssa'],ascending=[True,False])

profile = pd.DataFrame([{'campo':c,'linhas_nulas':int(raw[c].isna().sum()),'percentual_nulo':round(raw[c].isna().mean()*100,2),'valores_distintos':int(raw[c].nunique(dropna=True))} for c in source_columns])
# Sumários de primeira grandeza e comparabilidade por semana.
results=[]
for selected_period in ('outubro_2025','fevereiro_2026'):
    r=selected[selected.periodo_real.eq(selected_period)]
    f=filtered[filtered.periodo.eq(selected_period)]
    st=stage[stage.periodo.eq(selected_period)]
    rref=selected_all[selected_all.periodo_referencia.eq(selected_period)]
    exact=int(r.duplicated(subset=source_columns).sum())
    active=st[st.ligacao_com_pax]
    results.append({
        'periodo':selected_period,'datas_movimentacao_real':'20–26/10/2025' if selected_period=='outubro_2025' else '12–18/02/2026',
        'registros_filtrados_originais':len(r),'duplicados_exatos_removidos':int((r.duplicated(subset=source_columns)&r.passageiros_total.eq(0)).sum()),
        'duplicados_exatos_positivos_preservados':int((r.duplicated(subset=source_columns)&r.passageiros_total.gt(0)).sum()),
        'registros_od_higienizados':len(f),'etapas_fisicas_reconstruidas':len(st),
        'etapas_chegadas':int(st.movimento.eq('CHEGADA').sum()),'etapas_partidas':int(st.movimento.eq('PARTIDA').sum()),
        'etapas_sem_pax':int(st.movimento_sem_passageiro_reportado.sum()),
        'etapas_regulares':int(st.categoria_operacional.eq('REGULAR').sum()),
        'etapas_nao_regulares':int(st.categoria_operacional.eq('NÃO REGULAR').sum()),
        'passageiros_total':int(st.passageiros_total_movimento.sum()),
        'passageiros_chegadas':int(st.loc[st.movimento.eq('CHEGADA'),'passageiros_total_movimento'].sum()),
        'passageiros_partidas':int(st.loc[st.movimento.eq('PARTIDA'),'passageiros_total_movimento'].sum()),
        'passageiros_regulares':int(st.loc[st.categoria_operacional.eq('REGULAR'),'passageiros_total_movimento'].sum()),
        'passageiros_nao_regulares':int(st.loc[st.categoria_operacional.eq('NÃO REGULAR'),'passageiros_total_movimento'].sum()),
        'passageiros_od_com_escala':int(st.passageiros_od_com_escala.sum()),
        'aeroportos_adjacentes_com_pax':int(active.outra_ponta_icao.nunique()),
        'aeroportos_adjacentes_todos':int(st.outra_ponta_icao.nunique()),
        'arestas_dirigidas_com_pax':int(active.groupby(['origem_fisica_icao','destino_fisico_icao']).ngroups),
        'arestas_dirigidas_todas':int(st.groupby(['origem_fisica_icao','destino_fisico_icao']).ngroups),
        'etapas_icao_SSCE':int(st.outra_ponta_icao.eq('SSCE').sum()),
        'registros_sem_pax':int(f.passageiros_total.eq(0).sum()),
        'passageiros_recorte_data_referencia':int(rref.passageiros_total.sum()),
        'etapas_recorte_data_referencia':int((rref.sg_empresa_iata.astype(str)+'|'+rref.nr_voo.astype(str)+'|'+rref.dt_referencia_parsed.dt.strftime('%Y-%m-%d')+'|'+rref.movimento+'|'+rref.instante_movimento_ssa+'|'+np.where(rref.movimento.eq('CHEGADA'),rref.nr_escala_destino,rref.nr_etapa).astype(str)).nunique())
    })
summary=pd.DataFrame(results)
summary['crescimento_versus_controle_pax_%'] = (summary.passageiros_total / summary.passageiros_total.iloc[0]-1)*100
summary['crescimento_versus_controle_etapas_%'] = (summary.etapas_fisicas_reconstruidas / summary.etapas_fisicas_reconstruidas.iloc[0]-1)*100

# Auditoria por motivo de exclusão na comparação semanal, com universo inicial de datas efetivas.
week_raw=raw[raw.periodo_real.ne('fora')].copy()
def reason(row):
    if not ((row.sg_iata_origem=='SSA') ^ (row.sg_iata_destino=='SSA')):
        return 'SSA_em_ambas_as_pontas_ou_ausente'
    if row.nm_pais_origem!='BRASIL' or row.nm_pais_destino!='BRASIL':
        return 'internacional'
    if row.ds_servico_tipo_linha!='PASSAGEIRO':
        return 'servico_nao_passageiro'
    if row.ds_grupo_di not in ('REGULAR','NÃO REGULAR'):
        return 'operacao_improdutiva'
    if row.sg_empresa_iata=='TP':
        return 'TAP_excluida'
    return 'incluido'
week_raw['motivo_exclusao']=week_raw.apply(reason,axis=1)
audit=week_raw.groupby(['periodo_real','motivo_exclusao'],dropna=False).agg(registros=('sg_empresa_iata','size'),pax_registrados=('passageiros_total','sum')).reset_index()
# This is not a cut of entire months; only real days 20-26 Oct /12-18 Feb.

# Stage-level illustrative example, one known flight; preserve the lineage to help methodological review.
example=filtered[(filtered.sg_empresa_iata=='AD')&(filtered.nr_voo==4330)&(filtered.dt_referencia_parsed.eq('2025-10-22'))][['sg_empresa_iata','nr_voo','dt_referencia','movimento','sg_iata_origem','sg_iata_destino','nr_etapa','nr_escala_destino','par_direto','passageiros_total','origem_fisica_iata','destino_fisico_iata','chave_etapa_ssa']].copy()

# CSV output has no artificially inferred capacity or occupancy.
filtered_date_cols = ['periodo','data_movimento_ssa','chave_etapa_ssa','par_direto','passageiro_via_escala','aeroporto_adjacent_icao','aeroporto_adjacent_iata','origem_fisica_icao','destino_fisico_icao','passageiros_total']
reg_cols = source_columns + [c for c in filtered_date_cols if c not in source_columns]
filtered[reg_cols].sort_values(['data_movimento_ssa','sg_empresa_iata','nr_voo','movimento']).to_csv(OUT/'01_registros_od_higienizados.csv',index=False,encoding='utf-8-sig',date_format='%Y-%m-%d')
stage.sort_values(['periodo','data_movimento_ssa','hora_movimento_ssa','movimento']).to_csv(OUT/'02_etapas_fisicas_reconstruidas.csv',index=False,encoding='utf-8-sig',date_format='%Y-%m-%d')
route.to_csv(OUT/'03_rotas_diretas_agrupadas.csv',index=False,encoding='utf-8-sig')
summary.to_csv(OUT/'04_resumo_comparativo_e_sensibilidade.csv',index=False,encoding='utf-8-sig')
audit.to_csv(OUT/'05_auditoria_filtros.csv',index=False,encoding='utf-8-sig')
profile.to_csv(OUT/'06_perfil_completude_dos_campos.csv',index=False,encoding='utf-8-sig')
example.to_csv(OUT/'07_exemplo_trajeto_com_escala.csv',index=False,encoding='utf-8-sig')
duplicated_positive.to_csv(OUT/'08_alertas_duplicados_com_pax.csv',index=False,encoding='utf-8-sig')

# Externalized checks for reproducibility
validations={
 'arquivo_original':str(SRC),
 'n_linhas_originais':len(raw),'n_colunas_originais':len(source_columns),
 'total_registros_validos_semanas_reais':len(selected),
 'duplicados_exatos_removidos':len(duplicated),
 'duplicados_exatos_positivos_preservados':len(duplicated_positive),
 'etapas_sem_registro_direto':len(set(filtered.chave_etapa_ssa)-set(adjacent.chave_etapa_ssa)),
 'etapas_com_aeroportos_adjacentes_conflitantes':int((per_key_neighbor>1).sum()),
 'etapas_com_naturezas_divergentes':int((per_key_nature>1).sum()),
 'registros_sem_par_adjacente':int(filtered.aeroporto_adjacent_icao.isna().sum()),
 'colunas_100pct_vazias':profile.loc[profile.percentual_nulo==100,'campo'].to_list(),
 'soma_pax_od_igual_soma_etapas':int(filtered.passageiros_total.sum())==int(stage.passageiros_total_movimento.sum()),
 'soma_movimentos_reconciliada':int(stage.passageiros_total_movimento.sum()),
 'aviso_unidade': 'Uma etapa fisica reconstruida agrega varias linhas de passageiros origem/destino. Pax indicam embarques ou desembarques em SSA, nao pessoas unicas.',
 'aviso_duplicados_positivos': 'Duplicidades exatas com pax >0 permanecem no resultado por nao haver comprovacao se sao erro de extracao ou linhas de COTRAN/segmentos distintos. Ha sensibilidade de 1 passageiro na semana de outubro por data real.',
 'aviso_chave': 'Chave operacional reconstruida a partir da empresa, numero voo, data referencia, sentido, horario real SSA e sequencia de escala. Nao ha identificador unico nativo de aeronave/etapa no CSV.',
 'aviso_fonte': 'Confirmar a correspondencia dos campos de sequencia com dicionario de origem e validar, se necessario, com microdados de etapas basicas da ANAC.'
}
(OUT/'verificacoes_automaticas.json').write_text(json.dumps(validations,ensure_ascii=False,indent=2),encoding='utf-8')
print(summary.to_string(index=False))
print('\nAUDIT:',audit.to_string(index=False))
print('\nTESTES:',json.dumps(validations,indent=2,ensure_ascii=False))
print('\nEXEMPLO:',example.to_string(index=False))

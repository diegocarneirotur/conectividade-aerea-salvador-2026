#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Etapa 2 do estudo SSA: indicadores e grafos direcionados de etapas fisicas.

Entrada: /mnt/data/etapa1_validacao_ssa/02_etapas_fisicas_reconstruidas.csv
Uso: python reproduzir_etapa2_ssa.py [diretorio_da_etapa_1] [diretorio_de_saida]
Dependencias: pandas, numpy, matplotlib. Nao modifica o CSV original.
"""
from pathlib import Path
import sys
import math
import itertools
import zipfile
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.lines import Line2D

BASE=Path(sys.argv[1] if len(sys.argv)>1 else '/mnt/data/etapa1_validacao_ssa')
OUT=Path(sys.argv[2] if len(sys.argv)>2 else '/mnt/data/etapa2_grafos_ssa')
OUT.mkdir(parents=True,exist_ok=True)
raw=pd.read_csv(BASE/'02_etapas_fisicas_reconstruidas.csv',encoding='utf-8-sig', low_memory=False)
raw['data_movimento_ssa']=pd.to_datetime(raw.data_movimento_ssa)
raw['pax']=pd.to_numeric(raw.passageiros_total_movimento)
raw['dia_semana']=raw.data_movimento_ssa.dt.weekday
assert len(raw)==2160 and raw.chave_etapa_ssa.is_unique
assert set(raw.periodo)=={'outubro_2025','fevereiro_2026'}
assert raw.companhia_iata.ne('TP').all()
assert raw.movimento.isin(['CHEGADA','PARTIDA']).all()
assert (raw.pax >= 0).all()
assert (raw.data_movimento_ssa.between('2025-10-20','2025-10-26') | raw.data_movimento_ssa.between('2026-02-12','2026-02-18')).all()

months=['outubro_2025','fevereiro_2026']
labels={'outubro_2025':'20 a 26 de outubro de 2025','fevereiro_2026':'12 a 18 de fevereiro de 2026'}
short={'outubro_2025':'Outubro / 2025','fevereiro_2026':'Fevereiro / 2026'}
COLORS={'navy':'#183247','blue':'#2c567a','teal':'#178a84','gray':'#758794','gold':'#bb8b45','pink':'#cf1e64','paper':'#ffffff','light':'#e7eef2','ghost':'#d9e2e8'}
plt.rcParams.update({'font.family':'DejaVu Sans','figure.facecolor':'white','savefig.facecolor':'white','svg.fonttype':'none',
                    'text.color':COLORS['navy'],'axes.labelcolor':COLORS['navy'],'xtick.color':COLORS['navy'],'ytick.color':COLORS['navy']})

def num(x):return f'{int(round(x)):,}'.replace(',','.')
def pct(x,n=1):return f'{x:.{n}f}'.replace('.',',')+'%'

def assoc_codes(d):return set(d.loc[d.pax.gt(0),'outra_ponta_icao'])

def airport_shares(d):
    z=d.groupby('outra_ponta_iata',dropna=False).pax.sum().loc[lambda x:x.gt(0)].sort_values(ascending=False)
    return z/z.sum()

def concentration(d):
    share=airport_shares(d)
    return {'hhi':float((share**2).sum()), 'shannon_effective_airports':float(np.exp(-(share*np.log(share)).sum()))}

# Operacoes por aresta fisica direcional. Identificar arestas com >0 passageiros.
edges=raw.groupby(['periodo','origem_fisica_icao','destino_fisico_icao','origem_fisica_iata','destino_fisico_iata'],dropna=False).agg(
    etapas=('chave_etapa_ssa','size'),passageiros_ssa=('pax','sum'),
    etapas_regulares=('categoria_operacional',lambda z: int(z.eq('REGULAR').sum())),
    etapas_nao_regulares=('categoria_operacional',lambda z: int(z.eq('NÃO REGULAR').sum())),
    etapas_latam=('companhia_iata',lambda z: int(z.eq('JJ').sum())),
    passageiros_latam=('pax',lambda z: int(z.loc[raw.loc[z.index,'companhia_iata'].eq('JJ')].sum())),
    cias=('companhia_iata',lambda z: ', '.join(sorted(set(z))))
).reset_index()
edges['origem']=edges.origem_fisica_iata
edges['destino']=edges.destino_fisica_iata if 'destino_fisica_iata' in edges else edges.destino_fisico_iata
edges['direcao']=np.where(edges.destino.eq('SSA'),'Chegadas a SSA','Partidas de SSA')
edges['aeroporto_conectado']=np.where(edges.destino.eq('SSA'),edges.origem,edges.destino)
edges['ligacao_com_passageiros']=edges.passageiros_ssa.gt(0)
edges.to_csv(OUT/'01_arestas_direcionadas.csv',index=False,encoding='utf-8-sig')

# Matriz por aeroporto, com mesmos codigos dos dois periodos.
air=raw.groupby(['periodo','outra_ponta_icao','outra_ponta_iata','movimento'],dropna=False).agg(
    etapas=('chave_etapa_ssa','size'),passageiros=('pax','sum'),
    etapas_nao_regulares=('categoria_operacional',lambda z:int(z.eq('NÃO REGULAR').sum())),
    etapas_latam=('companhia_iata',lambda z:int(z.eq('JJ').sum()))
).reset_index()
wide=air.pivot_table(index=['outra_ponta_icao','outra_ponta_iata'],columns=['periodo','movimento'],values=['etapas','passageiros','etapas_nao_regulares','etapas_latam'],aggfunc='sum',fill_value=0)
wide.columns=['__'.join(str(x) for x in c) for c in wide.columns]
wide=wide.reset_index()
for month in months:
    for typ in ('etapas','passageiros','etapas_nao_regulares','etapas_latam'):
        for movement in ('CHEGADA','PARTIDA'):
            col=f'{typ}__{month}__{movement}'
            if col not in wide: wide[col]=0
        wide[f'{typ}__{month}__total']=wide[f'{typ}__{month}__CHEGADA']+wide[f'{typ}__{month}__PARTIDA']
wide['delta_etapas']=wide.etapas__fevereiro_2026__total-wide.etapas__outubro_2025__total
wide['delta_passageiros']=wide.passageiros__fevereiro_2026__total-wide.passageiros__outubro_2025__total
wide['status_rede_passageiros']=np.select([
    (wide.passageiros__outubro_2025__total.eq(0)&wide.passageiros__fevereiro_2026__total.gt(0)),
    (wide.passageiros__outubro_2025__total.gt(0)&wide.passageiros__fevereiro_2026__total.eq(0)),
    (wide.passageiros__outubro_2025__total.gt(0)&wide.passageiros__fevereiro_2026__total.gt(0))
], ['nova','suprimida','mantida'],default='sem passageiro reportado')
wide=wide.sort_values('passageiros__fevereiro_2026__total',ascending=False)
wide.to_csv(OUT/'02_corredores_comparativos.csv',index=False,encoding='utf-8-sig')

# Sumarios populacionais para as 7 datas de cada periodo.
res=[]
central=['CGH','GRU','GIG','BSB','VCP']
for mo in months:
    d=raw[raw.periodo.eq(mo)].copy()
    byairport=d.groupby('outra_ponta_iata').pax.sum()
    active=d[d.pax.gt(0)]
    pairs=(active.groupby(['origem_fisica_icao','destino_fisico_icao']).ngroups)
    hi=concentration(d)
    res.append({'periodo':mo,'semana':labels[mo],
      'etapas_fisicas_total':len(d),'etapas_chegada':int(d.movimento.eq('CHEGADA').sum()),
      'etapas_partida':int(d.movimento.eq('PARTIDA').sum()),
      'etapas_regulares':int(d.categoria_operacional.eq('REGULAR').sum()),
      'etapas_nao_regulares':int(d.categoria_operacional.eq('NÃO REGULAR').sum()),
      'passageiros_ssa':int(d.pax.sum()),'pax_chegadas':int(d.loc[d.movimento.eq('CHEGADA'),'pax'].sum()),
      'pax_partidas':int(d.loc[d.movimento.eq('PARTIDA'),'pax'].sum()),
      'passageiros_regulares':int(d.loc[d.categoria_operacional.eq('REGULAR'),'pax'].sum()),
      'passageiros_nao_regulares':int(d.loc[d.categoria_operacional.eq('NÃO REGULAR'),'pax'].sum()),
      'etapas_latam':int(d.companhia_iata.eq('JJ').sum()),
      'passageiros_latam':int(d.loc[d.companhia_iata.eq('JJ'),'pax'].sum()),
      'aeroportos_com_passageiros':int(d.loc[d.pax.gt(0),'outra_ponta_icao'].nunique()),
      'arestas_direcionadas_com_passageiros':pairs,
      'etapas_sem_pax':int(d.pax.eq(0).sum()),
      'movimentos_para_SSCE_sem_pax':int(d.outra_ponta_icao.eq('SSCE').sum()),
      'concentracao_HHI_pax':hi['hhi'],
      'numero_efetivo_shannon':hi['shannon_effective_airports'],
      'cinco_corredores_pax':int(byairport.reindex(central,fill_value=0).sum()),
      'cinco_corredores_pct':float(byairport.reindex(central,fill_value=0).sum()/d.pax.sum()*100)
    })
summary=pd.DataFrame(res)
summary.to_csv(OUT/'03_indicadores_semanas.csv',index=False,encoding='utf-8-sig')

# Diferenca de ligacoes direcionadas com passageiros.
E={k:set(zip(edges.loc[edges.periodo.eq(k)&edges.ligacao_com_passageiros,'origem_fisica_icao'],
              edges.loc[edges.periodo.eq(k)&edges.ligacao_com_passageiros,'destino_fisico_icao'])) for k in months}
N={k:assoc_codes(raw[raw.periodo.eq(k)]) for k in months}
assert E[months[0]].issubset(E[months[1]])
assert (N[months[1]]-N[months[0]])=={'SBRJ','SBCY'}
assert len(E[months[0]])==54 and len(E[months[1]])==58
change=[]
for k in sorted(E[months[0]]|E[months[1]]):
    m0=edges[(edges.periodo.eq(months[0]))&(edges.origem_fisica_icao.eq(k[0]))&(edges.destino_fisico_icao.eq(k[1]))]
    m1=edges[(edges.periodo.eq(months[1]))&(edges.origem_fisica_icao.eq(k[0]))&(edges.destino_fisico_icao.eq(k[1]))]
    lo=int(m0.etapas.sum()); lf=int(m1.etapas.sum()); po=int(m0.passageiros_ssa.sum()); pf=int(m1.passageiros_ssa.sum())
    change.append({'origem_icao':k[0],'destino_icao':k[1],
      'origem_iata':m0.origem.iloc[0] if len(m0) else m1.origem.iloc[0],
      'destino_iata':m0.destino.iloc[0] if len(m0) else m1.destino.iloc[0],
      'etapas_out':lo,'etapas_fev':lf,'delta_etapas':lf-lo,
      'pax_out':po,'pax_fev':pf,'delta_pax':pf-po,
      'status':('mantida' if k in E[months[0]] and k in E[months[1]] else 'nova' if k in E[months[1]] else 'suprimida')})
diff=pd.DataFrame(change).sort_values(['status','delta_etapas'],ascending=[True,False])
diff.to_csv(OUT/'04_comparacao_arestas.csv',index=False,encoding='utf-8-sig')

# Observacoes por dia da semana para teste pareado apenas exploratorio.
days=(raw.groupby(['periodo','dia_semana']).agg(etapas=('chave_etapa_ssa','size'),pax=('pax','sum'),
      etapas_nao_regulares=('categoria_operacional',lambda z:int(z.eq('NÃO REGULAR').sum())),
      passageiros_nao_regulares=('pax',lambda z:int(z.loc[raw.loc[z.index,'categoria_operacional'].eq('NÃO REGULAR')].sum())))
      .reset_index().sort_values(['periodo','dia_semana']))
days['dia_nome']=days.dia_semana.map(dict(enumerate(['segunda','terca','quarta','quinta','sexta','sabado','domingo'])))
days.to_csv(OUT/'05_resumo_diario.csv',index=False,encoding='utf-8-sig')

# 7-weekday pairs, enumerating all 128 sign flips. Outcomes were defined before testing.
tests=[]
for col,description in [('etapas','Etapas fisicas (7 dias)'),('pax','Passageiros associados a SSA (7 dias)'),('etapas_nao_regulares','Etapas nao regulares (7 dias)')]:
    temp=days.pivot(index='dia_semana',columns='periodo',values=col)
    v=(temp[months[1]]-temp[months[0]]).to_numpy(dtype=float)
    obs=np.mean(v)
    null=np.array([np.mean(v*np.array(combination)) for combination in itertools.product((-1.0,1.0),repeat=len(v))])
    p2=float(np.mean(np.abs(null)>=abs(obs)-1e-12)); p1=float(np.mean(null>=obs-1e-12))
    tests.append({'indicador':col,'descricao':description,'diferenca_total':int(v.sum()),
       'diferenca_media_diaria':obs,'dias_positivos':int((v>0).sum()),'dias_negativos':int((v<0).sum()),
       'p_exato_bicaudal_exploratorio':p2,'p_exato_unicaudal_positivo':p1,'n_pares':7,
       'tipo_teste':'Permutacao exata de sinais com correspondencia por dia da semana'})
tests=pd.DataFrame(tests)
# Holm conservative familywise correction for 3 prespecified comparisons.
idx=np.argsort(tests.p_exato_bicaudal_exploratorio.to_numpy());pvals=tests.p_exato_bicaudal_exploratorio.to_numpy()
adj=np.empty(len(pvals));prev=0
for rank,i in enumerate(idx):
    prev=max(prev,min(1.0,(len(pvals)-rank)*pvals[i]));adj[i]=prev
tests['p_bicaudal_ajustado_Holm']=adj
tests.to_csv(OUT/'06_testes_exploratorios.csv',index=False,encoding='utf-8-sig')

# Color and position rules for graphic comparison.
active_airports={mo:sorted(raw.loc[raw.periodo.eq(mo)&raw.pax.gt(0),'outra_ponta_iata'].unique()) for mo in months}
union=sorted(set(active_airports[months[0]])|set(active_airports[months[1]]))
assert len(union)==29 and set(union)-set(active_airports[months[0]])=={'CGB','SDU'}
# Start at 12 o'clock and proceed clockwise: deterministic layout for all figures.
angle={a:np.pi/2-2*np.pi*i/len(union) for i,a in enumerate(union)}
position={a:(float(np.cos(angle[a])),float(np.sin(angle[a]))) for a in union}
# Reuse line width scaling for every period: global max per direction.
directional=raw.groupby(['periodo','outra_ponta_iata','movimento']).size().to_dict()
maxwidth=max(directional.values())

def graph(mo):
    d=raw.loc[raw.periodo.eq(mo)].copy()
    values=d.groupby(['outra_ponta_iata','movimento']).size().to_dict()
    latam=set(d.loc[d.companhia_iata.eq('JJ'),'outra_ponta_iata'])
    new=set(active_airports[months[1]])-set(active_airports[months[0]])
    present=set(active_airports[mo])
    fig=plt.figure(figsize=(13.4,12.9))
    ax=fig.add_axes([.06,.135,.88,.72])
    ax.set_xlim(-1.36,1.36);ax.set_ylim(-1.32,1.32);ax.set_aspect('equal');ax.axis('off')
    fig.text(.06,.955,f'Conectividade aérea direta de Salvador (SSA)',size=20,weight='bold',color=COLORS['navy'],ha='left',va='top')
    fig.text(.06,.918,labels[mo],size=15,color=COLORS['navy'],ha='left',va='top')
    s=summary.loc[summary.periodo.eq(mo)].iloc[0]
    fig.text(.06,.885,f"{int(s.aeroportos_com_passageiros)} aeroportos   •   {int(s.arestas_direcionadas_com_passageiros)} ligações direcionadas   •   {num(s.etapas_fisicas_total)} etapas físicas   •   {num(s.passageiros_ssa)} passageiros",size=11.5,color=COLORS['gray'],ha='left',va='top')
    # Quiet radial guides; these encode no geography, just an equal-space layout.
    ax.add_patch(Circle((0,0),1.0,fill=False,ec=COLORS['ghost'],lw=.75,ls='--',alpha=.7,zorder=0))
    for code in union:
        if code not in present:continue
        x,y=position[code]
        for movement, base,color in [('CHEGADA','inbound',COLORS['blue']),('PARTIDA','outbound',COLORS['teal'])]:
            n=values.get((code,movement),0)
            if not n:continue
            lw=.65+4.3*np.sqrt(n/maxwidth)
            if movement=='CHEGADA':
                a=(.925*x,.925*y); b=(.20*x,.20*y)
            else:
                a=(.20*x,.20*y); b=(.925*x,.925*y)
            # Curvature sign relative to arrow direction; same rad separates two orientations.
            arrow=FancyArrowPatch(a,b,arrowstyle='-|>',connectionstyle='arc3,rad=.13',
                                  mutation_scale=8.8+0.45*lw,linewidth=lw,color=color,alpha=.77,
                                  capstyle='round',joinstyle='round',zorder=2)
            ax.add_patch(arrow)
    # Central node.
    ax.add_patch(Circle((0,0),.153,fc=COLORS['navy'],ec='white',lw=3.0,zorder=8))
    ax.text(0,.02,'SSA',size=17,weight='bold',color='white',ha='center',va='center',zorder=9)
    ax.text(0,-.048,'Salvador',size=8.2,color='white',ha='center',va='center',zorder=9)
    # Airports ring. Keep nodes with no positive-pax link visible as gray references.
    for code in union:
        x,y=position[code]
        is_present=code in present
        is_new=code in new and is_present
        fg=(COLORS['pink'] if code in latam and is_present else COLORS['gold'] if is_new else COLORS['navy'] if is_present else COLORS['ghost'])
        bg=('white' if is_present else '#f1f4f5')
        ax.add_patch(Circle((x,y),.034,fc=bg,ec=fg,lw=2.4 if (is_new or code in latam) else 1.7,zorder=6))
        tx,ty=(x*1.065,y*1.065)
        h='left' if tx>=.05 else ('right' if tx<=-.05 else 'center')
        ax.text(tx,ty,code,fontsize=9.7 if is_present else 8.6,weight='bold' if is_present else 'normal',
                ha=h,va='center',color=fg,zorder=9)
        if is_new:
            ax.text(tx,ty-.058,'nova',fontsize=7.3,ha=h,color=COLORS['gold'],va='center')
    # Legend and notes outside plotting region.
    itemsy=.107
    fig.text(.065,itemsy,'Chegadas a SSA',weight='bold',color=COLORS['blue'],size=10.2)
    fig.text(.245,itemsy,'Partidas de SSA',weight='bold',color=COLORS['teal'],size=10.2)
    fig.text(.425,itemsy,'Contorno rosa = LATAM',weight='medium',color=COLORS['pink'],size=10.2)
    fig.text(.68,itemsy,'Espessura ∝ etapas',color=COLORS['gray'],size=10.2)
    fig.text(.065,.077,'Os sentidos são representados por duas setas; a escala de espessura é igual nos dois períodos.',size=9.1,color=COLORS['gray'])
    note=('Nódulos CGB e SDU, em cinza, não registraram passageiros nesta semana.' if mo==months[0] else
          'CGB e SDU são novas ligações com passageiros. Duas etapas para SSCE, sem passageiros, foram omitidas do grafo.')
    fig.text(.065,.056,note,size=9.2,color=COLORS['gray'])
    fig.text(.065,.034,'Fonte: ssa.csv; reconstrução de etapas físicas em SSA. Grafo focal, não representa a malha nacional completa.',size=8.5,color=COLORS['gray'])
    basename='grafo_direcionado_SSA_'+('outubro_2025' if mo==months[0] else 'fevereiro_2026')
    for ext in ('png','svg'):
        fig.savefig(OUT/(basename+'.'+ext),dpi=245,bbox_inches='tight',pad_inches=.22)
    plt.close(fig)

for mo in months:graph(mo)

# Comparative plate with identical framing, useful for reviewing both weeks side by side.
from PIL import Image, ImageDraw
images=[]
for mo in months:
    fname=OUT/('grafo_direcionado_SSA_'+('outubro_2025' if mo==months[0] else 'fevereiro_2026')+'.png')
    im=Image.open(fname).convert('RGB')
    factor=1550/im.width
    im=im.resize((1550,round(im.height*factor)),Image.Resampling.LANCZOS)
    images.append(im)
canvas=Image.new('RGB',(3160,max(im.height for im in images)+40),'white')
canvas.paste(images[0],(20,20))
canvas.paste(images[1],(1590,20))
canvas.save(OUT/'comparacao_grafos_lado_a_lado.png',optimize=True)

# Visually compare changes: same data, categories, and units. Rank by stages movement.
comp=wide[~wide.outra_ponta_iata.eq('...')].copy()
comp['abs_change']=comp.delta_etapas.abs()
chartdf=comp.sort_values('abs_change',ascending=False).head(14).sort_values('delta_etapas')
fig,ax=plt.subplots(figsize=(11.7,8.7));fig.subplots_adjust(left=.17,right=.89,top=.855,bottom=.16)
y=np.arange(len(chartdf))
barcolors=[COLORS['teal'] if v>=0 else COLORS['blue'] for v in chartdf.delta_etapas]
ax.barh(y,chartdf.delta_etapas,color=barcolors,height=.63)
ax.set_yticks(y,labels=chartdf.outra_ponta_iata,fontsize=11,weight='bold')
ax.axvline(0,color=COLORS['navy'],lw=1)
ax.set_xlim(min(-12,chartdf.delta_etapas.min()-7),chartdf.delta_etapas.max()+9)
ax.grid(axis='x',alpha=.18,zorder=0);ax.set_axisbelow(True)
for i,v in enumerate(chartdf.delta_etapas):
    ax.text(v+(.8 if v>=0 else -.8),i,f'{v:+d}',ha='left' if v>=0 else 'right',va='center',color=COLORS['navy'],size=10,weight='bold')
ax.set_xlabel('Variação no número de etapas físicas (fevereiro − outubro)',fontsize=11)
for spine in ax.spines.values():spine.set_visible(False)
fig.text(.06,.948,'Mudança na frequência de operações por corredor',fontsize=18,weight='bold')
fig.text(.06,.909,'Maiores variações absolutas entre os dois períodos — rotas com Salvador',fontsize=11.5,color=COLORS['gray'])
fig.text(.06,.071,'Corredores que surgiram: SDU (+10 etapas) e CGB (+4), ambos com chegadas e partidas.',fontsize=10,color=COLORS['navy'])
fig.text(.06,.048,'Fonte: ssa.csv; contagens por aeroporto adjacente. Valores incluindo operações com zero passageiros.',fontsize=9.2,color=COLORS['gray'])
for ext in ('png','svg'):fig.savefig(OUT/('variacao_etapas_por_aeroporto.'+ext),dpi=240,bbox_inches='tight',pad_inches=.17)
plt.close(fig)

# Two-period comparison chart: direct line count and dispersion share, accessible as separate files.
fig,ax=plt.subplots(figsize=(9.2,6.2));fig.subplots_adjust(left=.16,right=.96,top=.78,bottom=.2)
xx=np.arange(2)
series=summary.cinco_corredores_pct.values
ax.bar(xx,series,color=COLORS['blue'],width=.42)
ax.set_ylim(0,100)
ax.set_yticks([0,20,40,60,80,100]);ax.set_yticklabels([f'{k}%' for k in [0,20,40,60,80,100]])
ax.set_xticks(xx,labels=['20–26/out/2025','12–18/fev/2026'],fontsize=11)
ax.set_ylabel('Participação dos cinco corredores no total de passageiros (%)',fontsize=10.5)
ax.grid(axis='y',alpha=.17);ax.set_axisbelow(True)
for i,v in enumerate(series):ax.text(i,v+2.5,pct(v,2),ha='center',va='bottom',fontsize=13,weight='bold')
for spine in ax.spines.values():spine.set_visible(False)
fig.text(.06,.955,'Concentração de passageiros nos principais corredores',size=16.5,weight='bold')
fig.text(.06,.907,'CGH, GRU, GIG, BSB e VCP — os cinco maiores no período de controle',size=10.5,color=COLORS['gray'])
fig.text(.06,.07,'Unidade: registros de passageiros embarcados ou desembarcados em SSA, não turistas individuais.',fontsize=8.9,color=COLORS['gray'])
for ext in ('png','svg'):fig.savefig(OUT/('concentracao_cinco_corredores.'+ext),dpi=230,bbox_inches='tight',pad_inches=.15)
plt.close(fig)

# Data assertions and diagnostics after all transformations.
assert summary.etapas_fisicas_total.tolist()==[993,1167],summary.etapas_fisicas_total.to_list()
assert summary.passageiros_ssa.tolist()==[149367,164628]
assert summary.aeroportos_com_passageiros.tolist()==[27,29]
assert summary.arestas_direcionadas_com_passageiros.tolist()==[54,58]
assert summary.etapas_nao_regulares.tolist()==[24,86]
assert summary.passageiros_nao_regulares.tolist()==[2221,10907]
assert wide.loc[wide.outra_ponta_iata.eq('CGB'),'etapas__fevereiro_2026__total'].iat[0]==4
assert wide.loc[wide.outra_ponta_iata.eq('SDU'),'etapas__fevereiro_2026__total'].iat[0]==10
assert edges.loc[edges.periodo.eq(months[1])&edges.ligacao_com_passageiros,'etapas'].sum()==1165

s0,s1=summary.iloc[0],summary.iloc[1]
assert (s1.etapas_fisicas_total-s0.etapas_fisicas_total)==174
assert (s1.passageiros_ssa-s0.passageiros_ssa)==15261
assert np.isclose(s0.concentracao_HHI_pax,.115536987310684)
assert np.isclose(s1.concentracao_HHI_pax,.12035287279162354)
assert 0 <= min(tests.p_exato_bicaudal_exploratorio) <= 1

check={
    'periodos':labels,
    'etapas_fisicas':[int(x) for x in summary.etapas_fisicas_total],
    'passageiros_ssa':[int(x) for x in summary.passageiros_ssa],
    'aeroportos_com_pax':[int(x) for x in summary.aeroportos_com_passageiros],
    'arestas_com_pax':[int(x) for x in summary.arestas_direcionadas_com_passageiros],
    'arestas_comuns':int(len(E[months[0]]&E[months[1]])),
    'arestas_novas':sorted([str(x) for x in E[months[1]]-E[months[0]]]),
    'arestas_retiradas':sorted([str(x) for x in E[months[0]]-E[months[1]]]),
    'jaccard_direcionadas_ativas':float(len(E[months[0]]&E[months[1]])/len(E[months[0]]|E[months[1]])),
    'pax_cinco_corredores':[int(x) for x in summary.cinco_corredores_pax],
    'concentracao_cinco_pct':[float(x) for x in summary.cinco_corredores_pct],
    'concentracao_hhi':[float(x) for x in summary.concentracao_HHI_pax],
    'etapas_sem_pax':[int(x) for x in summary.etapas_sem_pax],
    'SSCE_nao_contribui_a_rede_pax':int(raw.query("periodo=='fevereiro_2026' and outra_ponta_icao=='SSCE'").pax.sum())==0,
    'latam_incluida': int(raw.companhia_iata.eq('JJ').sum())>0,
    'tap_excluida': bool(raw.companhia_iata.ne('TP').all()),
    'avisos':['Unidade: movimentos fisicos reconstruidos com chave inferida em SSA; validar com etapas basicas oficiais.',
              'Pesos de passageiros correspondem ao embarque ou desembarque em SSA, nao a ocupacao total no trecho.',
              'A topologia focal gera valores triviais para intermediação/proximidade global; nao computar.',
              'Testes estatisticos sao exploratorios, com 7 dias por periodo, sem identificacao causal.',
              'Dados somente de operacoes associadas a SSA; nao ha outras arestas nacionais.']
}
(OUT/'verificacao_etapa2.json').write_text(json.dumps(check,indent=2,ensure_ascii=False),encoding='utf-8')

# Narrative technical memo for use in the manuscript, including hypothesis results.
change_pax=(s1.passageiros_ssa/s0.passageiros_ssa-1)*100
change_etapas=(s1.etapas_fisicas_total/s0.etapas_fisicas_total-1)*100
hhi_change=s1.concentracao_HHI_pax-s0.concentracao_HHI_pax
share_pp=s1.cinco_corredores_pct-s0.cinco_corredores_pct
newp=wide[wide.status_rede_passageiros.eq('nova')][['outra_ponta_iata','etapas__fevereiro_2026__total','passageiros__fevereiro_2026__total']]
pf=tests.set_index('indicador')
text=f'''# Etapa 2 — Modelagem de grafos direcionados e reexame da hipótese

## 1. Escopo e proveniência

A comparação utiliza `ssa.csv`, com reconstrução em `etapa1_validacao_ssa/02_etapas_fisicas_reconstruidas.csv`. Semanas de movimentos reais em Salvador: **{labels[months[0]]}** e **{labels[months[1]]}**. Companhias domésticas de passageiros incluídas, entre elas LATAM/TAM (`JJ`); TAP (`TP`) excluída. `NÃO REGULAR` vem de `ds_grupo_di`, e não de `ds_tipo_empresa`. A unidade de voos físicos é a **etapa real de chegada ou saída de SSA**, reconstruída por chave composta (não identificador operacional nativo). Contagens ainda dependem de confrontação externa com etapas básicas da ANAC.

O indicador de passageiros é a soma dos embarques e desembarques reportados em SSA associados aos movimentos; os totais não equivalem a turistas únicos nem à lotação física das aeronaves.

## 2. Resultados comparativos

| Indicador | Outubro 2025 | Fevereiro 2026 | Diferença |
|---|---:|---:|---:|
| Etapas físicas reconstruídas | {num(s0.etapas_fisicas_total)} | {num(s1.etapas_fisicas_total)} | +{num(s1.etapas_fisicas_total-s0.etapas_fisicas_total)} ({pct(change_etapas)}) |
| Movimentos com passageiros associados a SSA | {num(s0.passageiros_ssa)} | {num(s1.passageiros_ssa)} | +{num(s1.passageiros_ssa-s0.passageiros_ssa)} ({pct(change_pax)}) |
| Aeroportos diretos com passageiros | {num(s0.aeroportos_com_passageiros)} | {num(s1.aeroportos_com_passageiros)} | +2 |
| Arestas direcionadas com passageiros | {num(s0.arestas_direcionadas_com_passageiros)} | {num(s1.arestas_direcionadas_com_passageiros)} | +4 |
| Etapas regulares | {num(s0.etapas_regulares)} | {num(s1.etapas_regulares)} | +{num(s1.etapas_regulares-s0.etapas_regulares)} |
| Etapas não regulares | {num(s0.etapas_nao_regulares)} | {num(s1.etapas_nao_regulares)} | +{num(s1.etapas_nao_regulares-s0.etapas_nao_regulares)} |
| Passageiros em operações não regulares | {num(s0.passageiros_nao_regulares)} | {num(s1.passageiros_nao_regulares)} | +{num(s1.passageiros_nao_regulares-s0.passageiros_nao_regulares)} |
| Etapas LATAM/TAM (`JJ`) | {num(s0.etapas_latam)} | {num(s1.etapas_latam)} | +{num(s1.etapas_latam-s0.etapas_latam)} |
| Passageiros LATAM/TAM (`JJ`) | {num(s0.passageiros_latam)} | {num(s1.passageiros_latam)} | +{num(s1.passageiros_latam-s0.passageiros_latam)} |

## 3. Mudança nas arestas e componentes do crescimento

- **Retidas:** 54 de 54 arestas direcionadas com passageiros presentes em outubro permanecem em fevereiro.
- **Adicionadas:** quatro arestas direcionadas correspondentes aos pares de ida e volta com **Santos Dumont (SDU/SBRJ)** e **Cuiabá (CGB/SBCY)**.
- **Removidas:** nenhuma aresta dirigida com passageiro positivo no período de controle.
- Similaridade de Jaccard entre conjuntos de arestas dirigidas: {pct(100*len(E[months[0]]&E[months[1]])/len(E[months[0]]|E[months[1]]),2)}.
- **SDU:** 10 etapas e 1.237 movimentos de passageiros; categoria `REGULAR`.
- **CGB:** quatro etapas e 504 movimentos de passageiros; categoria `NÃO REGULAR`.
- Novos corredores responderam por apenas 14 de 174 etapas adicionais e 1.741 dos 15.261 movimentos de passageiros adicionais. A maior parte do crescimento ocorreu em corredores previamente existentes. Duas etapas de fevereiro para SSCE, sem passageiros, são mantidas no universo operacional, mas não representadas no grafo de ligações com passageiros.

## 4. Concentração e hipótese de desconcentração

Os cinco maiores aeroportos do período controle foram CGH, GRU, GIG, BSB e VCP. Sua participação conjunta subiu de **{pct(s0.cinco_corredores_pct,2)}** para **{pct(s1.cinco_corredores_pct,2)}**, variação de **{share_pp:+.2f} p.p.** O HHI por aeroporto adjacente, ponderado pelos movimentos de passageiros, aumentou de **{s0.concentracao_HHI_pax:.5f}** para **{s1.concentracao_HHI_pax:.5f}** (variação {hhi_change:+.5f}). A ampliação da capilaridade não correspondeu a desconcentração de passageiros; na medida disponível, observou-se o contrário.

Os cinco corredores respondem por {num(s1.cinco_corredores_pax-s0.cinco_corredores_pax)} dos {num(s1.passageiros_ssa-s0.passageiros_ssa)} passageiros adicionais ({pct(100*(s1.cinco_corredores_pax-s0.cinco_corredores_pax)/(s1.passageiros_ssa-s0.passageiros_ssa),1)} do saldo líquido). Isso indica intensificação de corredores existentes, não a transferência comprovada de passageiros entre hubs.

## 5. Teste exploratório de diferenças diárias

Foram comparados 7 pares por dia da semana (segunda com segunda, etc.), enumerando todas as 128 possibilidades de inversão de sinais; teste **bicaudal**, com ajuste **Holm** para três desfechos principais. Esse procedimento **não estabelece causalidade** e possui poder estatístico reduzido em apenas 7 dias por período.

| Indicador | Valor-p bicaudal exato | Valor-p ajustado Holm |
|---|---:|---:|
| Etapas físicas/dia | {pf.loc['etapas','p_exato_bicaudal_exploratorio']:.5f} | {pf.loc['etapas','p_bicaudal_ajustado_Holm']:.5f} |
| Passageiros/dia | {pf.loc['pax','p_exato_bicaudal_exploratorio']:.5f} | {pf.loc['pax','p_bicaudal_ajustado_Holm']:.5f} |
| Etapas não regulares/dia | {pf.loc['etapas_nao_regulares','p_exato_bicaudal_exploratorio']:.5f} | {pf.loc['etapas_nao_regulares','p_bicaudal_ajustado_Holm']:.5f} |

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
'''
(OUT/'LEIA_ME_ETAPA2_ANALISE_CIENTIFICA.md').write_text(text,encoding='utf-8')

archive=OUT.parent/'etapa2_SSA_grafos_comparacao_e_testes.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for file in sorted(OUT.iterdir()):
        if file.is_file():z.write(file,arcname='etapa2/'+file.name)
    z.write(Path(__file__),arcname='etapa2/reproduzir_etapa2_ssa.py')

print('RESUMO\n'+summary.to_string(index=False))
print('\nTESTES\n'+tests.to_string(index=False))
print('\nNOVOS\n'+newp.to_string(index=False))
print('\nARQUIVOS\n'+'\n'.join(str(x) for x in sorted(OUT.iterdir())))
print('\nPACOTE',archive)

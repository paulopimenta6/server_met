#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  6 02:27:07 2021

@author: phpimenta
"""

import sys
from parse_param_MET import parse_param
from poligono_regiao_MET import met_poligono_regiao
from gera_mapas_MAN_MET import met_gera_mapas_man
from gera_matriz_MAN_MET import met_gera_matriz_man
from gera_matriz_vento_MAN_MET import met_gera_matriz_vento_man
from gera_mapas_vento_MAN_MET import met_gera_mapas_vento_man


var=parse_param(sys.argv).imprime_parse_MAN()
# =============================================================================
print("# =============================================================================")
print(var)
print("tamanho da variavel parseada: %d" %(len(var)))
print("Tipo da variavel: %s" %(type(var))) 
print("# =============================================================================")
# =============================================================================


# =============================================================================
# Funcoes base
# =============================================================================

def validada_data(data):
    
    ana_prev=["00", "06", "12", "18"]
    
    #exemplo da variavel data: 202111090000
    #data=AAAA+MM+DD+AnAn+PrPr
    #data tem tamanho 12
    if len(data)==12:        
        ano=data[0:4]
        mes=data[4:6]
        dia=data[6:8]
        ana=data[8:10]
        prev=data[10:]        
        
    # validando a analise e a previsao
    if ana in ana_prev and prev in ana_prev:
        return ano, mes, dia, ana, prev      

def define_nivel(nivel):    
    nivel=int(nivel)  
    niveis=[150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 975, 1000]
    i=0
    j=i+1
    
    while i<=len(niveis)-2:
        
        if niveis[i]<=nivel<niveis[j]:
            media=(niveis[i]+niveis[j])/2
            if nivel<media:
                nivel=niveis[i]
                break
            else:
                nivel=niveis[j]
                break
        i=i+1
        j=j+1

    if nivel<=niveis[0] or nivel>=niveis[len(niveis)-1]:
        if nivel<=niveis[0]:
            nivel=niveis[0]
        else:
            nivel=niveis[len(niveis)-1]

    print(nivel) 
    return nivel

def cria_intervalo_niveis(nivelminConvertido, nivelmaxConvertido):
    niveis=[150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 925, 950, 975, 1000]
    niveis_return=[]
    
    nivelmin=define_nivel(nivelminConvertido)
    nivelmax=define_nivel(nivelmaxConvertido)
    
    if nivelmin>nivelmax:
        print(nivelmin)
        print(nivelmax)
        
        if nivelmin in niveis:
            idx_nivel_min=niveis.index(nivelmin)
        if nivelmax in niveis:
            idx_nivel_max=niveis.index(nivelmax)            

        print(idx_nivel_min)
        print(idx_nivel_max)     

    for i in range(idx_nivel_max, idx_nivel_min+1):
        niveis_return.append(niveis[i])    

    print(niveis_return)
    return niveis_return

# =============================================================================
# Fim do bloco de funcoes base
# =============================================================================

# =============================================================================
flag=var[0] 

if flag==1: #aqui o nivel e uma string que e "surface"
    varMET=var[1] 
    lonmin=var[2] 
    lonmax=var[3] 
    latmin=var[4] 
    latmax=var[5] 
    nivel=var[6] 
    date=var[7] 
    saida=var[8]    
    lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono=met_poligono_regiao(lonmin, lonmax, latmin, latmax).cria_poligono()
    ano, mes, dia, ana, prev=validada_data(date)
    print(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, nivel, ano, mes, dia, ana, prev, saida)     

if flag==2: #aqui e o nivel normal em hpa
    varMET=var[1] 
    lonmin=var[2] 
    lonmax=var[3] 
    latmin=var[4] 
    latmax=var[5] 
    nivel=define_nivel(var[6]) 
    date=var[7] 
    saida=var[8]
    lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono=met_poligono_regiao(lonmin, lonmax, latmin, latmax).cria_poligono()
    ano, mes, dia, ana, prev=validada_data(date)
    print(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, nivel, ano, mes, dia, ana, prev, saida)    

if flag==3: #aqui e o nivel em lista
    varMET=var[1] 
    lonmin=var[2] 
    lonmax=var[3] 
    latmin=var[4] 
    latmax=var[5] 
    nivelmin=var[6]
    nivelmax=var[7]
    date=var[8] 
    saida=var[9]
    lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono=met_poligono_regiao(lonmin, lonmax, latmin, latmax).cria_poligono()
    ano, mes, dia, ana, prev=validada_data(date)
    print(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, nivelmin, ano, mes, dia, ana, prev, saida)    
# =============================================================================

# =============================================================================
# organizando as variaveis para enviar para o gerador de mapas e matrizes
# =============================================================================

if varMET=="wind" or varMET=="winds":
    if flag==1:    
        met_gera_mapas_vento_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).processamento_dados_e_gerador_mapas()
        met_gera_matriz_vento_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).processamento_dados_e_gerador_matrizes()
        
    if flag==2:
        met_gera_mapas_vento_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).processamento_dados_e_gerador_mapas()
        met_gera_matriz_vento_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).processamento_dados_e_gerador_matrizes()
    
    if flag==3:
        intervalo=cria_intervalo_niveis(nivelmin, nivelmax)
        for nivel in intervalo:        
            met_gera_mapas_vento_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).processamento_dados_e_gerador_mapas()        
            #met_gera_matriz_vento_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).processamento_dados_e_gerador_matrizes()        

if varMET!="wind" and varMET!="winds":    
    if flag==1:    
        met_gera_mapas_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).gera_mapas_final()
        met_gera_matriz_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).gera_matriz_final()
        
    if flag==2:
        met_gera_mapas_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).gera_mapas_final()
        met_gera_matriz_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).gera_matriz_final()
    
    if flag==3:
        intervalo=cria_intervalo_niveis(nivelmin, nivelmax)
        for nivel in intervalo:        
            met_gera_mapas_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).gera_mapas_final()        
            met_gera_matriz_man(varMET, lonmin_poligono, lonmax_poligono, latmin_poligono, latmax_poligono, ano, mes, dia, ana, prev, saida, nivel).gera_matriz_final()
   
        

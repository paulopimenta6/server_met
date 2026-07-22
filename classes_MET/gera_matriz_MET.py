#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 28 09:17:29 2021

@author: paulopimenta
"""
from regioes_predefinidas_MET import regioes_predefinidas
from ponto_regiao_MET import met_ponto_regiao
from parse_param_MET import parse_param
from processamento_dados_MET import processamento_dados_met_AUT
from mpl_toolkits.basemap import Basemap
import numpy as np
import sys
import csv
import os
import time
from controla_env import controla_dirs_MET

dir_save=controla_dirs_MET()

def geraMatriz(objGRIB, lon_lat, variavelMET, regiao, nivel):
    
    hora_grib=["00", "06", "12", "18"]
    data_horario=time.localtime()
    ano=data_horario.tm_year
    mes=data_horario.tm_mon
    dia=data_horario.tm_mday
    hora=data_horario.tm_hour
    minuto=data_horario.tm_min
    
    i=0
    j=i+1
    
    while i<=(len(hora_grib)-2):           
        if int(hora_grib[i])<=hora<int(hora_grib[j]):
            hh_analise=hora_grib[i]
        i=i+1
        j=j+1
        
    if hora>=int(hora_grib[len(hora_grib)-1]):
        hh_analise=hora_grib[len(hora_grib)-1]    
    
    if int(dia)<10:
        dia="0"+str(dia)
    if int(mes)<10:
        mes="0"+str(mes)   
    
    lons1=lon_lat[0][0]
    lons2=lon_lat[0][1]
    lats1=lon_lat[1][0]
    lats2=lon_lat[1][1]
    
    if 0<=lons1<180 and 0<=lons2<180:
        flag=1

    if -180<=lons1<0 and -180<=lons2<0:
        lons1=lons1+360
        lons2=lons2+360
        flag=2

    if -180<=lons1<0 and 0<=lons2<180:
        flag=3

    for objMET in objGRIB:

        if variavelMET=="chuvaConvec" or variavelMET=="chuvaNaoConvec":
            ft=objMET.forecastTime+6
            if ft<12:
                ft='0'+str(ft)
        else: 
            ft=objMET.forecastTime
            if ft<12:
                ft='0'+str(ft)

        f = open(dir_save.imprime_dirMatrizes() + "GFS_" + str(objMET.iDirectionIncrementInDegrees) + "_" + str(regiao) + "_" + "N" +str(nivel) + "_" + str(variavelMET) + "_" + hh_analise + "_" + str(objMET.dataDate) + "_" + str(ft)  + '.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)                

        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)
            data, lat, lon = objMET.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            if flag==2:
                lon=lon-360                           
            lon=lon[0,:]
            lat=lat[:,0]
            lat=lat[::-1]
            lon,lat=np.meshgrid(lon ,lat)           
            
        if flag==3:
            lons1_ini=lons1+360          
            lons2_ini=360
            lons1_fim=0          
            lons2_fim=lons2

            data_ini, lat_ini, lon_ini = objMET.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            lon_ini=lon_ini[0,:]
            lon_ini=lon_ini-360
            lat_ini=lat_ini[:,0]
            lat_ini=lat_ini[::-1]          

            data_fim, lat_fim, lon_fim = objMET.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            lon_fim=lon_fim[0,:]            
            lat_fim=lat_fim[:,0]
            lat_fim=lat_fim[::-1]        

            #latitude nao muda em momento algum, pois sua variacao nao precisa de correcao
            lat=lat_ini
            lon=np.append(lon_ini, lon_fim)
            lon,lat=np.meshgrid(lon ,lat)
 
            data=np.zeros((data_ini.shape[0],data_ini.shape[1]+data_fim.shape[1]))
            if data_ini.shape[0]==data_fim.shape[0]:
                for i in range(0,data_ini.shape[0]):
                    data[i,:]=np.append(data_ini[i,:],data_fim[i,:])

        linha=data.shape[0]
        coluna=data.shape[1]

        if variavelMET=="temp" or variavelMET=="temps":
            data=data-273.15            
        if variavelMET=="ps" or variavelMET=="prnm":    
            data=data/100    

        w.writerow(["lat", "lon", variavelMET])

        for i in range(linha):
            for j in range(coluna):
             #comentando a linha que escreve os dados de matriz                 
             #print("%f %f %f" %(lat[i,j], lon[i,j], data[i,j]))
                 w.writerow([lat[i,j], lon[i,j], data[i,j]])
                
        f.close()

# =============================================================================
# Parseando e adquirindo as variaveis
# Ajustando as variaveis
# =============================================================================

varMET, varNivel, varRegiao = parse_param(sys.argv).imprime_parse()
if (type(varRegiao) is tuple):
    print("Entrou no primeiro if")
    print("varRegiao: ")
    print(varRegiao)
    varRegiao=list(varRegiao)
    lon=int(varRegiao[0])
    lat=int(varRegiao[1])
    if (type(varRegiao) is list):    
        ptos=met_ponto_regiao(lon, lat)
        lonslats=ptos.imprime_longitude_latitude()
        print("Usando a classe ponto_regiao_MET")
        print(lonslats)
        varRegiaoNome=str("lon") + str(lon) + "_" + str("lat") + str(lat)

# =============================================================================
# Passando as variaveis para a classe correspondente - Usando a classe regioes_predefinidas_MET
# =============================================================================

if (type(varRegiao) is str):
    ptos=regioes_predefinidas(varRegiao)
    lonslats=ptos.imprime_regiao()
    print("Usando a classe regioes_predefinidas_MET")
    print(lonslats)
    varRegiaoNome=str(varRegiao)
    
# =============================================================================
# Passando as variaveis para a classe correspondente de leitura de dados - leituras_dados_MET    
# Passada a variavel de meteorologia e de nivel e conseguido 
# o conjunto de valores do nivel exato
# =============================================================================
print("Variavel MET: " + varMET)
print(varNivel)

if varNivel!="surface":
    dadosVarComNivelMET=processamento_dados_met_AUT(varMET, varNivel)
    lista_var_com_nivel_pretendido=dadosVarComNivelMET.define_lista_var_com_nivel_pressao()
    geraMatriz(lista_var_com_nivel_pretendido, lonslats, varMET, varRegiaoNome, varNivel)
if varNivel=="surface":
    dadosVarComNivelMET=processamento_dados_met_AUT(varMET)
    lista_var_com_nivel_pretendido=dadosVarComNivelMET.define_lista_var_com_nivel_superficie()
    geraMatriz(lista_var_com_nivel_pretendido, lonslats, varMET, varRegiaoNome, varNivel) 

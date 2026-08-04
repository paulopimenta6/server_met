#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Aug 22 18:55:50 2021

@author: phpimenta
"""
import matplotlib
matplotlib.use('Agg')
from matplotlib import rc
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from regioes_predefinidas_MET import regioes_predefinidas
from ponto_regiao_MET import met_ponto_regiao
from parse_param_MET import parse_param
from processamento_dados_MET import processamento_dados_met_AUT
import numpy as np
import sys
import time
import os
from controla_env import controla_dirs_MET

dir_save=controla_dirs_MET()

def O(dataVars):
    
    min_var_met=dataVars.min()-1
    max_var_met=dataVars.max()+1
    
    intervalo_valores=[]
    
    if len(dataVars)<=50:
        o=30
        intervalo_valores=np.linspace(int(min_var_met), int(max_var_met), o)

    elif 50<len(dataVars)<=100:
        o=50
        intervalo_valores=np.linspace(int(min_var_met), int(max_var_met), o)
    
    elif 100<len(dataVars)<=500:
        o=70
        intervalo_valores=np.linspace(int(min_var_met), int(max_var_met), o)
    
    elif 500<len(dataVars)<=1000:
        o=90
        intervalo_valores=np.linspace(int(min_var_met), int(max_var_met), o)

    elif 1000<len(dataVars)<=10000:
        o=110
        intervalo_valores=np.linspace(int(min_var_met), int(max_var_met), o)

    else:
        o=500
        intervalo_valores=np.linspace(int(min_var_met), int(max_var_met), o)
    
    return intervalo_valores

def gera_mapas(objGRIB, lon_lat, variavelMET, regiao, nivel):

    hora_grib=["00", "06", "12", "18"]
    data_horario=time.localtime()
    mes=data_horario.tm_mon
    dia=data_horario.tm_mday
    hora=data_horario.tm_hour
    
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
###
 
    for objMET in objGRIB:      

        if varMET=="chuvaConvec" or varMET=="chuvaNaoConvec":
            ft=objMET.forecastTime+6
            if ft<12:
                ft='0'+str(ft)  
        else:
            ft=objMET.forecastTime
            if ft<12:
                ft='0'+str(ft)        

        if flag==1 or flag==2: 
            map = Basemap(projection='mill', lat_0=0, lon_0=0)        
            data, lat, lon = objMET.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            if flag==2:
                lon=lon-360            
            lon=lon[0,:]
            lat=lat[:,0]
            lat=lat[::-1]
        
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

            print(data_ini.shape)          

            data_fim, lat_fim, lon_fim = objMET.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            
            lon_fim=lon_fim[0,:]            
            lat_fim=lat_fim[:,0]
            lat_fim=lat_fim[::-1]        

            print(data_fim.shape)
           
            #latitude nao muda em momento algum, pois sua variacao nao precisa de correcao
            lat=lat_ini
            lon=np.append(lon_ini, lon_fim)
            data=np.zeros((data_ini.shape[0],data_ini.shape[1]+data_fim.shape[1]))             
           
            if data_ini.shape[0]==data_fim.shape[0]:
                for i in range(0,data_ini.shape[0]):
                    data[i,:]=np.append(data_ini[i,:],data_fim[i,:])

        lon,lat=np.meshgrid(lon ,lat)

        if variavelMET=="temp" or variavelMET=="temps":
            data=data-273.15
        if variavelMET=="ps" or variavelMET=="prnm":    
            data=data/100
        if variavelMET=="umidadeRel" or variavelMET=="temps" or variavelMET=="ps" or variavelMET=="prnm":
            nivel="superficie"
 
        unidade=objMET.units
        if unidade=="Pa":
            unidade="hPa"
        if unidade=="K":
            unidade="°C"
        if unidade=="kg m**-2":
            unidade="mm"
    
        lon_min=lon.min()
        lon_max=lon.max()
        lat_min=lat.min()
        lat_max=lat.max()  

        m = Basemap(projection='mill',
            llcrnrlat=lat_min, 
            urcrnrlat=lat_max,
            llcrnrlon=lon_min,
            urcrnrlon=lon_max,
            resolution='i')

    # Usar a funcao extrai_lat_lon(lista_nivel_escolhida, data) para pegar os lat_reg e lon_reg

        rc('font',weight='normal') 
        rc('xtick',labelsize=12)  
        rc('font',size=12)
        rc('ytick',labelsize=12)    
        #plt.figure(figsize=(8,10))
        plt.figure(figsize=(18, 16))
        x,y=m(lon, lat)

        meridianinterval=np.arange(lon_min,lon_max,4)
        parallelsinterval=np.arange(lat_min,lat_max)    
        m.drawparallels(parallelsinterval,labels=[1,0,0,0],  color='k',linewidth=.3)
        m.drawmeridians(meridianinterval,labels=[0,0,0,1],color='k',linewidth=.3)

        try:
            m.drawcoastlines(linewidth=0.5)
        except:
            pass
            
        m.drawcountries()
        m.drawstates()

        intervalo_valores=O(data)  
    
        contourf = m.contourf(x, y, np.squeeze(data),cmap='viridis', levels=intervalo_valores)
        cs1 = m.contour(x, y, np.squeeze(data),colors='k', levels=intervalo_valores, linewidths=0.2)

        plt.clabel(cs1,fmt='%d',fontsize=8)

        print(contourf)
        cbar=m.colorbar(contourf, location='right', pad="1%")
        cbar.set_label(unidade)
        plt.title("GFS " + str(objMET.iDirectionIncrementInDegrees) + " - " + str(regiao).upper() + " " + str(variavelMET) + " [" + str(unidade) + "]" + " - Nivel: " + str(nivel)  + " Analise: " + str(hh_analise) + " Data: " + str(objMET.dataDate) + " Prev: " + str(ft), weight="normal", fontsize=12)
        #Usar diretorio para salvar imagens        
        plt.savefig(dir_save.imprime_dirMapas() + "GFS_" + str(objMET.iDirectionIncrementInDegrees) + "_" + str(regiao).upper() + "_" + "N" + str(nivel) + "_" + str(variavelMET) + "_" + str(hh_analise) + "_" + str(objMET.dataDate) + "_" + str(ft) + ".png",bbox_inches='tight')
        #plt.show()    


varMET, varNivel, varRegiao=parse_param(sys.argv).imprime_parse()

print("Aqui impresso as variaveis com o novo parseamento: ")
print(varMET, varNivel, varRegiao)

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

if (type(varRegiao) is str):
    ptos=regioes_predefinidas(varRegiao)
    lonslats=ptos.imprime_regiao()
    print("Usando a classe regioes_predefinidas_MET")
    print(lonslats)
    varRegiaoNome=str(varRegiao)

# =============================================================================
# Leitura do grib dentro da lib pygrib 
# Geracao de Mapas 
# =============================================================================
if varNivel!="surface":
    dadosVarComNivelMET=processamento_dados_met_AUT(varMET, varNivel)
    lista_var_com_nivel_pretendido=dadosVarComNivelMET.define_lista_var_com_nivel_pressao()
    gera_mapas(lista_var_com_nivel_pretendido, lonslats, varMET, varRegiaoNome, varNivel)
if varNivel=="surface":
    #dadosVarComNivelMET=processamento_dados_met_AUT(varMET, varNivel)
    dadosVarComNivelMET=processamento_dados_met_AUT(varMET)
    lista_var_com_nivel_pretendido=dadosVarComNivelMET.define_lista_var_com_nivel_superficie()
    gera_mapas(lista_var_com_nivel_pretendido, lonslats, varMET, varRegiaoNome, varNivel)

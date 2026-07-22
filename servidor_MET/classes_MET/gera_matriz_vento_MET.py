#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 19 23:27:01 2021

@author: phpimenta
"""

from regioes_predefinidas_MET import regioes_predefinidas
from ponto_regiao_MET import met_ponto_regiao
from parse_param_MET import parse_param
from processamento_dados_MET import processamento_dados_met_AUT
from mpl_toolkits.basemap import Basemap
import numpy as np
import csv
import os
import time
import sys
import math
from controla_env import controla_dirs_MET

dir_save=controla_dirs_MET()

def criaResultante(data_u, data_v):
    vResult=np.empty(data_u.shape)
    vResult=np.sqrt(np.power(data_u,2) + np.power(data_v,2))
    return vResult

def criaResultanteKnot(data_u, data_v):
    vResult=np.empty(data_u.shape)
    vResult=np.sqrt(np.power(data_u,2) + np.power(data_v,2))
    vResultKnot=vResult*1.943
    return vResultKnot 
    
def criaAngAzMET(data_u, data_v):
    angAzResult=np.empty(data_u.shape)
    angAzResult=(((180/np.pi)*(np.arctan2((data_u),(data_v)))))
    return angAzResult 

def criaAngMET(data_u, data_v):
    angResult=np.empty(data_u.shape)
    angResult=(((180/np.pi)*(np.arctan2((-data_u),(-data_v)))))
    return angResult 

def converte_altitude(pres):    
    #retorna a altitude em feet    
    p0=1013.25
    h_alt = (1 - (pres/p0)**0.190284) * 145366.45
    return h_alt
    
def geraMatriz_Vento_Resu(u_objGRIB, v_objGRIB, lon_lat, regNome, nivel):

#Gerador de vento para o BlueSky    
# =============================================================================
# from bluesky.traffic.windsim import WindSim
# wind = WindSim()
# Geracao de dados de vento de acordo com o seguinte criterio:
# wind.add(52, 4, 0, 270, 50)
# lat 	deg 	latitude
# lon 	deg 	longitude
# alt 	ft 	altitude
# winddir 	deg 	wind direction
# windspd 	kt 	wind speed
# link1: https://github.com/TUDelft-CNS-ATM/bluesky/wiki/windsim
# link2: https://www.weather.gov/media/epz/wxcalc/pressureAltitude.pdf (tranformando hPa de altitude em ft)     
# =============================================================================

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

    for i in range(len(u_objGRIB)):
        ft=u_objGRIB[i].forecastTime
        if ft<12:
            ft='0'+str(ft)
                
        f = open(dir_save.imprime_dirMatrizesBluesky() + "GFS_" + str(u_objGRIB[i].iDirectionIncrementInDegrees) + "_" + "matriz_lat_lon_alt_angMET_VentoResult" + "_" + str(regNome).upper() + "_" + "N" + str(nivel) + "_" + hh_analise + "_" + str(u_objGRIB[i].dataDate) + "_" + str(ft)  + '.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)          
        
        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)
            data_U, lat_u, lon_u = u_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_V, lat_v, lon_v = v_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            
            if flag==2:
                lon_u=lon_u-360
                lon_v=lon_v-360 
            lon_u=lon_u[0,:]
            lat_u=lat_u[:,0]
            lat_u=lat_u[::-1]  
            lon,lat=np.meshgrid(lon_u ,lat_u)        

        if flag==3:
            lons1_ini=lons1+360          
            lons2_ini=360
            lons1_fim=0          
            lons2_fim=lons2

            data_U_ini, lat_u_ini, lon_u_ini = u_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            data_V_ini, lat_v_ini, lon_v_ini = v_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)

            lon_u_ini=lon_u_ini[0,:]
            lon_u_ini=lon_u_ini-360
            lat_u_ini=lat_u_ini[:,0]
            lat_u_ini=lat_u_ini[::-1]          

            data_U_fim, lat_u_fim, lon_u_fim = u_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            data_V_fim, lat_v_fim, lon_v_fim = v_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)

            lon_u_fim=lon_u_fim[0,:]            
            lat_u_fim=lat_u_fim[:,0]
            lat_u_fim=lat_u_fim[::-1]        

            #latitude nao muda em momento algum, pois sua variacao nao precisa de correcao
            lat=lat_u_ini
            lon=np.append(lon_u_ini, lon_u_fim)
            lon,lat=np.meshgrid(lon ,lat)
 
            data_U=np.zeros((data_U_ini.shape[0],data_U_ini.shape[1]+data_U_fim.shape[1]))
            data_V=np.zeros((data_V_ini.shape[0],data_V_ini.shape[1]+data_V_fim.shape[1])) 
           
            if data_U_ini.shape[0]==data_U_fim.shape[0]:
                for i in range(0,data_U_ini.shape[0]):
                    data_U[i,:]=np.append(data_U_ini[i,:],data_U_fim[i,:])

            if data_V_ini.shape[0]==data_V_fim.shape[0]:
                for i in range(0,data_V_ini.shape[0]):
                    data_V[i,:]=np.append(data_V_ini[i,:],data_V_fim[i,:])                
   
    
        linha=data_U.shape[0]
        coluna=data_U.shape[1]   
        vento_resultante=criaResultanteKnot(data_U, data_V)        
        angMET=criaAngMET(data_U, data_V)
        hMET=converte_altitude(nivel)              

        w.writerow([ "lat", "lon", "hMET", "angMET", "vento_resultante" ])
        for i in range(linha):
            for j in range(coluna):
            #comentando a linha que escreve a matriz                   
            #print("%f %f %f %f %f" %(lat[ii,jj], lon[ii,jj], hMET, angMET[ii,jj], vento_resultante[ii,jj]))
                w.writerow([ lat[i,j], lon[i,j], hMET, angMET[i,j], vento_resultante[i,j] ])
        
        f.close()

def geraMatriz_Vento_UVT_predi(u_objGRIB, v_objGRIB, t_objGRIB, lon_lat, regNome, nivel):
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

    for i in range(len(u_objGRIB)):

        ft=u_objGRIB[i].forecastTime
        if ft<12:
            ft='0'+str(ft)
      
        f = open(dir_save.imprime_dirMatrizesPredi() + "GFS_" + str(u_objGRIB[i].iDirectionIncrementInDegrees) + "_" + "matriz_lat_lon_Vento_UVT_Predi" + "_" + str(regNome).upper()  + "_" + "N" +str(nivel) + "_" + str(hh_analise) + "_" + str(u_objGRIB[i].dataDate) + "_" + str(ft)  + '.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)
        
        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)
            data_U, lat_u, lon_u = u_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_V, lat_v, lon_v = v_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)    
            data_T, lat_t, lon_t = t_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            if flag==2:
                lon_u=lon_u-360
                lon_v=lon_v-360
        
            lon_u=lon_u[0,:]
            lat_u=lat_u[:,0]
            lat_u=lat_u[::-1]
            lon,lat=np.meshgrid(lon_u ,lat_u)
            
        if flag==3:
            lons1_ini=lons1+360          
            lons2_ini=360
            lons1_fim=0          
            lons2_fim=lons2

            data_U_ini, lat_u_ini, lon_u_ini = u_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            data_V_ini, lat_v_ini, lon_v_ini = v_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            data_T_ini, lat_t_ini, lon_t_ini = t_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini) 

            lon_u_ini=lon_u_ini[0,:]
            lon_u_ini=lon_u_ini-360
            lat_u_ini=lat_u_ini[:,0]
            lat_u_ini=lat_u_ini[::-1]          

            data_U_fim, lat_u_fim, lon_u_fim = u_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            data_V_fim, lat_v_fim, lon_v_fim = v_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            data_T_fim, lat_t_fim, lon_t_fim = t_objGRIB[i].data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim) 

            lon_u_fim=lon_u_fim[0,:]            
            lat_u_fim=lat_u_fim[:,0]
            lat_u_fim=lat_u_fim[::-1]        

            #latitude nao muda em momento algum, pois sua variacao nao precisa de correcao
            lat=lat_u_ini
            lon=np.append(lon_u_ini, lon_u_fim)
            lon,lat=np.meshgrid(lon ,lat)
 
            data_U=np.zeros((data_U_ini.shape[0],data_U_ini.shape[1]+data_U_fim.shape[1]))
            data_V=np.zeros((data_V_ini.shape[0],data_V_ini.shape[1]+data_V_fim.shape[1]))
            #a variavel "t" de temperatura foi incluida!   
            data_T=np.zeros((data_T_ini.shape[0],data_T_ini.shape[1]+data_T_fim.shape[1])) 
           
            if data_U_ini.shape[0]==data_U_fim.shape[0]:
                for i in range(0,data_U_ini.shape[0]):
                    data_U[i,:]=np.append(data_U_ini[i,:],data_U_fim[i,:])

            if data_V_ini.shape[0]==data_V_fim.shape[0]:
                for i in range(0,data_V_ini.shape[0]):
                    data_V[i,:]=np.append(data_V_ini[i,:],data_V_fim[i,:])

            if data_T_ini.shape[0]==data_T_fim.shape[0]:
                for i in range(0,data_T_ini.shape[0]):
                    data_T[i,:]=np.append(data_T_ini[i,:],data_T_fim[i,:])
                    
  
        linha=data_U.shape[0]
        coluna=data_U.shape[1]
        w.writerow([ "lat", "lon", "vento U", "vento V", "temp" ])
        for i in range(linha):
            for j in range(coluna):
                #comentando a linha que escreve a matriz de dados MET                
                #print("%f %f %f %f %f" %( lat[ii,jj], lon[ii,jj], data_UU[ii,jj], data_VV[ii,jj], data_T[ii,jj] ))
                w.writerow([ lat[i,j], lon[i,j], data_U[i,j], data_V[i,j], data_T[i,j] ])
        
        f.close()

def geraMatrizVentoSup(lon_lat, varReg):
    
    # =============================================================================
    # ventos e temperatura para o preditor
    # Para situacoes proximo a superficie
    # var impressas: <lat[deg]> <lon[deg]> <u[m**s-1]> <v[m**s-1]> <t[K]>
    # Passar como parametro o nivel de superficie... 
    
    varNivelVentoSup=[20, 30, 40, 50, 80]
    t_comp_supe=processamento_dados_met_AUT("temps").define_lista_var_com_nivel_superficie()    

    for varNivel_sup in varNivelVentoSup: 
        u_comp_supe=processamento_dados_met_AUT("uSupe", varNivel_sup).define_lista_var_com_altitude()
        v_comp_supe=processamento_dados_met_AUT("vSupe", varNivel_sup).define_lista_var_com_altitude()

        geraMatriz_Vento_Resu(u_comp_supe, v_comp_supe, lon_lat, varReg, varNivel_sup)
        geraMatriz_Vento_UVT_predi(u_comp_supe, u_comp_supe, t_comp_supe, lon_lat, varReg, varNivel_sup) 
 

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
        
if (type(varRegiao) is str):
    ptos=regioes_predefinidas(varRegiao)
    lonslats=ptos.imprime_regiao()
    print("Usando a classe regioes_predefinidas_MET")
    print(lonslats)
    varRegiaoNome=str(varRegiao)        


if varMET=="wind":    
    # =============================================================================
    # Calculando a altitude em ft 
    # =============================================================================
    u_comp=processamento_dados_met_AUT("u", varNivel).define_lista_var_com_nivel_pressao()
    v_comp=processamento_dados_met_AUT("v", varNivel).define_lista_var_com_nivel_pressao()
    t_comp=processamento_dados_met_AUT("temp", varNivel).define_lista_var_com_nivel_pressao()
    # =============================================================================
    # ventos para BlueSky
    # var impressas: <lat[deg]> <lon[deg]> <alt[feet]> <angMET[deg]> <VResul[m**s-1]> 
    geraMatriz_Vento_Resu(u_comp, v_comp, lonslats, varRegiaoNome, varNivel)
    # =============================================================================
    # =============================================================================
    # ventos e temperatura para o preditor
    # Para situacoes no nivel escolhido pelo usuario ou automacao 
    geraMatriz_Vento_UVT_predi(u_comp, v_comp, t_comp, lonslats, varRegiaoNome, varNivel)
    # =============================================================================
if varMET=="winds":
    # =============================================================================
    # Gerando as matrizes proximas da superfície
    # O nivel de altura considerado é a altura em relacao ao solo    
    geraMatrizVentoSup(lonslats, varRegiaoNome)
# =============================================================================

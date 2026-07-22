#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 07:15:27 2021

@author: phpimenta
"""
import matplotlib
from matplotlib import rc
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
import sys
import time
import os
from regioes_predefinidas_MET import regioes_predefinidas
from ponto_regiao_MET import met_ponto_regiao
from parse_param_MET import parse_param
from processamento_dados_MET import processamento_dados_met_AUT
from controla_env import controla_dirs_MET
dir_save=controla_dirs_MET()

varNivelProxSupe=[20, 30, 40, 50, 80]

def gera_mapas_vento(u_objGRIB, v_objGRIB, lon_lat, regNome, nivel):

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
        lons1_ini=lons1+360          
        lons2_ini=360
        lons1_fim=0          
        lons2_fim=lons2
        flag=3
    
    for i in range(len(u_objGRIB)):
        
        ft=u_objGRIB[i].forecastTime
        if ft<12:
            ft='0'+str(ft)
    
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
            
        if flag==3:
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
            lat_u=lat_u_ini
            lon_u=np.append(lon_u_ini, lon_u_fim)
            lon_v=lon_u
            data_U=np.zeros((data_U_ini.shape[0],data_U_ini.shape[1]+data_U_fim.shape[1]))
            data_V=np.zeros((data_V_ini.shape[0],data_V_ini.shape[1]+data_V_fim.shape[1])) 
           
            if data_U_ini.shape[0]==data_U_fim.shape[0]:
                for i in range(0,data_U_ini.shape[0]):
                    data_U[i,:]=np.append(data_U_ini[i,:],data_U_fim[i,:])

            if data_V_ini.shape[0]==data_V_fim.shape[0]:
                for i in range(0,data_V_ini.shape[0]):
                    data_V[i,:]=np.append(data_V_ini[i,:],data_V_fim[i,:])
###
        
        lons,lats=np.meshgrid(lon_u ,lat_u)
        
        lon_min=lons.min()
        lon_max=lons.max()
        lat_min=lats.min()
        lat_max=lats.max()  
        
        m = Basemap(projection='cyl',
            llcrnrlat=lat_min, 
            urcrnrlat=lat_max,
            llcrnrlon=lon_min,
            urcrnrlon=lon_max,
            resolution='i')
        
        fig1=plt.figure(figsize=(18, 16))
        ax=fig1.add_axes([0.1,0.1,0.7,0.7])
        clevs=np.arange(960,1061,5)
        x,y=m(lons, lats)
        
        meridianinterval=np.arange(lon_min,lon_max,4)
        parallelsinterval=np.arange(lat_min,lat_max)    
        m.drawparallels(parallelsinterval,labels=[1,0,0,0], color='k',linewidth=.3)
        m.drawmeridians(meridianinterval,labels=[0,0,0,1],color='k',linewidth=.3)

        if nivel>500 or nivel<=80:
            speed = np.sqrt(data_U**2+data_V**2)            
            strm=plt.streamplot(lons,lats,data_U,data_V,color=speed,linewidth = 1, cmap=plt.cm.inferno, density=5, arrowstyle='->', arrowsize = 1.5) 
            cb=plt.colorbar(strm.lines)
            cb.ax.set_ylabel("Vento m/s", fontsize = 14)
        else:
        # =============================================================================
        # Comandos para criar mapas com vetor
        # =============================================================================
            uproj,vproj,xx,yy=m.transform_vector(data_U,data_V,lon_u,lat_u,38,38,returnxy=True,masked=True)
            plt.barbs(xx,yy,uproj,vproj, pivot='middle', barbcolor='#333333')
        #   qk=plt.quiverkey(Q, 0.1, 0.0125, 5, '5 m/s', labelpos='W')
        # =============================================================================

        m.drawlsmask(land_color='tan', ocean_color='lightblue', lakes=True)
        #m.drawcoastlines(linewidth=1.5)

        try:
            m.drawcoastlines(linewidth=0.5)
        except:
            pass

        m.drawcountries(linewidth=0.25)        
        m.drawcountries()
        m.drawstates()
     
        #sera 12 temporariamente e nao str(hh_analise) 
        plt.title("GFS " + str(u_objGRIB[i].iDirectionIncrementInDegrees) + " - " + str(regNome).upper() + " - Vento [m/s]" + " - Nivel: " + str(nivel)  + " Analise: " + str(hh_analise) + " Data: " + str(u_objGRIB[i].dataDate) + " Prev: " + str(ft), weight="normal", fontsize=12)
        #Usar diretorio para salvar imagens        
        plt.savefig(dir_save.imprime_dirMapas() + "GFS_" + str(u_objGRIB[i].iDirectionIncrementInDegrees) + "_" + str(regNome).upper() + "_" + "N" + str(nivel) + "_" + "CampoVento" + "_" + hh_analise + "_" + str(u_objGRIB[i].dataDate) + "_" + str(ft) + ".png",bbox_inches='tight')
            
varMET, varNivel, varRegiao = parse_param(sys.argv).imprime_parse() #Ajustar a aquisicao de variaveis...

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

if varMET=="wind":
    u_comp=processamento_dados_met_AUT("u", varNivel).define_lista_var_com_nivel_pressao()
    v_comp=processamento_dados_met_AUT("v", varNivel).define_lista_var_com_nivel_pressao()
    gera_mapas_vento(u_comp, v_comp, lonslats, varRegiaoNome, varNivel)
if varMET=="winds" and varNivel=="surface":
    for nivelQuaseSupe in varNivelProxSupe: 
        u_comp=processamento_dados_met_AUT("uSupe", nivelQuaseSupe).define_lista_var_com_altitude()
        v_comp=processamento_dados_met_AUT("uSupe", nivelQuaseSupe).define_lista_var_com_altitude()
        gera_mapas_vento(u_comp, v_comp, lonslats, varRegiaoNome, nivelQuaseSupe)


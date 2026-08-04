#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 16 11:51:10 2021

@author: phpimenta
"""

from mpl_toolkits.basemap import Basemap
import numpy as np
import csv
from processamento_dados_MET import processamento_dados_met_MAN
from controla_env import controla_dirs_MET
dir_save=controla_dirs_MET()

class met_gera_matriz_vento_man:
    
    def __init__(self, varMET, lonmin, lonmax, latmin, latmax, ano, mes, dia, ana, prev, saida, nivel):
        
        self.varMET=varMET 
        self.lonmin=lonmin 
        self.lonmax=lonmax 
        self.latmin=latmin 
        self.latmax=latmax 
        self.nivel=nivel  
        self.ano=ano
        self.mes=mes
        self.dia=dia
        self.ana=ana
        self.prev=prev
        self.saida=saida
        self.regiao="LonMin:"+str(self.lonmin)+" LonMax:"+str(self.lonmax)+" LatMin:"+str(self.latmin)+" LatMax:"+str(self.latmax) 
        self.varNivelProxSupe=[20, 30, 40, 50, 80]

    def criaResultante(self, data_u, data_v):
        vResult=np.empty(data_u.shape)
        vResult=np.sqrt(np.power(data_u,2) + np.power(data_v,2))
        return vResult 

    def criaResultanteKnot(self, data_u, data_v):
        vResult=np.empty(data_u.shape)
        vResult=np.sqrt(np.power(data_u,2) + np.power(data_v,2))
        vResultKnot=vResult*1.943
        return vResultKnot
        
    def criaAngAzMET(self, data_u, data_v):
        angAzResult=np.empty(data_u.shape)
        angAzResult=(((180/np.pi)*(np.arctan2((data_u),(data_v)))))
        return angAzResult 
    
    def criaAngMET(self, data_u, data_v):
        angResult=np.empty(data_u.shape)
        angResult=(((180/np.pi)*(np.arctan2((-data_u),(-data_v)))))
        return angResult 
    
    def converte_altitude(self, pres):        
        #retorna a altitude em feet        
        p0=1013.25
        h_alt = (1 - (pres/p0)**0.190284) * 145366.45
        return h_alt

    def gera_matriz_vento(self, varMET_AUX_u, varMET_AUX_v, lonmin, lonmax, latmin, latmax, ana, prev, regiao, nivel, saida):
        
        lons1=lonmin
        lons2=lonmax
        lats1=latmin
        lats2=latmax        

        if 0<=lons1<180 and 0<=lons2<180:
            flag=1

        if -180<=lons1<0 and -180<=lons2<0:
            lons1=lons1+360
            lons2=lons2+360
            flag=2

        if -180<=lons1<0 and 0<=lons2<180:
            flag=3
                
        f = open(saida + "matriz_vento" + "_" + str(regiao) + "_" + "N" + str(nivel) + "_" + ana + "_" + str(varMET_AUX_u.dataDate) + "_" + prev  + '.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)

        if flag==1 or flag==2:
            map=Basemap(projection='mill', lat_0=0, lon_0=0)                         
            #Faz a aquisição dos dados de vento U e V
            data_U, lat_u, lon_u = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_V, lat_v, lon_v = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)

            if flag==2:
                lon_u=lon_u-360
                lon_v=lon_v-360                
            lon_u=lon_u[0,:]
            lat_u=lat_u[:,0]
            lat_u=lat_u[::-1]
            lon,lat=np.meshgrid(lon_u ,lat_u)
            #linha=data_U.shape[0]
            #coluna=data_U.shape[1]
            
        if flag==3:
            lons1_ini=lons1+360          
            lons2_ini=360
            lons1_fim=0          
            lons2_fim=lons2

            data_U_ini, lat_u_ini, lon_u_ini = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            data_V_ini, lat_v_ini, lon_v_ini = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)

            lon_u_ini=lon_u_ini[0,:]
            lon_u_ini=lon_u_ini-360
            lat_u_ini=lat_u_ini[:,0]
            lat_u_ini=lat_u_ini[::-1]          

            data_U_fim, lat_u_fim, lon_u_fim = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            data_V_fim, lat_v_fim, lon_v_fim = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)

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

            #linha=data_U.shape[0]
            #coluna=data_U.shape[1]

        linha=data_U.shape[0]
        coluna=data_U.shape[1]    
        vento_resultante=self.criaResultante(data_U, data_V)        
        angMET=self.criaAngMET(data_U, data_V)
        hMET=self.converte_altitude(nivel)

        w.writerow([ "lat", "lon", "nivel<hPa>", "halt<feet>", "angMET<grau>", "vento U<ms**-1>", "vento V<ms**-1>", "vento_resultante<ms**-1>" ])

        for i in range(linha):
            for j in range(coluna):
                #comentando a linha que escreve a matriz                   
                w.writerow([ lat[i,j], lon[i,j], nivel, hMET, angMET[i,j], data_U[i,j], data_V[i,j], vento_resultante[i,j] ])                                
                    
        f.close()

    def gera_matriz_vento_bluesky(self, varMET_AUX_u, varMET_AUX_v, lonmin, lonmax, latmin, latmax, ana, prev, regiao, nivel, saida):
    
    #descricao breve do uso de vento no blueSky        
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
            
        lons1=lonmin
        lons2=lonmax
        lats1=latmin
        lats2=latmax
        
        if 0<=lons1<180 and 0<=lons2<180:
            flag=1        
        
        if -180<=lons1<0 and -180<=lons2<0:
            lons1=lons1+360
            lons2=lons2+360
            flag=2

        if -180<=lons1<0 and 0<=lons2<180:
            flag=3

        f = open(saida + "matriz_vento_bluesky" + "_" + str(regiao) + "_" + "N" + str(nivel) + "_" + ana + "_" + str(varMET_AUX_u.dataDate) + "_" + prev  + '.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)

        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)
		        
	        #Faz a aquisição dos dados de vento U e V
            data_U, lat_u, lon_u = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)       
            data_V, lat_v, lon_v = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)

            if flag==2:
                lon_u=lon_u-360
                lon_v=lon_v-360               
            lon_u=lon_u[0,:]
            lat_u=lat_u[:,0]
            lat_u=lat_u[::-1]
            lon,lat=np.meshgrid(lon_u ,lat_u)
            #linha=data_U.shape[0]
            #coluna=data_U.shape[1]   

        if flag==3:        
            lons1_ini=lons1+360          
            lons2_ini=360
            lons1_fim=0          
            lons2_fim=lons2

            data_U_ini, lat_u_ini, lon_u_ini = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            data_V_ini, lat_v_ini, lon_v_ini = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)

            lon_u_ini=lon_u_ini[0,:]
            lon_u_ini=lon_u_ini-360
            lat_u_ini=lat_u_ini[:,0]
            lat_u_ini=lat_u_ini[::-1]          

            data_U_fim, lat_u_fim, lon_u_fim = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            data_V_fim, lat_v_fim, lon_v_fim = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)

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

            #linha=data_U.shape[0]
            #coluna=data_U.shape[1] 

        linha=data_U.shape[0]
        coluna=data_U.shape[1]    
        vento_resultante=self.criaResultanteKnot(data_U, data_V)        
        angMET=self.criaAngMET(data_U, data_V)
        hMET=self.converte_altitude(nivel)

        w.writerow([ "lat", "lon", "hMET<feet>", "angMET<grau>", "vento_resultante<knot>" ])

        for i in range(linha):
            for j in range(coluna):
                #comentando a linha que escreve a matriz                   
                w.writerow([ lat[i,j], lon[i,j], hMET, angMET[i,j], vento_resultante[i,j] ])                                
                    
        f.close()
    
    def gera_matriz_vento_predi(self, varMET_AUX_u, varMET_AUX_v, varMET_AUX_temp, lonmin, lonmax, latmin, latmax, ana, prev, regiao, nivel, saida):    
         
        lons1=lonmin
        lons2=lonmax
        lats1=latmin
        lats2=latmax

        if 0<=lons1<180 and 0<=lons2<180:
            flag=1
        
        if -180<=lons1<0 and -180<=lons2<0:
            lons1=lons1+360
            lons2=lons2+360
            flag=2

        if -180<=lons1<0 and 0<=lons2<180:
            flag=3    
                    
        f = open(saida + "matriz_vento_predi" + "_" + regiao  + "_" + "N" +str(nivel) + "_" + ana + "_" + str(varMET_AUX_u.dataDate) + "_" + prev  + '.csv', 'w', newline='', encoding='utf-8')
        w = csv.writer(f)

        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)               
            #Faz a aquisição dos dados de vento U, V e t
            data_U, lat_u, lon_u = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_V, lat_v, lon_v = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_T, lat_t, lon_t = varMET_AUX_temp.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            
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

            data_U_ini, lat_u_ini, lon_u_ini = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            data_V_ini, lat_v_ini, lon_v_ini = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini)
            data_T_ini, lat_t_ini, lon_t_ini = varMET_AUX_temp.data(lat1=lats1,lat2=lats2,lon1=lons1_ini,lon2=lons2_ini) 

            lon_u_ini=lon_u_ini[0,:]
            lon_u_ini=lon_u_ini-360
            lat_u_ini=lat_u_ini[:,0]
            lat_u_ini=lat_u_ini[::-1]          

            data_U_fim, lat_u_fim, lon_u_fim = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            data_V_fim, lat_v_fim, lon_v_fim = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim)
            data_T_fim, lat_t_fim, lon_t_fim = varMET_AUX_temp.data(lat1=lats1,lat2=lats2,lon1=lons1_fim,lon2=lons2_fim) 

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
        w.writerow([ "lat", "lon", "vento U", "vento V", "temperatura K" ])
        for i in range(linha):
            for j in range(coluna):                                
                w.writerow([ lat[i,j], lon[i,j], data_U[i,j], data_V[i,j], data_T[i,j] ])
        
        f.close()
            
    # =============================================================================
    def processamento_dados_e_gerador_matrizes(self):
        
        # =============================================================================
        # verificacao de variaveis MET de vento
        # "wind" deve ser decomposta em "u" e "v"
        # "winds" deve ser decomposta em "uSupe" e "vSupe"
        # "wind" leva a decomposicao de "u"e "v" e a niveis de pressao em hPa
        # "winds" leva a decomposicao em "uSupe" e "vSupe" em niveis de altitude sendo muito proximos do solo...
        # ..."winds" e um pseudo-vento superficial aproximado para as camadas mais proximas da superficie          
        # =============================================================================                

        # =============================================================================
        # pegando as variaveis vento ("u" e "v") e temperatura
        # =============================================================================

        if self.varMET=="wind":
            varMET_AUX_u=processamento_dados_met_MAN("u", self.ano, self.mes, self.dia, self.ana, self.prev, self.nivel).define_var_com_nivel_ou_superficie()
            varMET_AUX_v=processamento_dados_met_MAN("v", self.ano, self.mes, self.dia, self.ana, self.prev, self.nivel).define_var_com_nivel_ou_superficie()
            varMET_AUX_temp=processamento_dados_met_MAN("temp", self.ano, self.mes, self.dia, self.ana, self.prev, self.nivel).define_var_com_nivel_ou_superficie()      
              
        # =============================================================================
        # gera uma matriz de vento simples        
        # =============================================================================
            self.gera_matriz_vento(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, self.nivel, self.saida)
        # =============================================================================
        # ventos para BlueSky
        # var impressas: <lat[deg]> <lon[deg]> <alt[feet]> <angMET[deg]> <VResul[m**s-1]>
        #(objMET, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.varMET, self.regiao, self.nivel, self.saida)
            self.gera_matriz_vento_bluesky(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, self.nivel, self.saida)
        # =============================================================================
    
        # =============================================================================
        # ventos e temperatura para o preditor
        # Para situacoes no nivel escolhido pelo usuario ou automacao 
            self.gera_matriz_vento_predi(varMET_AUX_u, varMET_AUX_v, varMET_AUX_temp, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, self.nivel, self.saida)
        # =============================================================================

        if self.varMET=="winds":
            for nivelVento in self.varNivelProxSupe:
                varMET_AUX_u=processamento_dados_met_MAN("uSupe", self.ano, self.mes, self.dia, self.ana, self.prev, nivelVento).define_var_com_nivel_ou_superficie()
                varMET_AUX_v=processamento_dados_met_MAN("vSupe", self.ano, self.mes, self.dia, self.ana, self.prev, nivelVento).define_var_com_nivel_ou_superficie()
                varMET_AUX_temp=processamento_dados_met_MAN("temps", self.ano, self.mes, self.dia, self.ana, self.prev, self.nivel).define_var_com_nivel_ou_superficie()      
                
        # =============================================================================
        # gera uma matriz de vento simples        
        # =============================================================================
                self.gera_matriz_vento(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, nivelVento, self.saida)
        # =============================================================================
        # ventos para BlueSky
        # var impressas: <lat[deg]> <lon[deg]> <alt[feet]> <angMET[deg]> <VResul[m**s-1]>
        #(objMET, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.varMET, self.regiao, self.nivel, self.saida)
                self.gera_matriz_vento_bluesky(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, nivelVento, self.saida)
        # =============================================================================
    
        # =============================================================================
        # ventos e temperatura para o preditor
        # Para situacoes no nivel escolhido pelo usuario ou automacao 
                self.gera_matriz_vento_predi(varMET_AUX_u, varMET_AUX_v, varMET_AUX_temp, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, nivelVento, self.saida)
        # =============================================================================            
        

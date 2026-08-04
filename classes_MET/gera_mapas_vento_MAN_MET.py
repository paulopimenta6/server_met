#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 17 15:55:18 2021

@author: phpimenta
"""

import matplotlib
matplotlib.use('Agg')
from matplotlib import rc
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
from processamento_dados_MET import processamento_dados_met_MAN

class met_gera_mapas_vento_man:
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
        self.regiao="LonMin:"+str(self.lonmin)+"LonMax:"+str(self.lonmax)+"LatMin:"+str(self.latmin)+"LatMax:"+str(self.latmax) 
        self.varNivelProxSupe=[20, 30, 40, 50, 80]

    def gera_mapas_vento_LC(self, varMET_AUX_u, varMET_AUX_v, lonmin, lonmax, latmin, latmax, ana, prev, regiao, nivel, saida):       
        
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

        # =============================================================================
        # Aqui começa o processamento de dados de acordo com as coordenadas fornecidas
        # =============================================================================
        
        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)

            data_U, lat_u, lon_u = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_V, lat_v, lon_v = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)            

            if flag==2:
                lon_u=lon_u-360
                lon_v=lon_v-360
            lon_u=lon_u[0,:]
            lat_u=lat_u[:,0]
            lat_u=lat_u[::-1]
            
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

        # =============================================================================
        # Aqui comeca a geracao dos mapas
        # =============================================================================

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

        fig1 = plt.figure(figsize =(18, 16))
        ax = fig1.add_axes([0.1,0.1,0.7,0.7])
        clevs = np.arange(960,1061,5)
        x,y=m(lons, lats)

        meridianinterval=np.arange(lon_min,lon_max,6)
        parallelsinterval=np.arange(lat_min,lat_max)    
        m.drawparallels(parallelsinterval,labels=[1,0,0,0], color='k',linewidth=.3)
        m.drawmeridians(meridianinterval,labels=[0,0,0,1],color='k',linewidth=.3)

        # =============================================================================
        # Comandos para criar mapas com LC
        # =============================================================================
        speed = np.sqrt(data_U**2+data_V**2)            
        strm=plt.streamplot(lons,lats,data_U,data_V,color=speed,linewidth = 1, cmap=plt.cm.inferno, density=5, arrowstyle='->', arrowsize = 1.5) 
        cb=plt.colorbar(strm.lines)
        cb.ax.set_ylabel("Vento m/s", fontsize = 14)
        # =============================================================================
        
        m.drawlsmask(land_color='tan', ocean_color='lightblue', lakes=True)
        
        try:
            m.drawcoastlines(linewidth=0.5)
        except:
            pass
    
        m.drawcountries(linewidth=0.25)
        m.drawcountries()
        m.drawstates()     
         
        plt.title("GFS " + str(varMET_AUX_u.iDirectionIncrementInDegrees) + " - " + str(regiao) + " - Vento [m/s]" + " - Nivel: " + str(nivel)  + " Analise: " + ana + " Data: " + str(varMET_AUX_u.dataDate) + " Prev: " + prev, weight="normal", fontsize=11)
        #Usar diretorio para salvar imagens        
        plt.savefig(saida + "GFS_" + str(varMET_AUX_u.iDirectionIncrementInDegrees) + "_" + str(regiao) + "_" + "N" + str(nivel) + "_" + "CampoVento_LC" + "_" + ana + "_" + str(varMET_AUX_u.dataDate) + "_" + prev + ".png",bbox_inches='tight')


    def gera_mapas_vento_barb(self, varMET_AUX_u, varMET_AUX_v, lonmin, lonmax, latmin, latmax, ana, prev, regiao, nivel, saida):       
        
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

        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)
            data_U, lat_u, lon_u = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_V, lat_v, lon_v = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)

            if flag==2:
                lon_u=lon_u-360
                lon_v=lon_v-360
            lon_u=lon_u[0,:]
            lat_u=lat_u[:,0]
            lat_u=lat_u[::-1]

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

        fig1 = plt.figure(figsize =(18, 16))
        ax = fig1.add_axes([0.1,0.1,0.7,0.7])
        clevs = np.arange(960,1061,5)
        x,y=m(lons, lats)

        meridianinterval=np.arange(lon_min,lon_max,6)
        parallelsinterval=np.arange(lat_min,lat_max)    
        m.drawparallels(parallelsinterval,labels=[1,0,0,0], color='k',linewidth=.3)
        m.drawmeridians(meridianinterval,labels=[0,0,0,1],color='k',linewidth=.3)

        # =============================================================================
        # Comandos para criar mapas com barb
        # =============================================================================       
        uproj,vproj,xx,yy=m.transform_vector(data_U,data_V,lon_u,lat_u,38,38,returnxy=True,masked=True)
        plt.barbs(xx, yy, uproj, vproj, pivot='middle', barbcolor='#333333')
        # =============================================================================

        m.drawlsmask(land_color='tan', ocean_color='lightblue', lakes=True)
        
        try:
            m.drawcoastlines(linewidth=0.5)
        except:
            pass
    
        m.drawcountries(linewidth=0.25)
        m.drawcountries()
        m.drawstates()
     
        #sera 12 temporariamente e nao str(hh_analise) 
        plt.title("GFS " + str(varMET_AUX_u.iDirectionIncrementInDegrees) + " - " + str(regiao) + " - Vento [m/s]" + " - Nivel: " + str(nivel)  + " Analise: " + ana + " Data: " + str(varMET_AUX_u.dataDate) + " Prev: " + prev, weight="normal", fontsize=11)
        #Usar diretorio para salvar imagens        
        plt.savefig(saida + "GFS_" + str(varMET_AUX_u.iDirectionIncrementInDegrees) + "_" + str(regiao) + "_" + "N" + str(nivel) + "_" + "CampoVento_barb" + "_" + ana + "_" + str(varMET_AUX_u.dataDate) + "_" + prev + ".png",bbox_inches='tight')
  
    def gera_mapas_vento_LCbarb(self, varMET_AUX_u, varMET_AUX_v, lonmin, lonmax, latmin, latmax, ana, prev, regiao, nivel, saida):       
        
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

        if flag==1 or flag==2:
            map = Basemap(projection='mill', lat_0=0, lon_0=0)
            data_U, lat_u, lon_u = varMET_AUX_u.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)
            data_V, lat_v, lon_v = varMET_AUX_v.data(lat1=lats1,lat2=lats2,lon1=lons1,lon2=lons2)

            if flag==2:
                lon_u=lon_u-360
                lon_v=lon_v-360
            lon_u=lon_u[0,:]
            lat_u=lat_u[:,0]
            lat_u=lat_u[::-1]
            
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
            lat_u=lat_u_ini
            lon_u=np.append(lon_u_ini, lon_u_fim)
            lon_v=lon_u
            data_U=np.zeros((data_U_ini.shape[0],data_U_ini.shape[1]+data_U_fim.shape[1]))
            data_V=np.zeros((data_V_ini.shape[0],data_V_ini.shape[1]+data_V_fim.shape[1]))
            print(lon_u) 
           
            if data_U_ini.shape[0]==data_U_fim.shape[0]:
                for i in range(0,data_U_ini.shape[0]):
                    data_U[i,:]=np.append(data_U_ini[i,:],data_U_fim[i,:])

            if data_V_ini.shape[0]==data_V_fim.shape[0]:
                for i in range(0,data_V_ini.shape[0]):
                    data_V[i,:]=np.append(data_V_ini[i,:],data_V_fim[i,:])         

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

        fig1 = plt.figure(figsize =(18, 16))
        ax = fig1.add_axes([0.1,0.1,0.7,0.7])
        clevs = np.arange(960,1061,5)
        x,y=m(lons, lats)

        meridianinterval=np.arange(lon_min,lon_max,6)
        parallelsinterval=np.arange(lat_min,lat_max)    
        m.drawparallels(parallelsinterval,labels=[1,0,0,0], color='k',linewidth=.3)
        m.drawmeridians(meridianinterval,labels=[0,0,0,1],color='k',linewidth=.3)

        # =============================================================================
        # Comandos para criar mapas com barbela e Linhas de corrente
        # =============================================================================
        speed = np.sqrt(data_U**2+data_V**2)            
        strm=plt.streamplot(lons,lats,data_U,data_V,color=speed,linewidth = 1, cmap=plt.cm.inferno, density=5, arrowstyle='->', arrowsize = 1.5) 
        cb=plt.colorbar(strm.lines)
        cb.ax.set_ylabel("Vento m/s", fontsize = 14)
        m.drawlsmask(land_color='tan', ocean_color='lightblue', lakes=True)

        uproj,vproj,xx,yy=m.transform_vector(data_U,data_V,lon_u,lat_u,38,38,returnxy=True,masked=True)
        plt.barbs(xx, yy, uproj, vproj, pivot='middle', barbcolor='#333333')
    
        try:
            m.drawcoastlines(linewidth=0.5)
        except:
            pass
    
        m.drawcountries(linewidth=0.25)
        m.drawcountries()
        m.drawstates()
     
        #sera 12 temporariamente e nao str(hh_analise) 
        plt.title("GFS " + str(varMET_AUX_u.iDirectionIncrementInDegrees) + " - " + str(regiao) + " - Vento [m/s]" + " - Nivel: " + str(nivel)  + " Analise: " + ana + " Data: " + str(varMET_AUX_u.dataDate) + " Prev: " + prev, weight="normal", fontsize=11)
        #Usar diretorio para salvar imagens        
        plt.savefig(saida + "GFS_" + str(varMET_AUX_u.iDirectionIncrementInDegrees) + "_" + str(regiao) + "_" + "N" + str(nivel) + "_" + "CampoVento_barbLC" + "_" + ana + "_" + str(varMET_AUX_u.dataDate) + "_" + prev + ".png",bbox_inches='tight')
                
    def processamento_dados_e_gerador_mapas(self):
        
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
        # =============================================================================
        # gera uma matriz de vento simples        
        # =============================================================================
            #self.gera_mapas_vento(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, self.nivel, self.saida)
            self.gera_mapas_vento_LC(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, self.nivel, self.saida)
            self.gera_mapas_vento_barb(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, self.nivel, self.saida)
            self.gera_mapas_vento_LCbarb(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, self.nivel, self.saida)

        if self.varMET=="winds":
            for nivelVento in self.varNivelProxSupe:
                varMET_AUX_u=processamento_dados_met_MAN("uSupe", self.ano, self.mes, self.dia, self.ana, self.prev, nivelVento).define_var_com_nivel_ou_superficie()
                varMET_AUX_v=processamento_dados_met_MAN("vSupe", self.ano, self.mes, self.dia, self.ana, self.prev, nivelVento).define_var_com_nivel_ou_superficie()                
        # =============================================================================
        # gera uma matriz de vento simples        
        # =============================================================================
                #self.gera_mapas_vento(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, nivelVento, self.saida)
                self.gera_mapas_vento_LC(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, nivelVento, self.saida)
                self.gera_mapas_vento_barb(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, nivelVento, self.saida)
                self.gera_mapas_vento_LCbarb(varMET_AUX_u, varMET_AUX_v, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.regiao, nivelVento, self.saida)  

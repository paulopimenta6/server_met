#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  8 19:31:22 2021

@author: phpimenta
"""
import matplotlib
matplotlib.use('Agg')
from matplotlib import rc
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import numpy as np
from processamento_dados_MET import processamento_dados_met_MAN

class met_gera_mapas_man:
    
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
        
    def O(self, dataVars):
        
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

    
    def gera_mapas(self, objMET, lonmin, lonmax, latmin, latmax, ana, prev, varMET, regiao, nivel, saida):        
        
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
                    
        # =============================================================================
        # aqui e geracao de mapas, logo a grade pode sofrer um mesh aqui                     
        # =============================================================================
        lon,lat=np.meshgrid(lon ,lat)

        if varMET=="temp" or varMET=="temps":
            data=data-273.15            
        if varMET=="ps" or varMET=="prnm":    
            data=data/100            
 
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

        m = Basemap(projection='cyl',
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

        meridianinterval=np.arange(lon_min,lon_max,6)
        parallelsinterval=np.arange(lat_min,lat_max)    
        m.drawparallels(parallelsinterval,labels=[1,0,0,0], color='k',linewidth=.3)
        m.drawmeridians(meridianinterval,labels=[0,0,0,1],color='k',linewidth=.3)

        try:
            m.drawcoastlines(linewidth=0.5)
        except:
            pass
            
        m.drawcountries()
        m.drawstates()

        intervalo_valores=self.O(data)   
    
        contourf = m.contourf(x, y, np.squeeze(data),cmap='viridis', levels=intervalo_valores)
        cs1 = m.contour(x, y, np.squeeze(data),colors='k', levels=intervalo_valores, linewidths=0.2)

        plt.clabel(cs1,fmt='%d',fontsize=8)

        print(contourf)
        cbar=m.colorbar(contourf, location='right', pad="1%")
        cbar.set_label(unidade)
        plt.title("GFS " + str(objMET.iDirectionIncrementInDegrees) + " - " +  str(regiao) + " " + str(varMET) + " [" + str(unidade) + "]" + " - Nivel: " + str(nivel)  + " Analise: " + str(ana) + " Data: " + str(objMET.dataDate) + " Prev: " + prev, weight="normal", fontsize=12)
        #Usar diretorio para salvar imagens        
        plt.savefig(saida + "GFS_" + str(objMET.iDirectionIncrementInDegrees) + "_" + str(regiao) + "_" + "N" + str(nivel) + "_" + str(varMET) + "_" + str(ana) + "_" + str(objMET.dataDate) + "_" + prev + ".png",bbox_inches='tight')


    def processamento_dados_para_mapas(self):
        dadosVarComNivelMET=processamento_dados_met_MAN(self.varMET, self.ano, self.mes, self.dia, self.ana, self.prev, self.nivel)
        var_com_nivel_pretendido=dadosVarComNivelMET.define_var_com_nivel_ou_superficie()
        print("# =============================================================================")
        print("gerou dado para criar um mapa!")
        print(var_com_nivel_pretendido)
        print("# =============================================================================")
        return var_com_nivel_pretendido
    
    def gera_mapas_final(self):
        objMET=self.processamento_dados_para_mapas()        
        self.gera_mapas(objMET, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.varMET, self.regiao, self.nivel, self.saida)
    
    
    
    
    
    
    

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 12 01:12:16 2021

@author: phpimenta
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 28 09:17:29 2021

@author: paulopimenta
"""
from mpl_toolkits.basemap import Basemap
import numpy as np
import csv
from processamento_dados_MET import processamento_dados_met_MAN

class met_gera_matriz_man:
    
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
      
    def gera_matriz(self, objMET, lonmin, lonmax, latmin, latmax, ana, prev, varMET, regiao, nivel, saida):
        
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

        f = open(saida + "GFS_" + str(objMET.iDirectionIncrementInDegrees) + "_" + str(regiao) + "_" + "N" + str(nivel) + "_" + str(varMET) + "_" + ana + "_" + str(objMET.dataDate) + "_" + prev  + '.csv', 'w', newline='', encoding='utf-8')
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

        if varMET=="temp" or varMET=="temps":
            data=data-273.15
        if varMET=="ps" or varMET=="prnm":    
            data=data/100

        w.writerow(["lat", "lon", varMET])
        for i in range(linha):
            for j in range(coluna):
                w.writerow([lat[i,j], lon[i,j], data[i,j]])                
        f.close()

    def processamento_dados_para_matrizes(self):
        dadosVarComNivelMET=processamento_dados_met_MAN(self.varMET, self.ano, self.mes, self.dia, self.ana, self.prev, self.nivel)
        var_com_nivel_pretendido=dadosVarComNivelMET.define_var_com_nivel_ou_superficie()
        print("# =============================================================================")
        print("gerou dado para criar uma matriz!")
        print(var_com_nivel_pretendido)
        print("# =============================================================================")
        return var_com_nivel_pretendido        
        
    def gera_matriz_final(self):
        objMET=self.processamento_dados_para_matrizes()
        print(objMET)
        print(self.gera_matriz(objMET, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.varMET, self.regiao, self.nivel, self.saida))          
        self.gera_matriz(objMET, self.lonmin, self.lonmax, self.latmin, self.latmax, self.ana, self.prev, self.varMET, self.regiao, self.nivel, self.saida)        
        
      

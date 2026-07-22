#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 22 03:51:20 2021

@author: paulopimenta
"""
class met_ponto_regiao:
    
    def __init__(self, longitude, latitude):
        self.longitude=longitude
        self.latitude=latitude
        self.lon_ini=" "
        self.lon_fim=" "
        self.lat_ini=" "
        self.lat_fim=" "            
        self.lonlat=[]

    def limpa_longitude_latitude(self):
        
        self.lonlat=[]
        
        return self.lonlat        

    def verifica_longitude(self):        
        
        if(self.longitude<=0 and self.latitude>=-180):
            self.lon_fim=self.longitude+5
            if self.lon_fim<=-180:
                self.lon_fim=abs(180+self.lon_fim)
        self.lon_ini=self.longitude-5
        
        if(self.longitude>=0 and self.latitude<=180):
            self.lon_ini=self.longitude-5
            self.lon_fim=self.longitude+5
            if self.lon_fim >180:
                self.lon_fim=abs(180-self.lon_fim)
                
        return self.lon_ini, self.lon_fim        
             
    def verifica_latitude(self):
        if(self.latitude<=85 and self.latitude>=-85):
            self.lat_ini=self.latitude-5
            self.lat_fim=self.latitude+5
        else:
            if(self.latitude>85):
                self.latitude=85
                self.lat_ini=self.latitude-5
                self.lat_fim=self.latitude+5
            if(self.latitude<-85):
                self.latitude=-85
                self.lat_ini=self.latitude-5
                self.lat_fim=self.latitude+5
                
        return self.lat_ini, self.lat_fim

    def imprime_longitude_latitude(self):
        self.limpa_longitude_latitude()
        self.lonlat.append(self.verifica_longitude())
        self.lonlat.append(self.verifica_latitude())

        return self.lonlat


    
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  2 02:09:52 2021

@author: phpimenta
"""

class met_poligono_regiao:
    
    def __init__(self, lonmin, lonmax, latmin, latmax):
        self.lonmin=lonmin
        self.lonmax=lonmax
        self.latmin=latmin
        self.latmax=latmax   
        
    def valida_longitude(self):
        if -180<=self.lonmin<=180 and -180<=self.lonmax<=180:
            if self.lonmin < self.lonmax:
                return True
            else:
                return False
        else:
            return False    
            
    def valida_latitude(self):
        if -90<=self.latmin<=90 and -90<=self.latmax<=90:
            if self.latmin<self.latmax:
                return True
            else:
                return False
        else:
            return False                
                
    def cria_poligono(self):               
        if self.valida_longitude() and self.valida_latitude():
            return self.lonmin, self.lonmax, self.latmin, self.latmax       
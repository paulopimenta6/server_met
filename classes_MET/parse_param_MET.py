#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul  3 10:16:27 2021

@author: paulopimenta
"""

class parse_param:
    
    def __init__(self, param):
        #self.param=param[1:]
        #self.varMET=" "
        #self.varNivel=" "
        #self.varRegiao=" "
        
        self.param=param[1:]
        self.varMET=None
        self.varNivel=None
        self.varRegiao=None        
        
    def converte_feet_to_hPa(self, halt):
    
        Psta=((1-(halt/145366.45))**(1/0.19028))*1013.25
        return (Psta)       
        
    def imprime_parse(self):       
        if len(self.param)>1:
            if "-v" in self.param:
                if isinstance(self.param[self.param.index("-v")+1], str): 
                    idx_varMET=self.param.index("-v")
                    varMET=str(self.param[idx_varMET+1])
            if "-n" in self.param or "-ns" in self.param:
                if "-n" in self.param:
                    if type(int(self.param[self.param.index("-n")+1]))==int:
                        idx_nivel=self.param.index("-n")
                        varNivel=int(self.param[idx_nivel+1])
                if "-ns" in self.param: 
                        varNivel="surface"
            if "-r" in self.param or "-ll" in self.param:
                if "-r" in self.param:
                    if isinstance(self.param[self.param.index("-r")+1], str):
                        idx_reg=self.param.index("-r")  
                        varRegiao=str(self.param[idx_reg+1])
                if "-ll" in self.param:
                    if type(int(self.param[self.param.index("-ll")+1]))==int and type(int(self.param[self.param.index("-ll")+2]))==int:
                        idx_lonlat=self.param.index("-ll")
                        varRegiao=self.param[idx_lonlat+1],self.param[idx_lonlat+2]                       
     
        return varMET, varNivel, varRegiao
        
    def imprime_parse_SemVarMETParam(self):
        
        if len(self.param)>1:
            if self.param[0]=="-n" or self.param[0]=="--nivel":
                self.varNivel=int(self.param[1])
                if self.param[2]=="-r" or self.param[2]=="--regiao":
                    self.varRegiao=self.param[3]
                elif self.param[2]=="-ll" or self.param[2]=="--latlon":
                    self.varRegiao=self.param[3],self.param[4]
                else:
                    self.varRegiao=-1
                    print("Variavel Regiao vazia")
            else:
                self.varNivel=1
                print("Variavel Nivel vazia")
        else:
            print("Sem parametros")                     
     
        if self.varNivel!=-1 and self.varRegiao!=-1:
            return self.varNivel, self.varRegiao

    def imprime_parse_SemVarMETParamSemNivel(self):        
        if len(self.param)>1:                
            if self.param[0]=="-r" or self.param[0]=="--regiao":
                self.varRegiao=self.param[1]
            elif self.param[0]=="-ll" or self.param[0]=="--latlon":
                    self.varRegiao=self.param[1],self.param[2]
            else:
                self.varRegiao=-1
                print("Variavel Regiao vazia")
        else:
            print("Sem parametros")                     
     
        if self.varRegiao!=-1:
            return self.varRegiao

    def imprime_parse_MAN(self):
        
        #-------------------------------------------------------------------
        nivel=None
        flag=None
        #-------------------------------------------------------------------
        if "-v" in self.param:
            if isinstance(self.param[self.param.index("-v")+1], str):
                idx_varMET=self.param.index("-v")
                varMET=str(self.param[idx_varMET+1])
                #print("Variavel MET: %s" %varMET)
        
        #-------------------------------------------------------------------
        #coordenadas geograficas
        if "-lonmin" in self.param:
            
            #print("Lon min: ")
            if type(float(self.param[self.param.index("-lonmin")+1]))==float or type(int(self.param[self.param.index("-lonmin")+1]))==int:     
                idx_lonmin=self.param.index("-lonmin")
                lonmin=float(self.param[idx_lonmin+1])    
                #print("Longitude minima: %f" %lonmin)
        
        if "-lonmax" in self.param:
            if type(float(self.param[self.param.index("-lonmax")+1]))==float or type(int(self.param[self.param.index("-lonmax")+1]))==int:
                idx_lonmax=self.param.index("-lonmax")
                lonmax=float(self.param[idx_lonmax+1])
                #print("Longitude maxima: %f" %lonmax)
        
        if  "-latmin" in self.param:
            if type(float(self.param[self.param.index("-latmin")+1]))==float or type(int(self.param[self.param.index("-latmin")+1]))==int:
                idx_latmin=self.param.index("-latmin")
                latmin=float(self.param[idx_latmin+1])
                #print("Latitude minima: %f" %latmin)
        
        if  "-latmax" in self.param:
            if type(float(self.param[self.param.index("-latmax")+1]))==float or type(int(self.param[self.param.index("-latmax")+1]))==int:
                idx_latmax=self.param.index("-latmax")
                latmax=float(self.param[idx_latmax+1])
                #print("Latitude maxima: %f" %latmax)
        
        #-------------------------------------------------------------------
        if "-nf" in self.param or "-nhpa" in self.param:
            if "-nf" in self.param:
                if type(int(self.param[self.param.index("-nf")+1]))==int:
                    idx_nivel=self.param.index("-nf")
                    nivel=int(self.converte_feet_to_hPa(float(self.param[idx_nivel+1])))    
                    #print("Altitude em pressao em hPa: %d" %nivel)
        
            if "-nhpa" in self.param:
                #print("altitude iniciada em hPa: ")
                if type(int(self.param[self.param.index("-nhpa")+1]))==int:
                    idx_nivel=self.param.index("-nhpa")
                    nivel=int(self.param[idx_nivel+1])
                    #print("Altitude em pressao em hPa: %d" %nivel)
        
        elif ("-altminfeet" in self.param and "-altmaxfeet" in self.param) or ("-altminhpa" in self.param and "-altmaxhpa" in self.param):
            if "-altminfeet" in self.param:
                if type(int(self.param[self.param.index("-altminfeet")+1]))==int:
                    idx_altminfeet=self.param.index("-altminfeet")
                    altmin=int(self.converte_feet_to_hPa(int(self.param[idx_altminfeet+1])))
                    #print("Longitude minima em hPa (transformado de feet): %d" %altmin)
        
            if "-altmaxfeet" in self.param:
                if type(int(self.param[self.param.index("-altmaxfeet")+1]))==int:
                    idx_altmaxfeet=self.param.index("-altmaxfeet")
                    altmax=int(self.converte_feet_to_hPa(int(self.param[idx_altmaxfeet+1])))
                    #print("Longitude maxima em hPa (transformado de feet): %d" %altmax)
        
            if "-altminhpa" in self.param:
                if type(int(self.param[self.param.index("-altminhpa")+1]))==int:
                    idx_altminhpa=self.param.index("-altminhpa")
                    altmin=int(self.param[idx_altminhpa+1])
                    #print("Longitude minima em hPa: %d" %altmin)
        
            if "-altmaxhpa" in self.param:
                if type(int(self.param[self.param.index("-altmaxhpa")+1]))==int:
                    idx_altmaxhpa=self.param.index("-altmaxhpa")
                    altmax=int(self.param[idx_altmaxhpa+1])
                    #print("Longitude maxima em hPa: %d" %altmax)
                    
        elif "-ns" in self.param:
            nivel="surface"        

        #-------------------------------------------------------------------
        #data
        if "-datetime" in self.param:
            if type(int(self.param[self.param.index("-datetime")+1]))==int: 
                idx_date=self.param.index("-datetime")
                date=str(self.param[idx_date+1])
                #print("Data do usuario: %d" %date)
        
        #-------------------------------------------------------------------
        #saida
        if "-out" in self.param:
            if isinstance(self.param[self.param.index("-out")+1], str):
                idx_saida=self.param.index("-out") 
                saida=self.param[idx_saida+1]    
                #print("Saida do arquivo: %s" %saida)
                
        if type(nivel) is str:
            flag=1
            print("# =============================================================================")
            print("Variavel MET: %s" %varMET)
            print("Longitude minima: %f" %lonmin)
            print("Longitude maxima: %f" %lonmax)
            print("Latitude minima: %f" %latmin)
            print("Latitude maxima: %f" %latmax)
            print("O nivel: %s" %nivel)
            print("Data do usuario: %s" %date)
            print("Saida do arquivo: %s" %saida)
            print("# =============================================================================")            
            return flag, varMET, lonmin, lonmax, latmin, latmax, nivel, date, saida         
        elif nivel is not None and type(nivel) is not str:
            flag=2
            print("# =============================================================================")
            print("Variavel MET: %s" %varMET)
            print("Longitude minima: %f" %lonmin)
            print("Longitude maxima: %f" %lonmax)
            print("Latitude minima: %f" %latmin)
            print("Latitude maxima: %f" %latmax)
            print("Altitude em pressao em hPa: %d" %nivel)
            print("Data do usuario: %s" %date)
            print("Saida do arquivo: %s" %saida)
            print("# =============================================================================")
            return flag, varMET, lonmin, lonmax, latmin, latmax, nivel, date, saida
        elif nivel is None:
            flag=3
            print("# =============================================================================")
            print("Variavel MET: %s" %varMET)
            print("Longitude minima: %f" %lonmin)
            print("Longitude maxima: %f" %lonmax)
            print("Latitude minima: %f" %latmin)
            print("Latitude maxima: %f" %latmax)
            print("Altitude minima: %d" %altmin)
            print("Altitude maxima: %d" %altmax)
            print("Data do usuario: %s" %date)
            print("Saida do arquivo: %s" %saida)
            print("# =============================================================================")            
            return flag, varMET, lonmin, lonmax, latmin, latmax, altmin, altmax, date, saida

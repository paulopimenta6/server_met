#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 22 06:02:44 2021

@author: paulopimenta
"""
from leitura_dados_grib_MET import leitura_dados_gribs_AUT, leitura_dados_gribs_MAN

# =============================================================================
# Inicio da classe
# =============================================================================
class processamento_dados_met_AUT:
    
    def __init__(self, varMET, nivel=None):
        
        self.varMET=varMET 
        self.nivel=nivel                                   
        self.dict_var_met={"ps": ["Surface pressure", "surface"],
                            "prnm": ["Pressure reduced to MSL", "meanSea"],
                            "temp": ["Temperature", "isobaricInhPa"],
                            "temps": ["Temperature", "surface"],
                            "nuvem": ["Total Cloud Cover", "isobaricInhPa"],                            
                            "chuvaNaoConvec": ["Total Precipitation", "surface"],
                            "chuvaConvec": ["Convective precipitation (water)", "surface"],  
                            "umidadeRel": ["Relative humidity", "isobaricInhPa"],
                            "u": ["U component of wind", "isobaricInhPa"],
                            "v": ["V component of wind", "isobaricInhPa"],
                            "uSupe": ["U component of wind", "heightAboveGround"],
                            "vSupe": ["V component of wind", "heightAboveGround"]}

        self.varMET_dict=self.dict_var_met[varMET][0] 
        self.tipo_nivel_dict=self.dict_var_met[varMET][1]
        
        print(self.varMET_dict, self.tipo_nivel_dict)
        
        self.obj_GRIBS=leitura_dados_gribs_AUT().imprime_lista_obj_gribs_AUT()        

# =============================================================================
# Aqui recebera os objetos de leitura do GRIB
# Uma lista de objetos sera adquirida, serao 4 objetos referente aos arquivos GRIBs...
# ...de 00 06 12 18 horas. Lembrando que as propriedades de um vale para todos, desde que...
# ...sejam da mesma variavel MET  
# =============================================================================    
      
# =============================================================================
# Verificacao de nivel
# =============================================================================

    def define_lista_var_com_nivel_pressao(self):
        self.lista_var_met=[]
        self.lista_niveis=[]
        self.lista_var_com_niveis_pres_hPa_aceitaveis=[]
        i=0
        j=i+1

        for self.grb in self.obj_GRIBS:                   
            self.lista_var_met=self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict)
    
            if len(self.lista_var_met)>2:
                for n in self.lista_var_met:
                    if n.level >= 150:
                        self.lista_niveis.append(n.level)                            
                #=============================================================================
                if self.nivel>=self.lista_niveis[0] and self.nivel<=self.lista_niveis[len(self.lista_niveis)-1]:             
                    while i<=(len(self.lista_niveis)-2):
                        if self.lista_niveis[i]<=self.nivel<=self.lista_niveis[j]:
                            media=(self.lista_niveis[i]+self.lista_niveis[j])/2
                            if self.nivel>=media:
                                self.nivel=self.lista_niveis[j]
                                break
                            else:
                                self.nivel=self.lista_niveis[i]
                                break
                    
                        i=i+1            
                        j=i+1
                        
                else:
                    #recebera o nivel padrao quando for fora do intervalo                               
                    self.nivel=self.lista_var_met[0].level
                
                self.lista_var_com_niveis_pres_hPa_aceitaveis.append(self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=self.nivel)[0])
                    
            else:
                print("So ha um nivel para o tipo de nivel: " + self.tipo_nivel_dict)
                nivel_escolhido=self.lista_var_met[0].level
                self.lista_var_com_niveis_pres_hPa_aceitaveis.append(self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=nivel_escolhido)[0])            
                        
            self.lista_niveis=[]        
        
        print(self.lista_var_com_niveis_pres_hPa_aceitaveis)
        return self.lista_var_com_niveis_pres_hPa_aceitaveis
    
    def define_lista_var_com_altitude(self): #nivel de quase-superficie
        self.lista_var_met=[]
        self.lista_niveis=[]
        self.lista_var_com_niveis=[]
        i=0
        j=i+1

        for self.grb in self.obj_GRIBS:     
            self.lista_var_met=self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict)
    
            if len(self.lista_var_met)>2:
                for n in self.lista_var_met:
                    print(n.level)
                    if n.level <= self.lista_var_met[len(self.lista_var_met)-1].level: 
                        self.lista_niveis.append(n.level)

                print("GRIB e lista de nivel:...")
                print(self.grb)
                print(self.lista_niveis)                                                               
                
                if self.nivel>=self.lista_niveis[0] and self.nivel<=self.lista_niveis[len(self.lista_niveis)-1]:             
                    while i<=(len(self.lista_niveis)-2):
                        if self.lista_niveis[i]<=self.nivel<=self.lista_niveis[j]:
                            media=(self.lista_niveis[i]+self.lista_niveis[j])/2
                            if self.nivel>=media:
                                self.nivel=self.lista_niveis[j]
                                break
                            else:
                                self.nivel=self.lista_niveis[i]
                                break                    
                        i=i+1            
                        j=i+1                        
                else:
                    self.nivel=self.lista_var_met[0].level           
                
                self.lista_var_com_niveis.append(self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=self.nivel)[0])
    
            else:
                print("So ha um nivel para o tipo de nivel: " + self.tipo_nivel_dict)
                nivel_escolhido=self.lista_var_met[0].level
                self.lista_var_com_niveis.append(self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=nivel_escolhido)[0])            
            
            self.lista_niveis=[]
            
        print(self.lista_var_com_niveis)
        return self.lista_var_com_niveis

    def define_lista_var_com_nivel_superficie(self):
        #self.lista_var_met=[]
        lista_var_com_nivel=[]

        for self.grb in self.obj_GRIBS:
            if self.tipo_nivel_dict=="surface" or self.tipo_nivel_dict=="meanSea":
                #var_met=self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict)
                try:
                    var_met=self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict)[0]                      
                #except ValueError:
                except ValueError:   
                    print("Nao ha chuva para Analise: ")
                    print(self.grb)
                else:
                    nivel_escolhido=var_met.level
                    lista_var_com_nivel.append(self.grb.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=nivel_escolhido)[0])
      
        return lista_var_com_nivel

    def imprime_nivel(self):        
        print("No interior da funcao imprime_nivel")
        print("tamanho do vetor de objetos de Gribs: %d" %(len(self.obj_GRIBS)))
        print(self.define_lista_var_com_nivel_pressao())
        
class processamento_dados_met_MAN:    
    def __init__(self, varMET, ano, mes, dia, ana, prev, nivel):
        
        self.varMET=varMET
        self.ano=ano
        self.mes=mes
        self.dia=dia
        self.ana=ana
        self.prev=prev
        self.nivel=nivel                                   
        self.dict_var_met={"ps": ["Surface pressure", "surface"],
                            "prnm": ["Pressure reduced to MSL", "meanSea"],
                            "temp": ["Temperature", "isobaricInhPa"],
                            "temps": ["Temperature", "surface"],
                            "nuvem": ["Total Cloud Cover", "isobaricInhPa"],                            
                            "chuvaNaoConvec": ["Total Precipitation", "surface"],
                            "chuvaConvec": ["Convective precipitation (water)", "surface"],
                            "umidadeRel": ["Relative humidity", "isobaricInhPa"],                            
                            "u": ["U component of wind", "isobaricInhPa"],
                            "v": ["V component of wind", "isobaricInhPa"],
                            "uSupe": ["U component of wind", "heightAboveGround"],
                            "vSupe": ["V component of wind", "heightAboveGround"]}

        self.varMET_dict=self.dict_var_met[varMET][0] 
        self.tipo_nivel_dict=self.dict_var_met[varMET][1]
        self.obj_GRIB=leitura_dados_gribs_MAN(self.ano, self.mes, self.dia, self.ana, self.prev).imprime_obj_grib_MAN() #passar ano, mes, dia, ana, prev       
        
    def define_var_com_nivel_ou_superficie(self):
        if type(self.nivel)!=str:
            print("tem mais de um nivel")
            self.var_met_com_nivel=self.obj_GRIB.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=self.nivel)[0]       
        else:
            print("tem somente o nivel de superficie")
            if self.tipo_nivel_dict=="surface" or self.tipo_nivel_dict=="meanSea":
                self.var_met_com_nivel_superficie=self.obj_GRIB.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict)    
                print("tipo de nivel: " + self.tipo_nivel_dict)
                nivel_escolhido=self.var_met_com_nivel_superficie[0].level
                self.var_met_com_nivel=self.obj_GRIB.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=nivel_escolhido)[0]
        
        print("# =============================================================================")                 
        print("#conseguiu processar o dado")
        print(self.var_met_com_nivel)
        print("# =============================================================================")
        return self.var_met_com_nivel        

    def define_var_com_nivel(self):
        if type(self.nivel)!=str:
            print("tem mais de um nivel")
            self.var_met_com_nivel=self.obj_GRIB.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=self.nivel)[0]   
                                           
        print(self.var_met_com_nivel)
        return self.var_met_com_nivel       
        
    def define_var_com_nivel_superficie(self):
        if self.tipo_nivel_dict=="surface" or self.tipo_nivel_dict=="meanSea":
            self.var_met_com_nivel_superficie=self.obj_GRIB.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict)    
            print("tipo de nivel: " + self.tipo_nivel_dict)
            nivel_escolhido=self.var_met_com_nivel_superficie[0].level
            self.var_com_nivel=self.obj_GRIB.select(name=self.varMET_dict, typeOfLevel=self.tipo_nivel_dict, level=nivel_escolhido)[0]            
                                        
        print(self.var_com_nivel)
        return self.var_com_nivel

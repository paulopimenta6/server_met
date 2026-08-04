#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import os.path
import time

# =============================================================================
#Exemplo de dicionario, keys e values:
#{'dir_gribs': '"/media/utrecht/12382BE468602ECF/goGrib/"',
# 'dir_mapas': '"/media/utrecht/12382BE468602ECF/goGrib/mapasGrib/"',
# 'dir_matrizes': '"/media/utrecht/12382BE468602ECF/goGrib/matrizeGrib/"',
# 'dir_matrizes_predi': '"/media/utrecht/12382BE468602ECF/goGrib/matrizeGrib/predi"',
# 'dir_matrizes_bluesky': '"/media/utrecht/12382BE468602ECF/goGrib/matrizeGrib/bluesky"'}
# =============================================================================

class controla_dirs_MET:
    def __init__(self):
        
        self.data_horario=time.localtime()
        self.ano=self.data_horario.tm_year
        self.mes=self.data_horario.tm_mon
        self.dia=self.data_horario.tm_mday
        self.hora=self.data_horario.tm_hour
        self.minuto=self.data_horario.tm_min

        if self.mes<10:
            self.mes="0"+str(self.mes)
        if self.dia<10:
            self.dia="0"+str(self.dia)

        self.var_data_dir=str(self.ano)+str(self.mes)+str(self.dia)
        
        self.dict_dirs={}
        archivo=open("../environment/path.conf")
        for linha in archivo.readlines():
            self.dict_dirs[linha.split("=")[0]]=linha.split("=")[1].strip("\n")
        print(self.dict_dirs)

    def hora_dirs(self):
        #Esta funcao tera objetivo de verificar se os diretorios existem...
        #...se sim, pular, se nao, criar diretorios
        lista_horario=["00","06","12","18"]
        i=0
        j=i+1

        while i<=len(lista_horario)-2:
            if int(lista_horario[i])<=int(self.hora)<int(lista_horario[j]):       
                self.hh=lista_horario[i]
            i=i+1
            j=i+1
        if int(self.hora)>=int(lista_horario[len(lista_horario)-1]):
            self.hh=lista_horario[len(lista_horario)-1]      

        print(self.hh)        
        return self.hh

    def imprime_dirGrib(self):
        print(self.dict_dirs["dir_gribs"]) 
        return self.dict_dirs["dir_gribs"]
    
    def imprime_dirMapas(self):
        hora_fct_diretorio=self.hora_dirs()        
        if os.path.exists(self.dict_dirs["dir_mapas"]):
            os.chdir(self.dict_dirs["dir_mapas"])
        else:
            os.mkdir(self.dict_dirs["dir_mapas"])
            os.chdir(self.dict_dirs["dir_mapas"])
            
        if os.path.exists(self.var_data_dir):
            os.chdir(self.var_data_dir)
        else:
            os.mkdir(self.var_data_dir)
            os.chdir(self.var_data_dir)
            
        if os.path.exists(hora_fct_diretorio):
            os.chdir(hora_fct_diretorio)
            dir_caminho_mapas=os.getcwd()
        else:        
            os.mkdir(hora_fct_diretorio)        
            os.chdir(hora_fct_diretorio)    
            dir_caminho_mapas=os.getcwd()
        
        print(dir_caminho_mapas + str("/"))
        return dir_caminho_mapas + str("/")
    
    def imprime_dirMatrizes(self):
        hora_fct_diretorio=self.hora_dirs()        
        if os.path.exists(self.dict_dirs["dir_matrizes"]):
            os.chdir(self.dict_dirs["dir_matrizes"])
        else:
            os.mkdir(self.dict_dirs["dir_matrizes"])
            os.chdir(self.dict_dirs["dir_matrizes"])
            
        if os.path.exists(self.var_data_dir):
            os.chdir(self.var_data_dir)
        else:
            os.mkdir(self.var_data_dir)
            os.chdir(self.var_data_dir)
            
        if os.path.exists(hora_fct_diretorio):
            os.chdir(hora_fct_diretorio)
            dir_caminho_matrizes=os.getcwd()
        else:        
            os.mkdir(hora_fct_diretorio)        
            os.chdir(hora_fct_diretorio)    
            dir_caminho_matrizes=os.getcwd()
        
        print(dir_caminho_matrizes + str("/"))
        return dir_caminho_matrizes + str("/")

    def imprime_dirMatrizesPredi(self):        
        hora_fct_diretorio=self.hora_dirs()        
        if os.path.exists(self.dict_dirs["dir_matrizes_predi"]):
            os.chdir(self.dict_dirs["dir_matrizes_predi"])
        else:
            os.mkdir(self.dict_dirs["dir_matrizes_predi"])
            os.chdir(self.dict_dirs["dir_matrizes_predi"])
            
        if os.path.exists(self.var_data_dir):
            os.chdir(self.var_data_dir)
        else:
            os.mkdir(self.var_data_dir)
            os.chdir(self.var_data_dir)
            
        if os.path.exists(hora_fct_diretorio):
            os.chdir(hora_fct_diretorio)
            dir_caminho_matrizes_predi=os.getcwd()
        else:        
            os.mkdir(hora_fct_diretorio)        
            os.chdir(hora_fct_diretorio)    
            dir_caminho_matrizes_predi=os.getcwd()
        
        print(dir_caminho_matrizes_predi + str("/"))
        return dir_caminho_matrizes_predi + str("/")
    
    def imprime_dirMatrizesBluesky(self):
        hora_fct_diretorio=self.hora_dirs()        
        if os.path.exists(self.dict_dirs["dir_matrizes_bluesky"]):
            os.chdir(self.dict_dirs["dir_matrizes_bluesky"])
        else:
            os.mkdir(self.dict_dirs["dir_matrizes_bluesky"])
            os.chdir(self.dict_dirs["dir_matrizes_bluesky"])
            
        if os.path.exists(self.var_data_dir):
            os.chdir(self.var_data_dir)
        else:
            os.mkdir(self.var_data_dir)
            os.chdir(self.var_data_dir)
            
        if os.path.exists(hora_fct_diretorio):
            os.chdir(hora_fct_diretorio)
            dir_caminho_matrizes_bluesky=os.getcwd()
        else:        
            os.mkdir(hora_fct_diretorio)        
            os.chdir(hora_fct_diretorio)    
            dir_caminho_matrizes_bluesky=os.getcwd()
        
        print(dir_caminho_matrizes_bluesky + str("/"))
        return dir_caminho_matrizes_bluesky + str("/")

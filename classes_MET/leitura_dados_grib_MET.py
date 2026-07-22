#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 29 01:59:54 2021

@author: phpimenta
"""
import os
import os.path
import time
import pygrib
from controla_env import controla_dirs_MET

dir_save=controla_dirs_MET()

class leitura_dados_gribs_AUT:
    
    def __init__(self):
        
        self.data_horario=time.localtime()
        self.ano=self.data_horario.tm_year
        self.mes=self.data_horario.tm_mon
        self.dia=self.data_horario.tm_mday
        self.hora=self.data_horario.tm_hour
        self.minuto=self.data_horario.tm_min

        self.prev_ana=["00", "06", "12", "18"]
        self.obj_lista_grib=[]
        self.lista_dir=[]
        self.lista_grib=[]

        print("ano: " + str(self.ano))
        print("mes: " + str(self.mes))
        print("dia: " + str(self.dia))
        print("hora: " + str(self.hora))
        print("minuto: " + str(self.minuto))

        if int(self.dia)<10:
            self.dia="0"+str(self.dia)
        if int(self.mes)<10:
            self.mes="0"+str(self.mes)

        self.var_data_dir=str(self.ano)+str(self.mes)+str(self.dia)
        print("data correspondente dos GRIBS do dia: " + self.var_data_dir)

    def limpa_lista_obj_gribs(self):
        self.obj_lista_grib=[]

    def imprime_lista_obj_gribs_AUT(self):        
        self.limpa_lista_obj_gribs()
        ###Entrando no diretorio Grib
        self.dir_grib_completo=dir_save.imprime_dirGrib()
        os.chdir(self.dir_grib_completo)
        ###Mostrando diretorio
        print("Diretorio de armazenamento dos GRIBS: " + self.dir_grib_completo)

        ###Verificando os arquivos e diretorios
        for elementos in os.listdir("."):
            if os.path.isdir(elementos):
                self.lista_dir.append(elementos)
            else:
                self.lista_grib.append(elementos)

        print("lista de diretorios: ")
        print(self.lista_dir)
        print("lista de arquivos no interior do diretorio de diretorios de GRIBS: ") 
        print(self.lista_grib)

        ###verificando a existencia do diretorio
        if os.path.exists(self.var_data_dir):
            os.chdir(self.var_data_dir)    
            print("entrou no diretorio dos GRIBS correspondentes do dia: " + self.var_data_dir)
            print(os.listdir("."))
            i=0
            j=i+1
                                    
            while i<=(len(self.prev_ana)-2):
                
                print((int(self.prev_ana[i])<=int(self.hora)<int(self.prev_ana[j])))
                print("%d<=%d<%d" %(int(self.prev_ana[i]), int(self.hora), int(self.prev_ana[j])))
                print("hora do primeiro GRIB de compracao: %d" %(int(self.prev_ana[i])))
                print("hora atual: %d" %(int(self.hora)))
                print("hora do segundo GRIB de compracao: %d " %(int(self.prev_ana[j])))
                
                if int(self.prev_ana[i])<=int(self.hora)<=int(self.prev_ana[j]): 
                   if os.path.exists(self.prev_ana[i]):
                       os.chdir(self.prev_ana[i])
                       print("entrou no diretorio: " + os.getcwd())
                       print("hora atual: " + str(self.hora))   
                       print(os.listdir(".")) 
                       for p in self.prev_ana:
                           #if os.path.exists("gfs.t" + self.prev_ana[i] + "z.pgrb2.0p25.f0" + p):
                           #    print("gfs.t" + self.prev_ana[i] + "z.pgrb2.0p25.f0" + p)                       
                           #   self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[i] + "z.pgrb2.0p25.f0" + p))
                           
                        try:
                            print("# =============================================================================")
                            print("GRIB de 0.25 grau")
                            self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[i] + "z.pgrb2.0p25.f0" + p))
                            print("# =============================================================================")
                        except OSError:
                            try:
                                print("# =============================================================================")
                                print("arquivo de GRIB de 0.25 grau nao foi encontrado...")
                                print("GRIB de 0.50 grau")
                                self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[i] + "z.pgrb2.0p50.f0" + p))
                                print("# =============================================================================")
                            except OSError:
                                try:
                                    print("# =============================================================================")
                                    print("arquivo de GRIB de 0.50 grau nao foi encontrado...")
                                    print("GRIB de 1.00 grau")
                                    self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[i] + "z.pgrb2.1p00.f0" + p))
                                    print("# =============================================================================")
                                except OSError:
                                    try:
                                        print("# =============================================================================")
                                        print("arquivo de GRIB de 1.00 grau nao foi encontrado...")
                                        print("GRIB de 1.00 grau do Lab MASTER")
                                        self.obj_lista_grib.append(pygrib.open("gfs" + self.ano + self.mes + self.dia + self.prev_ana[i] + "00_000.grb"))
                                        print("# =============================================================================")
                                    except OSError:
                                        print("# =============================================================================")
                                        print("arquivo de GRIB de 1.00 grau do laboratorio MASTER nao foi encontrado")
                                        print("# =============================================================================")                      
                                               
                i=i+1
                j=j+1
        
            if int(self.hora)>=int(self.prev_ana[len(self.prev_ana)-1]):        
                if os.path.exists(self.prev_ana[len(self.prev_ana)-1]):
                    os.chdir(self.prev_ana[len(self.prev_ana)-1])
                    print("entrou no diretorio: " + os.getcwd())
                    print("entrou na hora: " + str(self.hora)) 
                    print(os.listdir(".")) 
                    for p in self.prev_ana:                
                        #if os.path.exists("gfs.t" + self.prev_ana[len(self.prev_ana)-1] + "z.pgrb2.0p25.f0" + p):
                        #    print("gfs.t" + self.prev_ana[len(self.prev_ana)-1] + "z.pgrb2.0p25.f0" + p)
                        #    self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[len(self.prev_ana)-1] + "z.pgrb2.0p25.f0" + p))       
                        try:
                            print("# =============================================================================")
                            print("GRIB de 0.25 grau")
                            self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[len(self.prev_ana)-1] + "z.pgrb2.0p25.f0" + p))
                            print("# =============================================================================")
                        except OSError:
                            try:
                                print("# =============================================================================")
                                print("arquivo de GRIB de 0.25 grau nao foi encontrado...")
                                print("GRIB de 0.50 grau")
                                self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[len(self.prev_ana)-1] + "z.pgrb2.0p50.f0" + p))
                                print("# =============================================================================")
                            except OSError:
                                try:
                                    print("# =============================================================================")
                                    print("arquivo de GRIB de 0.50 grau nao foi encontrado...")
                                    print("GRIB de 1.00 grau")
                                    self.obj_lista_grib.append(pygrib.open("gfs.t" + self.prev_ana[len(self.prev_ana)-1] + "z.pgrb2.1p00.f0" + p))
                                    print("# =============================================================================")
                                except OSError:
                                    try:
                                        print("# =============================================================================")
                                        print("arquivo de GRIB de 1.00 grau nao foi encontrado...")
                                        print("GRIB de 1.00 grau da USP")
                                        self.obj_lista_grib.append(pygrib.open("gfs" + self.ano + self.mes + self.dia + self.prev_ana[len(self.prev_ana)-1] + "00_000.grb"))
                                        print("# =============================================================================")
                                    except OSError:
                                        print("# =============================================================================")
                                        print("arquivo de GRIB de 1.00 grau da USP nao foi encontrado")
                                        print("# =============================================================================")   
        
        if len(self.obj_lista_grib)>0:
            print(self.obj_lista_grib)
        print(len(self.obj_lista_grib))
        return self.obj_lista_grib
    
class leitura_dados_gribs_MAN:
    
    def __init__(self, ano, mes, dia, ana, prev):
        self.ano=ano
        self.mes=mes
        self.dia=dia
        self.ana=ana
        self.prev=prev
        self.obj_grib=None       

        print("ano: " + self.ano)
        print("mes: " + self.mes)
        print("dia: " + self.dia)
        print("Analise: " + self.ana)
        print("Previsao: " + self.prev)

        self.var_data_dir=str(self.ano)+str(self.mes)+str(self.dia)
        print("data correspondente dos GRIBS do dia: " + self.var_data_dir)

    def imprime_obj_grib_MAN(self):
        lista_dir=[]
        lista_grib=[]
        ###Entrando no diretorio Grib
        self.dir_grib_completo=dir_save.imprime_dirGrib()
        os.chdir(self.dir_grib_completo)
        ###Mostrando diretorio
        print("diretorio de armazenamento dos GRIBS: " + self.dir_grib_completo)

        ###Verificando os arquivos e diretorios
        for elementos in os.listdir("."):
            if os.path.isdir(elementos):
                lista_dir.append(elementos)
            else:
                lista_grib.append(elementos)

        print("lista de diretorios: ")
        print(lista_dir)
        print("lista de arquivos no interior do diretorio de diretorios de GRIBS: ") 
        print(lista_grib)


        ###verificando a existencia do diretorio
        if os.path.exists(self.var_data_dir):
            os.chdir(self.var_data_dir)    
            print("entrou no diretorio dos GRIBS correspondentes do dia: " + self.var_data_dir)
            print(os.listdir("."))
            
            if os.path.exists(self.ana):
                os.chdir(self.ana)
                print("entrou no diretorio: " + os.getcwd())
                print("Analise desejada: " + str(self.ana))
                print(os.listdir("."))
                #if os.path.exists("gfs.t" + self.ana + "z.pgrb2.0p25.f0" + self.prev):
                    #print("gfs.t" + self.ana + "z.pgrb2.0p25.f0" + self.prev)                       
                    #self.obj_grib=(pygrib.open("gfs.t" + self.ana + "z.pgrb2.0p25.f0" + self.prev))
                try:
                    print("# =============================================================================")
                    print("GRIB de 0.25 grau")
                    self.obj_grib=(pygrib.open("gfs.t" + self.ana + "z.pgrb2.0p25.f0" + self.prev))
                    print("# =============================================================================")
                except OSError:
                    try:
                        print("# =============================================================================")
                        print("arquivo de GRIB de 0.25 grau nao foi encontrado...")
                        print("GRIB de 0.50 grau")
                        self.obj_grib=(pygrib.open("gfs.t" + self.ana + "z.pgrb2.0p50.f0" + self.prev))
                        print("# =============================================================================")
                    except OSError:
                        try:
                            print("# =============================================================================")
                            print("arquivo de GRIB de 0.50 grau nao foi encontrado...")
                            print("GRIB de 1.00 grau")
                            self.obj_grib=(pygrib.open("gfs.t" + self.ana + "z.pgrb2.1p00.f0" + self.prev))
                            print("# =============================================================================")
                        except OSError:
                            try:
                                print("# =============================================================================")
                                print("arquivo de GRIB de 1.00 grau nao foi encontrado...")
                                print("GRIB de 1.00 grau do Lab MASTER")
                                self.obj_grib=(pygrib.open("gfs" + self.ano + self.mes + self.dia + self.ana + "00_000.grb"))
                                print("# =============================================================================")
                            except OSError:
                                print("# =============================================================================")
                                print("arquivo de GRIB de 1.00 grau do laboratorio MASTER nao foi encontrado")
                                print("# =============================================================================")                  
       
        print("# =============================================================================")
        print("entregando o objeto de GRIB de analise: %s e previsao: %s" %(self.ana,self.prev))
        print(self.obj_grib)
        print("# =============================================================================")
        return self.obj_grib
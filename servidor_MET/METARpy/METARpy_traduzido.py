#from decodMETAR import decodMetar
from GoMETAR import pegaMETAR
from datetime import datetime
import json

#Aerodromos importantes para obter metar:
#SP: SBGR
#RJ: SBGL
#CW: SBCT
#PA: SBPA
#BH: SBCF
#Belem: SBBE
#Manaus: SBBEG
#Recife: SBRF
#Fortaleza: SBFZ

dict_aerodromos={"SP": "SBGR", # Aeroporto de Guarulhos
                 "RJ": "SBGL", # Aeroporto do Galeao
                 "CW": "SBCT", # Aeroporto de Curitiba
                 "PA": "SBPA", # Aeroporto de Porto Alegre
                 "BH": "SBCF", # Aeroporto de Belo Horizonte
                 "BE": "SBBE", # Aeroporto de Belem
                 "MA": "SBEG",# Aeroporto de Manaus
                 "RF": "SBRF", # Aeroporto de Recife
                 "FZ": "SBFZ", # Aeroporto de Fortaleza
}

def cria_dados_nuvem(dados):
    #dados cod.imprime_nuvem()
    if dados is not None:        
        dict_nuvem_condicao={}
        dict_nuvem_condicao["nuvem"]=[]
        for i in range(len(dados)):         
            dict_nuvem_condicao["nuvem"].append({            
            "Tipo de nuvem ":  dados[i]["code"],
            "Tipo de nuvem (nome completo) ": dados[i]["meaning"],
            "Cobertura minima de nuvem [em oitavos]": str(dados[i]["oktaMin"]),
            "Cobertura maxima de nuvem [em oitavos]": str(dados[i]["oktaMax"]),
            "Altitude da nuvem [ft]": str(dados[i]["altitude"])
        })
        return dict_nuvem_condicao
    else:
        return "informacao ausente"
            
def cria_resultado_visibilidade(autoOunao, nuvem, visibilidade):    
    if str(autoOunao)=="False" and str(nuvem) is not None and str(visibilidade)=="9999":
        return "superior a 10000"
    elif str(autoOunao)=="False" and str(nuvem) is None and str(visibilidade)=="9999":
        return "10000"
    else:
        return visibilidade

def cria_json_metar_traduzido(sigla, data, cod, mens):

    dict_metar_traduzido={}
    dict_metar_traduzido["data"]=[]

    dict_metar_traduzido_vento={ 
        "vento [KT]": cod.imprime_vento_VEL(),
        "rajada [KT]": cod.imprime_vento_RAJ(),
        "direcao_do_vento [graus]": cod.imprime_vento_DIR(),
        "coordenada_da_direcao_do_vento": cod.imprime_vento_DIR_COOR(),
        "variacao_do_vento": cod.imprime_vento_VAR()
     }
    
    dict_metar_traduzido["data"].append({
    "estacao": sigla,
    "data" : data,
    "mensagem_metar" : mens,
    "temperatura [C]" : cod.imprime_temp(),
    "temperatura_pto_orvalho [C]": cod.imprime_tempPtoOrvalho(),
    "visibilidade [m]": cria_resultado_visibilidade(cod.imprime_estAuto(), cod.imprime_nuvem(), cod.imprime_visi()),
    "pressao_atmosferica [mb]": cod.imprime_PRES(),
    "condicao_nuvem" : cria_dados_nuvem(cod.imprime_nuvem()), 
    "vento" : dict_metar_traduzido_vento        
    })

    print(dict_metar_traduzido)
    x=json.dumps(dict_metar_traduzido)
    arquivo = open(sigla + data + "_traduzido.json", "a")
    arquivo.write(x)

for siglaReg in dict_aerodromos:
    codMetar=pegaMETAR(dict_aerodromos[siglaReg])
    siglaMETAR=codMetar.imprime_aerodromo()
    mensMETAR=codMetar.imprime_metar()  

    dataMETAR=codMetar.imprime_data()
    dataPy=datetime.now().strftime("%Y%m")
    data=dataPy + dataMETAR[0] + dataMETAR[1] + dataMETAR[2]    

    cria_json_metar_traduzido(siglaMETAR, data, codMetar, mensMETAR)

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

def cria_json_metar(sigla, data, mens):

    dict_metar={}
    dict_metar["data"]=[]
    dict_metar["data"].append({
    "id_localidade ": sigla,
    "data ": data,
    "mensagem_metar ": mens
    })

    print(dict_metar)    
    y=json.dumps(dict_metar)
    arquivo = open(sigla + data + ".json", "a")
    arquivo.write(y)

for siglaReg in dict_aerodromos:
    codMetar=pegaMETAR(dict_aerodromos[siglaReg])
    siglaMETAR=codMetar.imprime_aerodromo()
    mensMETAR=codMetar.imprime_metar()  

    dataMETAR=codMetar.imprime_data()
    dataPy=datetime.now().strftime("%Y%m")
    data=dataPy + dataMETAR[0] + dataMETAR[1] + dataMETAR[2]    

    cria_json_metar(siglaMETAR, data ,mensMETAR)


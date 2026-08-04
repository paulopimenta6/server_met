from PythonMETAR import *

class pegaMETAR:
    def __init__(self, aerodromo):
        self.aerodromo=aerodromo
        self.codMETAR=Metar(self.aerodromo)

#airport (string): ICAO code of METAR airport
#data_date (string): Date provided by NOAA server. None if text enter manually
#date_time (tuple): Tuple of date with day, hour & minutes
#wind (dictionary): Dictionary with wind information
#cloud (tuple): Tuple of dictionaries with cloud detected information
#temperatures (dictionary): Dictionary of integers with temperature and dewpoint information
#qnh (integer OR float): Information of QNH (integer if hPA, float if inHG)
#visibility(integer): Information about visibility

    def imprime_aerodromo(self):       
        #print(self.codMETAR.airport)
        return self.codMETAR.airport

    def imprime_dataNOAA(self):
        #print(self.codMETAR.data_date)
        return self.codMETAR.data_date 

    def imprime_data(self):
        #print(self.codMETAR.date_time)
        return self.codMETAR.date_time 

    def imprime_metar(self):
        #print(self.codMETAR)
        return self.codMETAR.metar

    def imprime_vento(self):
        #print(self.codMETAR.wind)
        #Direcao em graus
        return self.codMETAR.wind

    def imprime_vento_DIR(self):
        #print(self.codMETAR.wind)
        #Direcao em graus
        return self.codMETAR.wind["direction"]

    def imprime_vento_DIR_COOR(self):
        #print(self.codMETAR.wind)
        #Direcao em graus
        if type(self.codMETAR.wind["direction"]) is str:
            return self.codMETAR.wind["direction"]
        else:
            if self.codMETAR.wind["direction"]==0:
                return "N"
            elif 0<self.codMETAR.wind["direction"]<45:
                return "NNE"
            elif self.codMETAR.wind["direction"]==45:
                return "NE"
            elif 45<self.codMETAR.wind["direction"]<90:
                return "ENE"
            elif self.codMETAR.wind["direction"]==90:
                return "E"
            elif 90<self.codMETAR.wind["direction"]<135:
                return "ESE"
            elif self.codMETAR.wind["direction"]==135:
                return "SE"
            elif 135<self.codMETAR.wind["direction"]<180:
                return "SSE"
            elif self.codMETAR.wind["direction"]==180:
                return "S"
            elif 180<self.codMETAR.wind["direction"]<225:
                return "SSW"
            elif self.codMETAR.wind["direction"]==225:
                return "SW"
            elif 225<self.codMETAR.wind["direction"]<270:
                return "WSW"
            elif self.codMETAR.wind["direction"]==270:
                return "W"
            elif 270<self.codMETAR.wind["direction"]<315:
                return "WNW"
            elif self.codMETAR.wind["direction"]==315:
                return "NW"
            elif 315<self.codMETAR.wind["direction"]<360:
                return "NNW"
            elif self.codMETAR.wind["direction"]==360:
                return "N"        
            else:
                return "informacao ausente"

    def imprime_vento_VEL(self):
        #print(self.codMETAR.wind)
        #Velocidade em KT
        return self.codMETAR.wind["speed"]

    def imprime_vento_RAJ(self):
        #print(self.codMETAR.wind)
        #Rajadas em KT
        if self.codMETAR.wind["gust"] is not None:
            return self.codMETAR.wind["gust"]
        else:
            return "informacao ausente"

    def imprime_vento_VAR(self):
        #print(self.codMETAR.wind)
        #Variacao em graus
        if self.codMETAR.wind["variation"] is not None:
            return self.codMETAR.wind["variation"]
        else:
            return "informacao ausente"

    def imprime_nuvem(self):
        #print(self.codMETAR.cloud)
        return self.codMETAR.cloud        

    def imprime_temp(self):
        #print(self.codMETAR.temperatures["temperature"])
        #Em C
        return self.codMETAR.temperatures["temperature"]

    def imprime_tempPtoOrvalho(self):
        #print(self.codMETAR.temperatures["dewpoint"])
        return self.codMETAR.temperatures["dewpoint"]

    def imprime_PRES(self):
        #print(self.codMETAR.qnh)
        #Em mb que e equivalente a hPa
        return self.codMETAR.qnh

    def imprime_visi(self):
        #print(self.codMETAR.visibility)
        return self.codMETAR.visibility 

#rvr (tuple): Tuple of dictionaries with RVR information
#weather (dictionary): Dictionary of tuple with significant weather information
#properties(dictionary): Dictionary of attribute
#vmc(dictionnary):Dictionary of 2 booleans
#metar (string): Complete METAR message
#changements (string) : Changements
#auto (boolean): Define if a METAR isfrom an automatic station or not

    def imprime_rvr(self):
        #print(self.codMETAR.rvr)
        return self.codMETAR.rvr

    def imprime_tempo(self):
        #print(self.codMETAR.weather)
        return self.codMETAR.weather       

    def imprime_prop(self):
        #print(self.codMETAR.properties)
        return self.codMETAR.properties       
    
    def imprime_vmc(self):
        #print(self.codMETAR.vmc)
        return self.codMETAR.vmc

    def imprime_changements(self):
        #print(self.codMETAR.changements)
        return self.codMETAR.changements

    def imprime_estAuto(self):
        #print(self.codMETAR.auto)
        return self.codMETAR.auto

    def imprime_todosAtrib(self):
        #print(self.codMETAR.getAll())
        return self.codMETAR.getAll()


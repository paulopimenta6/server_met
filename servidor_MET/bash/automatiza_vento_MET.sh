#!/bin/bash

echo "=============================================================================="
echo "Automacao em Python para servidor MET" 
echo "=============================================================================="

mensagem_de_uso="$(basename "$0") [OPCOES]

	OPCOES:	   

	-h | --help	Mostra menu de ajuda \n
	-n | --nivel de altitude	Os niveis de altitude sao dados em niveis de pressao \n
	-r | --regiao	Regiao de interesse como SP, RJ, DF ou MN \n
	-ll | --lonlat	Dado uma lon (-180 a 180) e lat (-90 a 90) e definido uma regiao de interesse \n

	exemplos de uso: ./automatiza_semVarMETParam.sh -n 1000 -r SP
                         ./automatiza_semVarMETParam.sh -n 1000 -ll -56 -30

    OBS: Variaveis com nivel em superficie podem ter quaisquer nivel colocados que o valor final sera do nivel de superficie    	
"

if test -z "${1}"
then

    echo -e "${mensagem_de_uso}"
fi

if [ -n ${1} ] && [ ${1} == "-v" ] 
then
    if [ -n ${3} ] && [ ${3} == "-n" ]
    then        
        if  [ -n ${5} ]  && [ ${5} == "-r" ] 
        then            
            echo ${1} ${2} ${3} ${4} ${5} ${6}
            cd ../classes_MET/
            python3 gera_mapas_vento_MET.py ${1} ${2} ${3} ${4} ${5} ${6}
            python3 gera_matriz_vento_MET.py ${1} ${2} ${3} ${4} ${5} ${6} 
        #fi        
        elif [ -n ${5} ] && [ ${5} == "-ll" ] 
        then
            echo ${1} ${2} ${3} ${4} ${5} ${6} ${7}
            cd ../classes_MET/
            python3 gera_mapas_vento_MET.py ${1} ${2} ${3} ${4} ${5} ${6} ${7} 
            python3 gera_matriz_vento_MET.py ${1} ${2} ${3} ${4} ${5} ${6} ${7}   
        fi
    fi
    if [ -n ${3} ] && [ ${3} == "-ns" ]
    then
        if [ -n ${4} ] && [ ${4} == "-r" ]
        then 
            echo ${1} ${2} ${3} ${4} ${5}
            cd ../classes_MET/
            python3 gera_mapas_vento_MET.py ${1} ${2} ${3} ${4} ${5}
            python3 gera_matriz_vento_MET.py ${1} ${2} ${3} ${4} ${5}
        #fi
        elif [ -n ${4} ] && [ ${4} == "-ll" ]
        then
            echo ${1} ${2} ${3} ${4} ${5} ${6}
            cd ../classes_MET/
            python3 gera_mapas_vento_MET.py ${1} ${2} ${3} ${4} ${5} ${6} 
            python3 gera_matriz_vento_MET.py ${1} ${2} ${3} ${4} ${5} ${6} 
        fi
    fi  
fi

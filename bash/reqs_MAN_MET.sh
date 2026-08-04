#!/bin/bash

dir_executa_reqs="/media/MET/servidor_MET/classes_MET/executa_reqs_param.py"

echo "=============================================================================="
echo "Automacao em Python para servidor MET" 
echo "=============================================================================="

mensagem_de_uso="$(basename "$0") [OPCOES]

	OPCOES:	   

	-h | --help	Mostra menu de ajuda \n
	-v | --variavel		temp: Temperatura, temps: Temperatura em superficie, u: Componente do vento em \"x\", v: Componente do vento em \"y\", ps: Pressao em Superficie \n
	-n[s/hpa/f] | --nivel de altitude	Os niveis de altitude sao dados em: vazio (surface), niveis de pressao ou feet \n
        -altm[minhpa/maxhpa] | --intervalo de niveis de altitude em hPa
        -alt[minfeet/maxfeet] | --intervao de niveis de altitude em feet
	-lonmin/-lonmax/-latmin/-latmax | valores de min e max para longitude (-180 a 180) e latitude em graus (-90 a 90)  \n
        -datetime | data referente as informacoes MET requeridas. sempre no formato AAAAMMDD[ANAlise]ANAlise][PREVisao][PREVisao]
        -out | endereco de saida para os arquivos gerados (matrizes e mapas)

	 exemplos de uso: ./reqs_MAN_MET.sh -v winds -lonmin 3.75 -lonmax 6 -latmin 8 -latmax 9 -ns -datetime 202111020006 -out /home/phpimenta/
                          ./reqs_MAN_MET.sh -v temp -lonmin 3.75 -lonmax 6 -latmin 8 -latmax 9 -nhpa 500 -datetime 202111020006 -out /home/phpimenta/
                          ./reqs_MAN_MET.sh -v temp -lonmin 3.75 -lonmax 6 -latmin 8 -latmax 9 -nf 33999 -datetime 202111020006 -out /home/phpimenta/
                          ./reqs_MAN_MET.sh -v temp -lonmin 3.75 -lonmax  6 -latmin 8 -latmax 9 -altminhpa 500 -altmaxhpa 200 -datetime 202111020000 -out /home/phpimenta/

         OBS1: variaveis: ps, prnm, temp, temps, nuvem, chuva, umidadeRel, wind, winds
         OBS2: Variaveis com nivel em superficie podem ter quaisquer nivel colocados que o valor final sera do nivel de superficie    	
"

if test -z "${1}"
then

    echo -e "${mensagem_de_uso}"

fi

########################################################################
#Pegando a variavel MET
if test -n "${1}" && [[ "${1}" == "-v" ]]
then
    case "${1}" in
        -v) #A variavel MET de identificacao foi achada
            if test -n "${2}" #A variavel de valor da variavel MET sendo identificada
                then
                    echo "Variavel MET: ${2}"
            else
                echo "Variavel MET: Vazio"
                exit 0
            fi         
    esac
fi     

#Pegando lonmin
if test -n "${3}" && [[ "${3}" == "-lonmin" ]]
then
    case "${3}" in
        -lonmin) #A variavel de nivel de altitude sendo identificada
            if test -n "${4}"
                then
                    echo "lonmin: ${4}"
            else
                echo "Variavel lonmin: Vazio"
                exit 0
            fi
    esac
fi

#Pegando lonmax
if test -n "${5}" && [[ "${5}" == "-lonmax" ]]
then
    case "${5}" in
        -lonmax) #A variavel de nivel de altitude sendo identificada
            if test -n "${6}"
                then
                    echo "lonmax: ${6}"
            else
                echo "Variavel lonmin: Vazio"
                exit 0
            fi
    esac
fi

#Pegando latmin
if test -n "${7}" && [[ "${7}" == "-latmin" ]]
then
    case "${7}" in
        -latmin) #A variavel de nivel de altitude sendo identificada
            if test -n "${8}"
                then
                    echo "latmin: ${8}"
            else
                echo "Variavel lonmin: Vazio"
                exit 0
            fi
    esac
fi

#Pegando latmax
if test -n "${9}" && [[ "${9}" == "-latmax" ]]
then
    case "${9}" in
        -latmax) #A variavel de nivel de altitude sendo identificada
            if test -n "${10}"
                then
                    echo "latmax: ${10}"
            else
                echo "Variavel lonmin: Vazio"
                exit 0
            fi
    esac
fi

###Pegando o nivel de altitude
if test -n "${11}" && [[ "${11}" == "-nhpa" || "${11}" == "-nf" || "${11}" == "-ns" ]]
then
    case "${11}" in
        -nhpa) #A variavel de nivel de altitude sendo identificada
            if test -n "${12}"
                then
                    echo "Variavel nivel: ${12}"
                    flag=1
            fi
            ;;            
        -nf) #A variavel de nivel de altitude sendo identificada
            if test -n "${12}"
                then
                    echo "Variavel nivel: ${12}"
                    flag=1
            fi
            ;;
        -ns) #A variavel de nivel de altitude sendo identificada
            flag=2
            echo "Variavel nivel: superficie"            
    esac
fi

########################################################################
if [[ $flag == 1 ]]
then 
    #A partir daqui tudo fica relativo a ser em um indice n ou n+1...
    if test -n "${13}" && [[ "${13}" == "-datetime" ]]
    then
        case "${13}" in
	    -datetime) 
	        if test -n "${14}" 
	            then
	                echo "datetime: ${14}"
	        fi         
        esac
    fi

    if test -n "${15}" && [[ "${15}" == "-out" ]]
    then
        case "${15}" in
	    -out) 
	        if test -n "${16}" 
	            then
	                echo "caminho para salvar saida: ${16}"
	        fi         
        esac

    fi
   
    #rodar aqui com o python3
    python3 ${dir_executa_reqs} ${1} ${2} ${3} ${4} ${4} ${5} ${6} ${7} ${8} ${9} ${10} ${11} ${12} ${13} ${14} ${15} ${16} 

fi

if [[ $flag == 2 ]]
then
    if test -n "${12}" && [[ "${12}" == "-datetime" ]]
    then
        case "${12}" in
	    -datetime) 
	        if test -n "${13}" 
	            then
	                echo "datetime: ${13}"
	        fi         
        esac
    fi

    if test -n "${14}" && [[ "${14}" == "-out" ]]
    then
        case "${14}" in
	    -out) 
	        if test -n "${15}" 
	            then
	                echo "caminho para salvar saida: ${15}"
	        fi         
        esac
    fi

    #rodar aqui com o python3
    python3 ${dir_executa_reqs} ${1} ${2} ${3} ${4} ${4} ${5} ${6} ${7} ${8} ${9} ${10} ${11} ${12} ${13} ${14} ${15}

fi
########################################################################


########################################################################
###Pegando o intervalo do nivel de altitude em hPa
if test -n "${11}" && test -n "${13}" && [[ "${11}" == "-altminhpa" && "${13}" == "-altmaxhpa" ]] 
then
    case "${11}" in
        -altminhpa) #A variavel de nivel de altitude sendo identificada
            if test -n "${12}"
                then
                    echo "primeiro intervalo de nivel (hPa): ${12}"
                    flag=3
            fi
    esac
    case "${13}" in                    
        -altmaxhpa) #A variavel de nivel de altitude sendo identificada
            if test -n "${14}"
                then
                    echo "segundo intervalo de Variavel (hPa): ${14}"
                    flag=3
            fi
    esac
    if test -n "${15}" && [[ "${15}" == "-datetime" ]]
    then
        case "${15}" in
	    -datetime) 
	        if test -n "${16}" 
	            then
	                echo "datetime: ${16}"
	        fi         
        esac
    fi
    if test -n "${17}" && [[ "${17}" == "-out" ]]
    then
        case "${17}" in
	    -out) 
	        if test -n "${18}" 
	            then
	                echo "caminho para salvar saida: ${18}"
	        fi         
        esac
    fi    

    #rodar o codigo python3
    python3 ${dir_executa_reqs} ${1} ${2} ${3} ${4} ${4} ${5} ${6} ${7} ${8} ${9} ${10} ${11} ${12} ${13} ${14} ${15} ${16} ${17} ${18}
        
fi

###Pegando o intervalo do nivel de altitude em feet
if test -n "${11}" && test -n "${13}" && [[ "${11}" == "-altminfeet" && "${13}" == "-altmaxfeet" ]] 
then
    case "${11}" in
        -altminfeet) #A variavel de nivel de altitude sendo identificada
            if test -n "${12}"
                then
                    echo "primeiro intervalo de nivel (feet): ${12}"
                    flag=3
            fi
    esac
    case "${13}" in                    
        -altmaxfeet) #A variavel de nivel de altitude sendo identificada
            if test -n "${14}"
                then
                    echo "segundo intervalo de Variavel (feet): ${14}"
                    flag=3
            fi
    esac
    if test -n "${15}" && [[ "${15}" == "-datetime" ]]
    then
        case "${15}" in
	    -datetime) 
	        if test -n "${16}" 
	            then
	                echo "datetime: ${16}"
	        fi         
        esac
    fi
    if test -n "${17}" && [[ "${17}" == "-out" ]]
    then
        case "${17}" in
	    -out) 
	        if test -n "${18}" 
	            then
	                echo "caminho para salvar saida: ${18}"
	        fi         
        esac
    fi

    #rodar o codigo python3
    python3 ${dir_executa_reqs} ${1} ${2} ${3} ${4} ${4} ${5} ${6} ${7} ${8} ${9} ${10} ${11} ${12} ${13} ${14} ${15} ${16} ${17} ${18}
        
fi     
########################################################################

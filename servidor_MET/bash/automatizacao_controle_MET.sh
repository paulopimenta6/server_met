#!/bin/bash

#/media/utrecht/12382BE468602ECF/goGrib/bash/automatizacao_matrizes.sh
dir_principal="/media/MET/servidor_MET/"
dir_bash="bash"

data_ano=`date +"%Y"`
data_mes=`date +"%m"`
data_dia=`date +"%d"`

cd ${dir_principal}${dir_bash}

#Criar estrutura de diretorio para abrigar os dados de acordo com a localizacao
#############################
# matrizes e mapas de vento # 
#############################
./automatiza_vento_MET.sh "-v" "winds" "-r" "SP"
./automatiza_vento_MET.sh "-v" "winds" "-r" "RJ" 

./automatiza_vento_MET.sh "-v" "wind" "-n" "1000" "-r" "SP"
./automatiza_vento_MET.sh "-v" "wind" "-n" "1000" "-r" "RJ"

./automatiza_vento_MET.sh "-v" "wind" "-n" "200" "-r" "SP"
./automatiza_vento_MET.sh "-v" "wind" "-n" "200" "-r" "RJ"

#############################
#   temperatura em niveis   #
#############################
./automatiza_MET.sh "-v" "temp" "-n" "1000" "-r" "SP"
./automatiza_MET.sh "-v" "temp" "-n" "1000" "-r" "RJ"

#################################
#   temperatura em superficie   #
#################################
./automatiza_MET.sh "-v" "temps" "-ns" "-r" "SP"
./automatiza_MET.sh "-v" "temps" "-ns" "-r" "RJ"

################################
# pressao em superficie e prnm #
################################
#./automatiza_MET.sh "-v" "ps" "-ns" "-r" "SP"
./automatiza_MET.sh "-v" "prnm" "-ns" "-r" "SP"
#./automatiza_MET.sh "-v" "ps" "-ns" "-r" "RJ"
./automatiza_MET.sh "-v" "prnm" "-ns" "-r" "RJ"

######################################
#     nuvem e umidade relativa       # 
######################################
./automatiza_MET.sh "-v" "nuvem" "-n" "700" "-r" "SP"
./automatiza_MET.sh "-v" "nuvem" "-n" "500" "-r" "SP"
./automatiza_MET.sh "-v" "nuvem" "-n" "200" "-r" "SP"
./automatiza_MET.sh "-v" "umidadeRel" "-ns" "-r" "SP"

./automatiza_MET.sh "-v" "nuvem" "-n" "700" "-r" "RJ"
./automatiza_MET.sh "-v" "nuvem" "-n" "500" "-r" "RJ"
./automatiza_MET.sh "-v" "nuvem" "-n" "200" "-r" "RJ"
./automatiza_MET.sh "-v" "umidadeRel" "-ns" "-r" "RJ"

#############################
# matrizes e mapas de vento # 
#############################
./automatiza_vento_MET.sh "-n" "1000" "-r" "SP"
./automatiza_vento_MET.sh "-n" "200" "-r" "SP"
./automatiza_vento_MET.sh "-n" "1000" "-r" "RJ"
./automatiza_vento_MET.sh "-n" "200" "-r" "RJ"

#############################
# matrizes e mapas de chuva # 
#############################
./automatiza_MET.sh "-v" "chuvaConvec" "-ns" "-r" "SP"
./automatiza_MET.sh "-v" "chuvaConvec" "-ns" "-r" "RJ"
./automatiza_MET.sh "-v" "chuvaNaoConvec" "-ns" "-r" "SP"
./automatiza_MET.sh "-v" "chuvaNaoConvec" "-ns" "-r" "RJ"

exit 1

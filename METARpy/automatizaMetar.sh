#!/bin/bash

data_ano=`date +"%Y"`
data_mes=`date +"%m"`
data_dia=`date +"%d"`
dir="/media/MET/servidor_MET/METARpy"     
dirMetarJson=${data_ano}${data_mes}${data_dia}${data_hora}${data_min}

cd ${dir}
if test -d ${dir}/${dirMetarJson}
then 
    echo "O diretorio existe"
    cd ${dir}/${dirMetarJson}
    python3 ../METARpy.py
    python3 ../METARpy_traduzido.py
else
    echo "O diretorio nao existe..."
    echo "Criando diretorio..."
    mkdir ${dir}/${dirMetarJson}
    cd ${dir}/${dirMetarJson}
    python3 ../METARpy.py
    python3 ../METARpy_traduzido.py
fi

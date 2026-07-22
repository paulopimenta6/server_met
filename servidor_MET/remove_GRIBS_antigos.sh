#!/bin/bash

dir="/media/MET/servidor_MET/gribs"
dir_mapas="/media/MET/servidor_MET/mapasGrib"
dir_matrizes="/media/MET/servidor_MET/matrizGrib"
dir_matrizes_bluesky="/media/MET/servidor_MET/matrizGrib/bluesky"
dir_matrizes_predi="/media/MET/servidor_MET/matrizGrib/predi"

data_ano=`date +"%Y"`
data_mes=`date +"%m"`
#data_dia=`date +"%d"`
data_dia_anterior=`date -d "-2 days" +"%d"`

#data_completa="${data_ano}""${data_mes}""${data_dia}" 
data_final_anterior=${data_ano}${data_mes}${data_dia_anterior}

#diretorios de arquivos a serem removidos
data_final_anterior_mapas=${dir_mapas}/${data_final_anterior}
data_final_anterior_matrizes=${dir_matrizes}/${data_final_anterior}
data_final_anterior_matrizes_bluesky=${dir_matrizes_bluesky}/${data_final_anterior}
data_final_anterior_matrizes_predi=${dir_matrizes_predi}/${data_final_anterior}

echo "==============================================================="
echo "    verificando gribs    "
echo "Verificando a data anterior..." ${data_final_anterior}

cd ${dir}
if test -d "${data_final_anterior}"
then 
    echo "Os arquivos do diretorio ${data_final_anterior} existem e as analises de 0.25 serao removidas..."
    cd ${data_final_anterior}
    echo "diretorios com as analises de 0.25 no interior: " 
    ls
    for tAnalise in 00 06 12 18
    do
        if test -d "${tAnalise}"
        then    
            for tPrev in 00 06 12 18
            do
                if test -e ${tAnalise}/"gfs.t"${tAnalise}"z.pgrb2.0p25.f0"${tPrev}
                then 
                    rm ${tAnalise}/"gfs.t"${tAnalise}"z.pgrb2.0p25.f0"${tPrev}
                fi 
            done
        fi       
    done
else
    echo "O diretorio nao existe..."
    echo "Diretorios existentes contendo GRIBS: "
    ls    
fi
echo "==============================================================="

echo "==============================================================="
echo "    verificando mapas    "
echo "Verificando a data anterior..." ${data_final_anterior}

cd ${dir_mapas}
if test -d "${data_final_anterior_mapas}"
then 
    echo "Os arquivos de mapas do diretorio ${data_final_anterior} existem e serao removidas..."
    rm -r ${data_final_anterior_mapas}
else
    echo "O diretorio nao existe..."
    echo "Diretorios existentes de mapas: "
    ls    
fi
echo "==============================================================="

echo "==============================================================="
echo "    verificando matrizes    "
echo "Verificando a data anterior..." ${data_final_anterior}

cd ${dir_matrizes}
if test -d "${data_final_anterior_matrizes}"
then 
    echo "Os arquivos de matrizes do diretorio ${data_final_anterior} existem e serao removidas..."
    rm -r ${data_final_anterior_matrizes}
else
    echo "O diretorio nao existe..."
    echo "Diretorios existentes de matrizes: "
    ls    
fi
echo "==============================================================="

echo "==============================================================="
echo "    verificando matrizes bluesky    "
echo "Verificando a data anterior..." ${data_final_anterior}

cd ${dir_matrizes_bluesky}
if test -d "${data_final_anterior_matrizes_bluesky}"
then 
    echo "Os arquivos de matrizes bluesky do diretorio ${data_final_anterior} existem e serao removidas..."
    rm -r ${data_final_anterior_matrizes_bluesky}
else
    echo "O diretorio nao existe..."
    echo "Diretorios existentes de matrizes bluesky: "
    ls    
fi
echo "==============================================================="

echo "==============================================================="
echo "    verificando matrizes predi    "
echo "Verificando a data anterior..." ${data_final_anterior}

cd ${dir_matrizes_predi}
if test -d "${data_final_anterior_matrizes_predi}"
then 
    echo "Os arquivos de matrizes predi do diretorio ${data_final_anterior} existem e serao removidas..."
    rm -r ${data_final_anterior_matrizes_predi}
else
    echo "O diretorio nao existe..."
    echo "Diretorios existentes de matrizes predi: "
    ls    
fi
echo "==============================================================="

exit 1

#!/bin/bash
#SBATCH -t 0-0:30
#SBATCH -p short 
#SBATCH -J trigMov
#SBATCH -o eventTriggeredMovie_%j.log
#SBATCH -e eventTriggeredMovie_%j.log
#SBATCH -c 1
#SBATCH --mem=16G


frameIndexMat=$1
sessionMat=$2
frameOutMat=$3

echo "Exporting frames ${frameIndexMat} from ${sessionMat} to ${frameOutMat}."

module load matlab/2021a
matlab -batch "eventTriggeredMovieFileIO('${frameIndexMat}', '${sessionMat}', '${frameOutMat}')"

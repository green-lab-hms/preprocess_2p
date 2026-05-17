#!/bin/bash
#SBATCH -t 0-0:30
#SBATCH -p short 
#SBATCH -J vrmov
#SBATCH -o write_vr_movie_%j.log
#SBATCH -e write_vr_movie_%j.log
#SBATCH -c 1
#SBATCH --mem=8G

mouse=$1
date=$2
session=$3
trial=$4
fps=$5

echo "Writing VR movie for ${mouse} ${date} ${session} trail ${trial} at ${fps} frames per second."

source /n/app/conda2/etc/profile.d/conda.sh
conda activate mouse_imaging

python $CODE/preprocess_2p/write_vr_movie.py --mouse $mouse --date $date --session $session --trial $trial --fps $fps

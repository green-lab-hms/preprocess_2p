#!/bin/bash
#SBATCH -t 0-0:10
#SBATCH -p short 
#SBATCH -J update_ad
#SBATCH -o update_anndata_%j.log
#SBATCH -e update_anndata_%j.log
#SBATCH -c 1
#SBATCH --mem=16G

mouse=$1
date=$2
session=$3

source /n/app/conda2/etc/profile.d/conda.sh
conda activate mouse_imaging
echo "Updating anndata object for mouse ${mouse} date ${date} ${session}."
python $CODE/mouse_imaging/session.py --mouse $mouse --date $date --session $session --update


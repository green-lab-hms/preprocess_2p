#!/bin/bash
#SBATCH -t 0-12:00 # 0-6:30
#SBATCH -p redhat_test 
#SBATCH -J oasis
#SBATCH -o oasis_%j.log
#SBATCH -e oasis_%j.log
#SBATCH -c 1
#SBATCH --mem=8G

mouse=$1
date=$2
session=$3
ops=$4

echo "Performing OASIS deconvolution for ${mouse} ${date} ${session} with ops ${ops}."

module load conda/miniforge3
conda activate mouse_imaging

python $CODE/preprocess_2p/oasis_RHEL9.py --mouse $mouse --date $date --session $session --ops $ops

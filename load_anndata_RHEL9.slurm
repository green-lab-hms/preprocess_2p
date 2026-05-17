#!/bin/bash
#SBATCH -t 0-6:00
#SBATCH -p redhat_test 
#SBATCH -J anndata
#SBATCH -o load_anndata_%j.log
#SBATCH -e load_anndata_%j.log
#SBATCH -c 1
#SBATCH --mem=64G

mouse=$1
date=$2
session=$3
ops=$4

module load conda/miniforge3
conda activate mouse_imaging_RHEL9
echo "Loading anndata object for mouse ${mouse} date ${date} ${session} using ${ops} parameters."
python $CODE/mouse_imaging/session.py --mouse $mouse --date $date --session $session --ops $ops


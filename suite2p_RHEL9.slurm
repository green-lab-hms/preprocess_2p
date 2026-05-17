#!/bin/bash
#SBATCH -t 0-4:00
#SBATCH -p redhat_test 
#SBATCH -J suite2p
#SBATCH -o suite2p_%j.log
#SBATCH -e suite2p_%j.log
#SBATCH -c 4
#SBATCH --mem=64G

movPath=$1
ops=$2
module load conda/miniforge3
conda activate suite2p_RHEL9

echo "Running suite2p ROI extraction and trace deconvolution on $movPath with $ops."
python $CODE/preprocess_2p/suite2p_script_RHEL9.py $movPath $ops


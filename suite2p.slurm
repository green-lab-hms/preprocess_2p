#!/bin/bash
#SBATCH -t 0-4:00
#SBATCH -p short 
#SBATCH -J suite2p
#SBATCH -o suite2p_%j.log
#SBATCH -e suite2p_%j.log
#SBATCH -c 4
#SBATCH --mem=64G

movPath=$1
ops=$2
source /n/app/conda2/etc/profile.d/conda.sh
conda activate suite2p

echo "Running suite2p ROI extraction and trace deconvolution on $movPath with $ops."
python $CODE/preprocess_2p/suite2p_script.py $movPath $ops


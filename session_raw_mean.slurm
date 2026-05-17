#!/bin/bash
#SBATCH -J rawmean		# Job name
#SBATCH -o session_raw_mean_%j.log      # Standard out
#SBATCH -e session_raw_%j.log      # Standard error
#SBATCH -t 0-0:30       	# Runtime days-hours:minutes
#SBATCH -p priority		# Partition
#SBATCH -c 1    		# CPUs
#SBATCH --mem=64G     		# Memory

mouse=$1
date=$2
session=$3

source /n/app/conda2/etc/profile.d/conda.sh
conda activate suite2p

echo "Computing raw session mean for ${mouse} ${date} ${session}."

python $CODE/preprocess_2p/session_raw_mean.py --mouse $mouse --date $date --session $session

#!/bin/bash
#SBATCH -J demix		# Job name
#SBATCH -o demix_channel_%j.log      # Standard out
#SBATCH -e demix_channel_%j.log      # Standard error
#SBATCH -t 0-0:30       	# Runtime days-hours:minutes
#SBATCH -p redhat_test		# Partition
#SBATCH -c 1    		# CPUs
#SBATCH --mem=1G     		# Memory

tif_dir=$1
demix_chan=$2
donor_chan=$3

module load conda/miniforge3
conda activate suite2p

echo "Demixing channel ${demix_chan} using donor channel ${donor_chan} in directory ${tif_dir}."

python $CODE/preprocess_2p/demix_channel.py --tif_dir $tif_dir --demix_chan $demix_chan --donor_chan $donor_chan --filename *mean.tiff

#!/bin/bash
#SBATCH -J cellpose		# Job name
#SBATCH -o cellpose_%j.log      # Standard out
#SBATCH -e cellpose_%j.log      # Standard error
#SBATCH -t 0-1:00       	# Runtime days-hours:minutes
#SBATCH -p short		# Partition
#SBATCH -c 1    		# CPUs
#SBATCH --mem=16G     		# Memory

model=$1
channel=$2
dir=$3
img_filter=$4

# setup cellpose directory
cellpose_dir=$dir/cellpose/chan${channel}
mkdir -p $cellpose_dir
cp $dir/*${img_filter}.tif? $cellpose_dir/

source /n/app/conda2/etc/profile.d/conda.sh
conda activate cellpose-0.0.2.8

echo "Running cellpose on ${dir}, files ending in ${img_filter}, channel ${channel}, using model ${model}."
python -m cellpose --dir $cellpose_dir --pretrained_model $model --chan $channel --chan2 0 --diameter 14 --img_filter $img_filter

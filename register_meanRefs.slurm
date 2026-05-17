#!/bin/bash
#SBATCH -t 0-0:05
#SBATCH -p short
#SBATCH -J regmeanref
#SBATCH -o register_meanRefs_%j.log
#SBATCH -e register_meanRefs_%j.log
#SBATCH -c 1
#SBATCH --mem=8G

mouse=$1
date=$2
session=$3
ops=$4
image=$5
source_=$6
target=$7
ref_ichannel=$8

source /n/app/conda2/etc/profile.d/conda.sh
conda activate suite2p

echo "Registering meanRef for ${mouse} ${date} ${session} with ${ops} parameters."
echo "Registering ${image} using ${source_} as source and ${target} as target with ref_ichannel ${ref_ichannel}."

time python $CODE/preprocess_2p/register_meanRefs.py --mouse $mouse --date $date --session $session --ops $ops --image $image --source $source_ --target $target --ref_ichannel $ref_ichannel


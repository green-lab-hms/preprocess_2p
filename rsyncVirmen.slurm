#!/bin/bash
#SBATCH -t 0-1:00
#SBATCH -p transfer
#SBATCH -J rsync   
#SBATCH -c 1
#SBATCH --mem=1G

mouse=$1
date=$2
session=$3

source /n/app/conda2/etc/profile.d/conda.sh
conda activate suite2p

nfiles=$TIER1DATA
scratch=$SCRATCH
data2=$O2DATA
session_branch=$mouse/$date/$session
raw2p=$scratch/2P/$session_branch
meanRef_dir=$data2/$session_branch/meanRef

# Copy virmen (mat) file
mkdir -p $data2/$session_branch/virmen
rsync -vuziht $nfiles/Virmen/$session_branch/sessionData.mat $data2/$session_branch/virmen/

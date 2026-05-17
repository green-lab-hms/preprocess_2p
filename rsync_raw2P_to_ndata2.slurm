#!/bin/bash
#SBATCH -t 0-1:00
#SBATCH -p transfer
#SBATCH -J rsync   
#SBATCH -o rsync_%j.log
#SBATCH -e rsync_%j.log
#SBATCH -c 1
#SBATCH --mem=1G

mouse=$1
date=$2
session=$3

nfiles=$TIER1DATA
scratch=$SCRATCH
data2=$O2DATA
session_branch=$mouse/$date/$session

# Copy first ScanImage tif file
mkdir -p $data2/$session_branch/2P/filter2
rsync -vuziht $nfiles/2P/$session_branch/filter2/*_00001.tif $data2/$session_branch/2P/filter2/


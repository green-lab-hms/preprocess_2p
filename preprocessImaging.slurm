#!/bin/bash
#SBATCH -t 0-12:00
#SBATCH -p short
#SBATCH -J preprocess   
#SBATCH -c 1
#SBATCH --mem=32M
#SBATCH --mail-type=end

mouse=$1
date=$2
session=$3

nfiles=$TIER1DATA
scratch=$SCRATCH
data2=$O2DATA
session_branch=$mouse/$date/$session

# Transfer files to scratch
sbatch --wait $CODE/preprocess_2p/rsync.slurm 2P/$session_branch $nfiles $scratch
sbatch --wait $CODE/preprocess_2p/rsync.slurm Sync/$mouse/$date $nfiles $scratch
sbatch --wait $CODE/preprocess_2p/rsync.slurm Virmen/$session_branch $nfiles $scratch

# Motion correct (Acquisition_2P)
sbatch --wait $CODE/preprocess_2p/motionCorrect.slurm $scratch/2P/$session_branch

# Extract ROIs and deconvolve traces (Suite2P)
sbatch --wait $CODE/preprocess_2p/suite2p.slurm $scratch/2P/$session_branch

# Transfer processed data back to nfiles
sbatch $CODE/preprocess_2p/rsync.slurm 2P/$session_branch $scratch $nfiles
sbatch $CODE/preprocess_2p/rsync.slurm $session_branch $data2 $nfiles/Preprocessed

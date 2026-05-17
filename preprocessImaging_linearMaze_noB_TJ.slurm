#!/bin/bash
#SBATCH -t 2-0:00
#SBATCH -p medium
#SBATCH -J preprocess   
#SBATCH -c 1
#SBATCH --mem=64M

mouse=$1
date=$2
session=$3

source /n/app/conda2/etc/profile.d/conda.sh

nfiles=$TIER1DATA
scratch=$SCRATCH
data2=$O2DATA
session_branch=$mouse/$date/$session
raw2p=$scratch/2P/$session_branch
meanRef_dir=$data2/$session_branch/meanRef

echo "Processing ${mouse} ${date} ${session} with G1R1 pipeline."

# Transfer files to scratch
sbatch --wait $CODE/preprocess_2p/rsync_ssh.slurm 2P/$session_branch $nfiles $scratch

# Motion correct (Acquisition_2P)
sbatch --wait $CODE/preprocess_2p/motionCorrect.slurm -c Green -r $scratch/2P/$session_branch

# Copy meanRef composite tifs to ndata2
mkdir -p $meanRef_dir/filter1; cp $raw2p/Corrected/*mean.tiff $meanRef_dir/filter1/

# Call cellpose args: model channel preprocessed_dir filter
model=/n/data2/hms/neurobio/harvey/jonathan/data/imaging/cellpose_models/cellpose_False_images_2_2020_06_08_03_03_45.183249
sbatch --wait $CODE/preprocess_2p/cellpose.slurm $model 3 $meanRef_dir/filter1 mean

# Extract ROIs (Suite2P)
sbatch --wait $CODE/preprocess_2p/suite2p.slurm $scratch/2P/$session_branch SstCreRFP_linearMaze_ops

# Deconvolve ROI traces (baseline subtraction + OASIS)
sbatch --wait $CODE/preprocess_2p/oasis.slurm $mouse $date $session maximin_baseline_ops

# Transfer data to ndata2 
sbatch --wait $CODE/preprocess_2p/rsync_ndata2_ssh.slurm $mouse $date $session

# Load anndata
sbatch --wait $CODE/preprocess_2p/load_anndata.slurm $mouse $date $session SstCreRFP_linearMaze_ops

# Sync back to nfiles
sbatch $CODE/preprocess_2p/rsync_ssh.slurm 2P/$session_branch $scratch $nfiles
#sbatch $CODE/preprocess_2p/rsync_ssh.slurm $session_branch $data2 $nfiles/Preprocessed


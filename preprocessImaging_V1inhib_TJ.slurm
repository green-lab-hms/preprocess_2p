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
sbatch --wait $CODE/preprocess_2p/rsync_ssh.slurm 2P/$session_branch $nfiles $scratch

# Motion correct (Acquisition_2P)
sbatch --wait $CODE/preprocess_2p/motionCorrect.slurm -c Red -r $scratch/2P/$session_branch

# Copy meanRef composite tifs to ndata2
mkdir -p $meanRef_dir/filter1; cp $raw2p/Corrected/*mean.tiff $meanRef_dir/filter1/
for dir in $raw2p/filter*/; do filter2_dir=$(basename $dir); mkdir -p $meanRef_dir/$filter2_dir; cp $raw2p/$filter2_dir/Corrected/*mean.tiff $meanRef_dir/$filter2_dir/; done

# Extract ROIs (Suite2P)
sbatch --wait $CODE/preprocess_2p/suite2p.slurm $scratch/2P/$session_branch jRGECO_Sst44GFP_ops

# Deconvolve ROI traces (baseline subtraction + OASIS)
sbatch --wait $CODE/preprocess_2p/oasis.slurm $mouse $date $session jRGECO_Sst44GFP_ops

# Transfer data to ndata2 
sbatch --wait $CODE/preprocess_2p/rsync_ndata2_ssh_V1inhibition.slurm $mouse $date $session

# Load anndata
sbatch --wait $CODE/preprocess_2p/load_anndata.slurm $mouse $date $session jRGECO_Sst44GFP_ops

# Sync back to nfiles
sbatch $CODE/preprocess_2p/rsync_ssh.slurm 2P/$session_branch $scratch $nfiles

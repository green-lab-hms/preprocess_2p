#!/bin/bash
#SBATCH -t 0-3:00
#SBATCH -p short
#SBATCH -J rsync   
#SBATCH -o rsync_%j.log
#SBATCH -e rsync_%j.log
#SBATCH -c 1
#SBATCH --mem=128M

mouse=$1
date=$2
session=$3

nfiles=$TIER1DATA
scratch=$SCRATCH
data2=$O2DATA
session_branch=$mouse/$date/$session

# Copy sync (abf) file
mkdir -p $data2/$session_branch/sync
$CODE/preprocess_2p/rsync_ssh.sh $nfiles/Sync/$mouse/$date/session_000${session: -1}.* $data2/$session_branch/sync/

# Copy virmen (mat) file
mkdir -p $data2/$session_branch/virmen
$CODE/preprocess_2p/rsync_ssh.sh $nfiles/Virmen/$session_branch/sessionData.mat $data2/$session_branch/virmen/

# Copy first ScanImage tif file
mkdir -p $data2/$session_branch/2P
$CODE/preprocess_2p/rsync_ssh.sh $nfiles/2P/$session_branch/session_*_00001.tif $data2/$session_branch/2P/


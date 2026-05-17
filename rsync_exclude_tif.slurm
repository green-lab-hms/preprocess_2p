#!/bin/bash
#SBATCH -t 0-6:00
#SBATCH -p transfer
#SBATCH -J rsync   
#SBATCH -o rsync_%j.log
#SBATCH -e rsync_%j.log
#SBATCH -c 1
#SBATCH --mem=1G

session_branch=$1
from_root=$2
to_root=$3

mkdir -p $to_root/$session_branch
echo "from:" $from_root/$session_branch
echo "to:" $to_root/$session_branch
rsync -rlDvuziht --exclude '*.tif' $from_root/$session_branch/ $to_root/$session_branch

# Copy first tif file for metadata
for f in $from_root/$session_branch/*.tif; do
    cp "$f" $to_root/$session_branch/
    break
done

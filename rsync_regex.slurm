#!/bin/bash
#SBATCH -t 0-12:00
#SBATCH -p transfer
#SBATCH -J rsync   
#SBATCH -o rsync_%j.log
#SBATCH -e rsync_%j.log
#SBATCH -c 1
#SBATCH --mem=1G

session_branch=$1
from_root=$2
to_root=$3
regex=$4

mkdir -p $to_root/$session_branch
echo "from:" $from_root/$session_branch
echo "to:" $to_root/$session_branch
rsync -rlDvuziht $from_root/$session_branch/$regex $to_root/$session_branch

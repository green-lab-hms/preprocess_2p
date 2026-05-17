#!/bin/bash
#SBATCH -t 0-11:30
#SBATCH -p redhat_test
#SBATCH -J rsync
#SBATCH -o rsync_%j.log
#SBATCH -e rsync_%j.log
#SBATCH -c 1
#SBATCH --mem=128M

session_branch=$1
from_root=$2
to_root=$3

mkdir -p $to_root/$session_branch
echo "from:" $from_root/$session_branch
echo "to:" $to_root/$session_branch

while ! ssh transfer rsync -rlDvuziht $from_root/$session_branch/ $to_root/$session_branch
do
   echo "command failed try again in 10 min"
   sleep 10m
done

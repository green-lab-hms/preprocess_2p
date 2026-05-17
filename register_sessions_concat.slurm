#!/bin/bash
#SBATCH -t 0-0:10
#SBATCH -p short
#SBATCH -J regcat
#SBATCH -o register_sessions_concat_%j.log
#SBATCH -e register_sessions_concat_%j.log
#SBATCH -c 1
#SBATCH --mem=1G

mouse=$1
dates=$2
min_corr=$3
source /n/app/conda2/etc/profile.d/conda.sh
conda activate suite2p

echo "Concatenating source registrations across planes for ${mouse} dates ${dates}."
python $CODE/preprocess_2p/register_sessions.py --mouse $mouse --dates $dates --plane concatenate --min_corr $min_corr

